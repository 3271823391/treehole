from pathlib import Path


def _s(*codes):
    return "".join(chr(c) for c in codes)


def _kw():
    return [
        _s(22909,24863,24230), _s(20146,23494,24230), _s(20851,31995,20540), _s(20851,31995,24230), _s(40664,22865), _s(20449,20219,24230),
        _s(102,97,118,111,114), _s(102,97,118,111,117,114), _s(102,97,118,111,114,97,98,105,108,105,116,121), _s(97,102,102,101,99,116,105,111,110),
        _s(114,101,108,97,116,105,111,110,115,104,105,112), _s(98,111,110,100), _s(108,105,107,101,95,115,99,111,114,101),
        _s(102,97,118,111,114,95,115,99,111,114,101), _s(114,101,108,97,116,105,111,110,115,104,105,112,95,115,99,111,114,101),
        _s(97,102,102,101,99,116,105,111,110,95,115,99,111,114,101), _s(98,111,110,100,83,99,111,114,101), _s(108,105,107,101,83,99,111,114,101),
    ]


def test_keywords_cleared():
    root = Path(__file__).resolve().parent.parent
    skip = {".git", "venv", "node_modules", "dist", "__pycache__", ".pytest_cache"}
    this_name = "test_" + _s(102,97,118,111,114,97,98,105,108,105,116,121) + "_removed.py"
    hits = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in skip for part in p.parts):
            continue
        if p.name == this_name:
            continue
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pyc"}:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for kw in _kw():
            if kw in text:
                hits.append((str(p.relative_to(root)), kw))
    assert not hits, hits
