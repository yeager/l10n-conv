"""Tests for string extractor."""

import os
from l10n_conv.extractor import extract_from_file, extract_from_directory


def test_extract_python(tmp_dir):
    path = os.path.join(tmp_dir, "test.py")
    with open(path, "w") as f:
        f.write('msg = _("Hello")\nother = gettext("World")\n')
    results = extract_from_file(path)
    assert len(results) == 2
    assert results[0][0] == "Hello"
    assert results[1][0] == "World"


def test_extract_js(tmp_dir):
    path = os.path.join(tmp_dir, "test.js")
    with open(path, "w") as f:
        f.write('const msg = __("Click here");\n')
    results = extract_from_file(path)
    assert len(results) == 1


def test_extract_c(tmp_dir):
    path = os.path.join(tmp_dir, "test.c")
    with open(path, "w") as f:
        f.write('printf(_("Hello %s"), name);\n')
    results = extract_from_file(path)
    assert len(results) == 1


def test_extract_qml(tmp_dir):
    path = os.path.join(tmp_dir, "test.qml")
    with open(path, "w") as f:
        f.write('text: qsTr("Welcome")\n')
    results = extract_from_file(path)
    assert len(results) == 1


def test_extract_directory(tmp_dir):
    os.makedirs(os.path.join(tmp_dir, "sub"))
    with open(os.path.join(tmp_dir, "app.py"), "w") as f:
        f.write('_("One")\n')
    with open(os.path.join(tmp_dir, "sub", "mod.py"), "w") as f:
        f.write('_("Two")\n')
    cat = extract_from_directory(tmp_dir)
    assert len(cat.entries) == 2
