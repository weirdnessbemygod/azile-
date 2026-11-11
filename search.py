"""Extração por página e busca lexical no acervo carregado na sessão."""

import re
from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


STOP_WORDS = """
a ao aos aquela aquelas aquele aqueles aquilo as ate com como da das de dela
delas dele deles depois do dos e ela elas ele eles em entre era eram essa essas
esse esses esta estas este estes eu foi foram ha isso isto ja lhe lhes mais mas
me mesmo meu meus minha minhas muito na nas nao nem no nos nossa nosso num
numa o os ou para pela pelas pelo pelos por qual quando que quem se sem seu
seus sua suas sao ser so sou sua tambem te tem temos tenho ter teu teus tu tua
um uma umas uns voce voces vos sobre quero queria diga dizer fala falar pode
poderia gostaria saber explique explicar favor algo coisa
""".split()


@dataclass(frozen=True)
class Passage:
    text: str
    title: str
    filename: str
    page: int
    document_id: str


def open_pdf(content: bytes) -> PdfReader:
    try:
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted and not reader.decrypt(""):
            raise ValueError("O PDF pede senha. Envie uma cópia desbloqueada.")
        if not reader.pages:
            raise ValueError("O arquivo não contém páginas.")
        return reader
    except ValueError:
        raise
    except Exception as error:
        raise ValueError("Não foi possível abrir este PDF.") from error


def readable(text: str) -> bool:
    """Rejeita páginas vazias ou com codificação claramente defeituosa."""
    visible = [char for char in text if not char.isspace()]
    if len(visible) < 50:
        return False
    controls = sum(not char.isprintable() for char in visible)
    letters = sum(char.isalpha() for char in visible)
    return controls / len(visible) < 0.02 and letters / len(visible) > 0.45


def clean_text(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line and not re.fullmatch(r"\d+", line)]
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def split_passages(text: str, max_chars: int = 700) -> list[str]:
    """Mantém a ordem do texto e prefere encerrar trechos entre frases."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    passages = []
    current = ""
    for sentence in sentences:
        if current and len(current) + len(sentence) + 1 > max_chars:
            passages.append(current)
            current = ""
        # Sentenças extensas são divididas somente entre palavras.
        for word in sentence.split():
            if current and len(current) + len(word) + 1 > max_chars:
                passages.append(current)
                current = ""
            current = f"{current} {word}".strip()
    if current:
        passages.append(current)
    return [passage for passage in passages if len(passage) >= 60]


def extract_passages(
    reader: PdfReader,
    document_id: str,
    filename: str,
    title: str,
    start_page: int,
    end_page: int,
    sections: list[dict] | None = None,
) -> tuple[list[Passage], list[int]]:
    if not 1 <= start_page <= end_page <= len(reader.pages):
        raise ValueError("O intervalo de páginas está fora do PDF.")
    passages = []
    skipped = []
    for page in range(start_page, end_page + 1):
        try:
            raw = reader.pages[page - 1].extract_text() or ""
        except Exception:
            skipped.append(page)
            continue
        if not readable(raw):
            skipped.append(page)
            continue
        page_title = title
        for section in sections or []:
            if section["start"] <= page <= section["end"]:
                page_title = section["title"]
                break
        chunks = split_passages(clean_text(raw))
        if not chunks:
            skipped.append(page)
        passages.extend(
            Passage(chunk, page_title, filename, page, document_id)
            for chunk in chunks
        )
    return passages, skipped


class SearchIndex:
    def __init__(self, passages: list[Passage]):
        if not passages:
            raise ValueError("Não há passagens legíveis no intervalo selecionado.")
        self.passages = passages
        self.vectorizer = TfidfVectorizer(
            strip_accents="unicode",
            lowercase=True,
            stop_words=STOP_WORDS,
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=50000,
        )
        try:
            self.matrix = self.vectorizer.fit_transform(p.text for p in passages)
        except ValueError as error:
            raise ValueError("O texto extraído não contém vocabulário suficiente.") from error

    def search(self, query: str, limit: int = 3, min_score: float = 0.12):
        if not query.strip() or limit < 1:
            return []
        vector = self.vectorizer.transform([query])
        if vector.nnz == 0:
            return []
        scores = cosine_similarity(vector, self.matrix).ravel()
        order = scores.argsort()[::-1]
        results = []
        seen = set()
        for position in order:
            score = float(scores[position])
            if score <= 0 or score < min_score:
                break
            passage = self.passages[position]
            # Uma alternativa por página, evitando repetir fragmentos vizinhos.
            page_key = (passage.document_id, passage.page)
            if page_key in seen:
                continue
            seen.add(page_key)
            results.append((passage, score))
            if len(results) == limit:
                break
        return results
