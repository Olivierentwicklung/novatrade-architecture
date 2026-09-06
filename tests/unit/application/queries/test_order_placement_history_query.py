from novatrade.application.queries.order_placement_history import (
    OrderPlacementHistoryQuery,
)


def test_order_placement_history_query_represents_the_request_for_history() -> None:
    query = OrderPlacementHistoryQuery()

    assert isinstance(query, OrderPlacementHistoryQuery)
