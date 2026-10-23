import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from support import ROOT, service
from storyboard_addon import clip_snapshot, nodes
from tools import build_demo


class DemoBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / 'dist').mkdir(exist_ok=True)
        cls.temporary = tempfile.TemporaryDirectory(prefix='demo-test-', dir=ROOT / 'dist')
        cls.destination = Path(cls.temporary.name)
        with patch.object(service.providers, 'generate_json', side_effect=AssertionError('No AI in a static build')), \
             patch.object(service.providers, 'load_settings', side_effect=AssertionError('Do not read private settings')), \
             contextlib.redirect_stdout(io.StringIO()):
            cls.data = build_demo.build(cls.destination)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_build_is_allowlisted_and_has_all_languages_without_private_files(self):
        self.assertEqual({p.name for p in self.destination.iterdir()}, set(build_demo.ASSETS) | {'data.json', '.nojekyll'})
        self.assertEqual(set(self.data['samples']), {'en', 'ko', 'ja'})
        self.assertEqual(len(self.data['engine_commit']), 40)
        for sample in self.data['samples'].values():
            self.assertEqual(len(sample['variants']), 6)

    def test_real_snapshots_survive_browser_numeric_round_trip_and_output_original_dialogue(self):
        for sample in self.data['samples'].values():
            source = sample['document']['story']['shots']
            for key, bundle in sample['variants'].items():
                with self.subTest(key=key):
                    self.assertEqual(sum(c['duration'] for c in bundle['clips']), 30)
                    self.assertEqual([s for c in bundle['clips'] for s in c['source_shots']], [s['id'] for s in source])
                    combined = '\n'.join(c['prompt'] for c in bundle['clips'])
                    for shot in source:
                        for line in shot['dialogue']:
                            self.assertIn(line['text'], combined)
                    for clip in bundle['clips']:
                        self.assertIs(type(clip['duration']), int)
                        encoded = json.dumps(clip, ensure_ascii=False)
                        clip_snapshot.decode_snapshot(encoded)
                        self.assertEqual(nodes.StoryboardClipPrompt().output_clip(encoded),
                                         (clip['prompt'], float(clip['duration']), clip['clip_id']))

    def test_target_syntax_is_assembled_by_the_shared_formatter(self):
        sample = self.data['samples']['en']['variants']
        self.assertIn('<d>', sample['minimax-h3-text:15']['clips'][0]['prompt'])
        self.assertIn('{Still raining.}', sample['seedance-2-text:15']['clips'][0]['prompt'])
        self.assertNotIn('[Shot', sample['ltx-2.5-text:15']['clips'][0]['prompt'])
        self.assertIn('Still raining.', sample['ltx-2.5-text:15']['clips'][0]['prompt'])

    def test_build_refuses_other_repository_or_private_output_paths(self):
        for path in (ROOT, ROOT / 'storage/demo', ROOT.parent / 'demo-output'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                build_demo.build(path)
