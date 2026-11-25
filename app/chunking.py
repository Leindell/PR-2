"""Стадии 1-2: извлечение текста (PDF/DOCX), очистка и чанкинг по структуре документа."""
import re

HEADING = re.compile(r"^\d+\.\s+\S")                      # "3. Проезд и проживание"
FOOTER = re.compile(r"^Внутренний документ\. Страница \d+$")
MAX_CHARS, OVERLAP_SENT = 400, 1


def extract_pdf(path):
    """PDF -> (title, [(section, text)]). Заголовки разделов - строки вида 'N. ...'."""
    from pypdf import PdfReader
    lines = []
    for page in PdfReader(path).pages:
        for ln in page.extract_text().splitlines():
            ln = ln.strip()
            if ln and not FOOTER.match(ln):              # очистка: колонтитулы, пустые строки
                lines.append(ln)
    return lines[0], split_sections(lines[1:])


def extract_docx(path):
    from docx import Document
    d = Document(path)
    title, lines = None, []
    for p in d.paragraphs:
        t = p.text.strip()
        if not t:
            continue
        if p.style.name == "Title" and title is None:
            title = t
        else:
            lines.append(t)
    return title, split_sections(lines)


def split_sections(lines):
    sections, head, buf = [], "Без раздела", []
    for ln in lines:
        if HEADING.match(ln) and len(ln) < 90:
            if buf:
                sections.append((head, " ".join(buf)))
            head, buf = ln, []
        else:
            buf.append(ln)
    if buf:
        sections.append((head, " ".join(buf)))
    # PDF рвёт строки посередине слова/фразы: склеиваем и нормализуем пробелы
    return [(h, re.sub(r"\s+", " ", t).strip()) for h, t in sections]


def chunk_section(text):
    """Раздел короче MAX_CHARS - один чанк. Длиннее - режем по предложениям с перекрытием в 1 предложение."""
    if len(text) <= MAX_CHARS:
        return [text]
    sents = re.split(r"(?<=[.!?])\s+", text)
    chunks, cur = [], []
    for s in sents:
        if cur and len(" ".join(cur + [s])) > MAX_CHARS:
            chunks.append(" ".join(cur))
            cur = cur[-OVERLAP_SENT:]
        cur.append(s)
    chunks.append(" ".join(cur))
    return chunks
