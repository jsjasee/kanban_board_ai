import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.openrouter import BOARD_CHAT_RESPONSE_FORMAT, BoardChatResponse, complete_board_chat
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
        expected = {
            "columns": [
                {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1"]},
                {"id": "col-discovery", "title": "Discovery", "cardIds": []},
                {"id": "col-progress", "title": "In Progress", "cardIds": []},
                {"id": "col-review", "title": "Review", "cardIds": []},
                {"id": "col-done", "title": "Done", "cardIds": []},
            ],
            "cards": payload["cards"],
        }

        put_response = self.client.put("/api/board", json=payload)
        get_response = self.client.get("/api/board")

        self.assertEqual(put_response.status_code, 200)
        self.assertEqual(put_response.json(), expected)
        self.assertEqual(get_response.json(), expected)

    def test_invalid_json_body_is_rejected(self) -> None:
        response = self.client.put(
            "/api/board",
            content="not-json",
            headers={"content-type": "application/json"},
        )

        self.assertEqual(response.status_code, 422)

    @patch("backend.main.complete_prompt", return_value="AI ok")
    def test_ai_route_returns_model_reply(self, complete_prompt_mock) -> None:
        response = self.client.post("/api/ai/test", json={"prompt": "Say hi"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"reply": "AI ok"})
        complete_prompt_mock.assert_called_once_with("Say hi")

    def test_ai_route_rejects_blank_prompt(self) -> None:
        response = self.client.post("/api/ai/test", json={"prompt": "   "})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Prompt is required"})

    @patch("backend.main.complete_prompt", side_effect=RuntimeError("upstream failed"))
    def test_ai_route_maps_client_errors_to_502(self, _complete_prompt_mock) -> None:
        response = self.client.post("/api/ai/test", json={"prompt": "Say hi"})

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json(), {"detail": "upstream failed"})


class OpenRouterSchemaTests(unittest.TestCase):
    def test_board_chat_wire_schema_is_provider_safe(self) -> None:
        schema = BOARD_CHAT_RESPONSE_FORMAT["json_schema"]["schema"]

        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["properties"]), {"reply", "board_json"})
        self.assertEqual(schema["required"], ["reply", "board_json"])

    @patch("backend.openrouter._client")
    def test_complete_board_chat_parses_board_json_string(self, client_mock) -> None:
        client_mock.return_value.chat.completions.create.return_value.choices = [
            type(
                "Choice",
                (),
                {
                    "message": type(
                        "Message",
                        (),
                        {
                            "content": (
                                '{"reply":"Done","board_json":"{\\"columns\\":[{\\"id\\":\\"col-backlog\\",'
                                '\\"title\\":\\"Backlog\\",\\"cardIds\\":[\\"card-1\\"]}],'
                                '\\"cards\\":{\\"card-1\\":{\\"id\\":\\"card-1\\",\\"title\\":\\"Task\\",'
                                '\\"details\\":\\"Notes\\"}}}"}'
                            )
                        },
                    )()
                },
            )()
        ]

        result = complete_board_chat(
            {"columns": [{"id": "col-backlog", "title": "Backlog", "cardIds": []}], "cards": {}},
            [],
            "add a task",
        )

        self.assertEqual(result["reply"], "Done")
        self.assertEqual(result["board"]["cards"]["card-1"]["title"], "Task")

    @patch("backend.openrouter._client")
    def test_complete_board_chat_allows_noop_board_json(self, client_mock) -> None:
        client_mock.return_value.chat.completions.create.return_value.choices = [
            type(
                "Choice",
                (),
                {"message": type("Message", (), {"content": '{"reply":"Hi","board_json":null}'})()},
            )()
        ]

        result = complete_board_chat(
            {"columns": [{"id": "col-backlog", "title": "Backlog", "cardIds": []}], "cards": {}},
            [],
            "hi there",
        )

        self.assertEqual(result, {"reply": "Hi", "board": None})


if __name__ == "__main__":
    unittest.main()
