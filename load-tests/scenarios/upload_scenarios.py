"""
Upload scenario: simulates a user uploading a CV file via POST /upload.

The endpoint only accepts PDF or DOCX files.  We reuse a single small PDF
from load-tests/data/sample.pdf to avoid generating files on every request.
"""

import os
from locust import HttpUser, between, task

# Resolve the sample file path relative to this module, regardless of cwd
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_SAMPLE_PDF = os.path.join(_DATA_DIR, "sample.pdf")


class UploadUser(HttpUser):
    """
    Simulates a user uploading a CV (PDF) to the /upload endpoint.
    Runs at ~10% weight when combined with other user classes.
    """

    weight = 1
    wait_time = between(3, 8)

    # Pre-read the file bytes once per user instance to avoid repeated disk I/O
    _pdf_bytes: bytes = b""

    def on_start(self) -> None:
        if os.path.exists(_SAMPLE_PDF):
            with open(_SAMPLE_PDF, "rb") as f:
                self._pdf_bytes = f.read()
        else:
            # Minimal valid PDF as fallback if file is missing
            self._pdf_bytes = (
                b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
                b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
                b"3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj\n"
                b"xref\n0 4\n0000000000 65535 f \n"
                b"0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n"
                b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
            )

    @task
    def upload_cv(self) -> None:
        """POST /upload — multipart upload of a sample PDF file."""
        files = {
            "file": ("cv_test.pdf", self._pdf_bytes, "application/pdf"),
        }

        with self.client.post(
            "/upload",
            files=files,
            name="/upload [POST]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code == 400:
                # File validation error — not a system failure
                resp.success()
            else:
                resp.failure(f"POST /upload failed: {resp.status_code} — {resp.text[:200]}")
