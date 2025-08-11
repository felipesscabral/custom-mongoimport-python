# 📦 mongoimport.py

Um script Python flexível para importar dados de arquivos flatfile delimitados (como CSV ou arquivos Pipe-Delimited) para o MongoDB. Ele lida com campos de texto livre que podem conter quebras de linha, garantindo que cada registro seja importado como um único documento no MongoDB.

-----

## ✨ Funcionalidades

  * **Leitura de Arquivos Delimitados:** Suporta delimitadores configuráveis (padrão: `|`).
  * **Manipulação de Campos Citados:** Lida corretamente com campos de string envoltos em aspas duplas (`"`) que podem conter o delimitador ou quebras de linha internas.
  * **Inferência/Validação de Cabeçalho:** Lê o cabeçalho do arquivo para determinar a quantidade esperada de campos, ou infere a estrutura se não houver cabeçalho.
  * **Processamento em Lotes (Batch Import):** Insere documentos no MongoDB em lotes para melhor performance.
  * **Controle de Coleção:** Opção para dropar (excluir) a coleção antes da importação.
  * **Tratamento de Linhas Problemáticas:** Avisa e ignora linhas que não correspondem à quantidade de campos esperada.

-----

## 🚀 Como Usar

### Pré-requisitos

Certifique-se de ter o Python 3 instalado e o driver `pymongo` para MongoDB:

```bash
pip install pymongo
```

### Execução

Use o script via linha de comando, especificando os parâmetros necessários:

```bash
python3 mongoimport.py --file <caminho_do_arquivo> --db <nome_do_banco> --collection <nome_da_colecao> [opções]
```

-----

## ⚙️ Parâmetros

  * `--file <caminho_do_arquivo>` ( **Obrigatório** ): O caminho para o seu arquivo flatfile de entrada (ex: `dados.csv`, `meu_arquivo.txt`).
  * `-d <nome_do_banco>`, `--db <nome_do_banco>` ( **Obrigatório** ): O nome do banco de dados no MongoDB onde os documentos serão inseridos.
  * `-c <nome_da_colecao>`, `--collection <nome_da_colecao>` ( **Obrigatório** ): O nome da coleção no MongoDB para a importação.
  * `--uri <uri_conexao>` (Opcional): URI de conexão do MongoDB (padrão: `mongodb://localhost:27017/`).
      * **Exemplo:** `--uri "mongodb://user:pass@host:port/"`
  * `--delimiter <caractere>` (Opcional): O caractere usado como delimitador de campos no arquivo (padrão: `|`).
      * **Exemplo:** `--delimiter=','` para arquivos CSV.
  * `--batchSize <numero>` (Opcional): Número de documentos para inserir por lote (padrão: `1000`).
  * `--noHeaderline` (Flag Opcional): Se presente, indica que o arquivo de entrada **não possui** uma linha de cabeçalho. O script inferirá nomes de campos genéricos (`field_1`, `field_2`, etc.).
  * `--drop` (Flag Opcional): Se presente, a coleção especificada será **dropada (excluída)** antes de iniciar a importação. **Use com cautela\!**
  * `--noCoerce` (Flag Opcional): Se presente, impede qualquer tentativa futura de converter automaticamente os tipos de dados (todos os campos serão importados como strings). Atualmente, a coerção de tipos não está implementada.

-----

## 📝 Exemplos de Uso

1.  **Importar um arquivo pipe-delimited (`|`) com cabeçalho:**

    ```bash
    python3 mongoimport.py --file dummy_pipe.csv --db meu_banco --collection produtos_importados
    ```

2.  **Importar um arquivo CSV (vírgula `,`) e dropar a coleção existente:**

    ```bash
    python3 mongoimport.py --file dados.csv --delimiter=',' --db vendas --collection dados_vendas --drop
    ```

3.  **Importar um arquivo sem cabeçalho e com lote de 500 documentos:**

    ```bash
    python3 mongoimport.py --file log_events.txt --delimiter='|' --db logs --collection eventos --noHeaderline --batchSize 500
    ```

4.  **Importar para um MongoDB remoto (exemplo com URI):**

    ```bash
    python3 mongoimport.py --file dados.csv --delimiter=',' --uri "mongodb://usuario:senha@meu-servidor-mongo:27017/admin" --db meu_banco --collection dados_remotos
    ```

-----

## 🗃️ Formato do Arquivo de Entrada

O arquivo flatfile deve seguir as seguintes regras para uma importação bem-sucedida:

  * **Delimitador:** Os campos devem ser separados pelo caractere especificado (padrão `|`).
  * **Campos de String Citados:** Campos que podem conter o caractere delimitador, quebras de linha ou outros caracteres especiais **devem ser envoltos em aspas duplas (`"`).**
      * **Exemplo:** `"Este é um campo com | pipe interno e\nquebra de linha."`
  * **Aspas Duplas Internas:** Se um campo citado precisar conter uma aspa dupla literal, ela deve ser duplicada.
      * **Exemplo:** `"Texto com ""aspas"" internas."`
  * **Consistência:** Todas as linhas de dados devem ter o mesmo número de campos que o cabeçalho (ou a primeira linha de dados, se não houver cabeçalho). O script avisará e ignorará as linhas que não seguirem essa consistência.

-----
