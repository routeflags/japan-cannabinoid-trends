"""X adapter package: dry-run / request planning only (COL-016 safe slice).

What lives here (all offline, no live transport):

- :mod:`collection.adapters.x.request`: pure X API v2 search request
  planner — turns declared query text + absolute UTC bounds into the request
  parameters a live collection *would* send, without sending anything;
- :mod:`collection.adapters.x.dry_run`: contract-shaped dry-run adapter whose
  ``collect`` always fails closed (no token, no HTTP, no response handling);
- :mod:`collection.adapters.x.compiler`: absolute-window compiler producing
  request parameters only (WIN-002 slice).

COL-030 boundary (no exceptions): nothing here reads credentials, issues a
live request, or handles a response body.  No tweet IDs / user IDs / text /
URLs / per-post records exist anywhere in this package — only request-side
facts (endpoint, query text, absolute bounds).  Live collection stays with
``ISS-20261015-COL-031`` (collector registration), live-request control
(count limits) with ``ISS-20261015-COL-032``, and request-only evidence with
``ISS-20261015-PRV-033``.

Nothing in this package is registered in ``collection.adapters`` dispatch
(``_FACTORIES`` / ``_WINDOW_COMPILERS``): the ``x-api-v2`` collector does not
exist in ``config/collectors.json`` yet, and registering a source that cannot
collect would imply an unevidenced capability.  Build the pieces explicitly.
"""

from collection.adapters.x.compiler import XApiWindowCompiler
from collection.adapters.x.dry_run import (
    XApiDryRunAdapter,
    XDryRunError,
    build_dry_run_adapter,
)
from collection.adapters.x.request import (
    ENDPOINT,
    METHOD,
    XRequestError,
    build_search_request,
    plan_search_request,
)

__all__ = [
    "ENDPOINT",
    "METHOD",
    "XApiDryRunAdapter",
    "XApiWindowCompiler",
    "XDryRunError",
    "XRequestError",
    "build_dry_run_adapter",
    "build_search_request",
    "plan_search_request",
]
