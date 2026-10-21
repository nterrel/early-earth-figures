#!/usr/bin/env python3
"""Read public Discussions and compile the current version-bound shared review.

GitHub is authoritative. This code never posts or edits a discussion. Workflows
hold the read token; it is never written into the published snapshot.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request

import export_share
import gallery_discussion_titles

FIGURES = Path(__file__).resolve().parents[1]
POLICY = FIGURES / 'metadata/discussion_review_policy.json'


def configs(site):
    result = {}
    for collection in (site, site / 'supplement'):
        page = (collection / 'index.html').read_text()
        result.update(json.loads(re.search(r'id="gallery-comment-config">(.*?)</script>', page)[1])['figures'])
    return result


def graphql(query, variables, token):
    request = urllib.request.Request('https://api.github.com/graphql',
        data=json.dumps({'query': query, 'variables': variables}).encode(),
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', 'User-Agent': 'early-earth-figure-review'})
    with urllib.request.urlopen(request, timeout=45) as response:
        data = json.load(response)
    if data.get('errors'):
        raise RuntimeError('GitHub Discussions read failed: ' + str(data['errors']))
    return data['data']


def fetch_source(figures, token, call=None):
    call = call or (lambda query, variables: graphql(query, variables, token))
    category = json.loads((FIGURES / 'metadata/gallery_comments.json').read_text())['category_id']
    identities = {f.get('identity_term', f['term']) for f in figures.values()}
    registry = {f.get('identity_term', f['term']): {} for f in figures.values()}
    query = '''query($after:String){repository(owner:"nterrel",name:"early-earth-figures"){
      isPrivate hasDiscussionsEnabled discussions(first:100,after:$after){pageInfo{hasNextPage endCursor}
      nodes{id number title body url closed category{id}}}}}'''
    threads, after = [], None
    while True:
        repository = call(query, {'after': after})['repository']
        if repository['isPrivate'] or not repository['hasDiscussionsEnabled']:
            raise RuntimeError('Public Discussions are not available; keep the prior deployment')
        connection = repository['discussions']
        for item in connection['nodes']:
            identity = gallery_discussion_titles.identify(item, registry)
            if item['category']['id'] != category or identity not in identities:
                continue
            item['identity'] = identity
            comments, cursor = [], None
            while True:
                comment_query = '''query($number:Int!,$after:String){repository(owner:"nterrel",name:"early-earth-figures"){
                  discussion(number:$number){comments(first:100,after:$after){pageInfo{hasNextPage endCursor}
                  nodes{id body url createdAt updatedAt isMinimized author{login} replies(first:100){
                  pageInfo{hasNextPage endCursor} nodes{id body url createdAt updatedAt isMinimized author{login}}}}}}}}'''
                data = call(comment_query, {'number': item['number'], 'after': cursor})['repository']['discussion']
                if data is None:
                    raise RuntimeError('Discussion changed during the read; retry the workflow')
                page = data['comments']
                for comment in page['nodes']:
                    replies = comment.pop('replies')
                    if comment.get('isMinimized'):
                        # Do not republish replies hidden under a minimized parent.
                        continue
                    comments.append(comment)
                    comments.extend(replies['nodes'])
                    while replies['pageInfo']['hasNextPage']:
                        reply_query = '''query($id:ID!,$after:String){node(id:$id){... on DiscussionComment{
                          replies(first:100,after:$after){pageInfo{hasNextPage endCursor}
                          nodes{id body url createdAt updatedAt isMinimized author{login}}}}}'''
                        replies = call(reply_query, {'id': comment['id'], 'after': replies['pageInfo']['endCursor']})['node']['replies']
                        comments.extend(replies['nodes'])
                if not page['pageInfo']['hasNextPage']:
                    break
                cursor = page['pageInfo']['endCursor']
            item['comments'] = comments
            threads.append(item)
        if not connection['pageInfo']['hasNextPage']:
            break
        after = connection['pageInfo']['endCursor']
    return {'schema_version': 1, 'repository': 'nterrel/early-earth-figures', 'threads': threads}


def compile_review(figures, source, policy):
    if source['repository'] != policy['repository']:
        raise ValueError('Feedback repository differs from selected policy')
    identities = {entry.get('identity_term', entry['term']): key for key, entry in figures.items()}
    entries = {key: {'state': 'unreviewed', 'position': 0, 'notes': [],
                     'rating': {'count': 0, 'average': None}} for key in figures}
    events, seen = [], set()
    threads = {}
    for thread in source['threads']:
        key = identities.get(thread['identity'])
        if not key:
            continue
        previous = threads.get(thread['identity'])
        if previous is None or not thread['closed']:
            threads[thread['identity']] = {'number': thread['number'], 'url': thread['url'], 'closed': thread['closed'] and (previous is None or previous['closed'])}
        for comment in thread['comments']:
            if comment['id'] in seen or comment.get('isMinimized') or not comment.get('author'):
                continue
            if not re.fullmatch(r'https://github\.com/nterrel/early-earth-figures/discussions/\d+#discussioncomment-\d+', comment['url']):
                raise ValueError('Unexpected feedback permalink')
            seen.add(comment['id'])
            # GitHub timestamps have second precision; numeric permalink IDs
            # keep two posts in the same second in creation order.
            events.append((comment['updatedAt'], int(comment['url'].rsplit('-', 1)[1]), key, comment))
    events.sort()
    curators = {login.casefold() for login in policy['curators']}
    ratings, ignored, rank = {}, [], 0
    for _, _, key, comment in events:
        entry = entries[key]
        author = comment['author']['login']
        text = comment['body'].strip()
        first = text.splitlines()[0] if text else ''
        state_match = re.fullmatch(r'Meeting:\s*(priority|discuss|later|hidden|unreviewed|up|down)', first, re.I)
        rating_match = re.fullmatch(r'Rating:\s*([1-5])', first, re.I)
        if state_match and author.casefold() in curators:
            target = state_match[1].lower()
            if target in ('up', 'down'):
                if entry['state'] in ('priority', 'discuss'):
                    ordered = sorted((k for k in entries if entries[k]['state'] == entry['state']), key=lambda k: (entries[k]['position'], k))
                    index = ordered.index(key)
                    neighbor = index + (-1 if target == 'up' else 1)
                    if 0 <= neighbor < len(ordered):
                        ordered[index], ordered[neighbor] = ordered[neighbor], ordered[index]
                        for position, selected_key in enumerate(ordered, 1):
                            entries[selected_key]['position'] = position
            else:
                others = [value['state'] for k, value in entries.items() if k != key]
                overflow = (target == 'priority' and others.count('priority') >= policy['limits']['priority']) or (
                    target in ('priority', 'discuss') and sum(s in ('priority', 'discuss') for s in others) >= policy['limits']['discussion'])
                if overflow:
                    ignored.append({'key': key, 'url': comment['url'], 'reason': 'Selection limit reached; set another figure aside first.'})
                else:
                    if target != entry['state']:
                        rank = max([rank, *(v['position'] for v in entries.values())]) + 1
                        entry['position'] = rank
                    entry['state'] = target
                    entry['updated_by'] = author
                    entry['updated'] = datetime.fromisoformat(comment['updatedAt'].replace('Z', '+00:00')).timestamp()
                    entry['selection_url'] = comment['url']
        elif state_match:
            ignored.append({'key': key, 'url': comment['url'], 'reason': 'Only configured curators change the shared selection.'})
        if rating_match:
            ratings[(key, author.casefold())] = int(rating_match[1])
        # Commands remain readable in GitHub; ordinary text and command notes
        # are shown with attribution and a direct link to their authoritative post.
        body = '\n'.join(text.splitlines()[1:]).strip() if state_match or rating_match else text
        if body:
            entry['notes'].append({'id': comment['id'], 'reviewer': author, 'body': body[:10000],
                'truncated': len(body) > 10000, 'url': comment['url'],
                'created': datetime.fromisoformat(comment['createdAt'].replace('Z', '+00:00')).timestamp()})
    for key, entry in entries.items():
        values = [value for (rating_key, _), value in ratings.items() if rating_key == key]
        entry['rating'] = {'count': len(values), 'average': sum(values) / len(values) if values else None}
    source_hash = hashlib.sha256(json.dumps(source, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'schema_version': 1, 'repository': policy['repository'], 'revision': source_hash,
            'generated_utc': datetime.now(timezone.utc).isoformat(), 'limits': policy['limits'],
            'curators': policy['curators'], 'figures': entries, 'threads': threads, 'ignored': ignored,
            'metadata': {key: {'source_group': value['source_group'], 'artwork_sha256': value['version'],
                              'title': value['title'], 'reference': value.get('discussion_title', value['title'])}
                         for key, value in figures.items()}}


def bind_snapshot(site, snapshot):
    """Change generated feedback files only; immutable artwork records stay exact."""
    path = site / 'review_state.json'
    path.write_text(json.dumps(snapshot, indent=2) + '\n')
    for package in (site, site / 'supplement'):
        manifest_path = package / 'export_manifest.json'
        manifest = json.loads(manifest_path.read_text())
        generated = {entry['path']: entry for entry in manifest['generated_files']}
        if package == site:
            generated['review_state.json'] = {'path': 'review_state.json'}
        status_path = package / 'feedback_status.json'
        if status_path.exists():
            status_path.write_text(json.dumps({'schema_version': 1, 'repository': snapshot['repository'],
                'checked_utc': snapshot['generated_utc'], 'threads': snapshot['threads']}, indent=2) + '\n')
        for entry in generated.values():
            entry['sha256'] = export_share.digest(package / entry['path'])
        manifest['generated_files'] = list(generated.values())
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    master_path = site / 'pages_manifest.json'
    master = json.loads(master_path.read_text())
    master['files'] = [{'path': p.relative_to(site).as_posix(), 'sha256': export_share.digest(p), 'bytes': p.stat().st_size}
                       for p in sorted(site.rglob('*')) if p.is_file() and p != master_path]
    master_path.write_text(json.dumps(master, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path, required=True)
    parser.add_argument('--source', type=Path, help='Previously fetched source for offline compilation')
    parser.add_argument('--save-source', type=Path)
    parser.add_argument('--use-git-credential', action='store_true')
    args = parser.parse_args()
    figures = configs(args.site)
    if args.source:
        source = json.loads(args.source.read_text())
    else:
        environment = os.environ
        if args.use_git_credential:
            import gallery_feedback
            environment = gallery_feedback.cli_environment(True)
        token = environment.get('GH_TOKEN') or environment.get('GITHUB_TOKEN')
        if not token:
            parser.error('A read token is required for GitHub synchronization')
        source = fetch_source(figures, token)
    if args.save_source:
        args.save_source.write_text(json.dumps(source, indent=2) + '\n')
    snapshot = compile_review(figures, source, json.loads(POLICY.read_text()))
    bind_snapshot(args.site, snapshot)
    print(json.dumps({'revision': snapshot['revision'], 'figures': len(figures), 'notes': sum(len(e['notes']) for e in snapshot['figures'].values()),
                      'review_state_sha256': export_share.digest(args.site / 'review_state.json')}))


if __name__ == '__main__':
    main()
