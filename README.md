<div align="center">

# azile

**leituras em diálogo**

Uma pergunta sua. Leituras com fontes.

Python · Streamlit · scikit-learn · PDF

</div>

## O experimento

Azile é um anagrama de ELIZA. Neste projeto, a interface de conversa dá acesso a um acervo de PDFs de Georges Bataille. A cada mensagem, o aplicativo busca passagens próximas e apresenta o texto extraído com título da obra, arquivo e página do PDF.

A recuperação utiliza **TF-IDF e similaridade de cosseno**, sem embeddings. No modo **Consultar trechos**, cada pergunta é uma busca independente, com até três resultados. O modo opcional **Conversar com IA** usa até seis fontes recuperadas e um modelo configurado no Ollama para elaborar uma síntese interpretativa. Esse modo ainda precisa de avaliação com um modelo real e com os livros.

## Experimentar no computador

Requer Python 3.10 ou superior. Baixe o repositório e abra o terminal na pasta do projeto.

```bash
python -m venv .venv
```

No Windows PowerShell, ative o ambiente com:

```powershell
.venv\Scripts\Activate.ps1
```

No macOS ou Linux:

```bash
source .venv/bin/activate
```

Instale as dependências e abra a interface:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

O terminal informa o endereço local, normalmente `http://localhost:8501`.

## Consultar o acervo

1. Carregue seus PDFs na barra lateral. São aceitos até cinco arquivos, com limite de 30 MB por arquivo e 100 MB no total.
2. Confira os títulos e os intervalos de páginas. Use a prévia para examinar o texto extraído.
3. Clique em **preparar acervo**.
4. Escreva uma pergunta ou algumas palavras. Por exemplo, “transgressão e interdito”, “despesa improdutiva e luxo” ou “continuidade e morte”.
5. Leia a passagem selecionada e consulte a referência e as alternativas.

Ao modificar os arquivos, títulos ou intervalos, prepare o acervo novamente. A conversa é reiniciada para acompanhar a seleção atual.

## Conversar com IA (experimental)

1. Instale o [Ollama](https://ollama.com/) no computador que executa a Azile.
2. Instale um modelo de conversa adequado à memória do seu computador. Não há modelo incluído nem download automático neste projeto. Consulte o catálogo do Ollama e use `ollama pull NOME_DO_MODELO` com o nome escolhido.
3. Confirme o nome instalado com `ollama list` e mantenha o serviço Ollama em execução.
4. Abra a Azile, selecione **Conversar com IA** e informe esse nome na barra lateral.
5. Autorize o envio da pergunta, histórico recente e passagens ao servidor configurado. Carregue os PDFs, prepare o acervo e pergunte.

Por padrão, o app chama `http://localhost:11434/api/chat`. `localhost` é o computador/servidor que executa o Streamlit, não o navegador do visitante. Se a Azile estiver hospedada, instalar Ollama no computador do visitante não conecta os dois automaticamente.

Configuração opcional no PowerShell, antes de iniciar o Streamlit:

```powershell
$env:AZILE_MODEL = "NOME_DO_MODELO_INSTALADO"
$env:AZILE_OLLAMA_URL = "http://localhost:11434"
python -m streamlit run app.py
```

Um endereço remoto deve usar HTTPS. O conector atual não implementa autenticação de servidor remoto; prefira o Ollama local e não exponha esse serviço publicamente. Nenhuma API paga é acionada por padrão. O desempenho e a qualidade dependem do modelo e do hardware.

A geração usa uma janela de até seis mensagens anteriores, com limites de tamanho. Referências à conversa anterior podem expandir a consulta com a última pergunta do usuário; essa heurística lexical pode trazer resultados irrelevantes. O histórico não é fonte documental. Trocar o acervo ou limpar a conversa remove o histórico usado pela IA.

Cada parágrafo gerado deve indicar IDs das fontes recuperadas. O código rejeita referências inexistentes e respostas fora do formato esperado; isso **não garante que a interpretação esteja sustentada pelo trecho**. Confira as passagens. Não há verificador semântico nem garantia contra alucinações. As fontes e o histórico são tratados como dados, com instruções para ignorar comandos contidos neles; isso não elimina todos os riscos de injeção de prompt.

Sem resultados, o app não chama o modelo. Se ele indicar evidência insuficiente, a interface informa isso; em caso de falha, apresenta um aviso e mantém os trechos disponíveis. Não há nova tentativa automática nem geração a cada renderização da interface.

Contrato da integração: [documentação de chat do Ollama](https://docs.ollama.com/api/chat).

## Preparação e referências

O arquivo `profiles.json` contém intervalos iniciais sugeridos para três cópias examinadas durante o desenvolvimento. Cada cópia é reconhecida pelo SHA-256 do arquivo completo, permitindo renomear o PDF sem perder a configuração.

| Cópia examinada | Páginas do PDF sugeridas | Observação |
| --- | --- | --- |
| O erotismo | 7–177 | Exclui capas, ficha editorial, sumário e apresentação dos editores |
| História do olho | 13–52 | Exclui o prefácio da tradutora e os ensaios finais de outros autores |
| A noção de despesa / A parte maldita | 19–160 | Exclui a introdução de outro autor e identifica cada obra por intervalo |

Esses intervalos são pontos de partida sujeitos à revisão. Para outras cópias, selecione manualmente as páginas do texto que deseja consultar. Os metadados de título fornecidos pelo usuário orientam a referência exibida.

As referências indicam a **posição da página no PDF, contando a capa**, que pode diferir da página impressa. O PDF de História do olho tem páginas duplas e erros de OCR. Citações internas de outros autores também podem estar presentes no texto de Bataille. Confira o contexto e a edição antes de usar uma passagem como citação acadêmica.

## Como funciona

| Etapa | Implementação |
| --- | --- |
| Leitura | pypdf extrai texto por página no intervalo escolhido |
| Preparação | Normaliza espaços, remove números de página isolados e reúne palavras hifenizadas entre linhas |
| Fragmentação | Separa passagens de até 700 caracteres, respeitando palavras e preferindo limites de frases |
| Representação | TF-IDF com palavras e pares de palavras, remoção de termos frequentes em português e normalização de acentos |
| Recuperação | Similaridade de cosseno com até três páginas distintas acima do limiar escolhido |
| Exibição | Passagem extraída, obra, arquivo e página do PDF |

Uma consulta sem vocabulário compartilhado ou sem resultados acima do limiar recebe uma mensagem para reformular a busca. O valor de similaridade representa proximidade lexical e não deve ser interpretado como probabilidade de compreensão.

## Escopo da primeira versão

A busca depende das palavras presentes no texto. Sinônimos, perguntas abstratas e mensagens muito curtas podem recuperar resultados fracos. No modo textual, a consulta considera a mensagem atual. Há espaço para explorar embeddings e avaliação de relevância em versões futuras.

Páginas com pouco texto ou codificação claramente defeituosa são informadas no relatório de leitura. O aplicativo depende da camada textual do PDF. Documentos digitalizados podem precisar de OCR prévio, e erros que formam palavras aparentemente válidas podem passar pelo filtro.

Os PDFs e a conversa são mantidos na memória da sessão do Streamlit, no computador ou servidor que executa o aplicativo. Alterações no acervo ou o botão de limpeza reiniciam o histórico visível. Os livros são fornecidos pelo usuário durante o uso e ficam fora do repositório.

## Arquivos

| Arquivo | Responsabilidade |
| --- | --- |
| `app.py` | Interface, seleção de páginas, modos de consulta e histórico de sessão |
| `conversation.py` | Contexto limitado, cliente Ollama e validação de referências |
| `tests/` | Testes automatizados da geração e da interface |
| `search.py` | Extração, fragmentação e busca |
| `profiles.json` | Intervalos de leitura para cópias examinadas |
| `requirements.txt` | Dependências Python |
| `.streamlit/config.toml` | Tema visual e limite de upload |
| `data/` | Curadoria de frases da etapa inicial, separada da busca nos PDFs |

## Verificação e limites da entrega

Para executar os testes automatizados:

```bash
python -m unittest discover -s tests -v
```

Os testes do conector usam respostas simuladas: validam contexto, referências inexistentes, ausência de fontes, formato e falhas de rede sem baixar modelos ou enviar os livros. Os testes da interface verificam consulta textual e geração simulada.

A documentação anterior registrava 1.728 passagens e verificações manuais nas três cópias. Esse é um registro histórico, não um resultado dos testes da integração com IA. A quantidade varia conforme os PDFs e intervalos escolhidos.

**Pendente:** teste integrado com Ollama e modelo real, avaliação humana das respostas nos livros, comparação de relevância e avaliação de desempenho no computador de uso. A busca semântica com embeddings é uma etapa futura; esta entrega mantém recuperação lexical.

Roteiro manual: compare uma pergunta conceitual nos dois modos, uma pergunta de continuação, uma pergunta sem evidência, o servidor desligado e a limpeza do histórico. Confira cada referência no PDF. Não use somente a fluência da resposta como medida de qualidade.

## Autoria

Projeto experimental de **Beatriz Barreto Pinto**, conectando estudos de sistemas conversacionais, leitura e programação. Os textos retornados pertencem às obras carregadas e às respectivas traduções.

Os arquivos de curadoria em `data/` preservam a etapa anterior do projeto. Frases marcadas como atribuições a conferir continuam pendentes de verificação. A versão atual consulta exclusivamente os PDFs carregados na sessão.
