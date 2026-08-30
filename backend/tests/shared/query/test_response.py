from app.shared.query import QueryResponse


def test_total_pages():
    result = QueryResponse(
        items=[],
        total_items=101,
        page=1,
        page_size=25,
    )

    assert result.total_pages == 5


def test_has_next():
    result = QueryResponse(
        items=[],
        total_items=100,
        page=2,
        page_size=25,
    )

    assert result.has_next is True


def test_has_previous():
    result = QueryResponse(
        items=[],
        total_items=10,
        page=2,
        page_size=25,
    )

    assert result.has_previous is True