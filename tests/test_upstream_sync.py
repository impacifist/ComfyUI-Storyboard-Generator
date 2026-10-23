import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import sync_upstream


class UpstreamSyncTests(unittest.TestCase):
    def test_archive_is_canonical_even_when_source_config_enables_windows_line_endings(self):
        with tempfile.TemporaryDirectory(prefix='storyboard-sync-test-') as folder:
            root = Path(folder)
            source, destination = root / 'source', root / 'vendor'
            source.mkdir()
            destination.mkdir()

            def git(*args):
                return subprocess.check_output(['git', '-C', str(source), *args], stderr=subprocess.STDOUT)

            git('init')
            git('config', 'core.autocrlf', 'true')
            files = {'storyboard/example.py': b'value = "sample"\n',
                     'docs/guides/example.md': b'# Sample\n', 'web/example.js': b'"use strict";\n',
                     'examples/rainy-classroom.json': b'{}\n'}
            for name, content in files.items():
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            git('add', '.')
            git('-c', 'user.name=Sample test', '-c', 'user.email=test@example.invalid', 'commit', '-m', 'Sample')
            with patch.object(sync_upstream, 'DESTINATION', destination), contextlib.redirect_stdout(io.StringIO()):
                sync_upstream.sync(str(source), 'HEAD')
                # A subsequent sync still verifies the previous manifest before updating.
                sync_upstream.sync(str(source), 'HEAD')
            metadata = json.loads((destination / 'upstream.json').read_text())
            for name, content in files.items():
                self.assertEqual((destination / name).read_bytes(), content)
                self.assertEqual(metadata['files'][name], hashlib.sha256(content).hexdigest())
