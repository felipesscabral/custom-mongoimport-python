import csv
import argparse
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

def read_flat_file(file_path, delimiter, has_header=True):
    try:
        f = open(file_path, 'r', newline='', encoding='utf-8')
        # Use the provided 'delimiter' parameter
        reader = csv.reader(f, delimiter=delimiter, quotechar='"', doublequote=True)

        header = None
        num_expected_fields = 0
        first_data_row = None

        if has_header:
            try:
                header = next(reader)
                num_expected_fields = len(header)
                print(f"[DEBUG] Cabeçalho encontrado: {header}")
                print(f"[DEBUG] Número de campos esperado (do cabeçalho): {num_expected_fields}")
            except StopIteration:
                print(f"[ERROR] Arquivo '{file_path}' está vazio ou não possui cabeçalho.")
                f.close()
                return None, None
            except Exception as e:
                print(f"[ERROR] Erro ao ler o cabeçalho: {e}")
                f.close()
                return None, None
        else:
            print("[DEBUG] Nenhum cabeçalho esperado. Inferindo campos da primeira linha de dados.")
            try:
                first_data_row = next(reader)
                num_expected_fields = len(first_data_row)
                header = [f"field_{i+1}" for i in range(num_expected_fields)]
                print(f"[DEBUG] Cabeçalho inferido: {header}")
                print(f"[DEBUG] Número de campos esperado (inferido): {num_expected_fields}")
            except StopIteration:
                print(f"[ERROR] Arquivo '{file_path}' está vazio.")
                f.close()
                return None, None
            except Exception as e:
                print(f"[ERROR] Erro ao ler a primeira linha sem cabeçalho: {e}")
                f.close()
                return None, None

        def record_generator():
            nonlocal num_expected_fields
            nonlocal header

            if not has_header and first_data_row:
                yield first_data_row

            line_number = 1 if has_header else (1 if first_data_row else 0)
            for row in reader:
                line_number += 1
                if num_expected_fields == 0 and len(row) > 0:
                    num_expected_fields = len(row)
                    if not has_header:
                        header = [f"field_{i+1}" for i in range(num_expected_fields)]
                    print(f"[DEBUG] Número de campos inferido da primeira linha de dados em tempo de execução: {num_expected_fields}")

                if len(row) == num_expected_fields:
                    yield row
                else:
                    print(f"[WARNING] Linha {line_number} com inconsistência de campos ({len(row)} vs {num_expected_fields}). Ignorando: {row}")
        
        return header, record_generator()

    except FileNotFoundError:
        print(f"[FATAL] Erro: O arquivo '{file_path}' não foi encontrado.")
        return None, None
    except Exception as e:
        print(f"[FATAL] Ocorreu um erro ao abrir/ler o arquivo: {e}")
        return None, None

def import_pipe_csv(uri, db_name, coll_name, file_path, delimiter, batch_size, headerline, drop, coerce):
    print(f"[INFO] Conectando ao MongoDB em: {uri}")
    client = None
    try:
        client = MongoClient(uri)
        client.admin.command('ping')
        print("[INFO] Conexão com MongoDB estabelecida com sucesso.")
    except Exception as e:
        print(f"[FATAL] Erro ao conectar ao MongoDB: {e}")
        return

    db = client[db_name]
    collection = db[coll_name]

    if drop:
        print(f"[INFO] Dropando coleção '{coll_name}' no banco de dados '{db_name}'...")
        collection.drop()
        print("[INFO] Coleção dropada com sucesso.")

    # Pass the 'delimiter' to read_flat_file
    header, records_generator = read_flat_file(file_path, delimiter, has_header=headerline)

    if not header or not records_generator:
        print("[FATAL] Não foi possível processar o arquivo. Nenhuma importação será realizada.")
        client.close()
        return

    docs_to_insert = []
    total_inserted = 0
    skipped_count = 0

    print(f"[INFO] Iniciando importação para '{db_name}.{coll_name}' do arquivo '{file_path}' com delimitador '{delimiter}'...")
    try:
        for i, record in enumerate(records_generator):
            if len(record) != len(header):
                print(f"[WARNING] Registro na linha {i+1} não corresponde ao número de campos do cabeçalho ({len(record)} vs {len(header)}). Ignorando: {record}")
                skipped_count += 1
                continue

            doc = {}
            for j, field_name in enumerate(header):
                doc[field_name] = record[j]
            docs_to_insert.append(doc)

            if len(docs_to_insert) >= batch_size:
                try:
                    collection.insert_many(docs_to_insert)
                    total_inserted += len(docs_to_insert)
                    print(f"[PROGRESS] Inseridos {total_inserted} documentos até agora. (Batch de {len(docs_to_insert)})")
                    docs_to_insert = []
                except BulkWriteError as bwe:
                    print(f"[ERROR] Erro de escrita em lote: {bwe.details}")
                    for error in bwe.details.get('writeErrors', []):
                        print(f"[ERROR] Erro no documento: {error}")
                    docs_to_insert = []
                except Exception as e:
                    print(f"[ERROR] Erro inesperado ao inserir lote: {e}")
                    docs_to_insert = []

        if docs_to_insert:
            try:
                collection.insert_many(docs_to_insert)
                total_inserted += len(docs_to_insert)
                print(f"[INFO] Inseridos {total_inserted} documentos no total. (Lote final de {len(docs_to_insert)})")
            except BulkWriteError as bwe:
                print(f"[ERROR] Erro de escrita no lote final: {bwe.details}")
                for error in bwe.details.get('writeErrors', []):
                    print(f"[ERROR] Erro no documento: {error}")
            except Exception as e:
                print(f"[ERROR] Erro inesperado ao inserir lote final: {e}")

        print(f"\n[SUCCESS] Importação concluída. Total de documentos inseridos: {total_inserted}")
        if skipped_count > 0:
            print(f"[WARNING] Total de documentos ignorados devido a inconsistência de campos: {skipped_count}")

    except Exception as e:
        print(f"[FATAL] Ocorreu um erro crítico durante a importação: {e}")
    finally:
        if client:
            client.close()
            print("[INFO] Conexão com MongoDB fechada.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Importa arquivo de texto delimitado com aspas duplas para o MongoDB.")
    ap.add_argument("--uri", default="mongodb://localhost:27017/", help="URI de conexão do MongoDB.")
    ap.add_argument("-d", "--db", required=True, help="Nome do banco de dados MongoDB.")
    ap.add_argument("-c", "--collection", required=True, help="Nome da coleção MongoDB.")
    ap.add_argument("--file", required=True, help="Caminho para o arquivo flatfile de entrada.")
    # Add new argument for delimiter
    ap.add_argument("--delimiter", default="|", help="Caractere delimitador de campos no arquivo (padrão: '|').")
    ap.add_argument("--batchSize", type=int, default=1000, help="Número de documentos para inserir por lote.")
    ap.add_argument("--noHeaderline", action="store_true", help="Indica que o arquivo não possui linha de cabeçalho.")
    ap.add_argument("--drop", action="store_true", help="Dropa a coleção antes de iniciar a importação.")
    ap.add_argument("--noCoerce", action="store_true", help="Não tenta converter tipos de dados (todos os campos serão string).")
    
    print("[DEBUG] Analisando argumentos da linha de comando...")
    args = ap.parse_args()
    print(f"[DEBUG] Argumentos recebidos: {args}")

    import_pipe_csv(
        uri=args.uri,
        db_name=args.db,
        coll_name=args.collection,
        file_path=args.file,
        delimiter=args.delimiter, # Pass the new delimiter argument
        batch_size=args.batchSize,
        headerline=not args.noHeaderline,
        drop=args.drop,
        coerce=not args.noCoerce,
    )
    print("[DEBUG] Função import_pipe_csv finalizada.")