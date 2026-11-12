"""azile — interface de conversa para explorar PDFs por busca textual."""

import hashlib
import json
import os
from pathlib import Path

import streamlit as st

from search import SearchIndex, extract_passages, open_pdf
from conversation import GenerationError, generate_answer, retrieval_query


st.set_page_config(page_title="azile · leituras em diálogo", page_icon="◌", layout="wide")
st.markdown(
    """<style>
    .block-container { max-width: 1000px; padding-top: 2.5rem; }
    h1 { font-family: Georgia, serif; font-size: 4.5rem !important;
         font-weight: 400 !important; letter-spacing: -.06em; }
    [data-testid="stChatMessage"] { border: 1px solid #38312b; border-radius: 14px; }
    </style>""",
    unsafe_allow_html=True,
)

profiles = json.loads((Path(__file__).parent / "profiles.json").read_text(encoding="utf-8"))

st.caption("UM EXPERIMENTO DE LEITURA · GEORGES BATAILLE")
st.title("azile")
st.markdown("Uma pergunta sua. Leituras com fontes.")
st.caption("Consulte passagens dos PDFs ou experimente uma síntese com IA configurada no servidor.")

with st.sidebar:
    st.subheader("modo de leitura")
    mode = st.radio("Como responder", ["Consultar trechos", "Conversar com IA"])
    model = st.text_input("Modelo instalado no Ollama", value=os.environ.get("AZILE_MODEL", ""))
    if mode == "Conversar com IA":
        st.caption("Requer Ollama e um modelo instalado no computador que executa a Azile. Nenhum modelo é baixado automaticamente.")
        ai_consent = st.checkbox("Enviar minha pergunta, histórico recente e trechos ao servidor de IA configurado")
    else:
        ai_consent = False
    st.subheader("seu acervo")
    uploads = st.file_uploader("Carregue até 5 PDFs", type=["pdf"], accept_multiple_files=True)
    st.caption("Os arquivos são processados na memória desta sessão, no computador ou servidor que executa o app.")

if not uploads:
    for key in list(st.session_state):
        if key.startswith("reader_"):
            del st.session_state[key]
    st.session_state.pop("active_corpus", None)
    st.session_state.pop("index", None)
    st.session_state.pop("report", None)
    st.session_state["messages"] = []
    st.info("Comece carregando os livros na barra lateral. Depois escolha as páginas e prepare o acervo.")
    st.markdown("**Para experimentar**\n\n• o que significa gastar sem utilidade?\n\n• por que o interdito se relaciona com a transgressão?\n\n• o que buscamos na continuidade?")
    st.stop()

if len(uploads) > 5 or sum(file.size for file in uploads) > 100 * 1024 * 1024:
    st.error("Use até 5 arquivos e no máximo 100 MB no total.")
    st.stop()

documents = []
with st.sidebar:
    for upload in uploads:
        content = upload.getvalue()
        digest = hashlib.sha256(content).hexdigest()
        # O nome integra a chave para aceitar cópias idênticas com nomes distintos.
        document_id = hashlib.sha256(content + upload.name.encode()).hexdigest()
        reader_key = f"reader_{document_id}"
        if reader_key not in st.session_state:
            try:
                st.session_state[reader_key] = open_pdf(content)
            except ValueError as error:
                st.error(f"{upload.name}: {error}")
                continue
        reader = st.session_state[reader_key]
        profile = profiles.get(digest, {})
        page_count = len(reader.pages)
        with st.expander(upload.name, expanded=len(uploads) == 1):
            title = st.text_input(
                "Título da obra", value=profile.get("title", Path(upload.name).stem),
                key=f"title_{document_id}",
            ).strip()
            start = int(st.number_input(
                "Primeira página do PDF", min_value=1, max_value=page_count,
                value=profile.get("start", 1), key=f"start_{document_id}",
            ))
            end = int(st.number_input(
                "Última página do PDF", min_value=1, max_value=page_count,
                value=profile.get("end", page_count), key=f"end_{document_id}",
            ))
            st.caption(profile.get("note", "Escolha o texto da obra. Prefácios e ensaios podem ter outros autores."))
            preview = int(st.number_input(
                "Prévia da página", min_value=1, max_value=page_count,
                value=profile.get("start", 1), key=f"preview_{document_id}",
            ))
            if st.checkbox("Ver texto extraído", key=f"show_{document_id}"):
                try:
                    st.text((reader.pages[preview - 1].extract_text() or "Página sem texto extraível.")[:2500])
                except Exception:
                    st.warning("Não foi possível extrair esta página.")
        documents.append({
            "id": document_id, "reader": reader, "filename": upload.name,
            "title": title, "start": start, "end": end,
            "sections": profile.get("sections", []) if title == profile.get("title") else [],
        })

    # Descarta leitores de arquivos removidos, sem cache global compartilhado.
    reader_keys = {f"reader_{document['id']}" for document in documents}
    for key in list(st.session_state):
        if key.startswith("reader_") and key not in reader_keys:
            del st.session_state[key]
    min_score = st.slider("Similaridade mínima", 0.05, 0.40, 0.12, 0.01)
    st.caption("A similaridade mede proximidade lexical. Ajuste para explorar resultados mais amplos ou mais restritos.")
    build = st.button("preparar acervo", type="primary", use_container_width=True)

signature = tuple((doc["id"], doc["title"], doc["start"], doc["end"]) for doc in documents)
if st.session_state.get("active_corpus") != signature:
    st.session_state.pop("index", None)
    st.session_state.pop("report", None)
    st.session_state["messages"] = []

if build:
    st.session_state.pop("index", None)
    st.session_state.pop("report", None)
    st.session_state["messages"] = []
    if not documents or any(not doc["title"] or doc["start"] > doc["end"] for doc in documents):
        st.error("Confira o título e o intervalo de páginas de cada arquivo.")
    else:
        passages = []
        report = []
        with st.spinner("Lendo páginas e preparando a busca…"):
            for doc in documents:
                extracted, skipped = extract_passages(
                    doc["reader"], doc["id"], doc["filename"], doc["title"],
                    doc["start"], doc["end"], doc["sections"],
                )
                passages.extend(extracted)
                report.append({"arquivo": doc["filename"], "trechos": len(extracted), "paginas_ignoradas": skipped})
            try:
                index = SearchIndex(passages)
            except ValueError as error:
                st.error(str(error))
            else:
                st.session_state["index"] = index
                st.session_state["report"] = report
                st.session_state["active_corpus"] = signature

if "index" not in st.session_state:
    st.info("Confira os títulos e as páginas na barra lateral e clique em preparar acervo.")
    st.stop()

index = st.session_state["index"]
st.caption(f"{len(documents)} arquivo(s) · {len(index.passages):,} passagens disponíveis")
with st.expander("sobre a leitura dos arquivos"):
    for item in st.session_state["report"]:
        st.write(f"{item['arquivo']} — {item['trechos']} trechos")
        if item["paginas_ignoradas"]:
            st.caption("Páginas sem texto suficiente, com erro ou codificação inadequada: " + ", ".join(map(str, item["paginas_ignoradas"])))
    st.caption("As referências usam a posição da página no PDF, contando a capa. Páginas duplas e erros de OCR permanecem sujeitos à revisão da edição. No modo IA, referências à conversa anterior podem ampliar a busca lexical.")

if st.sidebar.button("limpar conversa", use_container_width=True):
    st.session_state["messages"] = []


def display_answer(message):
    if message.get("error"):
        st.warning(message["error"])
    if message.get("kind") == "generated":
        st.caption(f"Síntese interpretativa gerada por IA · {message['model']}")
        for paragraph in message["paragraphs"]:
            st.text(paragraph["texto"])
            st.caption("Fontes: " + ", ".join(f"[{i}]" for i in paragraph["fontes"]))
        st.caption("Referências conferidas quanto à existência; a fidelidade da interpretação precisa de leitura humana.")
    elif message.get("kind") == "insufficient":
        st.info("Os trechos recuperados não foram suficientes para elaborar uma resposta fundamentada. Reformule a pergunta ou consulte as passagens abaixo.")
    if not message["results"]:
        st.write("Não encontrei uma passagem suficientemente próxima. Tente outras palavras ou ajuste a similaridade mínima.")
        return
    if message.get("kind") != "generated":
        passage, score = message["results"][0]
        st.text(passage.text)
        st.caption(f"[1] {passage.title} · página {passage.page} do PDF · similaridade lexical {score:.2f}")
    with st.expander("conferir fontes e trechos"):
        for i, (passage, score) in enumerate(message["results"], 1):
            st.text(passage.text)
            st.caption(f"[{i}] {passage.title} · página {passage.page} do PDF · similaridade lexical {score:.2f}")
            st.text(f"Arquivo: {passage.filename}")


for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.text(message["text"])
        else:
            display_answer(message)

query = st.chat_input("escreva uma pergunta ou uma palavra…", max_chars=1000,
                      disabled=mode == "Conversar com IA" and (not model.strip() or not ai_consent))
if query:
    history = st.session_state["messages"][:]
    st.session_state["messages"].append({"role": "user", "text": query})
    with st.chat_message("user"):
        st.text(query)
    search_query = retrieval_query(query, history) if mode == "Conversar com IA" else query
    results = index.search(search_query, limit=6 if mode == "Conversar com IA" else 3, min_score=min_score)
    answer = {"role": "assistant", "results": results, "kind": "search"}
    if mode == "Conversar com IA" and results:
        try:
            with st.spinner("Relacionando a pergunta aos trechos do acervo…"):
                paragraphs = generate_answer(query, results, history, model)
            answer.update(kind="generated" if paragraphs else "insufficient", paragraphs=paragraphs, model=model)
        except GenerationError as error:
            answer["error"] = str(error)
    st.session_state["messages"].append(answer)
    with st.chat_message("assistant"):
        display_answer(answer)
