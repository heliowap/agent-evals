"""Behavioral tests through the package's public task/audit/fixture interfaces."""

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tasks.web.verify import ROOT, VerificationError, candidate_tasks, fixture_packet, verify


class WebTasksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_packets = [fixture_packet(f'W{i:02}', kind)
                               for i in range(1, 13)
                               for kind in ('correct', 'wrong', 'omitted', 'unsupported', 'contradictory', 'alternative')]

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='webtasks-')
        self.root = Path(self.temp.name)
        for relative in ('tasks/web', 'gold/web', 'contracts'):
            shutil.copytree(ROOT / relative, self.root / relative)

    def tearDown(self):
        self.temp.cleanup()

    def change_json(self, relative, change):
        path = self.root / relative
        data = json.loads(path.read_text())
        change(data)
        path.write_text(json.dumps(data))

    def test_frozen_package_passes_public_audit(self):
        result = verify(self.root)
        self.assertEqual(result['tasks'], 12)
        self.assertEqual(result['sources'], 19)
        self.assertEqual(result['fixtures'], 72)

    def test_candidate_view_works_without_gold_or_sources(self):
        shutil.rmtree(self.root / 'gold')
        tasks = candidate_tasks(self.root)
        self.assertEqual(len(tasks), 12)
        self.assertNotIn('reference_answer', repr(tasks))
        self.assertNotIn('https://', repr(tasks))

    def test_candidate_answer_leak_is_rejected(self):
        self.change_json('tasks/web/tasks.json', lambda tasks: tasks[0].update(reference_answer='3.10'))
        with self.assertRaisesRegex(VerificationError, 'question-only'):
            candidate_tasks(self.root)

    def test_candidate_url_leak_is_rejected(self):
        self.change_json('tasks/web/tasks.json', lambda tasks: tasks[0].update(
            prompt=tasks[0]['prompt'] + ' https://docs.djangoproject.com/en/5.2/faq/install/'))
        with self.assertRaisesRegex(VerificationError, 'contains a URL'):
            candidate_tasks(self.root)

    def test_raw_archive_tampering_is_rejected(self):
        path = self.root / 'gold/web/sources/django-install.raw'
        path.write_bytes(path.read_bytes() + b'changed')
        with self.assertRaisesRegex(VerificationError, 'raw hash mismatch'):
            verify(self.root)

    def test_extracted_archive_tampering_is_rejected(self):
        path = self.root / 'gold/web/sources/postgres-policy.txt'
        path.write_text(path.read_text().replace('November 9, 2028', 'November 9, 2029'))
        with self.assertRaisesRegex(VerificationError, 'text hash mismatch'):
            verify(self.root)

    def test_paraphrase_is_not_accepted_as_an_exact_quote(self):
        self.change_json('gold/web/gold.json', lambda gold: gold['W01']['units'][3]['evidence'][0].update(
            quote='Only the newest Python patch release is officially supported.'))
        with self.assertRaisesRegex(VerificationError, 'quote absent'):
            verify(self.root)

    def test_wrong_source_hash_reference_is_rejected(self):
        self.change_json('gold/web/gold.json', lambda gold: gold['W01']['units'][0]['evidence'][0].update(
            hash_reference='gold/web/sources/manifest.json#node-schedule.text_sha256'))
        with self.assertRaisesRegex(VerificationError, 'hash reference'):
            verify(self.root)

    def test_outside_source_path_is_rejected(self):
        self.change_json('gold/web/gold.json', lambda gold: gold['W01']['units'][0]['evidence'][0].update(
            path='contracts/runtime.json'))
        with self.assertRaisesRegex(VerificationError, 'outside web sources'):
            verify(self.root)

    def test_missing_fixture_kind_is_rejected(self):
        self.change_json('gold/web/gold.json', lambda gold: gold['W08']['fixtures'].pop())
        with self.assertRaisesRegex(VerificationError, 'six fixture kinds'):
            verify(self.root)

    def test_hidden_unit_weight_is_rejected(self):
        self.change_json('gold/web/gold.json', lambda gold: gold['W04']['units'][0].update(weight=10))
        with self.assertRaisesRegex(VerificationError, 'hidden weighting'):
            verify(self.root)

    def test_missing_route_evidence_is_rejected(self):
        self.change_json('tasks/web/author_routes.json', lambda routes: routes['routes']['W12']['fetches'][1].update(limit=1000))
        with self.assertRaisesRegex(VerificationError, 'omits scored evidence'):
            verify(self.root)

    def test_over_budget_route_is_rejected(self):
        self.change_json('tasks/web/author_routes.json', lambda routes: routes['routes']['W01'].update(
            search_queries=['one'] * 5))
        with self.assertRaisesRegex(VerificationError, 'search route over budget'):
            verify(self.root)

    def test_archived_quote_index_cannot_be_silently_changed(self):
        self.change_json('gold/web/sources/evidence-index.json', lambda index: index['spans'][0].update(start_line=1))
        with self.assertRaisesRegex(VerificationError, 'spans/hash index mismatch'):
            verify(self.root)

    def test_w09_default_removal_requires_no_unasked_opt_out_flag(self):
        task = next(task for task in candidate_tasks(self.root) if task['id'] == 'W09')
        # The frozen gold JSON is the documented oracle interface, not a grader's internals.
        entry = json.loads((self.root / 'gold/web/gold.json').read_text())['W09']
        unit = next(unit for unit in entry['units'] if unit['id'] == 'U3')
        self.assertNotIn('--inexact', task['prompt'])
        self.assertTrue(unit['essential'])
        self.assertNotRegex(unit['description'], r'--[a-z][a-z0-9-]*')
        for answer in (entry['reference_answer'], fixture_packet('W09', 'correct', self.root)['answer']):
            self.assertNotIn('--inexact', answer)
            self.assertRegex(answer, r'exact.*default.*remov')
        packet = fixture_packet('W09', 'correct', self.root)
        label = next(label for label in packet['expected_units'] if label['id'] == 'U3')
        self.assertTrue(label['correct'] and label['supported'])
        self.assertTrue(any(span['unit_id'] == 'U3' and 'remove any packages' in span['quote']
                            for span in packet['evidence']))

    def test_all_six_answer_fixtures_per_task_have_explicit_grounding_labels(self):
        self.assertEqual(len(self.fixture_packets), 72)
        for packet in self.fixture_packets:
            with self.subTest(task=packet['task_id'], kind=packet['kind']):
                labels = packet['expected_units']
                self.assertTrue(packet['answer'])
                if packet['kind'] in ('correct', 'alternative'):
                    self.assertTrue(all(unit['correct'] and unit['supported'] for unit in labels))
                    self.assertFalse(packet['expected_critical_errors'])
                    self.assertTrue(packet['evidence'])
                elif packet['kind'] == 'unsupported':
                    self.assertTrue(all(unit['correct'] and not unit['supported'] for unit in labels))
                    self.assertEqual(packet['evidence'], [])
                else:
                    self.assertTrue(any(not unit['correct'] for unit in labels))
                    self.assertTrue(packet['evidence'])
                    self.assertEqual(bool(packet['expected_critical_errors']), packet['kind'] != 'omitted')


if __name__ == '__main__':
    unittest.main()
