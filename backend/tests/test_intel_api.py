def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_overview_has_corpus(client):
    res = client.get("/api/intel/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["total_documents"] >= 20
    assert data["total_entities"] >= 10
    assert data["discovered_entities"] >= 1
    types = {row["key"] for row in data["doc_type_counts"]}
    assert "scam_report" in types or "complaint" in types
    assert data["emerging_entities"] or data["discovered_entities"] > 0


def test_search_discovers_scam_and_new_platform(client):
    scam = client.get("/api/intel/search", params={"q": "scam"}).json()
    assert scam["total"] >= 1
    assert any(item["doc_type"] in {"scam_report", "complaint", "forum_thread"} for item in scam["items"])

    flash = client.get("/api/intel/search", params={"q": "FlashCards"}).json()
    assert flash["total"] >= 1
    titles = " ".join(item["title"] for item in flash["items"])
    assert "FlashCards" in titles


def test_flashcards_is_discovered_entity_not_seed(client):
    entities = client.get("/api/intel/entities", params={"q": "FlashCards", "discovered_only": True}).json()
    assert any(e["name"] == "FlashCards NG" and e["is_seeded"] is False for e in entities)
    entity = next(e for e in entities if e["name"] == "FlashCards NG")
    detail = client.get(f"/api/intel/entities/{entity['id']}").json()
    assert len(detail["documents"]) >= 1


def test_document_detail_keeps_full_text(client):
    listing = client.get("/api/intel/search", params={"q": "Nairaland", "limit": 5}).json()
    assert listing["items"]
    doc = client.get(f"/api/intel/documents/{listing['items'][0]['id']}").json()
    assert doc["full_text"]
    assert doc["summary_zh"]
    assert isinstance(doc["facts"], list)


def test_create_watch_persists(client):
    created = client.post("/api/watches", json={"query": "Kenya gift card buyer", "label": "肯尼亚"}).json()
    assert created["query"] == "Kenya gift card buyer"
    assert created["is_system"] is False
    watches = client.get("/api/watches").json()
    assert any(w["id"] == created["id"] for w in watches)


def test_price_board_still_works_as_derived_view(client):
    board = client.get("/api/prices/board").json()
    assert isinstance(board, list)
    # 派生报价至少应覆盖演示语料里抽到的 Amazon 等
    assert any(cell["gift_card_type_name"].lower().startswith("amazon") for cell in board)
