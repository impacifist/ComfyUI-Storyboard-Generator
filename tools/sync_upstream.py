"""Import an explicit engine/UI revision, without copying private or generated files."""

import argparse
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path

DESTINATION = Path(__file__).resolve().parents[1] / "_vendor"
UPSTREAM = "https://github.com/impacifist/ai-video-storyboard-generator"
PATHS = ["storyboard", "docs/guides", "web", "examples/rainy-classroom.json"]


def sync(repository, revision):
    commit = subprocess.check_output(["git", "-C", repository, "rev-parse", revision + "^{commit}"], text=True).strip()
    manifest = DESTINATION / "upstream.json"
    if manifest.exists():
        old = json.loads(manifest.read_text(encoding="utf-8"))
        for name, digest in old["files"].items():
            path = DESTINATION / name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise RuntimeError("Vendor snapshot has local changes: " + name)
    archive = subprocess.check_output(["git", "-C", repository, "archive", commit, "--", *PATHS])
    files = {}
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for item in tar.getmembers():
            if item.isdir():
                continue
            path = DESTINATION / item.name
            if not item.isfile() or not path.resolve().is_relative_to(DESTINATION.resolve()):
                raise RuntimeError("Unexpected archive entry")
            data = tar.extractfile(item).read()
            files[item.name] = hashlib.sha256(data).hexdigest()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    manifest.write_text(json.dumps({"repository": UPSTREAM, "commit": commit, "files": files}, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {len(files)} tracked files at {commit}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", help="Local checkout of the upstream repository")
    parser.add_argument("revision", help="Explicit tag or commit; never implicitly follows main")
    args = parser.parse_args()
    sync(args.repository, args.revision)
