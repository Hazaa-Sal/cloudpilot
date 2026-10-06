"""Bounded metric labels: never include application names, IDs, or raw URLs."""
from time import perf_counter

from prometheus_client import Counter, Histogram

PLANS = Counter("cloudpilot_plans_total", "Successfully persisted plans",
                ["environment", "decision", "cost_risk"])
VIOLATIONS = Counter("cloudpilot_policy_violations_total", "Policy violations",
                     ["environment"])
REQUESTS = Counter("cloudpilot_http_requests_total", "HTTP requests",
                   ["method", "route", "status"])
LATENCY = Histogram("cloudpilot_http_request_duration_seconds", "HTTP request duration",
                    ["method", "route"])


class MetricsMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] == "/metrics":
            await self.app(scope, receive, send)
            return
        start = perf_counter()
        status = 500

        async def capture(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, capture)
        finally:
            route = getattr(scope.get("route"), "path", "unmatched")
            method = scope["method"]
            if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
                method = "OTHER"
            REQUESTS.labels(method, route, str(status)).inc()
            LATENCY.labels(method, route).observe(perf_counter() - start)
