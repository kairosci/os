"""Check the ThinkPad T14s camera setup and its existing migration."""

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
    self.udev_log = self.scratch / "udev"
    self.environment = test_environment(
      SCRATCH=self.scratch,
      PACKAGE_LOG=self.package_log,
      UDEV_LOG=self.udev_log,
      TEST_SOC="qualcomm",
      TEST_MODEL="21N10000US",
    )
    self.environment["PATH"] = f"{self.bin}:{ROOT / 'src/cli'}:{self.environment['PATH']}"
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
    self._executable(
      "sudo",
      self._sudo_stub(),
      imports="from pathlib import Path\nimport subprocess\nimport sys\n",
    )

  def _executable(self, name: str, body: str, *, imports: str = "") -> None:
    path = self.bin / name
    path.write_text(
      "#!/usr/bin/python3 -I\nimport os\n" + imports + body,
      encoding="utf-8",
    )
    path.chmod(0o755)

  def _sudo_stub(self) -> str:
    return '''arguments = sys.argv[1:]
if arguments[0] == "udevadm":
  with Path(os.environ["UDEV_LOG"]).open("a", encoding="utf-8") as log:
    log.write(" ".join(arguments) + "\\n")
elif arguments[0] == "install":
  destination = Path(os.environ["SCRATCH"]) / arguments[-1].lstrip("/")
  subprocess.run(["install", *arguments[1:-1], str(destination)], check=True)
else:
  raise SystemExit(f"unexpected privileged command: {arguments!r}")
'''

  def _run(self, name: str) -> subprocess.CompletedProcess[str]:
    if name == "setup":
      command = ["/usr/bin/python3", "-I", str(ROOT / "src/python/installer/hardware/lenovo/thinkpad_t14s_camera.py")]
    else:
      command = ["/usr/bin/python3", "-I", str(ROOT / "migrations/1791080527.py")]
    return subprocess.run(command, check=False, capture_output=True, text=True, env=self.environment)

  def _reset(self) -> None:
    self.package_log.unlink(missing_ok=True)
    self.udev_log.unlink(missing_ok=True)
    self.rule.unlink(missing_ok=True)

  def test_setup_and_migration_are_scoped_and_repeatable(self) -> None:
    for entry in ("setup", "migration"):
      for soc in ("qualcomm", "other"):
        for model in ("21N10000US", "21N20000US", "83ED", "21F60000US"):
          with self.subTest(entry=entry, soc=soc, model=model):
            self._reset()
            self.environment.update(TEST_SOC=soc, TEST_MODEL=model)
            result = self._run(entry)
            self.assertEqual(result.returncode, 0, result.stderr)
            if soc == "qualcomm" and re.match(r"^21N[12]", model, re.IGNORECASE):
              self.assertEqual(self.package_log.read_text(encoding="utf-8"), "pipewire-libcamera\n")
              self.assertEqual(
                self.rule.read_bytes(),
                (ROOT / "default/udev/thinkpad-t14s-camera.rules").read_bytes(),
              )
              self.assertEqual(self.rule.stat().st_mode & 0o777, 0o644)
              if entry == "migration":
                self.assertIn(
                  "udevadm trigger --action=add --subsystem-match=dma_heap --sysname-match=system",
                  self.udev_log.read_text(encoding="utf-8"),
                )
              else:
                self.assertFalse(self.udev_log.exists())
              result = self._run(entry)
              self.assertEqual(result.returncode, 0, result.stderr)
              self.assertEqual(
                self.rule.read_bytes(),
                (ROOT / "default/udev/thinkpad-t14s-camera.rules").read_bytes(),
              )
            else:
              self.assertFalse(self.package_log.exists())
              self.assertFalse(self.rule.exists())
              self.assertFalse(self.udev_log.exists())

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
