<div align="center">

# azile

**leituras em diálogo**

Uma pergunta sua. Uma passagem dos livros.

Python · Streamlit · scikit-learn · PDF

</div>

## O experimento

Azile é um anagrama de ELIZA. Neste projeto, a interface de conversa dá acesso a um acervo de PDFs de Georges Bataille. A cada mensagem, o aplicativo busca passagens próximas e apresenta o texto extraído com título da obra, arquivo e página do PDF.

O protótipo utiliza **TF-IDF e similaridade de cosseno**. Cada pergunta é uma busca independente. A interface permite inspecionar até três resultados e ajustar o limiar de similaridade.

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

## Conversar com o acervo

1. Carregue seus PDFs na barra lateral. São aceitos até cinco arquivos, com limite de 30 MB por arquivo e 100 MB no total.
2. Confira os títulos e os intervalos de páginas. Use a prévia para examinar o texto extraído.
3. Clique em **preparar acervo**.
4. Escreva uma pergunta ou algumas palavras. Por exemplo, “transgressão e interdito”, “despesa improdutiva e luxo” ou “continuidade e morte”.
5. Leia a passagem selecionada e consulte a referência e as alternativas.

Ao modificar os arquivos, títulos ou intervalos, prepare o acervo novamente. A conversa é reiniciada para acompanhar a seleção atual.

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

A busca depende das palavras presentes no texto. Sinônimos, perguntas abstratas e mensagens muito curtas podem recuperar resultados fracos. A consulta considera a mensagem atual. Há espaço para explorar embeddings e avaliação de relevância em versões futuras.

Páginas com pouco texto ou codificação claramente defeituosa são informadas no relatório de leitura. O aplicativo depende da camada textual do PDF. Documentos digitalizados podem precisar de OCR prévio, e erros que formam palavras aparentemente válidas podem passar pelo filtro.

Os PDFs e a conversa são mantidos na memória da sessão do Streamlit, no computador ou servidor que executa o aplicativo. Alterações no acervo ou o botão de limpeza reiniciam o histórico visível. Os livros são fornecidos pelo usuário durante o uso e ficam fora do repositório.

## Arquivos

| Arquivo | Responsabilidade |
| --- | --- |
| `app.py` | Interface, seleção de páginas e conversa |
| `search.py` | Extração, fragmentação e busca |
| `profiles.json` | Intervalos de leitura para cópias examinadas |
| `requirements.txt` | Dependências Python |
| `.streamlit/config.toml` | Tema visual e limite de upload |
| `data/` | Curadoria de frases da etapa inicial, separada da busca nos PDFs |

## Verificação da primeira versão

A extração e a busca foram exercitadas nas três cópias fornecidas, produzindo 1.728 passagens com os intervalos sugeridos. Foram verificados os fluxos de carregar arquivo, preparar acervo, perguntar, limpar conversa e invalidar a busca ao alterar a seleção. Também foram conferidos arquivos inválidos, páginas vazias e consultas sem correspondência.

## Autoria

Projeto experimental de **Beatriz Barreto Pinto**, conectando estudos de sistemas conversacionais, leitura e programação. Os textos retornados pertencem às obras carregadas e às respectivas traduções.

Os arquivos de curadoria em `data/` preservam a etapa anterior do projeto. Frases marcadas como atribuições a conferir continuam pendentes de verificação. A versão atual consulta exclusivamente os PDFs carregados na sessão.
