# проверка разбора разделов и нарезки, запускается при сборке образа
from chunking import FOOTER, MAX_CHARS, chunk_section, split_sections

secs = split_sections(["1. Общие", "Текст про", "отпуск.", "2. Второй", "Ещё."])
assert secs == [("1. Общие", "Текст про отпуск."), ("2. Второй", "Ещё.")], secs
assert chunk_section("Коротко.") == ["Коротко."]
long = " ".join(f"Предложение номер {i} про суточные и проезд." for i in range(30))
parts = chunk_section(long)
assert len(parts) > 1 and all(len(p) <= MAX_CHARS + 60 for p in parts)
assert parts[0].split(". ")[-1].rstrip(".") in parts[1]   # перекрытие в одно предложение
assert FOOTER.match("Внутренний документ. Страница 3")
print("test_chunking: OK")
