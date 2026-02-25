"""
AI4Devs — Locust stress test entry point.

User class weights (total = 10):
  ReadUser   → 7  (70%)  — recruiters browsing the dashboard
  WriteUser  → 2  (20%)  — HR users creating / updating candidates
  UploadUser → 1  (10%)  — users uploading CV files

Usage examples
--------------
Interactive UI (default port 8089):
    locust -f load-tests/locustfile.py --host http://localhost:8080

Headless / CI:
    locust -f load-tests/locustfile.py \
        --headless \
        --users 50 \
        --spawn-rate 5 \
        --run-time 60s \
        --host http://localhost:8080 \
        --html load-tests/report.html

Quality thresholds enforced at runtime:
  - Error rate  < 1 %
  - P95 latency < 2 000 ms
"""

import logging
from locust import events
from locust.env import Environment

from scenarios.read_scenarios import ReadUser  # noqa: F401 — re-exported for Locust discovery
from scenarios.write_scenarios import WriteUser  # noqa: F401
from scenarios.upload_scenarios import UploadUser  # noqa: F401

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Quality-gate: fail the run if thresholds are exceeded
# ---------------------------------------------------------------------------
ERROR_RATE_THRESHOLD = 0.01   # 1 %
P95_LATENCY_THRESHOLD = 2000  # milliseconds


@events.quitting.add_listener
def _enforce_quality_gates(environment: Environment, **_kwargs) -> None:
    """
    Called by Locust just before it exits.
    Sets exit_code = 1 when quality thresholds are breached so that CI
    pipelines detect the failure.
    """
    stats = environment.runner.stats if environment.runner else None
    if stats is None:
        return

    total = stats.total
    num_requests = total.num_requests

    if num_requests == 0:
        logger.warning("No requests were made — skipping quality gate checks.")
        return

    error_rate = total.num_failures / num_requests
    p95_ms = total.get_response_time_percentile(0.95)

    logger.info(
        "Quality gates — error_rate=%.2f%% (threshold: %.2f%%) | "
        "P95=%.0fms (threshold: %dms)",
        error_rate * 100,
        ERROR_RATE_THRESHOLD * 100,
        p95_ms,
        P95_LATENCY_THRESHOLD,
    )

    failures: list[str] = []

    if error_rate > ERROR_RATE_THRESHOLD:
        failures.append(
            f"Error rate {error_rate * 100:.2f}% exceeds threshold {ERROR_RATE_THRESHOLD * 100:.2f}%"
        )

    if p95_ms > P95_LATENCY_THRESHOLD:
        failures.append(
            f"P95 latency {p95_ms:.0f}ms exceeds threshold {P95_LATENCY_THRESHOLD}ms"
        )

    if failures:
        for msg in failures:
            logger.error("QUALITY GATE FAILED: %s", msg)
        environment.process_exit_code = 1
    else:
        logger.info("All quality gates passed.")
