"""Стадия 4: поиск. Вектор (HNSW), полнотекст (GIN) и гибрид через Reciprocal Rank Fusion."""
import os

import psycopg
from fastembed import TextEmbedding
from pgvector.psycopg import register_vector

_model = TextEmbedding(os.environ["EMBED_MODEL"])
conn = psycopg.connect(os.environ["PG_DSN"], autocommit=True)
register_vector(conn)
conn.execute("SET hnsw.ef_search = 40")

COLS = "c.chunk_id, d.title, c.section, c.content, d.source_path"


def vector(q, k=5):
    emb = next(iter(_model.embed([q])))
    return conn.execute(f"SELECT {COLS} FROM chunks c JOIN documents d USING (doc_id) "
                        "ORDER BY c.embedding <=> %s LIMIT %s", (emb, k)).fetchall()


def fulltext(q, k=5):
    # OR вместо AND: вопрос на естественном языке почти никогда не содержит все слова чанка
    return conn.execute(f"""
        WITH q AS (SELECT replace(plainto_tsquery('russian', %s)::text, '&', '|')::tsquery AS tq)
        SELECT {COLS} FROM chunks c JOIN documents d USING (doc_id), q
        WHERE c.tsv @@ q.tq ORDER BY ts_rank_cd(c.tsv, q.tq) DESC LIMIT %s""", (q, k)).fetchall()


def hybrid(q, k=5, pool=20, rrf_k=60):
    """RRF: score = sum 1/(rrf_k + rank) по обоим спискам. Шкалы косинуса и ts_rank несравнимы - ранги сравнимы."""
    scores, rows = {}, {}
    for results in (vector(q, pool), fulltext(q, pool)):
        for rank, r in enumerate(results, 1):
            scores[r[0]] = scores.get(r[0], 0) + 1 / (rrf_k + rank)
            rows[r[0]] = r
    return [rows[i] for i in sorted(scores, key=scores.get, reverse=True)[:k]]


MODES = {"vector": vector, "fulltext": fulltext, "hybrid": hybrid}
