"""Offline tests for fingerprint matching.

Run with: python -m pytest test_webtech.py   (or: python test_webtech.py)
"""
import os
import tempfile

import webtech

RESPONSE = """HTTP/1.1 200 OK
Content-Type: text/html

<html><head>
<meta name="generator" content="Webflow">
<script src="https://js.hs-scripts.com/8778274.js"></script>
<script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
</head><body></body></html>
"""

# Shaped like entries in enthec/webappanalyzer: "scriptSrc", not "script".
DB = {"apps": {
    "HubSpot": {"scriptSrc": ["\\.hs-scripts\\.com/"]},
    "jQuery": {"scriptSrc": ["jquery-([\\d.]+)\\.min\\.js\\;version:\\1"]},
    "Webflow": {"meta": {"generator": "Webflow"}},
    "Nothing": {"scriptSrc": ["this-is-not-on-the-page"]},
    # legacy key, still used by webtech.json's own entries
    "LegacyTech": {"script": ["code\\.jquery\\.com"]},
}}


def detect(db=DB):
    fd, path = tempfile.mkstemp(suffix=".http")
    with os.fdopen(fd, "w") as f:
        f.write(RESPONSE)
    try:
        wt = webtech.WebTech(options={"json": True})
        wt.db = db
        return {t["name"]: t.get("version") for t in
                wt.start_from_url("file://" + path)["tech"]}
    finally:
        os.unlink(path)


def test_scriptsrc_fingerprints_match():
    """Regression: webtech read t["script"], the db ships "scriptSrc", so every
    one of the 3889 scriptSrc fingerprints silently never matched."""
    found = detect()
    assert "HubSpot" in found
    assert "jQuery" in found


def test_scriptsrc_reports_version():
    assert detect()["jQuery"] == "3.5.1"


def test_legacy_script_key_still_works():
    assert "LegacyTech" in detect()


def test_meta_fingerprints_unaffected():
    assert "Webflow" in detect()


def test_no_false_positive():
    assert "Nothing" not in detect()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
