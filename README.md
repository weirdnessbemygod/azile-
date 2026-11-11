# azile

Chatbot experimental que seleciona passagens de Georges Bataille por similaridade textual em um acervo curado.

## Proposta

Receber uma mensagem e selecionar um trecho do acervo usando TF-IDF e similaridade de cosseno. Cada resposta deverá exibir sua referência e a informação sobre a tradução.

## Acervo inicial

O arquivo [data/trechos.csv](data/trechos.csv) contém dois fragmentos curtos de *L’Expérience intérieure*, com tradução de trabalho em português. A fonte francesa está registrada em cada entrada. Os fragmentos pertencem à mesma passagem e servem apenas para iniciar a estrutura dos dados.

As traduções de trabalho devem ser revisadas antes de uso acadêmico. Ao incluir trechos de uma edição publicada, registrar tradutor, edição e página conferida. Os temas são etiquetas editoriais para organizar a busca.

## Desenvolvimento

O repositório contém a estrutura inicial do acervo. A busca textual e a interface Streamlit serão implementadas após ampliar a curadoria.

## Autoria

Projeto experimental de Beatriz Barreto Pinto. Os trechos citados são de Georges Bataille.
