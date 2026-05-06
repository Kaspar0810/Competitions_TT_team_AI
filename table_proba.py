from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,Paragraph, Spacer, KeepTogether)
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors

# --- Настройки страницы (в сантиметрах) ---
PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)  # 29.7 cm × 21.0 cm
MARGIN = 1.5 * cm
GAP_BETWEEN_TABLES = 0.6 * cm
HEADER_HEIGHT = 0.8 * cm

# Доступная ширина и высота
available_width = PAGE_WIDTH - 2 * MARGIN - GAP_BETWEEN_TABLES  # минус промежуток
table_width = available_width / 2  # поровну на две таблицы
available_height = PAGE_HEIGHT - 2 * MARGIN - HEADER_HEIGHT

# --- Регистрация шрифта (опционально, для кириллицы) ---
# Раскомментируйте, если нужны русские буквы (и положите шрифт, например DejaVuSans.ttf)
# pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
FONT_NAME = 'Helvetica'  # или 'DejaVuSans', если зарегистрирован

# --- Стили ---
title_style = ParagraphStyle(
    'TableTitle',
    fontName=FONT_NAME,
    fontSize=12,
    leading=14,
    alignment=1,  # CENTER
    spaceAfter=0.2 * cm
)

# --- Данные таблиц ---
data1 = [
    ['Имя', 'Возраст', 'Город'],
    ['Анна', '25', 'Москва'],
    ['Борис', '30', 'СПб'],
    ['Вера', '22', 'Екатеринбург'],
    ['Глеб', '35', 'Казань']
]

data2 = [
    ['Страна', 'Столица', 'Население (млн)'],
    ['Россия', 'Москва', '144'],
    ['Германия', 'Берлин', '84'],
    ['Франция', 'Париж', '68'],
    ['Италия', 'Рим', '59'],
    ['Испания', 'Мадрид', '48']
]

# --- Функция: подгонка ширины колонок под заданную общую ширину ---
def fit_table_to_width(data, total_width):
    # Простая равномерная разбивка (можно улучшить по содержимому)
    num_cols = len(data[0])
    col_width = total_width / num_cols
    return [col_width] * num_cols

# Создаём таблицы с фиксированной шириной
col_widths1 = fit_table_to_width(data1, table_width)
col_widths2 = fit_table_to_width(data2, table_width)

table1 = Table(data1, colWidths=col_widths1, rowHeights=None)
table2 = Table(data2, colWidths=col_widths2, rowHeights=None)

# Стиль таблиц
def style_table(t):
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

style_table(table1)
style_table(table2)

# --- Объединяем заголовок + таблицу в один блок (KeepTogether) ---
def make_table_block(title_text, table):
    title_para = Paragraph(title_text, title_style)
    return KeepTogether([title_para, table])

block1 = make_table_block("Таблица 1: Люди", table1)
block2 = make_table_block("Таблица 2: Страны", table2)

# --- Основная компоновка: 1 строка × 2 столбца ---
from reportlab.platypus import Table as PlatypusTable

main_table = PlatypusTable(
    [[block1, block2]],
    colWidths=[table_width, table_width],
    rowHeights=[available_height],  # максимизируем высоту
    hAlign='CENTER',
    vAlign='MIDDLE'
)

# Выравнивание внутри ячеек
main_table.setStyle(TableStyle([
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # таблицы прижимаются к верху блока (после заголовка)
    ('LEFTPADDING', (0, 0), (0, 0), 0),
    ('RIGHTPADDING', (1, 0), (1, 0), 0),
    ('LEFTPADDING', (1, 0), (1, 0), GAP_BETWEEN_TABLES / 2),
    ('RIGHTPADDING', (0, 0), (0, 0), GAP_BETWEEN_TABLES / 2),
]))

# --- Формируем PDF ---
pdf_path = "two_max_tables_centered.pdf"
doc = SimpleDocTemplate(
    pdf_path,
    pagesize=landscape(A4),
    leftMargin=MARGIN,
    rightMargin=MARGIN,
    topMargin=MARGIN,
    bottomMargin=MARGIN,
    showBoundary=0  # отключить рамки отладки
)

elements = [main_table]
doc.build(elements)

print(f"✅ PDF создан: {pdf_path}")
print(f"📄 Размер страницы: {PAGE_WIDTH / cm:.1f} см × {PAGE_HEIGHT / cm:.1f} см (альбомная)")
print(f"📊 Ширина каждой таблицы: {table_width / cm:.2f} см")
print(f"📈 Доступная высота под таблицы: {available_height / cm:.2f} см")