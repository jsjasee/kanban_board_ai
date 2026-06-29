import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
import backend.storage as storage


class BoardApiTests(unittest.TestCase):
    """Covers DB bootstrap plus board read and update routes."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = storage.DB_PATH
        storage.DB_PATH = Path(self.temp_dir.name) / "pm.db"
        self.client = TestClient(app)

    def tearDown(self) -> None:
        storage.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_get_board_creates_database_and_default_board(self) -> None:
        response = self.client.get("/api/board")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(storage.DB_PATH.exists())
        self.assertEqual(
            [column["title"] for column in response.json()["columns"]],
            ["Backlog", "Discovery", "In Progress", "Review", "Done"],
        )

    def test_put_board_replaces_persisted_board(self) -> None:
        payload = {
            "columns": [{"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1"]}],
            "cards": {"card-1": {"id": "card-1", "title": "Task", "details": "Notes"}},
        }

        put_response = self.client.put("/api/board", json=payload)
        get_response = self.client.get("/api/board")

        self.assertEqual(put_response.status_code, 200)
        self.assertEqual(put_response.json(), payload)
        self.assertEqual(get_response.json(), payload)

    def test_invalid_json_body_is_rejected(self) -> None:
        response = self.client.put(
            "/api/board",
            content="not-json",
            headers={"content-type": "application/json"},
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
