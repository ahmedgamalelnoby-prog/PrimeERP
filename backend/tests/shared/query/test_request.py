from app.shared.query import QueryRequest


def test_default_query_request():
    query = QueryRequest()

    assert query.page == 1
    assert query.page_size == 25
    assert query.filters == {}
    assert query.search is None
    assert query.sort is None
    assert query.include_deleted is False