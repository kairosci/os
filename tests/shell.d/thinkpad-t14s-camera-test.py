"""Check the ThinkPad T14s camera setup."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from base_test import ROOT, test_environment


class ThinkPadT14sCameraTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory()
    self.addCleanup(self.temporary.cleanup)
    self.scratch = Path(self.temporary.name)
    self.bin = self.scratch / "bin"
    self.bin.mkdir()
    self.rule = self.scratch / "etc/udev/rules.d/70-thinkpad-t14s-camera.rules"
    self.package_log = self.scratch / "packages"
    self.environment = test_environment(
      SCRATCH=self.scratch,
      PACKAGE_LOG=self.package_log,
      TEST_SOC="qualcomm",
      TEST_MODEL="21N10000US",
    )
    self.environment["PATH"] = f"{self.bin}:{ROOT / 'src/commands'}:{self.environment['PATH']}"
    self._executable("arch-hw-aarch64-qualcomm", 'raise SystemExit(0 if os.environ["TEST_SOC"] == "qualcomm" else 1)\n')
    self._executable(
      "arch-hw-match",
      'raise SystemExit(0 if re.search(sys.argv[1], os.environ["TEST_MODEL"], re.IGNORECASE) else 1)\n',
      imports="import re\nimport sys\n",
    )
    self._executable(
      "arch-pkg-add",
      'Path(os.environ["PACKAGE_LOG"]).write_text(" ".join(sys.argv[1:]) + "\\n", encoding="utf-8")\n',
      imports="from pathlib import Path\nimport sys\n",
    )

  def _executable(self, name: str, body: str, *, imports: str = "") -> None:
    path = self.bin / name
    path.write_text(
      "#!/usr/bin/python3 -I\nimport os\n" + imports + body,
      encoding="utf-8",
    )
    path.chmod(0o755)

  def _run(self) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
      ["/usr/bin/python3", "-I", str(ROOT / "src/python/installer/hardware/lenovo/thinkpad_t14s_camera.py")],
      check=False,
      capture_output=True,
      text=True,
      env=self.environment,
    )

  def _reset(self) -> None:
    self.package_log.unlink(missing_ok=True)
    self.rule.unlink(missing_ok=True)

  def test_setup_is_scoped_and_repeatable(self) -> None:
    for soc in ("qualcomm", "other"):
      for model in ("21N10000US", "21N20000US", "83ED", "21F60000US"):
        with self.subTest(soc=soc, model=model):
          self._reset()
          self.environment.update(TEST_SOC=soc, TEST_MODEL=model)
          result = self._run()
          self.assertEqual(result.returncode, 0, result.stderr)
          if soc == "qualcomm" and re.match(r"^21N[12]", model, re.IGNORECASE):
            self.assertEqual(self.package_log.read_text(encoding="utf-8"), "pipewire-libcamera\n")
            self.assertEqual(
              self.rule.read_bytes(),
              (ROOT / "default/udev/thinkpad-t14s-camera.rules").read_bytes(),
            )
            self.assertEqual(self.rule.stat().st_mode & 0o777, 0o644)
            result = self._run()
            self.assertEqual(result.returncode, 0, result.stderr)
          else:
            self.assertFalse(self.package_log.exists())
            self.assertFalse(self.rule.exists())

    rule = "\n".join(
      line for line in (ROOT / "default/udev/thinkpad-t14s-camera.rules").read_text(encoding="utf-8").splitlines()
      if line and not line.startswith("#")
    )
    self.assertEqual(rule, 'SUBSYSTEM=="dma_heap", KERNEL=="system", TAG+="uaccess"')
    self.assertIn(
      "pipewire-libcamera",
      (ROOT / "installer/arch-other.packages").read_text(encoding="utf-8").splitlines(),
    )


if __name__ == "__main__":
  unittest.main()
