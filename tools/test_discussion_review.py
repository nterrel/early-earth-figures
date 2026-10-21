"""Offline controls for public feedback reduction and paginated GitHub reads."""
import copy
import hashlib
import json
import unittest

import discussion_review as review


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.figures = {str(i): {'term': 'term-' + str(i), 'source_group': 'source-' + str(i), 'version': 'art-' + str(i), 'title': 'Figure ' + str(i)} for i in range(35)}
        self.policy = {'repository': 'nterrel/early-earth-figures', 'curators': ['nterrel', 'roitberg'], 'selection_goal': {'discussion': 'about 20–30', 'enforced': False}}
        self.source = {'repository': self.policy['repository'], 'threads': []}

    def post(self, key, body, author='roitberg', updated=None, minimized=False):
        thread = next((t for t in self.source['threads'] if t['identity'] == 'term-' + key), None)
        if thread is None:
            thread = {'identity': 'term-' + key, 'number': int(key) + 1, 'url': 'https://github.com/nterrel/early-earth-figures/discussions/' + str(int(key) + 1), 'closed': False, 'comments': []}
            self.source['threads'].append(thread)
        index = sum(len(t['comments']) for t in self.source['threads'])
        date = updated or '2026-10-21T00:%02d:%02dZ' % divmod(index, 60)
        comment = {'id': str(index), 'url': thread['url'] + '#discussioncomment-' + str(index), 'createdAt': date, 'updatedAt': date,
                   'body': body, 'author': {'login': author}, 'isMinimized': minimized}
        thread['comments'].append(comment)
        return comment

    def result(self):
        return review.compile_review(self.figures, self.source, self.policy)

    def test_curators_only_and_public_notes_ratings_edit_replaces(self):
        self.post('0', 'Meeting: priority', author='visitor')
        self.post('0', 'A useful public note', author='visitor')
        self.post('0', 'Rating: 2', author='visitor')
        self.post('0', 'Rating: 5', author='Visitor')
        self.post('0', 'Rating: 3', author='roitberg')
        self.assertEqual(self.result()['figures']['0']['state'], 'unreviewed')
        self.assertEqual(self.result()['figures']['0']['rating'], {'count': 2, 'average': 4.0})
        self.post('0', 'Meeting: priority\nExplain the panel.', author='RoItBeRg')
        data = self.result()['figures']['0']
        self.assertEqual(data['state'], 'priority')
        self.assertEqual([n['body'] for n in data['notes']], ['A useful public note', 'Explain the panel.'])

    def test_goals_do_not_block_selection_and_demotion(self):
        for i in range(12):
            self.post(str(i), 'Meeting: priority')
        data = self.result()
        self.assertEqual(sum(e['state'] == 'priority' for e in data['figures'].values()), 12)
        self.assertEqual(len(data['ignored']), 0)
        for i in range(12, 35):
            self.post(str(i), 'Meeting: discuss')
        self.assertEqual(sum(e['state'] in ('priority', 'discuss') for e in self.result()['figures'].values()), 35)
        self.assertFalse(self.result()['selection_goal']['enforced'])
        self.post('0', 'Meeting: later')
        self.post('34', 'Meeting: priority')
        self.assertEqual(self.result()['figures']['34']['state'], 'priority')

    def test_same_second_ratings_use_numeric_comment_order(self):
        for _ in range(12):
            self.post('0', 'Rating: 2', updated='2026-10-21T00:00:00Z')
        self.post('0', 'Rating: 5', updated='2026-10-21T00:00:00Z')
        self.assertEqual(self.result()['figures']['0']['rating'], {'count': 1, 'average': 5.0})

    def test_move_hide_restore_and_notes_preserved(self):
        for i in range(3):
            self.post(str(i), 'Meeting: discuss')
        self.post('1', 'Meeting: up')
        self.assertLess(self.result()['figures']['1']['position'], self.result()['figures']['0']['position'])
        self.post('1', 'Meeting: hidden\nSet aside for now.')
        self.post('1', 'Meeting: discuss')
        self.assertEqual(self.result()['figures']['1']['notes'][0]['body'], 'Set aside for now.')

    def test_edits_deletions_old_artwork_and_minimized_comments(self):
        old = self.post('0', 'Meeting: priority')
        later = self.post('0', 'Meeting: hidden')
        self.assertEqual(self.result()['figures']['0']['state'], 'hidden')
        old['updatedAt'] = '2026-10-21T01:00:00Z'
        self.assertEqual(self.result()['figures']['0']['state'], 'priority')
        old['isMinimized'] = True
        self.assertEqual(self.result()['figures']['0']['state'], 'hidden')
        self.source['threads'][0]['comments'].remove(later)
        self.assertEqual(self.result()['figures']['0']['state'], 'unreviewed')
        self.post('0', 'Meeting: discuss')
        self.figures['0']['term'] = 'new-artwork'
        self.assertEqual(self.result()['figures']['0']['state'], 'unreviewed')

    def test_untrusted_text_is_data_and_permalink_is_checked(self):
        self.post('0', '<script>bad()</script>\nMeeting: priority', author='nterrel')
        self.assertEqual(self.result()['figures']['0']['state'], 'unreviewed')
        self.assertIn('<script>', self.result()['figures']['0']['notes'][0]['body'])
        self.source['threads'][0]['comments'][0]['url'] = 'javascript:bad()'
        with self.assertRaises(ValueError): self.result()

    def test_all_comment_reply_and_thread_pages_are_read(self):
        identity = 'Early Earth figure review | ' + 'a' * 64 + ' | ' + 'b' * 64
        figures = {'key': {'term': identity}}
        comment = {'id': 'C1', 'body': 'One', 'url': 'url', 'createdAt': 'date', 'updatedAt': 'date', 'isMinimized': False, 'author': {'login': 'roitberg'}}
        def connection(nodes, more=False, cursor=None):
            return {'nodes': nodes, 'pageInfo': {'hasNextPage': more, 'endCursor': cursor}}
        calls = []
        def call(query, variables):
            calls.append(variables)
            if 'discussions(first' in query:
                if variables['after']:
                    return {'repository': {'isPrivate': False, 'hasDiscussionsEnabled': True, 'discussions': connection([])}}
                thread = {'id': 'D1', 'number': 1, 'title': identity, 'body': '', 'url': 'thread', 'closed': False, 'category': {'id': json.loads((review.FIGURES/'metadata/gallery_comments.json').read_text())['category_id']}}
                return {'repository': {'isPrivate': False, 'hasDiscussionsEnabled': True, 'discussions': connection([thread], True, 'T2')}}
            if 'comments(first' in query:
                if variables['after']:
                    return {'repository': {'discussion': {'comments': connection([])}}}
                c = copy.deepcopy(comment); c['replies'] = connection([dict(comment, id='R1')], True, 'R2')
                return {'repository': {'discussion': {'comments': connection([c], True, 'C2')}}}
            return {'node': {'replies': connection([dict(comment, id='R2')])}}
        source = review.fetch_source(figures, '', call)
        self.assertEqual([c['id'] for c in source['threads'][0]['comments']], ['C1', 'R1', 'R2'])
        self.assertEqual(len(calls), 5)


if __name__ == '__main__':
    unittest.main()
