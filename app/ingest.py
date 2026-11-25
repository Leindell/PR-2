"""Стадии 1-3: ingestion -> chunking -> embedding -> запись в pgvector. Инкрементально по sha256."""
import hashlib
import os
from pathlib import Path

import psycopg
from fastembed import TextEmbedding
from pgvector.psycopg import register_vector

from chunking import chunk_section, extract_docx, extract_pdf

DOCS = Path("/docs")
model = TextEmbedding(os.environ["EMBED_MODEL"])

with psycopg.connect(os.environ["PG_DSN"]) as conn:
    register_vector(conn)
    stats = {"new_or_changed": 0, "skipped_unchanged": 0, "chunks": 0}
    for path in sorted(DOCS.glob("*")):
        if path.suffix not in (".pdf", ".docx"):
            continue
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        row = conn.execute("SELECT sha256 FROM documents WHERE source_path = %s", (path.name,)).fetchone()
        if row and row[0] == sha:
            stats["skipped_unchanged"] += 1
            continue

        title, sections = (extract_pdf if path.suffix == ".pdf" else extract_docx)(path)
        chunks = [(sec, i, txt) for sec, body in sections for i, txt in enumerate(chunk_section(body))]
        # в эмбеддинг кладём и контекст (документ + раздел): короткий чанк без него теряет смысл
        vectors = list(model.embed([f"{title}. {sec}. {txt}" for sec, _, txt in chunks]))

        with conn.transaction():  # документ заменяется целиком: старые чанки удаляются каскадом
            conn.execute("DELETE FROM documents WHERE source_path = %s", (path.name,))
            doc_id = conn.execute(
                "INSERT INTO documents (source_path, title, doc_format, sha256) VALUES (%s, %s, %s, %s) "
                "RETURNING doc_id", (path.name, title, path.suffix[1:], sha)).fetchone()[0]
            with conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO chunks (doc_id, section, chunk_no, content, n_chars, embedding) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    [(doc_id, sec, i, txt, len(txt), vec) for (sec, i, txt), vec in zip(chunks, vectors)])
        stats["new_or_changed"] += 1
        stats["chunks"] += len(chunks)
        print(f"  {path.name}: {len(sections)} sections -> {len(chunks)} chunks")
    total = conn.execute("SELECT count(*), round(avg(n_chars)), max(n_chars) FROM chunks").fetchone()
    print(f"ingest: {stats}; in db: {total[0]} chunks, avg {total[1]} chars, max {total[2]}")
