from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from src.paths import PATH_TO_FONT


def save_string_to_pdf(text, path_to_save, filename, line_length=70):
    c = canvas.Canvas(f"{path_to_save}/{filename}.pdf", pagesize=A4)
    width, height = A4
    pdfmetrics.registerFont(TTFont("DejaVuSans", f"{PATH_TO_FONT}/DejaVuSans.ttf"))
    c.setFont("DejaVuSans", 12)

    # Разбиваем текст на строки по 90 символов (вы можете настроить это значение)
    lines = text.split('\n')
    text_lines = []
    for line in lines:
        while len(line) > line_length:
            text_lines.append(line[:line_length])
            line = line[line_length:]
        text_lines.append(line)

    # Печатаем текст в PDF, начиная с верхнего левого угла
    y = height - 40  # начальная позиция по Y
    for line in text_lines:
        if y < 40:  # если не хватает места на текущей странице, добавляем новую страницу
            c.showPage()
            c.setFont("DejaVuSans", 12)
            y = height - 40
        c.drawString(40, y, line)
        y -= 15  # смещаемся вниз на 15 пунктов

    # Сохраняем PDF
    c.save()

# Пример использования
