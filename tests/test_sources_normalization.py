"""Tests for job-board record normalization.

Run directly with: python tests/test_sources_normalization.py
"""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobradar import sources


class SourceNormalizationTests(unittest.TestCase):
    def test_missing_title_or_url_is_skipped_without_dropping_valid_jobs(self):
        payload = {
            "jobs": [
                {
                    "title": "  Backend Engineer  ",
                    "absolute_url": " https://jobs.example/valid ",
                    "location": {"name": " Remote "},
                    "content": None,
                },
                {"title": "", "absolute_url": "https://jobs.example/no-title"},
                {"title": "No URL", "absolute_url": ""},
                {"title": None, "absolute_url": None},
            ]
        }

        with patch("jobradar.sources._get", return_value=payload):
            jobs, error = sources.fetch_company({
                "name": " Acme ", "board": "greenhouse", "slug": "acme"
            })

        self.assertIsNone(error)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["company"], "Acme")
        self.assertEqual(jobs[0]["title"], "Backend Engineer")
        self.assertEqual(jobs[0]["url"], "https://jobs.example/valid")
        self.assertEqual(jobs[0]["location"], "Remote")
        self.assertEqual(jobs[0]["description"], "")

    def test_optional_fields_have_consistent_empty_values(self):
        payload = {
            "jobs": [{
                "title": "Data Engineer",
                "absolute_url": "https://jobs.example/data",
                "location": None,
                "content": None,
                "updated_at": None,
            }]
        }

        with patch("jobradar.sources._get", return_value=payload):
            jobs, error = sources.fetch_company({
                "name": "Acme", "board": "greenhouse", "slug": "acme",
                "domain": " acme.example ",
            })

        self.assertIsNone(error)
        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        self.assertEqual(job["location"], "")
        self.assertEqual(job["description"], "")
        self.assertIsNone(job["posted_at"])
        self.assertEqual(job["domain"], "acme.example")
        self.assertTrue(job["id"])

    def test_discovery_skips_records_without_required_fields(self):
        with patch("jobradar.sources._get", return_value={
            "jobs": [
                {"company_name": "Acme", "title": "Engineer",
                 "url": "https://jobs.example/1"},
                {"company_name": "Acme", "title": "Missing URL", "url": ""},
            ]
        }):
            jobs = sources.remotive("engineer", limit=10)

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["title"], "Engineer")

    def test_normalizer_ignores_non_dictionary_records(self):
        cleaned = sources._clean_jobs([
            None,
            "not a job",
            {"company": "Acme", "title": "Engineer", "url": "https://jobs.example/1"},
            {"company": "Acme", "title": "No URL", "url": "  "},
        ])

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned[0]["title"], "Engineer")


if __name__ == "__main__":
    unittest.main()
