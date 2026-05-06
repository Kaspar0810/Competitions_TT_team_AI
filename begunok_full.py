import os
from sys import platform
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle, Paragraph, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Spacer
from reportlab.pdfbase.pdfmetrics import registerFontFamily


# Регистрация шрифта для кириллицы
registerFontFamily('DejaVuSerif', normal='DejaVuSerif',
                   bold='DejaVuSerif-Bold', italic='DejaVuSerif-Italic')
outpath = os.path.join(os.getcwd(), 'font')
pdfmetrics.registerFont(TTFont('DejaVuSans', os.path.join(outpath, 'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', os.path.join(outpath, 'DejaVuSans-Bold.ttf')))
pdfmetrics.registerFont(TTFont('DejaVuSerif', os.path.join(outpath, 'DejaVuSerif.ttf')))
pdfmetrics.registerFont(TTFont('DejaVuSerif-Bold', os.path.join(outpath, 'DejaVuSerif-Bold.ttf')))
pdfmetrics.registerFont(TTFont('DejaVuSerif-Italic', os.path.join(outpath, 'DejaVuSerif-Italic.ttf')))
# Стили для текста
styles = getSampleStyleSheet()

# Размеры страницы A4 (книжная)
page_size = A4
width, height = page_size

# Параметры сетки
cols = 36
rows = 32
col_width = 5.5 * mm  # ширина колонки (~5.2 мм для 32 колонок на A4)
row_height = 4.4 * mm    # высота строки

# Количество бегунков на странице
BEGUNKI_PER_PAGE = 2

class BegunokPDF:
    """Класс для создания PDF с множеством бегунков"""
    
    def __init__(self, filename):
        self.filename = filename
        self.doc = SimpleDocTemplate(
            filename,
            pagesize=page_size,
            leftMargin=5*mm,
            rightMargin=5*mm,
            topMargin=4*mm,
            bottomMargin=4*mm
        )
        self.story = []
        
    def create_begunok(self, data, index):
        """
        Создает таблицу-бегунок с подставленными данными
        
        data: словарь с полями:
            - date: дата матча
            - time: время матча
            - table: номер стола
            - stage: стадия
            - match_num: номер матча
        """
        
        table_data = []
        
        # Строка 0: Министерство спорта
        row0 = [""] * cols
        row0[0] = "Министерство спорта Российской Федерации"
        table_data.append(row0)
        
        # Строка 1: Федерация
        row1 = [""] * cols
        row1[0] = "Общероссийская физкультурно-спортивная общественная организация «Федерация настольного тенниса России»"
        table_data.append(row1)
        
        # Строка 2: Федерация (продолжение)
        row2 = [""] * cols
        row2[0] = ""
        table_data.append(row2)
        
        # Строка 3: Протокол
        row3 = [""] * cols
        row3[0] = "Протокол одиночной встречи"
        row3[23] = "Дата"
        row3[28] =  f"{data.get('date', '________')}"
        table_data.append(row3)
        
        # Строка 4: =[1]Список!A1
        row4 = [""] * cols
        row4[0] = "ВСЕРОССИЙСКИЕ СОРЕВНОВАНИЯ ПО НАСТОЛЬНОМУ ТЕННИСУ"
        row4[23] = "Время"
        row4[28] = f"{data.get('time', '______')}"
        table_data.append(row4)
        
        # Строка 5: =[1]Список!A2
        row5 = [""] * cols
        row5[0] = "Надежды России"
        row5[23] = "Стол"
        row5[28] = f"{data.get('table', '___')}"
        table_data.append(row5)
        
        # Строка 6: =[1]Список!A3
        row6 = [""] * cols
        row6[0] = ""
        row6[23] = "Стадия"
        row6[28] = f"{data.get('stage', '_____')}"
        table_data.append(row6)
        
        # Строка 7: пустая + Матч №
        row7 = [""] * cols
        row7[23] = "Матч №"
        row7[28] = f"{data.get('match_num', '___')}"
        table_data.append(row7)
        
        # Строка 8: пустая
        row8 = [""] * cols
        table_data.append(row8)
        
        # Строка 9: Ф.И.О. участников ... (заголовки таблицы)
        row9 = [""] * cols
        row9[0] = "Ф.И.О. участников"        
        row9[9] = "R"
        row9[11] = "Субъект РФ"
        row9[16] = "П"
        row9[17] = "П1"
        row9[18] = "П2"
        row9[19] = "Счет в партиях"
        row9[33] = "Общий\nсчет\nпартий"
        table_data.append(row9)
        
        # Строка 10: номера партий
        row10 = [""] * cols
        row10[19] = "1"
        row10[21] = "2"
        row10[23] = "3"
        row10[25] = "4"
        row10[27] = "5"
        row10[29] = "6"
        row10[31] = "7"
        table_data.append(row10)
        
        # Строки 11-12: пустые (для участников)
        row11 = [""] * cols
        row11[0] =  f"{data.get('player1', '___')}"
        row11[9] =  f"{data.get('rank1', '___')}"
        row11[11] =  f"{data.get('city1', '___')}"
        table_data.append(row11)
        row12 = [""] * cols
        row12[0] =  f"{data.get('player2', '___')}"
        row12[9] =  f"{data.get('rank2', '___')}"
        row12[11] =  f"{data.get('city2', '___')}"
        table_data.append(row12)
        
        # Строка 13: пустая
        row13 = [""] * cols
        table_data.append(row13)
        
        # Строка 14: Победил(а)
        row14 = [""] * cols
        row14[0] = "Победил(а)"
        row14[13] = "Со счетом"
        table_data.append(row14)
        
        # Строки 15-16: пустые
        row15 = [""] * cols
        table_data.append(row15)
        row16 = [""] * cols
        table_data.append(row16)
        
        # Строка 17: Тренер
        row17 = [""] * cols
        row17[0] = "Тренер (секундант) участника"
        table_data.append(row17)
        
        # Строки 18-20: пустые
        for _ in range(3):
            table_data.append([""] * cols)
        
        # Строка 21: Ф.И.О. судей
        row21 = [""] * cols
        row21[0] = "Ф.И.О. судей"
        row21[18] = "Подписи судей"
        table_data.append(row21)
        
        # Строки 22-24: пустые
        for _ in range(3):
            table_data.append([""] * cols)
        
        # Строка 25: Сокращение в таблицах
        row25 = [""] * cols
        row25[0] = "Сокращение в таблицах:"
        row25[22] = "Контрольные отметки ГСК"
        table_data.append(row25)
        
        # Строка 26: пустая
        row26 = [""] * cols
        table_data.append(row26)
        
        # Строка 27: П - предупреждение
        row27 = [""] * cols
        row27[2] = "П -"
        row27[3] = "предупреждение"
        row27[22] = "1"
        row27[29] = "2"
        table_data.append(row27)
        
        # Строка 28: подписи
        row28 = [""] * cols
        row28[22] = "(Зам. главного судьи)"
        row28[29] = "(Зам. главного секретаря)"
        table_data.append(row28)
        
        # Строка 29: П1 - одно штрафное очко
        row29 = [""] * cols
        row29[2] = "П1 -"
        row29[4] = "одно штрафное очко"
        table_data.append(row29)
        
        # Строка 30: П2 - два штрафных очка
        row30 = [""] * cols
        row30[2] = "П2 -"
        row30[4] = "два штрафных очка"
        table_data.append(row30)
        
        # Строка 31: пустая
        row31 = [""] * cols
        table_data.append(row31)

        # Создание таблицы с точными размерами колонок
        # col_widths = [col_width] * cols

    #   Создание таблицы - ИСПРАВЛЕНО: используем правильные имена параметров
        col_widths_list = [col_width] * cols
        row_heights_list = [row_height] * rows
        # Увеличиваем высоту для некоторых строк
        row_heights_list[2] = 3 * mm
        row_heights_list[8] = 3 * mm
        row_heights_list[9] = 3.8 * mm
        row_heights_list[10] = 3.8 * mm
        row_heights_list[11] = 7 * mm
        row_heights_list[12] = 7 * mm
        row_heights_list[13] = 3 * mm
        row_heights_list[15] = 7 * mm
        row_heights_list[16] = 3 * mm
        row_heights_list[18] = 6 * mm
        row_heights_list[19] = 6 * mm
        row_heights_list[20] = 3 * mm
        row_heights_list[21] = 3.5 * mm
        row_heights_list[22] = 6 * mm
        row_heights_list[23] = 6 * mm
        row_heights_list[24] = 3 * mm
        row_heights_list[26] = 3 * mm
        row_heights_list[27] = 3.5 * mm
        row_heights_list[28] = 3.5 * mm
        
        table = Table(table_data, colWidths=col_widths_list, rowHeights=row_heights_list)

        # Стиль таблицы - точная копия всех линий
        style = [
            # Все линии сетки - черные, тонкие
            # ('GRID', (0, 0), (-1, -1), 0.2, colors.lightgrey),
            
            # Основной шрифт
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSerif'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('LEADING', (0, 0), (-1, -1), 7),
            
            # Выравнивание
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            
            # Отступы
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('LEFTPADDING', (0, 0), (-1, -1), 1),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1),
            
            # Объединение ячеек для заголовков столбцы от 0 до 7, строки 9-10
            ('SPAN', (0, 9), (8, 10)),  # Ф.И.О. участников (колонки 0-7)
            ('SPAN', (9, 9), (10, 10)),  # Рейтинг (колонки 8-10)
            ('SPAN', (11, 9), (15, 10)),  # Субъект РФ (колонки 11-15)        
            ('SPAN', (16, 9), (16, 10)),  # П (колонки 19-27)
            ('SPAN', (17, 9), (17, 10)),  # П1 (колонки 19-27)
            ('SPAN', (18, 9), (18, 10)),  # П2 (колонки 19-27)
            ('SPAN', (33, 9), (35, 10)),  # Общий счет в партиях (колонки 19-27)
            ('SPAN', (19, 9), (32, 9)),  # счет в партиях (колонки 19-27)     
            # Жирный шрифт для заголовков
            ('FONTSIZE', (0, 3), (20, 3), 11),
            ('FONTNAME', (0, 0), (0, 2), 'DejaVuSerif-Italic'),  # Министерство и федерация
            ('FONTNAME', (0, 3), (20, 3), 'DejaVuSerif-Bold'),  # Протокол
            ('FONTSIZE', (0, 4), (20, 4), 9),
            ('FONTNAME', (0, 4), (20, 5), 'DejaVuSerif'),  # Всероссийские соревнования
            ('FONTNAME', (23, 3), (23, 8), 'DejaVuSerif-Bold'),  # Протокол
            ('FONTNAME', (33, 9), (35, 10), 'DejaVuSerif'),  # Всероссийские соревнования
            ('FONTSIZE', (33, 9), (35, 10), 6),

            # Центрирование некоторых заголовков
            ('ALIGN', (0, 0), (35, 0), 'CENTER'),  # минспорта
            ('ALIGN', (0, 1), (35, 1), 'CENTER'),  # ФНТР
            ('ALIGN', (0, 3), (20, 3), 'CENTER'),  # Протокол
            ('ALIGN', (0, 4), (20, 4), 'CENTER'),  # соревнования
            ('ALIGN', (0, 5), (20, 5), 'CENTER'),  # название
            ('ALIGN', (8, 9), (10, 9), 'CENTER'),  # Рейтинг
            ('ALIGN', (0, 9), (8, 9), 'CENTER'),  # ФИО
            ('ALIGN', (10, 9), (15, 9), 'CENTER'),  # Субъект
            ('ALIGN', (16, 9), (18, 9), 'CENTER'),  # П, П1, П2
            ('VALIGN', (0, 9), (35, 10), 'MIDDLE'),  # блок счета
            ('ALIGN', (19, 10), (27, 10), 'CENTER'),  # Номера партий
            ('ALIGN', (19, 9), (32, 9), 'CENTER'),  # Счет в партиях 
            ('ALIGN', (33, 9), (35, 10), 'CENTER'),  # Общий счет
            ('ALIGN', (0, 14), (18, 14), 'CENTER'),  # Победил(а)
            ('ALIGN', (0, 17), (35, 17), 'CENTER'),  # тренер
            ('ALIGN', (0, 21), (18, 21), 'CENTER'),  # ФИО судей
            ('ALIGN', (18, 21), (35, 21), 'CENTER'),  # подпись судей
            ('ALIGN', (18, 25), (35, 28), 'CENTER'),  # контрольные отметки ГСК
            
            # Специальные объединения
            ('SPAN', (0, 0), (35, 0)),  # Министерство спорта
            ('SPAN', (0, 1), (35, 1)),  # Федерация (часть 1)
            ('SPAN', (0, 2), (22, 2)),  # Федерация (часть 2)
            ('SPAN', (0, 3), (22, 3)),  # Протокол
            ('SPAN', (0, 4), (22, 4)),  # =[1]Список!A1
            ('SPAN', (0, 5), (22, 5)),  # =[1]Список!A2
            ('SPAN', (0, 6), (22, 6)),  # =[1]Список!A3
        
            
            # == блок фио, рейтинг, ввод счета
            ('BOX', (0, 9), (8, 10), 0.5, colors.darkblue), # объединение ФИО столбцы от 0 до 7, строки 9-10
            ('BOX', (0, 11), (8, 11), 0.5, colors.darkblue), # столбцы от 0 до 7, строки 9-10
            ('BOX', (0, 12), (8, 12), 0.5, colors.darkblue), # столбцы от 0 до 7, строки 9-10
            # объединение рейтинг
            ('BOX', (8, 9), (10, 10), 0.5, colors.darkblue), # столбцы от 0 до 7, строки 9-10 рейтинг
            ('BOX', (8, 10), (10, 11), 0.5, colors.darkblue), # столбцы от 0 до 7, строки 9-10 рейтинг
            ('BOX', (8, 11), (10, 12), 0.5, colors.darkblue), # столбцы от 0 до 7, строки 9-10 рейтинг
            # объдинение субъекта РФ
            ('BOX', (11, 9), (15, 10), 0.5, colors.darkblue), # объдинение субъекта РФ столбцы от 0 до 7, строки 9-10 субъекты
            ('BOX', (11, 10), (15, 11), 0.5, colors.darkblue), # столбцы от 0 до 7, строки 9-10 субъекты
            ('BOX', (11, 11), (15, 12), 0.5, colors.darkblue), # столбцы от 0 до 7, строки 9-10 субъекты
            # объединяет счет в партиях
            ('BOX', (19, 9), (32, 9), 0.5, colors.darkblue), # столбцы от 0 до 7, строки 9-10
            # объединяет общий счет в партиях
            ('BOX', (33, 9), (36, 10), 0.5, colors.darkblue), # столбцы от 0 до 7, строки 9-10


            # Победитель
            ('SPAN', (0, 14), (12, 14)),  # Победил(а)
            ('SPAN', (0, 15), (12, 15)),  # Победил(а)
            ('SPAN', (13, 14), (18, 14)),  # Со счетом
            ('SPAN', (13, 15), (18, 15)),  # Со счетом
            ('GRID', (0, 14), (18, 15), 0.5, colors.darkblue), # столбцы от 0 до 7, строки 9-10 субъекты
            # Тренер
            ('SPAN', (0, 17), (35, 17)),  # Тренер
            ('SPAN', (0, 18), (18, 18)),  # Тренер
            ('SPAN', (19, 18), (35, 18)),  # Тренер
            ('SPAN', (0, 19), (18, 19)),  # Тренер
            ('SPAN', (19, 19), (35, 19)),  # Тренер
            ('GRID', (0, 17), (35, 19), 0.5, colors.darkblue), # столбцы от 0 до 7, строки 9-10 субъекты
            # Судьи
            ('SPAN', (0, 21), (18, 21)),  # Ф.И.О. судей
            ('SPAN', (18, 21), (35, 21)),  # Подписи судей
            ('SPAN', (0, 22), (18, 22)),  # Ф.И.О. судей
            ('SPAN', (0, 23), (18, 23)),  # Ф.И.О. судей
            ('SPAN', (19, 22), (35, 22)),  # Подписи судей
            ('SPAN', (19, 23), (35, 23)),  # Подписи судей
            ('GRID', (0, 21), (35, 23), 0.5, colors.darkblue), # столбцы от 0 до 7, строки 9-10 субъекты
            # Сокращения
            ('SPAN', (0, 25), (12, 25)),  # Сокращение в таблицах:
            ('SPAN', (22, 25), (35, 25)),  # Контрольные отметки ГСК
            ('SPAN', (22, 27), (28, 27)),  # 1
            ('SPAN', (29, 27), (35, 27)),  # 2
            ('SPAN', (22, 28), (28, 28)),  # (Зам. главного судьи)
            ('SPAN', (29, 28), (35, 28)),  # (Зам. главного секретаря)
            ('SPAN', (22, 29), (28, 30)),  # (Зам. главного судьи)
            ('SPAN', (29, 29), (35, 30)),  # (Зам. главного секретаря)
            ('GRID', (22, 29), (35, 30), 0.5, colors.darkblue), # столбцы от 0 до 7, строки 9-10 субъекты
            ('BOX', (22, 27), (28, 29), 0.5, colors.darkblue),
            ('BOX', (29, 27), (35, 29), 0.5, colors.darkblue)
        ]   
        # === блок ввода даты, номер стола встречи и т.д.
        for i in range(0, 5): 
            fn = ('SPAN', (23, 3 + i), (27, 3 + i))
            style.append(fn)  # Дата
            fn = ('SPAN', (28, 3 + i), (31, 3 + i))
            style.append(fn)  # Дата
            fn = ('BOX', (23, 3 + i), (27, 3 + i), 0.5, colors.darkblue)
            style.append(fn)
            fn = ('BOX', (27, 3 + i), (31, 3 + i), 0.5, colors.darkblue) # рисует внешние границы
            style.append(fn)
            fn =  ('BACKGROUND', (23, 3 + i), (27, 3 + i), colors.lightyellow)
            style.append(fn)
            fn = ('ALIGN', (23, 3 + i), (27, 3 + i), 'CENTER')  # минспорта
            style.append(fn)
            fn = ('FONTSIZE', (23, 3 + i), (27, 3 + i), 8)  # минспорта
            style.append(fn)

        for i in range(0, 2):
            fn = ('SPAN', (0, 11 + i), (8, 11 + i)) 
            style.append(fn) # ФИО
            fn = ('SPAN', (9, 11 + i), (10, 11 + i))  # поле рейтинг
            style.append(fn)  # Рейтинг
            fn = ('SPAN', (11, 11 + i), (15, 11 + i)) # поле субъекты столбцы от 0 до 7, строки 9-10
            style.append(fn) # Субъекты
            fn = ('SPAN', (33, 11 + i), (35, 11 + i)) # поле субъекты столбцы от 0 до 7, строки 9-10
            style.append(fn) # Общий счет в партии

        # блок ввода счета
        for k in range(19, 32, 2):
            for i in range(0, 3):
                fn = ('SPAN', (k, 10 + i), (k + 1, 10 + i)) # поле  от 0 до 7, строки 9-10
                style.append(fn) # счет в партиях
                fn = ('BOX', (k, 10 + i), (k + 1, 10 + i), 0.5, colors.darkblue)
                style.append(fn)
                fn = ('ALIGN', (k, 10 + i), (k + 1, 10 + i), 'CENTER')  # номера партий
                style.append(fn)
                fn = ('VALIGN', (k, 10 + i), (k + 1, 10 + i), 'MIDDLE')  # номера партий
                style.append(fn)
                fn = ('FONTNAME', (k, 10 + i), (k + 1, 10 + i), 'DejaVuSerif-Bold')  # минспорта
                style.append(fn)
                fn = ('FONTSIZE', (k, 10 + i), (k + 1, 10 + i), 7)  # минспорта
                style.append(fn)
        
        # === блок предупреждений
        for k in range(0, 2):
            for i in range(0, 3):
                fn = ('BOX', (16 + i, 9), (16 + i, 10), 0.5, colors.darkblue)
                style.append(fn)  # предупреждения
                fn = ('BOX', (16 + i, 11 + k), (16 + i, 11 + k), 0.5, colors.darkblue)
                style.append(fn)  # предупреждения
        
        # === общий счет        
        for i in range(0, 2):
                fn = ('BOX', (33, 11 + i), (36, 11 + i), 0.5, colors.darkblue)
                style.append(fn)  # предупреждения
        table.setStyle(TableStyle(style))

        return [table]
    
    def add_begunki(self, begunki_data):
        """Добавляет бегунки в PDF документ
        begunki_data: список словарей с данными для каждого бегунка
        """
        for i, data in enumerate(begunki_data, 1):
            # Создаем бегунок
            elements = self.create_begunok(data, i)
            self.story.extend(elements)
            
            # Добавляем разрыв страницы после каждого второго бегунка
            if i % BEGUNKI_PER_PAGE == 0 and i < len(begunki_data):
                self.story.append(PageBreak())
        return self.story        
    
    def save(self):
        """Сохраняет PDF документ"""
        self.doc.build(self.story)
        print(f"PDF '{self.filename}' успешно создан!")
        
