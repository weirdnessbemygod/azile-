import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from conversation import (GenerationError, build_messages, generate_answer,
                          retrieval_query, validate_answer)


def source():
    return [(SimpleNamespace(title="Obra", page=12, text="Trecho de teste."), 0.3)]


class ConversationTests(unittest.TestCase):
    def test_rejects_invented_reference(self):
        for ids in ([2], [True], [], [0]):
            with self.subTest(ids=ids), self.assertRaises(GenerationError):
                validate_answer(json.dumps({"status": "ok", "paragrafos": [
                    {"texto": "Interpretação", "fontes": ids}]}), 1)

    def test_rejects_malformed_output(self):
        for raw in ("texto livre", "[]", "null", '{"status":"ok","paragrafos":[]}'):
            with self.subTest(raw=raw), self.assertRaises(GenerationError):
                validate_answer(raw, 1)

    def test_insufficient_evidence(self):
        self.assertEqual(validate_answer('{"status":"insuficiente","paragrafos":[]}', 1), [])

    def test_no_sources_never_calls_model(self):
        with patch("conversation.urlopen") as network:
            self.assertEqual(generate_answer("pergunta", [], [], "modelo"), [])
            network.assert_not_called()

    def test_history_is_bounded_and_separate_from_sources(self):
        history = [{"role": "user", "text": str(i) * 2000} for i in range(12)]
        data = json.loads(build_messages("agora", source(), history)[1]["content"])
        self.assertEqual(len(data["historico_nao_e_fonte"]), 6)
        self.assertEqual(len(data["historico_nao_e_fonte"][0]["texto"]), 1000)
        self.assertEqual(data["FONTES"][0]["pagina_pdf"], 12)

    def test_followup_retrieval(self):
        history = [{"role": "user", "text": "despesa improdutiva"}]
        self.assertIn("despesa improdutiva", retrieval_query("e como isso aparece?", history))
        self.assertEqual(retrieval_query("erotismo e morte", history), "erotismo e morte")

    def test_provider_payload_and_valid_answer(self):
        content = json.dumps({"status": "ok", "paragrafos": [{"texto": "Síntese", "fontes": [1]}]})
        body = json.dumps({"done": True, "message": {"content": content}}).encode()
        with patch("conversation.urlopen", return_value=io.BytesIO(body)) as network:
            answer = generate_answer("pergunta", source(), [], "local")
            self.assertEqual(answer[0]["fontes"], [1])
            request = network.call_args.args[0]
            payload = json.loads(request.data)
            self.assertFalse(payload["stream"])
            self.assertEqual(payload["model"], "local")

    def test_safe_provider_errors(self):
        errors = [URLError("private secret"), HTTPError("url", 404, "secret", {}, None),
                  HTTPError("url", 500, "secret", {}, None), TimeoutError()]
        for error in errors:
            with self.subTest(error=error), patch("conversation.urlopen", side_effect=error):
                with self.assertRaises(GenerationError) as caught:
                    generate_answer("q", source(), [], "local")
                self.assertNotIn("secret", str(caught.exception))

    def test_unfinished_response_rejected(self):
        with patch("conversation.urlopen", return_value=io.BytesIO(b'{"done":false}')):
            with self.assertRaises(GenerationError):
                generate_answer("q", source(), [], "local")

    def test_insecure_remote_endpoint_rejected(self):
        with patch.dict("os.environ", {"AZILE_OLLAMA_URL": "http://example.com"}):
            with patch("conversation.urlopen") as network, self.assertRaises(GenerationError):
                generate_answer("q", source(), [], "local")
            network.assert_not_called()


if __name__ == "__main__":
    unittest.main()
