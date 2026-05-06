# import mysql.connector
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

class GroupSchedulePDF:
    def __init__(self, filename='schedule.pdf'):
        self.filename = filename
        self.doc = SimpleDocTemplate(
            filename,
            pagesize=landscape(A4),
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1.5*cm,
            bottomMargin=1*cm
        )
        self.styles = getSampleStyleSheet()
        self.elements = []
        
    def add_title(self):
        """Добавление заголовка"""
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            alignment=1,
            textColor=colors.darkblue,
            spaceAfter=20
        )
        title = Paragraph("Расписание игр", title_style)
        self.elements.append(title)
        
        # Дата создания
        date_style = ParagraphStyle(
            'DateStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=2,
            textColor=colors.grey
        )
        date_text = Paragraph(f"Создано: {datetime.now().strftime('%d.%m.%Y %H:%M')}", date_style)
        self.elements.append(date_text)
        self.elements.append(Spacer(1, 10))
    
    def create_group_table(self, group_name, rows):
        """Создание таблицы для одной группы"""
        
        # Заголовок группы
        group_style = ParagraphStyle(
            'GroupStyle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.darkblue,
            spaceAfter=5,
            spaceBefore=10,
            alignment=0
        )
        self.elements.append(Paragraph(f"Группа: {group_name}", group_style))
        
        # Подготовка данных
        table_data = []
        
        # Заголовки
        headers = ['№', 'Дата', 'Время', 'Стол', 'Тур', 'Игрок 1', 'Игрок 2']
        table_data.append(headers)
        
        # Данные
        for idx, row in enumerate(rows, 1):
            # Форматирование даты
            if row['schedule_date']:
                if isinstance(row['schedule_date'], datetime):
                    date_str = row['schedule_date'].strftime('%d.%m.%Y')
                else:
                    date_str = str(row['schedule_date'])
            else:
                date_str = ''
            
            table_row = [
                str(idx),
                date_str,
                str(row['schedule_time'] or ''),
                str(row['schedule_table'] or ''),
                str(row['tours'] or ''),
                str(row['player1'] or ''),
                str(row['player2'] or '')
            ]
            table_data.append(table_row)
        
        # Настройка ширины колонок
        col_widths = [0.8*cm, 2.2*cm, 1.8*cm, 1.8*cm, 1.8*cm, 4.5*cm, 4.5*cm]
        
        # Создание таблицы
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Стили
        style = TableStyle([
            # Заголовок
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            
            # Все ячейки
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Границы
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            
            # Выравнивание
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (2, 1), (4, -1), 'CENTER'),
            
            # Чередование цветов
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ])
        
        table.setStyle(style)
        self.elements.append(table)
        self.elements.append(Spacer(1, 15))
    
    def build(self, grouped_data):
        """Построение PDF"""
        self.add_title()
        
        for group_name, rows in grouped_data.items():
            self.create_group_table(group_name, rows)
        
        self.doc.build(self.elements)
        print(f"PDF создан: {self.filename}")

def main():
    # Подключение к БД
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='your_database',
            user='your_user',
            password='your_password'
        )
        
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT number_group, tours, player1, player2, 
               schedule_date, schedule_time, schedule_table
        FROM Result
        ORDER BY number_group, schedule_date, schedule_time
        """
        
        cursor.execute(query)
        data = cursor.fetchall()

        # ====
      
        
        # Группировка данных
        grouped_data = {}
        for row in data:
            group = row['number_group']
            if group not in grouped_data:
                grouped_data[group] = []
            grouped_data[group].append(row)
        
        # Создание PDF
        pdf = GroupSchedulePDF('groups_schedule.pdf')
        pdf.build(grouped_data)
        
    except mysql.connector.Error as error:
        print(f"Ошибка MySQL: {error}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    main()