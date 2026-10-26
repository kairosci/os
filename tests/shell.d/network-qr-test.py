"""Verify Wi-Fi QR encoding without querying the host network or printer."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
COMMAND = ROOT / "src/cli/arch-network-qr"
EXPECTED_MATRIX = "100\n010\n001"


class NetworkQrTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="network-qr-")
        self.stage = Path(self.temporary.name)
        self.bin_dir = self.stage / "bin"
        self.bin_dir.mkdir()
        self.payload_file = self.stage / "payload"
        self._write_stub(
            "ip",
            "#!/usr/bin/python3\n"
            "import os, sys\n"
            "if os.environ.get('QR_ROUTE_EXIT', '0') != '0':\n"
            "    raise SystemExit(int(os.environ['QR_ROUTE_EXIT']))\n"
            "print('1.1.1.1 dev lo')\n",
        )
        self._write_stub(
            "nmcli",
            "#!/usr/bin/python3\n"
            "import os, sys\n"
            "args = ' '.join(sys.argv[1:])\n"
            "if 'DEVICE,TYPE,STATE' in args:\n"
            "    print('eth0:ethernet:connected\\nwlan0:wifi:connected')\n"
            "elif 'GENERAL.CON-UUID' in args:\n"
            "    print('test-uuid')\n"
            "else:\n"
            "    sys.stdout.write(os.environ.get('QR_NMCLI_FIELDS', ''))\n",
        )
        self._write_stub(
            "qrencode",
            "#!/usr/bin/python3\n"
            "import os, sys\n"
            "if any(arg.startswith('WIFI:') for arg in sys.argv[1:]):\n"
            "    raise SystemExit(97)\n"
            "payload = sys.stdin.read()\n"
            "with open(os.environ['QR_PAYLOAD_FILE'], 'w', encoding='utf-8') as output:\n"
            "    output.write(payload)\n"
            "sys.stdout.write('##    \\n  ##  \\n    ##\\n')\n",
        )
        self.environment = os.environ.copy()
        self.environment.update(
            ARCH_PATH=str(ROOT),
            LANG="en_US.UTF-8",
            LC_ALL="en_US.UTF-8",
            PATH=f"{self.bin_dir}:{ROOT / 'src/cli'}:{self.environment.get('PATH', '')}",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_stub(self, name: str, source: str) -> None:
        path = self.bin_dir / name
        path.write_text(source, encoding="utf-8")
        path.chmod(0o700)

    def run_qr(self, fields: str, *args: str, route_exit: str = "0") -> subprocess.CompletedProcess[str]:
        self.payload_file.unlink(missing_ok=True)
        environment = self.environment.copy()
        environment.update(
            QR_NMCLI_FIELDS=fields,
            QR_PAYLOAD_FILE=str(self.payload_file),
            QR_ROUTE_EXIT=route_exit,
        )
        return subprocess.run(
            [str(COMMAND), *args],
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def assert_success_case(
        self,
        fields: str,
        expected_payload: str,
        *args: str,
        interface: str = "wlan0",
        metadata: bool = True,
        route_exit: str = "0",
    ) -> None:
        result = self.run_qr(fields, *args, route_exit=route_exit)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = result.stdout
        if metadata:
            header, matrix = output.split("\n", 1)
            security = expected_payload.removeprefix("WIFI:T:").split(";", 1)[0]
            ssid = fields.splitlines()[0]
            self.assertEqual(header, f"meta\t{interface}\t{security}\t{ssid}")
        else:
            matrix = output
        self.assertEqual(matrix.rstrip("\n"), EXPECTED_MATRIX)
        self.assertEqual(self.payload_file.read_text(encoding="utf-8"), expected_payload)

    def test_wifi_payload_encoding_interface_detection_and_enterprise_refusal(self) -> None:
        escaped_fields = "Cafe;Guest\\5G\nwpa-psk\np,a:ss;word\\42\nno\n"
        escaped_payload = r"WIFI:T:WPA;S:Cafe\;Guest\\5G;P:p\,a\:ss\;word\\42;;"
        self.assert_success_case(escaped_fields, escaped_payload, "--meta", "wlan0")
        self.assert_success_case(escaped_fields, escaped_payload, "wlan0", metadata=False)
        self.assert_success_case(
            "Cafe Detected\nwpa-psk\nsecret\nno\n",
            "WIFI:T:WPA;S:Cafe Detected;P:secret;;",
            "--meta",
        )
        self.assert_success_case(
            "Cafe No Route\nwpa-psk\nsecret\nno\n",
            "WIFI:T:WPA;S:Cafe No Route;P:secret;;",
            "--meta",
            route_exit="2",
        )
        self.assert_success_case(
            "Cafe Open\nnone\n\nno\n",
            "WIFI:T:nopass;S:Cafe Open;P:;;",
            "--meta",
            "wlan0",
        )
        self.assert_success_case(
            "Hidden Network\nwpa-psk\nsecret\nyes\n",
            "WIFI:T:WPA;S:Hidden Network;P:secret;H:true;;",
            "--meta",
            "wlan0",
        )
        self.assert_success_case(
            "Old Router\nnone\n\nno\nwep-secret\n",
            "WIFI:T:WEP;S:Old Router;P:wep-secret;;",
            "--meta",
            "wlan0",
        )

        result = self.run_qr("Enterprise\nwpa-eap\nsecret\nno\n", "wlan0")
        self.assertNotEqual(result.returncode, 0, "enterprise networks cannot produce a password QR")
        self.assertEqual(result.stderr.strip(), "Enterprise Wi-Fi cannot be shared with a password QR code")
        self.assertFalse(self.payload_file.exists(), "qrencode never receives enterprise credentials")


if __name__ == "__main__":
    unittest.main()
