import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from conversation import GenerationError


APP = str(Path(__file__).resolve().parents[1] / "app.py")
TEXT = "A despesa improdutiva envolve o luxo, a festa e o excesso. A utilidade não explica toda a atividade humana."


class AppTests(unittest.TestCase):
    def setUp(self):
        upload = SimpleNamespace(name="teste.pdf", size=10, getvalue=lambda: b"teste")
        reader = SimpleNamespace(pages=[SimpleNamespace(extract_text=lambda: TEXT)])
        self.upload_patch = patch("streamlit.file_uploader", return_value=[upload])
        self.reader_patch = patch("search.open_pdf", return_value=reader)
        self.upload_patch.start()
        self.reader_patch.start()
        self.addCleanup(self.upload_patch.stop)
        self.addCleanup(self.reader_patch.stop)

    def prepared_app(self):
        app = AppTest.from_file(APP).run()
        next(b for b in app.button if b.label == "preparar acervo").click().run()
        self.assertEqual(len(app.exception), 0)
        return app

    def test_text_search_and_clear(self):
        app = self.prepared_app()
        app.chat_input[0].set_value("despesa improdutiva").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.session_state["messages"][-1]["kind"], "search")
        self.assertTrue(app.session_state["messages"][-1]["results"])
        next(b for b in app.button if b.label == "limpar conversa").click().run()
        self.assertEqual(app.session_state["messages"], [])

    def test_generated_answer_and_followup_history(self):
        app = self.prepared_app()
        app.radio[0].set_value("Conversar com IA").run()
        self.assertTrue(app.chat_input[0].disabled)
        next(t for t in app.text_input if t.label == "Modelo instalado no Ollama").set_value("teste").run()
        next(c for c in app.checkbox if c.label.startswith("Enviar minha pergunta")).check().run()
        paragraphs = [{"texto": "Interpretação de teste", "fontes": [1]}]
        with patch("conversation.generate_answer", return_value=paragraphs) as generate:
            app.chat_input[0].set_value("despesa improdutiva").run()
            self.assertEqual(app.session_state["messages"][-1]["kind"], "generated")
            app.chat_input[0].set_value("e como isso se relaciona ao luxo?").run()
            self.assertEqual(len(generate.call_args.args[2]), 2)
        self.assertEqual(len(app.exception), 0)

    def test_generation_failure_preserves_passages(self):
        app = self.prepared_app()
        app.radio[0].set_value("Conversar com IA").run()
        next(t for t in app.text_input if t.label == "Modelo instalado no Ollama").set_value("teste").run()
        next(c for c in app.checkbox if c.label.startswith("Enviar minha pergunta")).check().run()
        with patch("conversation.generate_answer", side_effect=GenerationError("Servidor indisponível")):
            app.chat_input[0].set_value("despesa improdutiva").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.warning[0].value, "Servidor indisponível")
        self.assertTrue(app.session_state["messages"][-1]["results"])


if __name__ == "__main__":
    unittest.main()
