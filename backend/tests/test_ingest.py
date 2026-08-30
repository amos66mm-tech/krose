from app.agent.ingest import ingest_hit
from app.agent.textutil import canonicalize_url, fts_match_query, slugify
from app.agent.exa_client import SearchHit


def test_canonicalize_strips_tracking_and_www():
    url = "http://www.Nairaland.com/thread?utm_source=x&id=1"
    assert canonicalize_url(url) == "https://nairaland.com/thread?id=1"


def test_slugify_and_fts_query():
    assert slugify("FlashCards NG") == "flashcards-ng"
    assert '"scam" AND "momo"' in fts_match_query("scam MoMo")


def test_ingest_dedup(seeded_db):
    hit = SearchHit(
        title="Same article",
        url="https://example.com/a?utm_campaign=1",
        text="hello world " * 20,
        summary="hello",
        published_date=None,
        author=None,
    )
    doc1, created1 = ingest_hit(seeded_db, hit, stream="custom", query="test")
    hit2 = SearchHit(
        title="Same article longer",
        url="https://example.com/a",
        text="hello world " * 40,
        summary="hello",
        published_date=None,
        author=None,
    )
    doc2, created2 = ingest_hit(seeded_db, hit2, stream="custom", query="test")
    seeded_db.commit()
    assert created1 is True
    assert created2 is False
    assert doc1.id == doc2.id
    assert doc2.hit_count >= 2
    assert len(doc2.full_text) > len("hello world " * 20)
