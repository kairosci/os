"""Exercise the Wi-Fi QR parser against complete and malformed output."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "src/arch/shell/plugins/panels/wifiqr/Model.js"
NODE_TEST = r"""
const assert = require('node:assert/strict')
const wifiqr = require(process.argv[1])

assert.deepEqual(
  wifiqr.parseQrOutput('meta\twlan0\tWPA\tCafe WiFi\n010\n111\n010\n'),
  { meta: { iface: 'wlan0', security: 'WPA', ssid: 'Cafe WiFi' }, matrix: { rows: ['010', '111', '010'], size: 3 } }
)
assert.equal(
  wifiqr.parseQrOutput('meta\twlan0\tnopass\tTab\tName\n010\n111\n010\n').meta.ssid,
  'Tab\tName'
)
assert.deepEqual(
  wifiqr.parseQrOutput('010\n111\n010\n'),
  { meta: { iface: '', security: '', ssid: '' }, matrix: { rows: ['010', '111', '010'], size: 3 } }
)
assert.deepEqual(wifiqr.parseQrOutput('meta\twlan0\tWPA\tCafe\n01\n111\n').matrix, { rows: [], size: 0 })
assert.deepEqual(wifiqr.parseQrOutput('010\n101\n').matrix, { rows: [], size: 0 })
assert.deepEqual(wifiqr.parseQrOutput('010\n1x1\n010\n').matrix, { rows: [], size: 0 })
"""


class WifiQrTest(unittest.TestCase):
    def test_parser_handles_metadata_and_rejects_invalid_matrices(self) -> None:
        subprocess.run(
            ["node", "-e", NODE_TEST, str(MODEL)],
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
