# Collection adapter test fixtures

This directory holds **synthetic** replay fixtures for the G1 collection core
contract tests.

The fixtures are modeled on the *recorded response shape* of the
``google-trends-mcp`` server (``{keyword, geo, timeframe, collected_at,
 data:[{date, value}]}``; weekly buckets, Sunday start; values are relative
index 0-100).  The values themselves are invented - they are **not**
captured responses, and **no live collection is executed** by the tests or
by this repository.

| File | Request it answers |
|---|---|
| ``interest_over_time_cbx_rikiddo_12m.json`` | ``interest_over_time`` terms=["CBX リキッド"], geo="JP", timeframe="today 12-m" (52 weeks) |
| ``interest_over_time_cbx_rikiddo_5y.json`` | same terms/geo, timeframe="today 5-y" (261 weeks) |

The replay transport refuses to answer any other request, so a fixture can
never be mistaken for the result of a different collection.
