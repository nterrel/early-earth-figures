#!/usr/bin/env python3
"""Read version-bound figure feedback and close verified requests through gh."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import gallery_discussion_titles as titles

FIGURES = Path(__file__).resolve().parents[1]
REPOSITORY = 'nterrel/early-earth-figures'
CONFIG = FIGURES / 'metadata/gallery_comments.json'
STATUS = FIGURES / 'metadata/gallery_feedback_status.json'
GIT = '/mnt/c/Users/nick_/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'


def cli_environment(use_git_credential):
    environment = dict(os.environ)
    if use_git_credential and not environment.get('GH_TOKEN') and not environment.get('GITHUB_TOKEN'):
        # Capture the existing Git credential in memory; never print or save it.
        credential = subprocess.run([GIT, 'credential', 'fill'],
            input='protocol=https\nhost=github.com\n\n', text=True,
            capture_output=True, env=dict(environment, GCM_INTERACTIVE='Never'), check=True)
        fields = dict(line.split('=', 1) for line in credential.stdout.splitlines() if '=' in line)
        environment['GH_TOKEN'] = fields['password']
    return environment


def graphql(query, variables, environment):
    executable = shutil.which('gh') or str(FIGURES / 'build/tools/gh')
    request = json.dumps({'query': query, 'variables': variables})
    result = subprocess.run([executable, 'api', 'graphql', '--input', '-'],
        input=request, text=True, capture_output=True, env=environment)
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    response = json.loads(result.stdout)
    if response.get('errors'):
        raise RuntimeError(response['errors'])
    return response['data']


def discussions(environment):
    query = '''query($after:String){viewer{login} repository(owner:"nterrel",name:"early-earth-figures"){
      viewerPermission hasDiscussionsEnabled discussions(first:100,after:$after){
      pageInfo{hasNextPage endCursor} nodes{id number title body url closed viewerCanClose viewerCanReopen
      category{id name} comments{totalCount}}}}}'''
    items, cursor = [], None
    while True:
        data = graphql(query, {'after': cursor}, environment)
        repository = data['repository']
        items.extend(repository['discussions']['nodes'])
        page = repository['discussions']['pageInfo']
        if not page['hasNextPage']:
            return data['viewer']['login'], repository, items
        cursor = page['endCursor']


def write_status(items):
    category = json.loads(CONFIG.read_text())['category_id']
    selected = [item for item in items if item['category']['id'] == category
                and titles.identify(item)]
    record = {'schema_version': 1, 'repository': REPOSITORY,
              'checked_utc': datetime.now(timezone.utc).isoformat(),
              'threads': {titles.identify(item): {'number': item['number'], 'url': item['url'], 'closed': item['closed']}
                          for item in selected}}
    STATUS.write_text(json.dumps(record, indent=2) + '\n')
    return selected


def read_thread(number, environment):
    query = '''query($number:Int!,$after:String){repository(owner:"nterrel",name:"early-earth-figures"){
      discussion(number:$number){id number title url closed body comments(first:100,after:$after){
      pageInfo{hasNextPage endCursor} nodes{id body url author{login} replies(first:100){
      pageInfo{hasNextPage endCursor} nodes{id body url author{login}}}}}}}}'''
    cursor, comments = None, []
    while True:
        data = graphql(query, {'number': number, 'after': cursor}, environment)['repository']['discussion']
        if data is None:
            raise RuntimeError('Discussion not found')
        for comment in data['comments']['nodes']:
            replies = comment['replies']
            reply_items = replies['nodes']
            while replies['pageInfo']['hasNextPage']:
                reply_data = graphql('''query($id:ID!,$after:String){node(id:$id){... on DiscussionComment{
                  replies(first:100,after:$after){pageInfo{hasNextPage endCursor} nodes{id body url author{login}}}}}}''',
                  {'id': comment['id'], 'after': replies['pageInfo']['endCursor']}, environment)
                replies = reply_data['node']['replies']
                reply_items.extend(replies['nodes'])
            comment['replies'] = reply_items
            comments.append(comment)
        page = data['comments']['pageInfo']
        if not page['hasNextPage']:
            data['comments'] = comments
            return data
        cursor = page['endCursor']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['list', 'read', 'sync', 'close', 'reopen', 'rename-titles'])
    parser.add_argument('--number', type=int)
    parser.add_argument('--verified-change', help='Checked correction receipt or commit; required to close')
    parser.add_argument('--use-git-credential', action='store_true', help='Reuse signed-in Git credentials in memory')
    parser.add_argument('--site', type=Path, help='Refresh the closed-thread snapshot in a prepared gallery')
    args = parser.parse_args()
    if args.site:
        import prepare_pages
        site = args.site.resolve()
        site.relative_to(FIGURES)
        prepare_pages.check(site, verify_sources=False)
        for package in (site, site/'supplement'):
            config = json.loads(re.search(r'id="gallery-comment-config">(.*?)</script>', (package/'index.html').read_text())[1])
            if config.get('feedback_status_url') != 'feedback_status.json':
                raise RuntimeError('Build this gallery with the updated comments interface first')
    environment = cli_environment(args.use_git_credential)
    login, repository, items = discussions(environment)
    if args.command in ('read', 'close', 'reopen') and args.number is None:
        parser.error('--number is required')
    if args.command == 'read':
        print(json.dumps(read_thread(args.number, environment), indent=2))
        return
    if args.command in ('close', 'reopen'):
        item = next((item for item in items if item['number'] == args.number), None)
        if not item or item['category']['id'] != json.loads(CONFIG.read_text())['category_id'] or not titles.identify(item):
            raise RuntimeError('Only exact version-bound figure review discussions can be changed')
        if args.command == 'close' and not args.verified_change:
            parser.error('--verified-change is required; close only after the correction is checked')
        capability = 'viewerCanClose' if args.command == 'close' else 'viewerCanReopen'
        if not item[capability]:
            raise RuntimeError('The signed-in account cannot perform this action')
        mutation = 'closeDiscussion' if args.command == 'close' else 'reopenDiscussion'
        reason = ',reason:RESOLVED' if args.command == 'close' else ''
        graphql(f'mutation($id:ID!){{{mutation}(input:{{discussionId:$id{reason}}}){{discussion{{number closed}}}}}}',
                {'id': item['id']}, environment)
        audit = FIGURES/'build/feedback-actions.jsonl'
        audit.parent.mkdir(exist_ok=True)
        with audit.open('a') as handle:
            handle.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(), 'action':args.command,
                                    'number':item['number'], 'term':item['title'], 'verified_change':args.verified_change})+'\n')
        login, repository, items = discussions(environment)
    if args.command == 'rename-titles':
        registry = titles.entries()
        category = json.loads(CONFIG.read_text())['category_id']
        for item in items:
            identity = titles.identify(item, registry)
            if item['category']['id'] != category or identity not in registry:
                continue
            title = registry[identity]['title']
            if title == item['title']:
                continue
            # Keep body, strict-match markers, replies, number and closure state.
            graphql('mutation($id:ID!,$title:String!){updateDiscussion(input:{discussionId:$id,title:$title}){discussion{number title}}}',
                    {'id': item['id'], 'title': title}, environment)
        login, repository, items = discussions(environment)
    selected = write_status(items) if args.command != 'list' else items
    if args.site and args.command != 'list':
        import gallery_comments
        import export_share
        for package in (site, site/'supplement'):
            shutil.copy2(STATUS, package/'feedback_status.json')
            gallery_comments.bind_generated(package, site)
        manifest_path = site/'pages_manifest.json'
        manifest = json.loads(manifest_path.read_text())
        for entry in manifest['files']:
            path = site/entry['path']
            entry.update(sha256=export_share.digest(path), bytes=path.stat().st_size)
        manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'viewer': login, 'permission': repository['viewerPermission'],
        'discussions_enabled': repository['hasDiscussionsEnabled'],
        'open': [item for item in selected if not item['closed']],
        'status_file': str(STATUS) if args.command != 'list' else None}, indent=2))


if __name__ == '__main__':
    main()
