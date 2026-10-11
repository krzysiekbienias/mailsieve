from mailsieve.cache import ClassificationCache
from mailsieve.domain import Category, Classification


def test_roundtrip(tmp_path):
    path = tmp_path / "c.json"
    cache = ClassificationCache(path)
    cache.put(Classification("a@x.com", Category.JOB, 0.9, False))
    cache.save()

    loaded = ClassificationCache(path).get("a@x.com")
    assert loaded == Classification("a@x.com", Category.JOB, 0.9, False)


def test_unclassified_is_not_cached(tmp_path):
    cache = ClassificationCache(tmp_path / "c.json")
    cache.put(Classification("a@x.com", None, 0.0, True, "missing"))
    assert cache.get("a@x.com") is None
