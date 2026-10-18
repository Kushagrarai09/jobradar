"""Regression tests for job-board fetching and normalization edge cases.

Run directly with: python tests/test_sources_regression.py
All network calls are mocked; the tests are deterministic and offline.
"""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from jobradar import sources


class SourceRegressionTests(unittest.TestCase):
    def test_network_timeout_is_returned_as_fetch_error(self):
        with patch("jobradar.sources.requests.get", side_effect=requests.Timeout("slow")):
            jobs, error = sources.fetch_company({
                "name": "Acme", "board": "greenhouse", "slug": "acme"
            })

        self.assertEqual(jobs, [])
        self.assertIsNotNone(error)
        self.assertIn("Timeout", error)

    def test_malformed_greenhouse_payload_does_not_crash_caller(self):
        with patch("jobradar.sources._get", return_value={"jobs": None}):
            jobs, error = sources.fetch_company({
                "name": "Acme", "board": "greenhouse", "slug": "acme"
            })

        self.assertEqual(jobs, [])
        self.assertIsNotNone(error)

    def test_same_job_data_produces_stable_id(self):
        payload = {
            "jobs": [{
                "title": "Backend Engineer",
                "absolute_url": "https://jobs.example/123",
                "location": {"name": "Remote"},
                "updated_at": "2026-10-01T10:00:00Z",
                "content": "Build APIs",
            }]
        }
        entry = {"name": "Acme", "board": "greenhouse", "slug": "acme"}

        with patch("jobradar.sources._get", return_value=payload):
            first, first_error = sources.fetch_company(entry)
        with patch("jobradar.sources._get", return_value=payload):
            second, second_error = sources.fetch_company(entry)

        self.assertIsNone(first_error)
        self.assertIsNone(second_error)
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0]["id"], second[0]["id"])

    def test_http_error_is_reported_without_raising(self):
        response = requests.Response()
        response.status_code = 503
        error = requests.HTTPError("service unavailable", response=response)

        with patch("jobradar.sources.requests.get", side_effect=error):
            jobs, message = sources.fetch_company({
                "name": "Acme", "board": "greenhouse", "slug": "acme"
            })

        self.assertEqual(jobs, [])
        self.assertIsNotNone(message)
        self.assertIn("HTTPError", message)


if __name__ == "__main__":
    unittest.main()
