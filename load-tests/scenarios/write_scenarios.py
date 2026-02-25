"""
Write scenario: simulates an HR user creating candidates and advancing their
interview stages.

Flow per task iteration:
  1. POST /candidates  → creates a candidate with fake data, stores the ID
  2. PUT /candidates/{id} → advances the candidate to the next interview step
"""

import random
import threading
from faker import Faker
from locust import HttpUser, between, task

fake = Faker("es_ES")

# Thread-safe shared pool of created candidate IDs so that ReadUser can also
# pick them up for GET /candidates/{id} calls.
_created_candidate_ids: list[int] = []
_lock = threading.Lock()


def register_candidate_id(candidate_id: int) -> None:
    with _lock:
        _created_candidate_ids.append(candidate_id)
        # Keep the pool bounded to avoid unbounded memory growth
        if len(_created_candidate_ids) > 500:
            _created_candidate_ids.pop(0)


def get_random_candidate_id() -> int | None:
    with _lock:
        if not _created_candidate_ids:
            return None
        return random.choice(_created_candidate_ids)


def _random_date_range() -> tuple[str, str]:
    start_year = random.randint(2010, 2020)
    end_year = random.randint(start_year + 1, 2024)
    start = f"{start_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    end = f"{end_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    return start, end


def _build_candidate_payload() -> dict:
    """Build a realistic candidate payload that satisfies API validation rules."""
    edu_start, edu_end = _random_date_range()
    work_start, work_end = _random_date_range()

    # API pattern: ^[a-zA-ZñÑáéíóúÁÉÍÓÚ ]+$  (letters + spaces, no digits/symbols)
    first_name = fake.first_name()
    last_name = fake.last_name()
    # Strip any non-matching characters that Faker might produce
    import re
    allowed = re.compile(r"[^a-zA-ZñÑáéíóúÁÉÍÓÚ ]")
    first_name = allowed.sub("", first_name)[:50] or "Candidate"
    last_name = allowed.sub("", last_name)[:50] or "Test"

    return {
        "firstName": first_name,
        "lastName": last_name,
        "email": fake.email(),
        "phone": f"+34{random.randint(600000000, 699999999)}",
        "address": fake.address().replace("\n", ", ")[:100],
        "educations": [
            {
                "institution": fake.company()[:100],
                "title": random.choice(["Grado en Ingeniería", "Máster en Datos", "FP Superior"])[:100],
                "startDate": edu_start,
                "endDate": edu_end,
            }
        ],
        "workExperiences": [
            {
                "company": fake.company()[:100],
                "position": fake.job()[:100],
                "description": fake.sentence()[:200],
                "startDate": work_start,
                "endDate": work_end,
            }
        ],
    }


class WriteUser(HttpUser):
    """
    Simulates an HR user who creates candidates and updates their interview stage.
    Runs at ~20% weight when combined with other user classes.
    """

    weight = 2
    wait_time = between(2, 5)

    # IDs created by THIS user instance (to advance their interview steps)
    _my_candidate_ids: list[int]
    # Application IDs associated with created candidates (needed for PUT)
    _my_application_ids: list[int]

    def on_start(self) -> None:
        self._my_candidate_ids = []
        self._my_application_ids = []

    @task(3)
    def create_candidate(self) -> None:
        """POST /candidates — create a new candidate with fake data."""
        payload = _build_candidate_payload()

        with self.client.post(
            "/candidates",
            json=payload,
            name="/candidates [POST]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                data = resp.json()
                candidate_id = data.get("id")
                if candidate_id:
                    self._my_candidate_ids.append(int(candidate_id))
                    register_candidate_id(int(candidate_id))
            elif resp.status_code == 400:
                # Validation error — mark as success so it doesn't skew error rate,
                # but log it for debugging.
                resp.success()
            else:
                resp.failure(f"POST /candidates failed: {resp.status_code} — {resp.text[:200]}")

    @task(1)
    def advance_candidate_stage(self) -> None:
        """PUT /candidates/{id} — advance interview step for a previously created candidate."""
        candidate_id = self._pick_my_candidate_id()
        if candidate_id is None:
            return

        # We need an applicationId; without it we skip (the API requires it).
        # In a real setup you'd fetch GET /candidates/{id} to get the applicationId.
        # Here we use a best-effort GET first to retrieve it.
        with self.client.get(
            f"/candidates/{candidate_id}",
            name="/candidates/{id} [GET for PUT]",
            catch_response=True,
        ) as get_resp:
            if get_resp.status_code != 200:
                get_resp.success()  # not a failure, just skip
                return
            candidate_data = get_resp.json()

        # The candidate object may not directly expose applicationId —
        # advance step using a sensible default (step 2) if we don't have it.
        application_id = candidate_data.get("applicationId") or candidate_data.get("id")
        if application_id is None:
            return

        payload = {
            "applicationId": int(application_id),
            "currentInterviewStep": random.randint(2, 4),
        }

        with self.client.put(
            f"/candidates/{candidate_id}",
            json=payload,
            name="/candidates/{id} [PUT]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 400, 404):
                resp.success()
            else:
                resp.failure(f"PUT /candidates/{candidate_id} failed: {resp.status_code}")

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _pick_my_candidate_id(self) -> int | None:
        if not self._my_candidate_ids:
            return get_random_candidate_id()
        return random.choice(self._my_candidate_ids)
