from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class OntologyValidationTests(unittest.TestCase):
    def test_complete_ontology_validation(self) -> None:
        completed = subprocess.run(
            [sys.executable, "ontology/validate_ontology.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("ontology validation passed", completed.stdout)

    def test_generated_artifacts_are_current(self) -> None:
        completed = subprocess.run(
            [sys.executable, "ontology/generate_ontology.py", "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()