"""
Read-only scenario: simulates a recruiter browsing the dashboard.

Flow per task iteration:
  1. GET /positions              → pick a random position ID
  2. GET /positions/{id}/interviewflow
  3. GET /positions/{id}/candidates → pick a random candidate ID (if any)
  4. GET /candidates/{id}
"""

import random
from locust import HttpUser, between, task


class ReadUser(HttpUser):
    """
    Simulates a recruiter that only reads data.
    Runs at ~70% weight when combined with other user classes.
    """

    weight = 7
    wait_time = between(1, 3)

    # Shared state across tasks within the same user session
    _position_ids: list[int] = []
    _candidate_ids: list[int] = []

    def on_start(self) -> None:
        """Pre-load available position IDs once per simulated user."""
        with self.client.get("/positions", name="/positions", catch_response=True) as resp:
            if resp.status_code == 200:
                positions = resp.json()
                self._position_ids = [p["id"] for p in positions if isinstance(p, dict) and "id" in p]
            else:
                resp.failure(f"GET /positions failed: {resp.status_code}")

    @task(4)
    def browse_positions(self) -> None:
        """List all open positions — most frequent read operation."""
        self.client.get("/positions", name="/positions")

    @task(3)
    def get_interview_flow(self) -> None:
        """Fetch the interview flow for a random position."""
        position_id = self._pick_position_id()
        if position_id is None:
            return
        self.client.get(
            f"/positions/{position_id}/interviewflow",
            name="/positions/{id}/interviewflow",
        )

    @task(3)
    def get_candidates_for_position(self) -> None:
        """Get all candidates for a random position and cache their IDs."""
        position_id = self._pick_position_id()
        if position_id is None:
            return
        with self.client.get(
            f"/positions/{position_id}/candidates",
            name="/positions/{id}/candidates",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                candidates = resp.json()
                if isinstance(candidates, list):
                    # The API returns fullName, not id — we cannot cache IDs from this endpoint.
                    # Candidate IDs must come from POST /candidates (WriteUser) or seed data.
                    pass
            elif resp.status_code == 404:
                # Position may have been deleted between on_start and now
                resp.success()
            else:
                resp.failure(f"GET /positions/{position_id}/candidates failed: {resp.status_code}")

    @task(2)
    def get_candidate_by_id(self) -> None:
        """Fetch a specific candidate by ID (uses IDs cached from write operations)."""
        candidate_id = self._pick_candidate_id()
        if candidate_id is None:
            return
        with self.client.get(
            f"/candidates/{candidate_id}",
            name="/candidates/{id}",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"GET /candidates/{candidate_id} failed: {resp.status_code}")

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _pick_position_id(self) -> int | None:
        if not self._position_ids:
            return None
        return random.choice(self._position_ids)

    def _pick_candidate_id(self) -> int | None:
        if not self._candidate_ids:
            # Fall back to a low sequential ID that might exist from seed data
            return random.randint(1, 5)
        return random.choice(self._candidate_ids)
