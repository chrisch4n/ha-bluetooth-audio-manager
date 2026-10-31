"""The add-on folder's copy of the sources must match src/ and docker/.

This branch is built locally by the Supervisor with the add-on folder as
Docker context, so src/, docker/rootfs and the Dockerfile are copied into
it by tools/sync-addon-build.sh.  If someone edits src/ and forgets to
re-sync, the app on the box silently runs old code.
"""

import filecmp
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADDON = ROOT / "bluetooth_audio_manager"
IGNORE = ["__pycache__"]


def _diff(left: Path, right: Path) -> list[str]:
    cmp = filecmp.dircmp(left, right, ignore=IGNORE)
    problems = [f"only in {left.name}: {n}" for n in cmp.left_only]
    problems += [f"only in copy: {n}" for n in cmp.right_only]
    _, mismatch, errors = filecmp.cmpfiles(left, right, cmp.common_files, shallow=False)
    problems += [f"differs: {left / n}" for n in mismatch + errors]
    for sub in cmp.common_dirs:
        problems += _diff(left / sub, right / sub)
    return problems


@unittest.skipUnless((ADDON / "src").is_dir(), "no local-build copy in this checkout")
class AddonBuildContextTest(unittest.TestCase):
    msg = "run tools/sync-addon-build.sh"

    def test_sources_in_sync(self):
        self.assertEqual(_diff(ROOT / "src", ADDON / "src"), [], self.msg)

    def test_rootfs_in_sync(self):
        self.assertEqual(_diff(ROOT / "docker" / "rootfs", ADDON / "rootfs"), [], self.msg)

    def test_requirements_and_build_in_sync(self):
        for name in ("requirements.txt", "build.yaml"):
            with self.subTest(name=name):
                self.assertEqual(
                    (ROOT / "docker" / name).read_text(),
                    (ADDON / name).read_text(),
                    self.msg,
                )

    def test_dockerfile_matches_with_local_copy_paths(self):
        expected = (
            (ROOT / "docker" / "Dockerfile").read_text()
            .replace("COPY docker/requirements.txt ", "COPY requirements.txt ")
            .replace("COPY docker/rootfs /", "COPY rootfs /")
        )
        self.assertEqual((ADDON / "Dockerfile").read_text(), expected, self.msg)

    def test_config_has_no_prebuilt_image(self):
        # With "image:" set the Supervisor would pull scyto's image instead
        # of building these patches.
        config = (ADDON / "config.yaml").read_text().splitlines()
        self.assertFalse([l for l in config if l.startswith("image:")])


if __name__ == "__main__":
    unittest.main()
