"""
Locust stress test suite for the AI4Devs Candidate API.

User types:
  - ReadUser  (weight=3): simulates a recruiter browsing positions and candidates.
  - WriteUser (weight=1): simulates a HR operator adding new candidates.

Run via Docker profile:
  docker compose --profile loadtest up -d
  # UI → http://localhost:8089
"""

import random
import string
import uuid
from locust import HttpUser, between, task


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _random_name(min_len: int = 4, max_len: int = 10) -> str:
    """Return a random alphabetic string suitable as a first/last name."""
    length = random.randint(min_len, max_len)
    return "".join(random.choices(string.ascii_lowercase, k=length)).capitalize()


def _random_email() -> str:
    domains = ["example.com", "test.org", "locust.io", "qa.net"]
    return f"{_random_name().lower()}.{uuid.uuid4().hex[:6]}@{random.choice(domains)}"


def _random_date(start_year: int = 2010, end_year: int = 2023) -> str:
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year}-{month:02d}-{day:02d}"


def _candidate_payload() -> dict:
    return {
        "firstName": _random_name(),
        "lastName": _random_name(),
        "email": _random_email(),
        "phone": f"+34{random.randint(600000000, 699999999)}",
        "address": f"Calle Test {random.randint(1, 999)}, Madrid",
        "educations": [
            {
                "institution": f"Universidad {_random_name()}",
                "title": f"Grado en {_random_name()}",
                "startDate": _random_date(2005, 2015),
                "endDate": _random_date(2016, 2020),
            }
        ],
        "workExperiences": [
            {
                "company": f"{_random_name()} Corp",
                "position": f"Senior {_random_name()} Engineer",
                "description": "Responsibilities include testing and quality assurance.",
                "startDate": _random_date(2018, 2021),
                "endDate": _random_date(2022, 2023),
            }
        ],
    }


# ---------------------------------------------------------------------------
# Shared state — position IDs discovered at runtime
# ---------------------------------------------------------------------------

_position_ids: list[int] = []
_candidate_ids: list[int] = []


# ---------------------------------------------------------------------------
# User classes
# ---------------------------------------------------------------------------


class ReadUser(HttpUser):
    """
    Simulates a recruiter browsing the ATS.
    Heavy on GET endpoints; ratio 3:1 vs WriteUser.
    """

    weight = 3
    wait_time = between(1, 3)

    def on_start(self) -> None:
        """Prime the shared position list on first request."""
        self._refresh_positions()

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    @task(5)
    def list_positions(self) -> None:
        """GET /positions — most frequent action."""
        with self.client.get("/positions", catch_response=True) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    ids = [p["id"] for p in data if "id" in p]
                    if ids:
                        _position_ids.clear()
                        _position_ids.extend(ids)
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}")

    @task(3)
    def get_position_candidates(self) -> None:
        """GET /positions/{id}/candidates"""
        position_id = self._pick_position_id()
        if position_id is None:
            return
        with self.client.get(
            f"/positions/{position_id}/candidates",
            name="/positions/[id]/candidates",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}")

    @task(3)
    def get_interview_flow(self) -> None:
        """GET /positions/{id}/interviewflow"""
        position_id = self._pick_position_id()
        if position_id is None:
            return
        with self.client.get(
            f"/positions/{position_id}/interviewflow",
            name="/positions/[id]/interviewflow",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}")

    @task(2)
    def get_candidate_by_id(self) -> None:
        """GET /candidates/{id}"""
        candidate_id = self._pick_candidate_id()
        if candidate_id is None:
            return
        with self.client.get(
            f"/candidates/{candidate_id}",
            name="/candidates/[id]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}")

    @task(1)
    def health_check(self) -> None:
        """GET / — basic liveness probe."""
        with self.client.get("/", catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _refresh_positions(self) -> None:
        resp = self.client.get("/positions")
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                ids = [p["id"] for p in data if "id" in p]
                _position_ids.clear()
                _position_ids.extend(ids)

    def _pick_position_id(self) -> int | None:
        if not _position_ids:
            self._refresh_positions()
        if not _position_ids:
            return None
        return random.choice(_position_ids)

    def _pick_candidate_id(self) -> int | None:
        if not _candidate_ids:
            return random.randint(1, 50)
        return random.choice(_candidate_ids)


class WriteUser(HttpUser):
    """
    Simulates an HR operator submitting new candidates.
    Write-heavy; ratio 1:3 vs ReadUser.
    """

    weight = 1
    wait_time = between(2, 5)

    @task(3)
    def create_candidate(self) -> None:
        """POST /candidates — create a new candidate with random data."""
        payload = _candidate_payload()
        with self.client.post(
            "/candidates",
            json=payload,
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                data = resp.json()
                candidate_id = data.get("id")
                if candidate_id is not None:
                    _candidate_ids.append(candidate_id)
                    if len(_candidate_ids) > 500:
                        _candidate_ids.pop(0)
                resp.success()
            elif resp.status_code == 400:
                # Validation errors are expected with random data edge-cases
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}: {resp.text[:120]}")

    @task(1)
    def verify_created_candidate(self) -> None:
        """GET /candidates/{id} — read back a previously created candidate."""
        if not _candidate_ids:
            return
        candidate_id = random.choice(_candidate_ids)
        with self.client.get(
            f"/candidates/{candidate_id}",
            name="/candidates/[id] (verify)",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}")
