"""Verify the local monitoring stack; requires only Python's standard library."""
import json
import os
import time
from urllib.parse import quote
from urllib.request import Request, urlopen


def get(url):
    with urlopen(url, timeout=5) as response:
        return json.load(response)


api = "http://127.0.0.1:" + os.getenv("CLOUDPILOT_PORT", "8000")
prometheus = "http://127.0.0.1:" + os.getenv("PROMETHEUS_PORT", "9090")
grafana = "http://127.0.0.1:" + os.getenv("GRAFANA_PORT", "3000")

request = Request(api + "/api/v1/plans", data=json.dumps({
    "name": "monitoring-smoke", "environment": "prod", "replicas": 1,
}).encode(), headers={"Content-Type": "application/json"})
with urlopen(request, timeout=5) as response:
    plan = json.load(response)
assert plan["status"] == "denied"
assert plan in get(api + "/api/v1/history")

for attempt in range(30):
    try:
        query = 'cloudpilot_plans_total{environment="prod",decision="denied"}'
        result = get(prometheus + "/api/v1/query?query=" + quote(query))["data"]["result"]
        assert result and float(result[0]["value"][1]) >= 1
        dashboard = get(grafana + "/api/dashboards/uid/cloudpilot-overview")
        assert dashboard["meta"]["provisioned"]
        for panel in dashboard["dashboard"]["panels"]:
            for target in panel["targets"]:
                query_result = get(prometheus + "/api/v1/query?query=" + quote(target["expr"]))
                assert query_result["status"] == "success"
        break
    except (OSError, AssertionError, KeyError):
        if attempt == 29:
            raise
        time.sleep(2)
print("PASS: policy, saved history, live Prometheus metrics, provisioned Grafana panels")
