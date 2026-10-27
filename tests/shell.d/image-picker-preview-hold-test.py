"""Check that image picker previews are released after closing."""

from qml_test_support import run_qml_test


run_qml_test("image-picker-preview-hold", "image picker releases its previews after it closes")
