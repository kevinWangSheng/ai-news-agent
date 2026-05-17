from app.ingestion.normalize import normalize_url


def test_strips_www_and_lowercases_host():
    assert normalize_url("https://WWW.Example.COM/Foo/") == "https://example.com/Foo"


def test_drops_tracking_params():
    assert (
        normalize_url("https://x.com/a/b?utm_source=tw&id=1&fbclid=z")
        == "https://x.com/a/b?id=1"
    )


def test_adds_https_when_missing():
    assert normalize_url("example.com/foo").startswith("https://example.com")


def test_none_in_none_out():
    assert normalize_url(None) is None
    assert normalize_url("") is None
