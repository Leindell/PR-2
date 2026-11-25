CREATE EXTENSION IF NOT EXISTS vector;

-- Реестр документов: хэш содержимого -> повторная загрузка неизменённого файла пропускается
CREATE TABLE documents (
    doc_id       serial PRIMARY KEY,
    source_path  text UNIQUE NOT NULL,
    title        text NOT NULL,
    doc_format   text NOT NULL,          -- pdf / docx
    sha256       text NOT NULL,
    loaded_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE chunks (
    chunk_id     bigserial PRIMARY KEY,
    doc_id       int NOT NULL REFERENCES documents ON DELETE CASCADE,
    section      text NOT NULL,          -- заголовок раздела: цитата в ответе + фильтр
    chunk_no     int NOT NULL,
    content      text NOT NULL,
    n_chars      int NOT NULL,
    embedding    vector(384) NOT NULL,   -- paraphrase-multilingual-MiniLM-L12-v2
    tsv          tsvector GENERATED ALWAYS AS (to_tsvector('russian', section || ' ' || content)) STORED
);

-- Векторный индекс: HNSW (граф), косинусная метрика. m/ef_construction - баланс полноты и памяти.
CREATE INDEX chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
-- Полнотекстовый индекс для точных терминов: номера форм, коды, аббревиатуры
CREATE INDEX chunks_tsv_gin ON chunks USING gin (tsv);
