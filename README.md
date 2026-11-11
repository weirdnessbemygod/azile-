# azile

Chatbot experimental de busca textual em um acervo curado de passagens atribuídas a Georges Bataille.

## Proposta

Receber uma mensagem e selecionar um trecho usando TF-IDF e similaridade de cosseno. Cada resposta deverá indicar sua referência e a informação sobre a tradução.

## Curadoria do acervo

| Arquivo | Conteúdo | Situação |
| --- | --- | --- |
| [data/trechos.csv](data/trechos.csv) | Dois fragmentos curtos de *L’Expérience intérieure* | Traduções de trabalho com fonte francesa registrada |
| [data/em_revisao.csv](data/em_revisao.csv) | Vinte frases fornecidas pela autora do projeto, organizadas em quatro temas | Atribuição e redação a conferir |

Os temas são erotismo e morte, conhecimento e filosofia, economia geral e soberania, experiência interior e sagrado.

As frases em revisão podem incluir paráfrases. Sua autoria e sua redação literal ainda precisam ser conferidas em uma edição identificada. Cada registro possui campos para obra, edição, tradutor, página e fonte.

O conjunto em revisão está reservado à curadoria. A seleção de respostas do chatbot deverá utilizar apenas trechos aprovados, com a situação da tradução informada.

## Desenvolvimento

O repositório contém a estrutura inicial do acervo. A busca textual e a interface Streamlit serão implementadas na próxima etapa.

## Autoria

Projeto experimental de Beatriz Barreto Pinto. As atribuições dos textos seguem a situação de verificação registrada nos arquivos do acervo.
