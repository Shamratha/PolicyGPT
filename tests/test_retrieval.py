from pathlib import Path
from app.retrieval import HybridRetriever


def test_retrieval_prefers_matching_domain():
    retriever=HybridRetriever.from_json(Path("data/policies.json")); hits=retriever.search("student scholarship family income","education",3)
    assert hits and hits[0].document.id=="edu-nsp-01"


def test_search_is_deterministic():
    retriever=HybridRetriever.from_json(Path("data/policies.json")); q="farmer land records"
    assert [h.document.id for h in retriever.search(q,"agriculture",3)]==[h.document.id for h in retriever.search(q,"agriculture",3)]
