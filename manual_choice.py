import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from models import *
from models import db
import re

# ========== ДИАЛОГ ВЫБОРА ДЕЙСТВИЯ ==========
class ChoiceActionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Жеребьевка спортсменов")
        self.setModal(True)
        self.setFixedSize(450, 220)

        
        layout = QVBoxLayout(self)
        
        title_label = QLabel("Жеребьевка спортсменов")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        info_label = QLabel("В базе данных уже есть результаты жеребьевки.\n\nВыберите действие:")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        button_layout = QHBoxLayout()
        
        self.btn_reset = QPushButton("Сбросить")
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self.btn_reset.clicked.connect(lambda: self.done(1))
        button_layout.addWidget(self.btn_reset)
        
        self.btn_load = QPushButton("Загрузить")
        self.btn_load.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_load.clicked.connect(lambda: self.done(2))
        button_layout.addWidget(self.btn_load)
        
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.btn_cancel.clicked.connect(lambda: self.done(0))
        button_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(button_layout)
        
        info_text = QLabel("• Сбросить - начать новую жеребьевку\n• Загрузить - продолжить редактирование существующей\n• Отмена - выйти без изменений")
        info_text.setStyleSheet("color: #666; font-size: 11px; margin-top: 10px;")
        info_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_text)

# ========== ОСНОВНОЙ КЛАСС ЖЕРЕБЬЕВКИ ==========
class ChoiceGroupManual(QDialog):
    def __init__(self, athletes, num_groups, id_title, parent=None, existing_data=None):
        super().__init__(parent)
        self.athletes = athletes
        self.sorted_athletes = []
        self.groups = []
        self.num_groups = num_groups
        self.current_athlete_index = 0
        self.group_tables = []
        self.group_headers = []
        self.current_group_for_seed = None
        self.current_round = 1
        self.max_rows_per_group = 0
        self.existing_data = existing_data
        self.initUI()
        self.load_athletes()
        self.calculate_max_rows()
        self.init_groups()
        
        if self.existing_data:
            self.load_existing_draw()
        else:
            self.calculate_initial_group()
        
        self.setModal(True)
        
    def load_existing_draw(self):
        """Загрузка существующей жеребьевки из базы данных"""
        # Инициализируем группы
        self.groups = [[] for _ in range(self.num_groups)]
        
        # Заполняем группы данными из базы
        for item in self.existing_data:
            player_id = item.player_choice_id
            mark = item.group.find(" ")
            gr_num = int(item.group[:mark])
            group_num = gr_num - 1
            position = item.posev_group - 1
            
            # Находим спортсмена по id
            athlete = None
            for a in self.athletes:
                if a[0] == player_id:
                    athlete = a
                    break
            
            if athlete and group_num < self.num_groups:
                while len(self.groups[group_num]) <= position:
                    self.groups[group_num].append(None)
                self.groups[group_num][position] = athlete
                
                if athlete in self.sorted_athletes:
                    idx = self.sorted_athletes.index(athlete)
                    if idx >= self.current_athlete_index:
                        self.sorted_athletes.pop(idx)
        
        placed_count = sum(1 for group in self.groups for athlete in group if athlete)
        self.current_athlete_index = placed_count
        self.update_round_display()
        self.update_groups_display()
        self.highlight_current_group()
        
        if self.current_athlete_index >= len(self.athletes):
            QMessageBox.information(self, "Информация", "Жеребьевка уже завершена! Все спортсмены распределены.")

        
    def calculate_initial_group(self):
        """Определение начальной группы для посева"""
        if self.num_groups > 0:
            self.current_group_for_seed = self.num_groups - 1
            
    def calculate_max_rows(self):
        """Расчет максимального количества строк в группе"""
        total_athletes = len(self.athletes)
        self.max_rows_per_group = (total_athletes + self.num_groups - 1) // self.num_groups
        if self.max_rows_per_group < 1:
            self.max_rows_per_group = 1
            
    def get_current_round(self):
        """Определение текущего раунда на основе количества размещенных спортсменов"""
        placed_count = self.current_athlete_index
        
        if placed_count == 0:
            return 1
        
        if placed_count <= self.num_groups:
            return 1
        else:
            round_num = (placed_count - 1) // self.num_groups + 1
            return round_num
    
    def update_round_display(self):
        """Обновление отображения текущего раунда"""
        self.current_round = self.get_current_round()
        direction = "→" if self.current_round % 2 == 1 else "←"
        self.round_label.setText(f"Круг: {self.current_round}\nНаправление: {direction}")
        
    def _initUI(self):
        self.setWindowTitle('Ручная жеребьевка спортсменов')
        self.setGeometry(10, 10, 1700, 800)
        
        main_layout = QVBoxLayout(self)
        
        title_label = QLabel("Ручная жеребьевка спортсменов")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        content_layout = QHBoxLayout()
        
        # ========== ЛЕВАЯ ПАНЕЛЬ ==========
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.StyledPanel)
        left_panel.setMaximumWidth(330)
        left_layout = QVBoxLayout(left_panel)
        
        # Горизонтальный layout для информации
        info_layout = QHBoxLayout()
        
        # Информация о текущем спортсмене
        current_athlete_group = QGroupBox("Текущий спортсмен")
        current_athlete_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        current_athlete_layout = QVBoxLayout(current_athlete_group)
        
        self.current_athlete_label = QLabel("Спортсмен: -\nРейтинг: -\nРегион: -\nТренер: -")
        self.current_athlete_label.setStyleSheet("background-color: #ffe0b3; padding: 8px; font-size: 12px;")
        self.current_athlete_label.setWordWrap(True)
        current_athlete_layout.addWidget(self.current_athlete_label)
        
        left_layout.addWidget(current_athlete_group)
        
        # Информация о текущей группе
        current_group_group = QGroupBox("Текущая группа для посева")
        current_group_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        current_group_layout = QVBoxLayout(current_group_group)
        
        self.current_group_label = QLabel("Группа: -\nИгроков: -")
        self.current_group_label.setStyleSheet("background-color: #b3d9ff; padding: 8px; font-size: 11px;")
        current_group_layout.addWidget(self.current_group_label)
        
        info_layout.addWidget(current_group_group)
        
        # Информация о текущем круге
        round_group = QGroupBox("Текущий круг")
        round_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        round_layout = QVBoxLayout(round_group)
        
        self.round_label = QLabel("Круг: 1\nНаправление: →")
        self.round_label.setStyleSheet("background-color: #d4e6f1; padding: 8px; font-size: 11px;")
        round_layout.addWidget(self.round_label)
        
        info_layout.addWidget(round_group)
        
        left_layout.addLayout(info_layout)
        
        # Список участников
        athletes_group = QGroupBox("Список участников (по рейтингу ↓)")
        athletes_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        athletes_layout = QVBoxLayout(athletes_group)
        
        self.athletes_table = QTableWidget()
        self.athletes_table.setColumnCount(4)
        self.athletes_table.setHorizontalHeaderLabels(["ID", "ФИО", "Рейтинг", "Регион"])
        self.athletes_table.horizontalHeader().setStretchLastSection(True)
        self.athletes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.athletes_table.setAlternatingRowColors(True)
        athletes_layout.addWidget(self.athletes_table)
        
        left_layout.addWidget(athletes_group)
        
        # Статистика и управление
        control_group = QGroupBox("Управление и статистика")
        control_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        control_layout = QVBoxLayout(control_group)
        
        # Статистика
        stats_layout = QGridLayout()
        stats_layout.addWidget(QLabel("Всего спортсменов:"), 0, 0)
        self.total_label = QLabel("0")
        stats_layout.addWidget(self.total_label, 0, 1)
        stats_layout.addWidget(QLabel("Размещено:"), 1, 0)
        self.placed_label = QLabel("0")
        stats_layout.addWidget(self.placed_label, 1, 1)
        stats_layout.addWidget(QLabel("Осталось:"), 2, 0)
        self.remaining_label = QLabel("0")
        stats_layout.addWidget(self.remaining_label, 2, 1)
        stats_layout.addWidget(QLabel("Макс. в группе:"), 3, 0)
        self.max_rows_label = QLabel("0")
        stats_layout.addWidget(self.max_rows_label, 3, 1)
        stats_layout.addWidget(QLabel("Текущий круг:"), 4, 0)
        self.round_number_label = QLabel("1")
        stats_layout.addWidget(self.round_number_label, 4, 1)
        control_layout.addLayout(stats_layout)
        
        # Кнопки управления
        btn_layout = QGridLayout()

        self.btn_reset = QPushButton("Сбросить жеребьевку")
        self.btn_reset.clicked.connect(self.reset_draw)
        btn_layout.addWidget(self.btn_reset, 0, 0, 1, 1)
        
        self.btn_auto = QPushButton("Авто-заполнение (1 номера)")
        self.btn_auto.clicked.connect(self.auto_fill_first)
        btn_layout.addWidget(self.btn_auto, 1, 0, 1, 1)
        
        self.btn_clear = QPushButton("Очистить все группы")
        self.btn_clear.clicked.connect(self.clear_all_groups)
        btn_layout.addWidget(self.btn_clear, 0, 1, 1, 1)

        
        self.btn_edit = QPushButton("Редактировать группы")
        self.btn_edit.clicked.connect(self.open_editor)
        self.btn_edit.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        btn_layout.addWidget(self.btn_edit, 1, 1, 1, 1)

        control_layout.addLayout(btn_layout)
        
        # Кнопки OK и Cancel
        dialog_buttons = QHBoxLayout()
        
        self.btn_result = QPushButton("Показать результат")
        self.btn_result.clicked.connect(self.show_results)
        self.btn_result.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        dialog_buttons.addWidget(self.btn_result)
        
        self.btn_ok = QPushButton("Записать жеребьевку")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_ok.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        dialog_buttons.addWidget(self.btn_ok)
        
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.clicked.connect(self.reject)
        dialog_buttons.addWidget(self.btn_cancel)
        
        control_layout.addLayout(dialog_buttons)
        
        # Инструкция
        info_text = QTextEdit()
        info_text.setMaximumHeight(150)
        info_text.setReadOnly(True)
        info_text.setPlainText("Правила жеребьевки:\n"
                              "• Первые номера групп заполняются автоматически\n"
                              "• Желтая подсветка группы - текущая для посева\n"
                              "• Клик по ЛЮБОЙ зеленой/желтой ячейке для посева\n"
                              "• Наведите мышь на игрока для просмотра полной информации\n"
                              "• Если внести игрока в НЕ выделенную группу,\n"
                              "  выделение остается на прежней группе\n"
                              "• Выделение переходит на следующую группу\n"
                              "  только после внесения игрока в выделенную группу\n"
                              "• Следующая группа выбирается с наименьшим\n"
                              "  количеством игроков\n"
                              "• Зеленые ячейки - можно сеять\n"
                              "• Желтые - совпадение региона, можно сеять с подтверждением\n"
                              "• Красные - совпадение региона и тренера\n"
                              "• Двойной клик - редактирование ячейки")
        control_layout.addWidget(info_text)
        
        left_layout.addWidget(control_group)
        
        # ========== ЦЕНТРАЛЬНАЯ ПАНЕЛЬ (таблицы групп) ==========
        center_panel = QFrame()
        center_panel.setFrameStyle(QFrame.StyledPanel)
        center_layout = QVBoxLayout(center_panel)
        
        lbl_groups = QLabel(f"Жеребьевка групп (всего групп: {self.num_groups}, макс. в группе: {self.max_rows_per_group})")
        lbl_groups.setStyleSheet("font-weight: bold; font-size: 14px;")
        center_layout.addWidget(lbl_groups)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.groups_widget = QWidget()
        self.groups_layout = QGridLayout(self.groups_widget)
        self.groups_layout.setAlignment(Qt.AlignTop)
        self.groups_layout.setVerticalSpacing(15)
        self.groups_layout.setHorizontalSpacing(10)
        scroll_area.setWidget(self.groups_widget)
        center_layout.addWidget(scroll_area)
        
        content_layout.addWidget(left_panel)
        content_layout.addWidget(center_panel, stretch=1)
        
        main_layout.addLayout(content_layout)

# ========================================
    def initUI(self):
        self.setWindowTitle('Ручная жеребьевка спортсменов')
        # Уменьшаем размер окна под 1366x768
        self.setGeometry(50, 50, 1600, 850)  # Изменено с 1300x700
        self.setMaximumSize(1600, 850)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(5)  # Уменьшаем отступы
        main_layout.setContentsMargins(5, 5, 5, 5)  # Уменьшаем отступы
        
        title_label = QLabel("Ручная жеребьевка спортсменов")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 5px;")  # Уменьшен margin
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        content_layout = QHBoxLayout()
        content_layout.setSpacing(5)  # Уменьшаем отступ между панелями
        
        # ========== ЛЕВАЯ ПАНЕЛЬ ==========
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.StyledPanel)
        left_panel.setMaximumWidth(300)  # Уменьшено с 330
        left_panel.setMinimumWidth(280)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(3)  # Уменьшаем отступы
        left_layout.setContentsMargins(3, 3, 3, 3)
        
        # Горизонтальный layout для информации
        info_layout = QHBoxLayout()
        info_layout.setSpacing(3)
        
        # Информация о текущем спортсмене
        current_athlete_group = QGroupBox("Текущий спортсмен")
        current_athlete_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 11px; }")
        current_athlete_layout = QVBoxLayout(current_athlete_group)
        current_athlete_layout.setSpacing(2)
        
        self.current_athlete_label = QLabel("Спортсмен: -\nРейтинг: -\nРегион: -\nТренер: -")
        self.current_athlete_label.setStyleSheet("background-color: #ffe0b3; padding: 5px; font-size: 10px;")
        self.current_athlete_label.setWordWrap(True)
        current_athlete_layout.addWidget(self.current_athlete_label)
        
        left_layout.addWidget(current_athlete_group)
        
        # Информация о текущей группе
        current_group_group = QGroupBox("Текущая группа")
        current_group_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 11px; }")
        current_group_layout = QVBoxLayout(current_group_group)
        current_group_layout.setSpacing(2)
        
        self.current_group_label = QLabel("Группа: -\nИгроков: -")
        self.current_group_label.setStyleSheet("background-color: #b3d9ff; padding: 5px; font-size: 10px;")
        current_group_layout.addWidget(self.current_group_label)
        
        info_layout.addWidget(current_group_group)
        
        # Информация о текущем круге
        round_group = QGroupBox("Текущий круг")
        round_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 11px; }")
        round_layout = QVBoxLayout(round_group)
        round_layout.setSpacing(2)
        
        self.round_label = QLabel("Круг: 1\nНаправление: →")
        self.round_label.setStyleSheet("background-color: #d4e6f1; padding: 5px; font-size: 10px;")
        round_layout.addWidget(self.round_label)
        
        info_layout.addWidget(round_group)
        
        left_layout.addLayout(info_layout)
        
        # Список участников
        athletes_group = QGroupBox("Список участников")
        athletes_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 11px; }")
        athletes_layout = QVBoxLayout(athletes_group)
        athletes_layout.setSpacing(2)
        
        self.athletes_table = QTableWidget()
        self.athletes_table.setColumnCount(4)
        self.athletes_table.setHorizontalHeaderLabels(["ID", "ФИО", "Рейтинг", "Регион"])
        self.athletes_table.horizontalHeader().setStretchLastSection(True)
        self.athletes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.athletes_table.setAlternatingRowColors(True)
        self.athletes_table.verticalHeader().setDefaultSectionSize(20)  # Уменьшаем высоту строк
        athletes_layout.addWidget(self.athletes_table)
        
        left_layout.addWidget(athletes_group)
        
        # Статистика и управление
        control_group = QGroupBox("Управление")
        control_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 11px; }")
        control_layout = QVBoxLayout(control_group)
        control_layout.setSpacing(3)
        
        # Статистика
        stats_layout = QGridLayout()
        stats_layout.addWidget(QLabel("Всего спортсменов:"), 0, 0)
        self.total_label = QLabel("0")
        stats_layout.addWidget(self.total_label, 0, 1)
        stats_layout.addWidget(QLabel("Размещено:"), 1, 0)
        self.placed_label = QLabel("0")
        stats_layout.addWidget(self.placed_label, 1, 1)
        stats_layout.addWidget(QLabel("Осталось:"), 2, 0)
        self.remaining_label = QLabel("0")
        stats_layout.addWidget(self.remaining_label, 2, 1)
        stats_layout.addWidget(QLabel("Макс. в группе:"), 3, 0)
        self.max_rows_label = QLabel("0")
        stats_layout.addWidget(self.max_rows_label, 3, 1)
        stats_layout.addWidget(QLabel("Текущий круг:"), 4, 0)
        self.round_number_label = QLabel("1")
        stats_layout.addWidget(self.round_number_label, 4, 1)
        control_layout.addLayout(stats_layout)
        
        # Кнопки управления
        btn_layout = QGridLayout()
        btn_layout.setSpacing(2)

        self.btn_reset = QPushButton("Сбросить")
        self.btn_reset.setFixedHeight(25)  # Фиксированная высота
        self.btn_reset.clicked.connect(self.reset_draw)
        btn_layout.addWidget(self.btn_reset, 0, 0, 1, 1)
        
        self.btn_auto = QPushButton("Авто (1 номера)")
        self.btn_auto.setFixedHeight(25)
        self.btn_auto.clicked.connect(self.auto_fill_first)
        btn_layout.addWidget(self.btn_auto, 1, 0, 1, 1)
        
        self.btn_clear = QPushButton("Очистить")
        self.btn_clear.setFixedHeight(25)
        self.btn_clear.clicked.connect(self.clear_all_groups)
        btn_layout.addWidget(self.btn_clear, 0, 1, 1, 1)

        self.btn_edit = QPushButton("Редактор")
        self.btn_edit.setFixedHeight(25)
        self.btn_edit.clicked.connect(self.open_editor)
        self.btn_edit.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        btn_layout.addWidget(self.btn_edit, 1, 1, 1, 1)

        control_layout.addLayout(btn_layout)
        
        # Кнопки OK и Cancel
        dialog_buttons = QHBoxLayout()
        dialog_buttons.setSpacing(5)
        
        self.btn_result = QPushButton("Результат")
        self.btn_result.setFixedHeight(28)
        self.btn_result.clicked.connect(self.show_results)
        self.btn_result.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        dialog_buttons.addWidget(self.btn_result)
        
        self.btn_ok = QPushButton("Записать")
        self.btn_ok.setFixedHeight(28)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_ok.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        dialog_buttons.addWidget(self.btn_ok)
        
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.setFixedHeight(28)
        self.btn_cancel.clicked.connect(self.reject)
        dialog_buttons.addWidget(self.btn_cancel)
        
        control_layout.addLayout(dialog_buttons)
        
        # Инструкция - делаем более компактной
        info_text = QTextEdit()
        info_text.setMaximumHeight(120)  # Уменьшено с 150
        info_text.setReadOnly(True)
        info_text.setStyleSheet("font-size: 9px;")
        info_text.setPlainText("Правила:\n"
                            "• 1 номера групп - автоматически\n"
                            "• Желтая подсветка - текущая группа\n"
                            "• Клик по зеленой/желтой ячейке\n"
                            "• Зеленые - можно сеять\n"
                            "• Желтые - конфликт региона\n"
                            "• Красные - конфликт региона+тренера\n"
                            "• Двойной клик - редактирование")
        control_layout.addWidget(info_text)
        
        left_layout.addWidget(control_group)
        
        # ========== ЦЕНТРАЛЬНАЯ ПАНЕЛЬ ==========
        center_panel = QFrame()
        center_panel.setFrameStyle(QFrame.StyledPanel)
        center_layout = QVBoxLayout(center_panel)
        center_layout.setSpacing(3)
        
        lbl_groups = QLabel(f"Жеребьевка групп (групп: {self.num_groups}, макс: {self.max_rows_per_group})")
        lbl_groups.setStyleSheet("font-weight: bold; font-size: 12px;")
        center_layout.addWidget(lbl_groups)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.groups_widget = QWidget()
        self.groups_layout = QGridLayout(self.groups_widget)
        self.groups_layout.setAlignment(Qt.AlignTop)
        self.groups_layout.setVerticalSpacing(8)  # Уменьшено с 15
        self.groups_layout.setHorizontalSpacing(8)  # Уменьшено с 10
        self.groups_layout.setContentsMargins(5, 5, 5, 5)
        scroll_area.setWidget(self.groups_widget)
        center_layout.addWidget(scroll_area)
        
        content_layout.addWidget(left_panel)
        content_layout.addWidget(center_panel, stretch=1)
        
        main_layout.addLayout(content_layout)
 # ======================================================       
    def get_group_players_count(self, group_idx):
        """Получить количество игроков в группе"""
        if group_idx < len(self.groups):
            return len([a for a in self.groups[group_idx] if a is not None])
        return 0
    
    def find_next_group_for_seed(self):
        """Найти следующую группу для посева (с наименьшим количеством игроков)"""
        groups_info = []
        for g in range(self.num_groups):
            count = self.get_group_players_count(g)
            groups_info.append((g, count))
        
        if not groups_info:
            return 0
            
        min_count = min(count for _, count in groups_info)
        min_groups = [g for g, count in groups_info if count == min_count]
        
        if self.current_round % 2 == 1:
            for g in min_groups:
                if g >= self.current_group_for_seed:
                    return g
            return min_groups[0]
        else:
            for g in reversed(min_groups):
                if g <= self.current_group_for_seed:
                    return g
            return min_groups[-1]
    
    def move_to_next_group(self):
        """Переход к следующей группе"""
        self.update_round_display()
        next_group = self.find_next_group_for_seed()
        self.current_group_for_seed = next_group
        self.highlight_current_group()
    
    def highlight_current_group(self):
        """Подсветка текущей группы для посева"""
        for header in self.group_headers:
            header.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white; padding: 5px;")
        
        if self.current_group_for_seed is not None and self.current_group_for_seed < len(self.group_headers):
            self.group_headers[self.current_group_for_seed].setStyleSheet(
                "font-weight: bold; background-color: #FF9800; color: white; padding: 5px; border: 3px solid #FF5722;"
            )
            players_count = self.get_group_players_count(self.current_group_for_seed)
            self.current_group_label.setText(f"Группа: {self.current_group_for_seed + 1}\nИгроков: {players_count}")
    
    def load_athletes(self):
        """Загрузка и сортировка спортсменов"""
        self.sorted_athletes = sorted(self.athletes, key=lambda x: x[2], reverse=True)
        self.update_athletes_table()
        self.update_current_athlete()
        
    def update_athletes_table(self):
        """Обновление таблицы участников"""
        remaining_athletes = self.sorted_athletes[self.current_athlete_index:]
        
        self.athletes_table.setRowCount(len(remaining_athletes))
        for row, athlete in enumerate(remaining_athletes):
            id_player, name, rating, region, coach = athlete
            self.athletes_table.setItem(row, 0, QTableWidgetItem(str(id_player)))
            self.athletes_table.setItem(row, 1, QTableWidgetItem(name))
            self.athletes_table.setItem(row, 2, QTableWidgetItem(str(rating)))
            self.athletes_table.setItem(row, 3, QTableWidgetItem(region))
        
        self.athletes_table.resizeColumnsToContents()
        
    def init_groups(self):
        """Инициализация таблиц групп"""
        for i in reversed(range(self.groups_layout.count())):
            widget = self.groups_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        self.group_tables.clear()
        self.group_headers.clear()
        
        cols = min(4, self.num_groups)
# =====================================        
        # for g in range(self.num_groups):
        #     group_frame = QFrame()
        #     group_frame.setFrameStyle(QFrame.Box)
        #     group_frame.setMinimumWidth(300)
        #     group_frame.setMaximumWidth(400)
        #     group_layout = QVBoxLayout(group_frame)
        #     group_layout.setSpacing(5)
            
        #     header = QLabel(f"Группа {g+1}")
        #     header.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white; padding: 5px;")
        #     header.setAlignment(Qt.AlignCenter)
        #     group_layout.addWidget(header)
            
        #     table = QTableWidget()
        #     table.setColumnCount(2)
        #     table.setHorizontalHeaderLabels(["№", "Участник (регион) рейтинг"])

        for g in range(self.num_groups):
            group_frame = QFrame()
            group_frame.setFrameStyle(QFrame.Box)
            group_frame.setMinimumWidth(260)  # Уменьшено с 300
            group_frame.setMaximumWidth(320)  # Уменьшено с 400
            group_layout = QVBoxLayout(group_frame)
            group_layout.setSpacing(3)
            
            header = QLabel(f"Группа {g+1}")
            header.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white; padding: 3px; font-size: 11px;")
            header.setAlignment(Qt.AlignCenter)
            group_layout.addWidget(header)
            
            table = QTableWidget()
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["№", "Участник"])
# =======================================================            
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
            table.setColumnWidth(0, 40)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            
            table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            table.setRowCount(self.max_rows_per_group)
            
            table.verticalHeader().setVisible(False)
            table.setAlternatingRowColors(True)
            table.setSelectionBehavior(QTableWidget.SelectItems)
            table.cellClicked.connect(self.on_cell_clicked)
            table.setEditTriggers(QTableWidget.DoubleClicked)
            table.itemDoubleClicked.connect(self.on_item_double_clicked)
            
            table.setMouseTracking(True)
            table.cellEntered.connect(self.on_cell_entered)
            
            for row in range(self.max_rows_per_group):
                num_item = QTableWidgetItem(str(row + 1))
                num_item.setTextAlignment(Qt.AlignCenter)
                num_item.setFlags(num_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 0, num_item)
                table.setRowHeight(row, 22)
            
            group_layout.addWidget(table)
            
            table_height = table.horizontalHeader().height() + 2
            table_height += self.max_rows_per_group * 22
            table.setFixedHeight(table_height + 5)
            
            row = g // cols
            col = g % cols
            self.groups_layout.addWidget(group_frame, row, col)
            
            self.group_tables.append(table)
            self.group_headers.append(header)
        
        self.groups_layout.setSpacing(15)
        self.groups_layout.setContentsMargins(10, 10, 10, 10)
        
        if not self.groups:
            self.groups = [[] for _ in range(self.num_groups)]
        
        self.update_groups_display()
        self.highlight_current_group()
    
    def on_cell_entered(self, row, col):
        """Обработка наведения мыши на ячейку"""
        if col != 1:
            return
        
        table = self.sender()
        if not table:
            return
        
        for g_idx, t in enumerate(self.group_tables):
            if t == table:
                if g_idx < len(self.groups) and row < len(self.groups[g_idx]) and self.groups[g_idx][row]:
                    athlete = self.groups[g_idx][row]
                    if athlete:
                        id_player, name, rating, region, coach = athlete
                        tooltip_text = f"ID: {id_player}\nФИО: {name}\nРейтинг: {rating}\nРегион: {region}\nТренер: {coach}"
                        QToolTip.showText(QCursor.pos(), tooltip_text)
                break
    
    def update_groups_display(self):
        """Обновление отображения всех групп"""
        for g_idx, table in enumerate(self.group_tables):
            for row in range(self.max_rows_per_group):
                if g_idx < len(self.groups) and row < len(self.groups[g_idx]) and self.groups[g_idx][row]:
                    athlete = self.groups[g_idx][row]
                    if athlete:
                        id_player, name, rating, region, coach = athlete
                        display_text = f"{name} ({region}) R:{rating}"
                        item = QTableWidgetItem(display_text)
                        item.setData(Qt.UserRole, id_player)
                        item.setFlags(item.flags() | Qt.ItemIsEditable)
                        item.setToolTip(f"ID: {id_player}\nФИО: {name}\nРейтинг: {rating}\nРегион: {region}\nТренер: {coach}")
                        table.setItem(row, 1, item)
                    else:
                        empty_item = QTableWidgetItem("")
                        empty_item.setFlags(empty_item.flags() | Qt.ItemIsEditable)
                        table.setItem(row, 1, empty_item)
                else:
                    empty_item = QTableWidgetItem("")
                    empty_item.setFlags(empty_item.flags() | Qt.ItemIsEditable)
                    table.setItem(row, 1, empty_item)
        
        self.update_stats()
        self.update_athletes_table()
        
    def update_stats(self):
        """Обновление статистики"""
        total = len(self.athletes)
        placed = self.current_athlete_index
        remaining = total - placed
        self.total_label.setText(str(total))
        self.placed_label.setText(str(placed))
        self.remaining_label.setText(str(remaining))
        self.max_rows_label.setText(str(self.max_rows_per_group))
        self.round_number_label.setText(str(self.current_round))
        self.update_current_athlete()
        
    def update_current_athlete(self):
        """Обновление отображения текущего спортсмена"""
        if self.current_athlete_index < len(self.sorted_athletes):
            athlete = self.sorted_athletes[self.current_athlete_index]
            id_player, name, rating, region, coach = athlete
            self.current_athlete_label.setText(f"Спортсмен: {name}\nРейтинг: {rating}\nРегион: {region}\nТренер: {coach}")
            self.highlight_available_cells(athlete)
        else:
            self.current_athlete_label.setText("Жеребьевка завершена!\nВсе спортсмены\nраспределены")
            self.current_athlete_label.setStyleSheet("background-color: #90EE90; padding: 8px; font-size: 12px;")
    
    def check_conflicts(self, athlete, group_idx):
        """Проверка конфликтов"""
        if group_idx >= len(self.groups):
            return False, False
            
        _, _, _, region, coach = athlete
        
        group_regions = [a[3] for a in self.groups[group_idx] if a]
        group_coaches = [a[4] for a in self.groups[group_idx] if a]
        
        region_conflict = region in group_regions
        coach_conflict = coach in group_coaches and region_conflict
        
        return region_conflict, coach_conflict
    
    def highlight_available_cells(self, athlete):
        """Подсветка доступных ячеек"""
        for table in self.group_tables:
            for row in range(table.rowCount()):
                num_item = table.item(row, 0)
                if num_item:
                    num_item.setBackground(QBrush(QColor(255, 255, 255)))
                    
        if not athlete:
            return
            
        for g_idx, table in enumerate(self.group_tables):
            for row in range(table.rowCount()):
                item = table.item(row, 1)
                if not item or not item.text():
                    region_conflict, coach_conflict = self.check_conflicts(athlete, g_idx)
                    
                    num_item = table.item(row, 0)
                    if num_item:
                        if coach_conflict:
                            num_item.setBackground(QBrush(QColor(255, 100, 100)))
                        elif region_conflict:
                            num_item.setBackground(QBrush(QColor(255, 255, 150)))
                        else:
                            num_item.setBackground(QBrush(QColor(144, 238, 144)))
    
    def can_place_athlete(self, athlete, group_idx, row):
        """Проверка возможности размещения"""
        if group_idx >= len(self.groups):
            return False
            
        if row < len(self.groups[group_idx]) and self.groups[group_idx][row] is not None:
            return False
            
        return True
    
    def closeEvent(self, event):
        """Обработка закрытия окна через крестик"""
        if self.current_athlete_index < len(self.sorted_athletes):
            reply = QMessageBox.question(self, 'Подтверждение закрытия',
                f'Не все спортсмены распределены!\n'
                f'Осталось: {len(self.sorted_athletes) - self.current_athlete_index} спортсменов.\n\n'
                f'Вы уверены, что хотите закрыть окно жеребьевки?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
        
    def on_cell_clicked(self, row, col):
        """Обработка клика по ячейке"""
        if col != 1:
            return
            
        table = self.sender()
        if not table:
            return
            
        for g_idx, t in enumerate(self.group_tables):
            if t == table:
                if self.current_athlete_index >= len(self.sorted_athletes):
                    QMessageBox.information(self, "Информация", "Все спортсмены уже размещены!")
                    return
                
                current_athlete = self.sorted_athletes[self.current_athlete_index]
                
                if not self.can_place_athlete(current_athlete, g_idx, row):
                    QMessageBox.warning(self, "Ошибка", "Это место уже занято!")
                    return
                
                region_conflict, coach_conflict = self.check_conflicts(current_athlete, g_idx)
                
                if coach_conflict:
                    QMessageBox.warning(self, "Запрещено!",
                        f"Нельзя разместить {current_athlete[1]} в группу {g_idx + 1}!\n"
                        f"В группе уже есть спортсмен с таким же регионом ({current_athlete[3]}) и тренером ({current_athlete[4]}).")
                    return
                
                if region_conflict:
                    reply = QMessageBox.question(self, 'Конфликт регионов',
                        f'В группе {g_idx + 1} уже есть спортсмен из региона {current_athlete[3]}.\n'
                        f'Разместить {current_athlete[1]} в эту группу?',
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    
                    if reply == QMessageBox.No:
                        return
                
                while len(self.groups[g_idx]) <= row:
                    self.groups[g_idx].append(None)
                self.groups[g_idx][row] = current_athlete
                
                display_text = f"{current_athlete[1]} ({current_athlete[3]}) R:{current_athlete[2]}"
                item = QTableWidgetItem(display_text)
                item.setData(Qt.UserRole, current_athlete[0])
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                item.setToolTip(f"ID: {current_athlete[0]}\nФИО: {current_athlete[1]}\nРейтинг: {current_athlete[2]}\nРегион: {current_athlete[3]}\nТренер: {current_athlete[4]}")
                table.setItem(row, 1, item)
                
                self.current_athlete_index += 1
                self.update_round_display()
                
                if g_idx == self.current_group_for_seed:
                    self.move_to_next_group()
                else:
                    self.highlight_current_group()
                
                if self.current_athlete_index < len(self.sorted_athletes):
                    self.highlight_available_cells(self.sorted_athletes[self.current_athlete_index])
                
                self.update_stats()
                
                if self.current_athlete_index >= len(self.sorted_athletes):
                    QMessageBox.information(self, "Поздравляем!", "Жеребьевка успешно завершена!")
                    # self.save_to_database()
                break
    
    def on_item_double_clicked(self, item):
        """Редактирование ячейки"""
        if item.column() != 1:
            return
            
        table = item.tableWidget()
        row = item.row()
        
        for g_idx, t in enumerate(self.group_tables):
            if t == table:
                self.edit_cell(g_idx, row)
                break
    
    def edit_cell(self, group_idx, row):
        """Редактирование конкретной ячейки"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Редактирование ячейки")
        dialog.setModal(True)
        dialog.setMinimumWidth(500)
        layout = QVBoxLayout(dialog)
        
        all_unplaced = self.sorted_athletes[self.current_athlete_index:]
        
        list_widget = QListWidget()
        
        current_athlete = None
        if group_idx < len(self.groups) and row < len(self.groups[group_idx]):
            current_athlete = self.groups[group_idx][row]
            if current_athlete:
                list_widget.addItem(f"--- Текущий: {current_athlete[1]} (Рейтинг: {current_athlete[2]}, Тренер: {current_athlete[4]}) ---")
        
        for athlete in all_unplaced:
            list_widget.addItem(f"{athlete[1]} (Рейтинг: {athlete[2]}, Регион: {athlete[3]}, Тренер: {athlete[4]})")
        
        list_widget.addItem("--- Очистить ячейку ---")
        
        layout.addWidget(QLabel("Выберите спортсмена для размещения:"))
        layout.addWidget(list_widget)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        
        def on_accept():
            selected = list_widget.currentRow()
            if selected >= 0:
                offset = 1 if current_athlete else 0
                
                if selected < len(all_unplaced) + offset:
                    athlete_idx = selected - offset
                    if athlete_idx >= 0 and athlete_idx < len(all_unplaced):
                        athlete = all_unplaced[athlete_idx]
                        
                        region_conflict, coach_conflict = self.check_conflicts(athlete, group_idx)
                        
                        if coach_conflict:
                            QMessageBox.warning(dialog, "Запрещено!",
                                f"Нельзя разместить {athlete[1]} в группу {group_idx + 1}!\n"
                                f"В группе уже есть спортсмен с таким же регионом и тренером.")
                            return
                        
                        if region_conflict:
                            reply = QMessageBox.question(dialog, 'Конфликт регионов',
                                f'В группе {group_idx + 1} уже есть спортсмен из региона {athlete[3]}.\n'
                                f'Все равно разместить?',
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                            
                            if reply == QMessageBox.No:
                                return
                        
                        old_athlete = None
                        if group_idx < len(self.groups) and row < len(self.groups[group_idx]):
                            old_athlete = self.groups[group_idx][row]
                        
                        while len(self.groups[group_idx]) <= row:
                            self.groups[group_idx].append(None)
                        self.groups[group_idx][row] = athlete
                        
                        table = self.group_tables[group_idx]
                        display_text = f"{athlete[1]} ({athlete[3]}) R:{athlete[2]}"
                        item = QTableWidgetItem(display_text)
                        item.setData(Qt.UserRole, athlete[0])
                        item.setFlags(item.flags() | Qt.ItemIsEditable)
                        item.setToolTip(f"ID: {athlete[0]}\nФИО: {athlete[1]}\nРейтинг: {athlete[2]}\nРегион: {athlete[3]}\nТренер: {athlete[4]}")
                        table.setItem(row, 1, item)
                        
                        if athlete in self.sorted_athletes:
                            idx = self.sorted_athletes.index(athlete)
                            if idx >= self.current_athlete_index:
                                self.sorted_athletes.pop(idx)
                                if idx < self.current_athlete_index:
                                    self.current_athlete_index -= 1
                        
                        if old_athlete:
                            self.sorted_athletes.insert(self.current_athlete_index, old_athlete)
                        
                        self.update_athletes_table()
                        self.update_stats()
                        self.update_current_athlete()
                        dialog.accept()
                elif selected == len(all_unplaced) + offset:
                    if group_idx < len(self.groups) and row < len(self.groups[group_idx]):
                        athlete = self.groups[group_idx][row]
                        self.groups[group_idx][row] = None
                        
                        table = self.group_tables[group_idx]
                        table.setItem(row, 1, QTableWidgetItem(""))
                        
                        if athlete:
                            self.sorted_athletes.insert(self.current_athlete_index, athlete)
                            self.update_athletes_table()
                            self.update_stats()
                            self.update_current_athlete()
                            dialog.accept()
            else:
                QMessageBox.warning(dialog, "Ошибка", "Выберите спортсмена!")
        
        buttons.accepted.connect(on_accept)
        buttons.rejected.connect(dialog.reject)
        dialog.exec_()
    
    def open_editor(self):
        """Открыть редактор для обмена игроками между группами"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Редактор групп")
        dialog.setModal(True)
        dialog.setMinimumSize(800, 500)
        dialog.setMaximumSize(1000, 600)
        
        layout = QVBoxLayout(dialog)
        
        group_combos = []
        group_labels = []
        
        # Создаем копию текущих данных групп для редактирования
        group_data = []
        for g_idx in range(self.num_groups):
            group_copy = []
            for athlete in self.groups[g_idx]:
                group_copy.append(athlete)
            group_data.append(group_copy)
        
        scroll_widget = QWidget()
        scroll_layout = QGridLayout(scroll_widget)
        
        cols = min(4, self.num_groups)
        for g_idx in range(self.num_groups):
            group_frame = QFrame()
            group_frame.setFrameStyle(QFrame.Box)
            group_frame.setMaximumWidth(250)
            group_layout = QVBoxLayout(group_frame)
            group_layout.setSpacing(5)
            
            label = QLabel(f"Группа {g_idx + 1}")
            label.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white; padding: 3px;")
            label.setAlignment(Qt.AlignCenter)
            group_layout.addWidget(label)
            
            combo = QComboBox()
            combo.setMaximumWidth(230)
            combo.setProperty("group_idx", g_idx)
            combo.addItem("--- Выберите спортсмена для перемещения ---")
            
            for row, athlete in enumerate(group_data[g_idx]):
                if athlete:
                    short_name = athlete[1][:15] + "..." if len(athlete[1]) > 15 else athlete[1]
                    # Сохраняем полную информацию о спортсмене
                    combo.addItem(f"{row+1}. {short_name} ({athlete[3][:10]}) R:{athlete[2]}", (g_idx, row, athlete))
            
            group_layout.addWidget(combo)
            group_combos.append(combo)
            group_labels.append(label)
            
            scroll_layout.addWidget(group_frame, g_idx // cols, g_idx % cols)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        btn_layout = QHBoxLayout()
        
        btn_swap = QPushButton("Обменять выбранных")
        btn_swap.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        btn_layout.addWidget(btn_swap)
        
        btn_move = QPushButton("Переместить")
        btn_move.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        btn_layout.addWidget(btn_move)
        
        btn_save = QPushButton("Сохранить изменения")
        btn_save.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        btn_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setStyleSheet("background-color: #f44336; color: white; padding: 8px;")
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
        
        selected_athletes = []  # Список выбранных спортсменов (группа, индекс, спортсмен, комбобокс)
        
        def get_current_athlete_position(athlete, group_idx):
            """Получить актуальную позицию спортсмена в группе"""
            for idx, a in enumerate(group_data[group_idx]):
                if a and a[0] == athlete[0]:  # Сравниваем по ID
                    return idx
            return -1
        
        def refresh_combos():
            """Обновить все комбобоксы после изменений"""
            for g_idx in range(self.num_groups):
                current_text = group_combos[g_idx].currentText()
                current_data = group_combos[g_idx].currentData() if group_combos[g_idx].currentIndex() > 0 else None
                
                group_combos[g_idx].clear()
                group_combos[g_idx].addItem("--- Выберите спортсмена для перемещения ---")
                
                for row, athlete in enumerate(group_data[g_idx]):
                    if athlete:
                        short_name = athlete[1][:15] + "..." if len(athlete[1]) > 15 else athlete[1]
                        group_combos[g_idx].addItem(f"{row+1}. {short_name} ({athlete[3][:10]}) R:{athlete[2]}", (g_idx, row, athlete))
                
                group_combos[g_idx].setEnabled(True)
                group_labels[g_idx].setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white; padding: 3px;")
                
                # Восстанавливаем выбранный элемент если возможно
                if current_data:
                    for i in range(group_combos[g_idx].count()):
                        data = group_combos[g_idx].itemData(i)
                        if data and data[2][0] == current_data[2][0]:  # Сравниваем по ID
                            group_combos[g_idx].setCurrentIndex(i)
                            break
            
            # Очищаем список выбранных спортсменов
            selected_athletes.clear()
        
        def on_combo_change(idx, group_idx):
            if idx > 0:
                athlete_data = group_combos[group_idx].itemData(idx)
                if athlete_data:
                    # Проверяем, не выбран ли уже этот спортсмен
                    for existing in selected_athletes:
                        if existing[2][0] == athlete_data[2][0]:  # Сравниваем по ID
                            QMessageBox.warning(dialog, "Ошибка", "Этот спортсмен уже выбран!")
                            group_combos[group_idx].setCurrentIndex(0)
                            return
                    
                    selected_athletes.append((group_idx, athlete_data[1], athlete_data[2], group_combos[group_idx]))
                    group_combos[group_idx].setEnabled(False)
                    group_labels[group_idx].setStyleSheet("font-weight: bold; background-color: #FF9800; color: white; padding: 3px;")
        
        for g_idx, combo in enumerate(group_combos):
            combo.currentIndexChanged.connect(lambda idx, g=g_idx: on_combo_change(idx, g))
        
        def swap_athletes():
            if len(selected_athletes) == 2:
                g1, row1, athlete1, combo1 = selected_athletes[0]
                g2, row2, athlete2, combo2 = selected_athletes[1]
                
                # Получаем актуальные позиции спортсменов
                actual_row1 = get_current_athlete_position(athlete1, g1)
                actual_row2 = get_current_athlete_position(athlete2, g2)
                
                if actual_row1 == -1 or actual_row2 == -1:
                    QMessageBox.warning(dialog, "Ошибка", "Спортсмен не найден в группе!")
                    refresh_combos()
                    return
                
                # Проверяем конфликты при обмене
                conflict1 = False
                conflict2 = False
                
                # Проверяем для группы 1 с athlete2
                group1_regions = [a[3] for a in group_data[g1] if a and a[0] != athlete1[0]]
                if athlete2[3] in group1_regions:
                    group1_coaches = [a[4] for a in group_data[g1] if a and a[0] != athlete1[0]]
                    if athlete2[4] in group1_coaches:
                        conflict1 = True
                
                # Проверяем для группы 2 с athlete1
                group2_regions = [a[3] for a in group_data[g2] if a and a[0] != athlete2[0]]
                if athlete1[3] in group2_regions:
                    group2_coaches = [a[4] for a in group_data[g2] if a and a[0] != athlete2[0]]
                    if athlete1[4] in group2_coaches:
                        conflict2 = True
                
                if conflict1 or conflict2:
                    QMessageBox.warning(dialog, "Запрещено!",
                        "Обмен невозможен! Будет нарушено правило совпадения региона и тренера.")
                    return
                
                # Выполняем обмен
                group_data[g1][actual_row1], group_data[g2][actual_row2] = athlete2, athlete1
                
                refresh_combos()
                QMessageBox.information(dialog, "Успех", "Спортсмены успешно обменяны!")
            else:
                QMessageBox.warning(dialog, "Ошибка", "Выберите ровно двух спортсменов для обмена!")
        
        def move_athlete():
            if len(selected_athletes) == 1:
                g1, row1, athlete1, combo1 = selected_athletes[0]
                
                # Получаем актуальную позицию спортсмена
                actual_row1 = get_current_athlete_position(athlete1, g1)
                
                if actual_row1 == -1:
                    QMessageBox.warning(dialog, "Ошибка", "Спортсмен не найден в группе!")
                    refresh_combos()
                    return
                
                # Создаем диалог выбора цели
                target_dialog = QDialog(dialog)
                target_dialog.setWindowTitle("Выберите цель")
                target_layout = QVBoxLayout(target_dialog)
                target_dialog.setFixedSize(450, 300)
                
                target_layout.addWidget(QLabel("Выберите группу:"))
                target_combo = QComboBox()
                available_groups = [f"Группа {i+1}" for i in range(self.num_groups) if i != g1]
                target_combo.addItems(available_groups)
                target_layout.addWidget(target_combo)
                
                target_layout.addWidget(QLabel("Выберите строку (номер посева):"))
                target_row_combo = QComboBox()
                target_layout.addWidget(target_row_combo)
                
                def update_row_status():
                    target_row_combo.clear()
                    target_group_name = target_combo.currentText()
                    target_group = int(target_group_name.split()[1]) - 1
                    
                    # Определяем максимальное количество строк
                    max_rows = max(self.max_rows_per_group, len(group_data[target_group]) + 5)
                    
                    for i in range(max_rows):
                        # Проверяем, занято ли место
                        is_occupied = False
                        if i < len(group_data[target_group]) and group_data[target_group][i] is not None:
                            is_occupied = True
                        status = " (занято)" if is_occupied else " (свободно)"
                        target_row_combo.addItem(f"{i+1}{status}", i)
                
                update_row_status()
                target_combo.currentIndexChanged.connect(update_row_status)
                
                buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                target_layout.addWidget(buttons)
                
                def do_move():
                    target_group_name = target_combo.currentText()
                    target_group = int(target_group_name.split()[1]) - 1
                    target_row = target_row_combo.currentData()
                    
                    # Проверяем, что целевая строка существует и не занята
                    if target_group >= len(group_data):
                        QMessageBox.warning(self, "Ошибка", "Целевая группа не существует!")
                        return
                    
                    # Расширяем список группы если нужно
                    while len(group_data[target_group]) <= target_row:
                        group_data[target_group].append(None)
                    
                    if group_data[target_group][target_row] is not None:
                        QMessageBox.warning(self, "Ошибка", "Это место уже занято!")
                        return
                    
                    # Проверяем конфликты при перемещении
                    group_target_regions = [a[3] for a in group_data[target_group] if a]
                    group_target_coaches = [a[4] for a in group_data[target_group] if a]
                    
                    region_conflict = athlete1[3] in group_target_regions
                    coach_conflict = athlete1[4] in group_target_coaches and region_conflict
                    
                    if coach_conflict:
                        QMessageBox.warning(self, "Запрещено!",
                            f"Нельзя переместить {athlete1[1]} в группу {target_group + 1}!\n"
                            f"В группе уже есть спортсмен с таким же регионом и тренером.")
                        return
                    
                    if region_conflict:
                        reply = QMessageBox.question(target_dialog, 'Конфликт регионов',
                            f'В группе {target_group + 1} уже есть спортсмен из региона {athlete1[3]}.\n'
                            f'Все равно переместить?',
                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        
                        if reply == QMessageBox.No:
                            return
                    
                    # Выполняем перемещение
                    group_data[g1][actual_row1] = None
                    group_data[target_group][target_row] = athlete1
                    
                    target_dialog.accept()
                    refresh_combos()
                    QMessageBox.information(dialog, "Успех", "Спортсмен успешно перемещен!")
                
                buttons.accepted.connect(do_move)
                buttons.rejected.connect(target_dialog.reject)
                target_dialog.exec_()
            else:
                QMessageBox.warning(self, "Ошибка", "Выберите одного спортсмена для перемещения!")
        
        def save_changes():
            """Сохранить изменения и обновить основное отображение"""
            # Обновляем основные данные групп, удаляя None значения
            self.groups = []
            for g_idx in range(self.num_groups):
                group = []
                for athlete in group_data[g_idx]:
                    if athlete:
                        group.append(athlete)
                self.groups.append(group)
            
            # Обновляем индекс текущего спортсмена
            placed_count = sum(1 for group in self.groups for athlete in group if athlete)
            self.current_athlete_index = placed_count
            
            # Обновляем отображение
            self.update_groups_display()
            self.update_athletes_table()
            self.update_stats()
            self.update_current_athlete()
            
            # Пересчитываем текущую группу для посева
            self.current_group_for_seed = self.find_next_group_for_seed()
            self.highlight_current_group()
            
            dialog.accept()
            QMessageBox.information(self, "Успех", "Изменения сохранены!")
        
        btn_swap.clicked.connect(swap_athletes)
        btn_move.clicked.connect(move_athlete)
        btn_save.clicked.connect(save_changes)
        btn_cancel.clicked.connect(dialog.reject)
        
        dialog.exec_()
    
    def reset_draw(self):
        """Полный сброс"""
        self.load_athletes()
        self.current_athlete_index = 0
        self.groups = [[] for _ in range(self.num_groups)]
        self.current_group_for_seed = self.num_groups - 1
        self.init_groups()
        self.update_round_display()
        self.highlight_current_group()
        self.current_athlete_label.setStyleSheet("background-color: #ffe0b3; padding: 8px; font-size: 12px;")
    
    def auto_fill_first(self):
        """Автоматическое заполнение первых номеров"""
        self.reset_draw()
        
        for i in range(min(self.num_groups, len(self.sorted_athletes))):
            self.groups[i] = [self.sorted_athletes[i]]
            table = self.group_tables[i]
            athlete = self.sorted_athletes[i]
            display_text = f"{athlete[1]} ({athlete[3]}) R:{athlete[2]}"
            item = QTableWidgetItem(display_text)
            item.setData(Qt.UserRole, athlete[0])
            item.setToolTip(f"ID: {athlete[0]}\nФИО: {athlete[1]}\nРейтинг: {athlete[2]}\nРегион: {athlete[3]}\nТренер: {athlete[4]}")
            table.setItem(0, 1, item)
            self.current_athlete_index += 1
        
        self.update_round_display()
        self.current_group_for_seed = self.find_next_group_for_seed()
        self.update_athletes_table()
        self.update_stats()
        self.highlight_current_group()
    
    def clear_all_groups(self):
        """Очистка всех групп"""
        all_athletes = []
        for group in self.groups:
            for athlete in group:
                if athlete:
                    all_athletes.append(athlete)
        
        self.groups = [[] for _ in range(self.num_groups)]
        self.sorted_athletes = sorted(all_athletes + self.sorted_athletes[self.current_athlete_index:], 
                                     key=lambda x: x[2], reverse=True)
        self.current_athlete_index = 0
        self.current_group_for_seed = self.num_groups - 1
        
        for table in self.group_tables:
            for row in range(self.max_rows_per_group):
                table.setItem(row, 1, QTableWidgetItem(""))
        
        self.update_athletes_table()
        self.update_stats()
        self.update_round_display()
        self.highlight_current_group()
        self.update_current_athlete()
    
    def _show_results(self):
        """Показать результаты"""
        results = []
        for group_idx, group in enumerate(self.groups):
            gr = group_idx + 1
            for seed_num, athlete in enumerate(group, 1):
                if athlete:
                    results.append([
                        seed_num,
                        athlete[0],
                        athlete[1],
                        athlete[3],
                        gr
                    ])
        
        results.sort(key=lambda x: x[0])
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Результаты жеребьевки")
        dialog.setModal(True)
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        result_table = QTableWidget()
        result_table.setColumnCount(4)
        result_table.setHorizontalHeaderLabels(["№ посева", "ID игрока", "ФИО", "Регион"])
        result_table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            for col, value in enumerate(result):
                result_table.setItem(row, col, QTableWidgetItem(str(value)))
        
        result_table.horizontalHeader().setStretchLastSection(True)
        result_table.resizeColumnsToContents()
        
        layout.addWidget(QLabel("Результаты жеребьевки:"))
        layout.addWidget(result_table)
        
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        
        dialog.exec_()
    
    def show_results(self):
        """показать результаты жереьевки в pdf"""
        pass

    def get_results(self):
        """Получить результаты жеребьевки"""
        results = []
        for group_idx, group in enumerate(self.groups):
            gr = group_idx + 1
            for seed_num, athlete in enumerate(group, 1):
                if athlete:
                    results.append({
                        'seed_num': seed_num,
                        'id_player': athlete[0],
                        'name': athlete[1],
                        'region': athlete[3],
                        'group': gr
                    })
        return results

def load_existing_draw_from_db(id_title):
    """Загрузка существующей жеребьевки из базы данных через Peewee"""
    choices = Choice.select().where(Choice.title_id == id_title)
    try:
        results = choices.select().order_by(Choice.group, Choice.posev_group)
        return list(results) if results.exists() else None
    except Exception as e:
        print(f"Ошибка при загрузке из базы данных: {e}")
        return None

def clear_db_before_choice(self):
    """очищает базу данных -Game_list- и -Result- перед повторной жеребьевкой групп"""

    systems = System.select().where((System.stage == "Квалификация") & (System.title_id == self)).get()
    id_system = systems.id

    gamelist = Game_list.select().where((Game_list.title_id == self) & (Game_list.system_id == id_system))
    for i in gamelist:
        gl_d = Game_list.get(Game_list.id == i)
        gl_d.delete_instance()
    results = Result.select().where((Result.title_id == self) & (Result.system_id == id_system))
    for i in results:
        r_d = Result.get(Result.id == i)
        r_d.delete_instance()
    choice = Choice.select().where(Choice.title_id == self)
    for i in choice:
        Choice.update(group = None, posev_group=None).where(Choice.id == i).execute()

def choice_group_manual(self, athletes, num_groups, stage, parent=None):
    """
    Функция для вызова ручной жеребьевки
    
    Args:
        athletes: список списков [id игрока, фамилия_имя, рейтинг, регион, тренер]
        num_groups: количество групп (от 2 до 32)
        parent: родительское окно
    
    Returns:
        list: список результатов или None если отмена
    """

    existing_data = None
    if num_groups == 1:
        # одна таблица
        system = System.select().where((System.title_id == self.current_title_id) and (System.stage == "Одна таблица")).get()  # находит system id последнего
    elif num_groups > 1 or num_groups <= 48:
    #     raise ValueError("Количество групп должно быть от 2 до 32")
        system = System.select().where((System.title_id == self.current_title_id) and (System.stage == stage)).get()  # находит system id последнего
    
    check_flag = system.choice_flag
    if check_flag is True:
        # Проверяем, есть ли уже жеребьевка в базе данных
        existing_data = load_existing_draw_from_db(self.current_title_id)
    
    if existing_data:
        # Создаем диалог выбора действия
        action_dialog = ChoiceActionDialog(parent)
        result = action_dialog.exec_()
        
        if result == 1:  # Сбросить
            # Очищаем таблицу в БД
            clear_db_before_choice(self.current_title_id)
            try:
                existing_data = None
                QMessageBox.information(parent, "Информация", 
                    "Начинаем новую жеребьевку. Предыдущие данные удалены.")
            except Exception as e:
                QMessageBox.warning(parent, "Ошибка", f"Ошибка при очистке БД: {str(e)}")
                return None
        elif result == 2:  # Загрузить
            # Загружаем существующую жеребьевку
            pass
        else:  # Отмена
            return None
    
    dialog = ChoiceGroupManual(athletes, num_groups, self.current_title_id, parent, existing_data)
    result_code = dialog.exec_()
    
    if result_code == QDialog.Accepted:
        return dialog.get_results()
    else:
        return None
#====================== новый вариант с ручной жеребьевкой полуфиналов ===========
# ========== РУЧНАЯ ЖЕРЕБЬЁВКА ПОЛУФИНАЛОВ (ОБНОВЛЁННАЯ) ==========
class SemiFinalManual(QDialog):
    """
    Диалог ручной жеребьёвки полуфиналов.
    Автоматически заполняет 1-е и 2-е места из квалификационных групп.
    3-и и 4-е места распределяются вручную из списка, отсортированного
    от второй половины групп к первой.
    """
    def __init__(self, athletes, groups_data, title_id=None, parent=None):
        super().__init__(parent)
        self.athletes = athletes
        self.groups_data = groups_data          # [(номер_группы, [игрок1, игрок2, ...]), ...]
        self.title_id = title_id
        self.num_sf = 2                         # количество полуфиналов
        self.current_sf = 0                     # 0 - первый, 1 - второй
        self.players_per_group = 4              # в группе полуфинала 4 места

        # Данные полуфиналов
        self.sf_groups = []                     # для каждого полуфинала список групп (каждая группа - список из 4 элементов)
        self.available_players = []             # для каждого полуфинала список доступных игроков (кортежи (группа_квалиф, игрок))
        self.current_player_idx = 0             # индекс следующего игрока в списке

        self.conflicts = []                     # для сбора конфликтов
        self.initUI()
        self.prepare_data()
        self.update_interface()

    def prepare_data(self):
        """Формирует группы полуфиналов и списки доступных игроков."""
        total_qual_groups = len(self.groups_data)
        num_sf_groups = total_qual_groups // 2   # количество групп в каждом полуфинале

        # 1. Инициализация групп полуфиналов
        self.sf_groups = []
        for _ in range(self.num_sf):
            groups = []
            for _ in range(num_sf_groups):
                groups.append([None, None, None, None])  # 4 позиции
            self.sf_groups.append(groups)

        # 2. Автоматическое заполнение 1-х и 2-х мест (для обоих полуфиналов)
        # Первый полуфинал: 1-е и 2-е места из групп 1..num_sf_groups
        # Второй полуфинал: 1-е и 2-е места из групп num_sf_groups+1 .. total_qual_groups
        for sf_idx in range(self.num_sf):
            start_group = sf_idx * num_sf_groups + 1
            end_group = (sf_idx + 1) * num_sf_groups
            for qual_group_num in range(start_group, end_group + 1):
                # Находим данные по этой квалификационной группе
                group_data = None
                for g_num, players in self.groups_data:
                    if g_num == qual_group_num:
                        group_data = players
                        break
                if group_data and len(group_data) >= 2:
                    sf_group_idx = (qual_group_num - start_group)  # индекс группы в полуфинале
                    self.sf_groups[sf_idx][sf_group_idx][0] = group_data[0]  # 1-е место
                    self.sf_groups[sf_idx][sf_group_idx][1] = group_data[1]  # 2-е место

        # 3. Формирование списков доступных игроков для ручного заполнения (3-и и 4-е места)
        # Собираем всех игроков с 3-х и 4-х мест из всех групп квалификации
        all_players = []   # (номер_группы, игрок)
        for qual_group_num, players in self.groups_data:
            if len(players) >= 3:
                all_players.append((qual_group_num, players[2]))
            if len(players) >= 4:
                all_players.append((qual_group_num, players[3]))

        # Сортируем: сначала игроки из второй половины групп (от большего номера к меньшему)
        half = num_sf_groups
        second_half = [p for p in all_players if p[0] > half]
        first_half = [p for p in all_players if p[0] <= half]
        second_half.sort(key=lambda x: x[0], reverse=True)
        first_half.sort(key=lambda x: x[0], reverse=True)
        sorted_players = second_half + first_half

        # Разделяем на два полуфинала: для первого только из первой половины групп,
        # для второго – из второй половины.
        self.available_players = [
            [p for p in sorted_players if p[0] <= half],
            [p for p in sorted_players if p[0] > half]
        ]

        self.current_player_idx = 0

    def initUI(self):
        self.setWindowTitle('Ручная жеребьёвка полуфиналов')
        self.setGeometry(100, 100, 1300, 750)
        main_layout = QVBoxLayout(self)

        # Верхняя панель информации
        top_layout = QHBoxLayout()
        self.current_player_label = QLabel("Текущий игрок: -")
        top_layout.addWidget(self.current_player_label)
        self.current_sf_label = QLabel("Полуфинал: 1")
        top_layout.addWidget(self.current_sf_label)
        main_layout.addLayout(top_layout)

        # Основная часть: слева список игроков, справа таблицы групп
        content_layout = QHBoxLayout()

        # Левая панель – список доступных игроков
        left_panel = QFrame()
        left_panel.setMaximumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("Доступные игроки:"))
        self.players_list = QListWidget()
        self.players_list.setAlternatingRowColors(True)
        self.players_list.itemDoubleClicked.connect(self.on_player_double_click)
        left_layout.addWidget(self.players_list)
        content_layout.addWidget(left_panel)

        # Правая панель – группы полуфинала
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        self.groups_scroll = QScrollArea()
        self.groups_scroll.setWidgetResizable(True)
        self.groups_widget = QWidget()
        self.groups_layout = QGridLayout(self.groups_widget)
        self.groups_layout.setAlignment(Qt.AlignTop)
        self.groups_scroll.setWidget(self.groups_widget)
        right_layout.addWidget(self.groups_scroll)
        content_layout.addWidget(right_panel, stretch=1)
        main_layout.addLayout(content_layout)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        self.btn_prev_sf = QPushButton("◀ Предыдущий полуфинал")
        self.btn_prev_sf.clicked.connect(self.prev_semifinal)
        btn_layout.addWidget(self.btn_prev_sf)
        self.btn_next_sf = QPushButton("Следующий полуфинал ▶")
        self.btn_next_sf.clicked.connect(self.next_semifinal)
        btn_layout.addWidget(self.btn_next_sf)
        self.btn_reset = QPushButton("Сбросить текущий")
        self.btn_reset.clicked.connect(self.reset_current_sf)
        btn_layout.addWidget(self.btn_reset)
        self.btn_auto_fill = QPushButton("Авто-заполнить 3-4 места")
        self.btn_auto_fill.clicked.connect(self.auto_fill_remaining)
        btn_layout.addWidget(self.btn_auto_fill)
        self.btn_save = QPushButton("Записать результаты")
        self.btn_save.clicked.connect(self.save_results)
        btn_layout.addWidget(self.btn_save)
        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)
        main_layout.addLayout(btn_layout)

        self.setModal(True)

    def update_interface(self):
        """Обновляет список игроков и таблицы групп для текущего полуфинала."""
        self.update_players_list()
        self.update_groups_tables()
        self.current_sf_label.setText(f"Полуфинал: {self.current_sf + 1}")
        players = self.available_players[self.current_sf]
        if self.current_player_idx < len(players):
            p = players[self.current_player_idx][1]
            self.current_player_label.setText(f"Текущий игрок: {p[1]} (рейтинг {p[2]}, регион {p[3]})")
        else:
            self.current_player_label.setText("Все игроки распределены!")

    def update_players_list(self):
        """Заполняет список доступных игроков для текущего полуфинала."""
        self.players_list.clear()
        players = self.available_players[self.current_sf]
        for i in range(self.current_player_idx, len(players)):
            qual_group, player = players[i]
            self.players_list.addItem(f"{player[1]} (рейтинг {player[2]}, регион {player[3]}, из гр.{qual_group})")

    def update_groups_tables(self):
        """Перестраивает таблицы групп для текущего полуфинала."""
        # Очищаем старые таблицы
        for i in reversed(range(self.groups_layout.count())):
            widget = self.groups_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        groups = self.sf_groups[self.current_sf]
        cols = 4
        for g_idx, group in enumerate(groups):
            frame = QFrame()
            frame.setFrameStyle(QFrame.Box)
            frame.setMaximumWidth(320)
            frame_layout = QVBoxLayout(frame)

            header = QLabel(f"Группа {g_idx + 1}")
            header.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white; padding: 3px;")
            header.setAlignment(Qt.AlignCenter)
            frame_layout.addWidget(header)

            table = QTableWidget()
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["№", "Игрок"])
            table.horizontalHeader().setStretchLastSection(True)
            table.setRowCount(self.players_per_group)
            table.verticalHeader().setVisible(False)
            table.setAlternatingRowColors(True)
            table.cellClicked.connect(self.on_cell_clicked)
            table.setProperty("group_idx", g_idx)

            # Заполняем ячейки
            for row in range(self.players_per_group):
                num_item = QTableWidgetItem(str(row + 1))
                num_item.setTextAlignment(Qt.AlignCenter)
                num_item.setFlags(num_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 0, num_item)

                athlete = group[row] if row < len(group) else None
                if athlete:
                    item = QTableWidgetItem(f"{athlete[1]} ({athlete[3]}) R:{athlete[2]}")
                    item.setData(Qt.UserRole, athlete[0])
                    table.setItem(row, 1, item)
                else:
                    table.setItem(row, 1, QTableWidgetItem(""))

            # Подсветка конфликтов регионов с 1-м местом
            first_player = group[0] if len(group) > 0 else None
            if first_player:
                first_region = first_player[3]
                for row in range(2, self.players_per_group):  # 3-я и 4-я позиции (индексы 2,3)
                    athlete = group[row] if row < len(group) else None
                    if athlete and athlete[3] == first_region:
                        item = table.item(row, 1)
                        if item:
                            item.setBackground(QBrush(QColor(255, 200, 200)))  # светло-красный

            frame_layout.addWidget(table)
            row_pos = g_idx // cols
            col_pos = g_idx % cols
            self.groups_layout.addWidget(frame, row_pos, col_pos)

    def on_player_double_click(self, item):
        """Двойной клик по игроку в списке - размещает его в следующую свободную ячейку."""
        # Аналогично клику по ячейке, но используем текущего игрока
        # Найдём первую свободную ячейку (3-ю или 4-ю позицию) в группах текущего полуфинала
        groups = self.sf_groups[self.current_sf]
        for g_idx, group in enumerate(groups):
            for row in range(2, self.players_per_group):  # только 3-я и 4-я
                if len(group) <= row or group[row] is None:
                    self.place_player_to_cell(g_idx, row)
                    return
        QMessageBox.information(self, "Информация", "Нет свободных ячеек для размещения!")

    def on_cell_clicked(self, row, col):
        """Обработка клика по ячейке таблицы группы (только для 3-й и 4-й позиций)."""
        if col != 1:
            return
        if row < 2:  # 1-я и 2-я позиции заблокированы
            QMessageBox.warning(self, "Ошибка", "1-е и 2-е места заполняются автоматически!")
            return
        table = self.sender()
        if not table:
            return
        group_idx = table.property("group_idx")
        if group_idx is None:
            return

        self.place_player_to_cell(group_idx, row)

    def place_player_to_cell(self, group_idx, row):
        """Размещает следующего игрока на указанную ячейку (row = 2 или 3)."""
        players = self.available_players[self.current_sf]
        if self.current_player_idx >= len(players):
            QMessageBox.information(self, "Информация", "Нет доступных игроков!")
            return

        groups = self.sf_groups[self.current_sf]
        group = groups[group_idx]

        # Проверяем, свободна ли ячейка
        if len(group) > row and group[row] is not None:
            QMessageBox.warning(self, "Ошибка", "Эта ячейка уже занята!")
            return

        # Берём следующего игрока
        qual_group, athlete = players[self.current_player_idx]

        # Проверяем конфликт региона с 1-м местом
        first_player = group[0] if len(group) > 0 else None
        if first_player and first_player[3] == athlete[3]:
            reply = QMessageBox.question(self, 'Конфликт регионов',
                f'В группе уже есть игрок из региона {athlete[3]} на 1-м месте.\n'
                f'Все равно разместить {athlete[1]}?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        # Размещаем игрока на позицию row
        while len(group) <= row:
            group.append(None)
        group[row] = athlete
        self.current_player_idx += 1

        # Теперь автоматически заполняем 4-ю позицию (если это 3-я) парой из той же квалификационной группы
        if row == 2:  # разместили на 3-ю позицию
            # Ищем второго игрока из той же квалификационной группы (второе место)
            # Находим данные группы квалификации
            partner = None
            for qg, players_list in self.groups_data:
                if qg == qual_group:
                    if len(players_list) >= 4:
                        partner = players_list[3]  # 4-е место (индекс 3)
                    elif len(players_list) >= 3:
                        partner = players_list[2]  # если нет 4-го, берём 3-е (но такого быть не должно)
                    break
            if partner:
                # Проверяем, свободна ли 4-я позиция
                if len(group) <= 3 or group[3] is None:
                    # Проверяем конфликт региона с 1-м местом
                    if first_player and first_player[3] == partner[3]:
                        # Предупреждение, но размещаем
                        QMessageBox.warning(self, 'Конфликт регионов',
                            f'Автоматическое размещение {partner[1]} на 4-ю позицию вызывает конфликт региона.')
                    group[3] = partner
                    # Удаляем партнера из списка доступных, если он там есть
                    for idx, (qg, p) in enumerate(self.available_players[self.current_sf]):
                        if p[0] == partner[0] and qg == qual_group:
                            del self.available_players[self.current_sf][idx]
                            if idx < self.current_player_idx:
                                self.current_player_idx -= 1
                            break

        # Обновляем интерфейс
        self.update_interface()

        # Проверяем, все ли заполнено
        if self.current_player_idx >= len(players):
            QMessageBox.information(self, "Завершено", "Все игроки распределены!")

    def prev_semifinal(self):
        if self.current_sf > 0:
            self.current_sf -= 1
            self.current_player_idx = 0
            self.update_interface()

    def next_semifinal(self):
        if self.current_sf < self.num_sf - 1:
            self.current_sf += 1
            self.current_player_idx = 0
            self.update_interface()

    def reset_current_sf(self):
        """Сброс текущего полуфинала (очищает 3-и и 4-е места, возвращает игроков в список)."""
        reply = QMessageBox.question(self, 'Сброс', 'Очистить все 3-и и 4-е места текущего полуфинала?',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            groups = self.sf_groups[self.current_sf]
            # Собираем игроков с позиций 2 и 3 (индексы 2,3)
            removed = []
            for g in groups:
                for row in range(2, self.players_per_group):
                    if len(g) > row and g[row] is not None:
                        removed.append((g[row], self.current_sf))
                        g[row] = None
            # Возвращаем игроков в список доступных (в начало, чтобы их можно было снова распределить)
            # Для простоты просто добавляем в конец
            for player, _ in removed:
                # Находим квалификационную группу этого игрока
                qual_group = None
                for qg, pl in self.groups_data:
                    if player in pl:
                        qual_group = qg
                        break
                if qual_group is not None:
                    self.available_players[self.current_sf].append((qual_group, player))
            self.current_player_idx = 0
            self.update_interface()

    def auto_fill_remaining(self):
        """Автоматически заполняет все оставшиеся 3-и и 4-е места (без ручного выбора)."""
        # Просто последовательно размещаем всех доступных игроков
        groups = self.sf_groups[self.current_sf]
        players = self.available_players[self.current_sf]
        idx = self.current_player_idx
        for g_idx, group in enumerate(groups):
            for row in range(2, self.players_per_group):
                if idx >= len(players):
                    break
                if len(group) <= row or group[row] is None:
                    qual_group, athlete = players[idx]
                    # Проверяем конфликт региона с 1-м местом (просто предупреждаем, но размещаем)
                    first_player = group[0] if len(group) > 0 else None
                    if first_player and first_player[3] == athlete[3]:
                        self.conflicts.append(f"Конфликт региона: {athlete[1]} в группе {g_idx+1}")
                    while len(group) <= row:
                        group.append(None)
                    group[row] = athlete
                    idx += 1
                    # Если это 3-я позиция, пытаемся автоматически добавить партнера на 4-ю
                    if row == 2:
                        partner = None
                        for qg, pl in self.groups_data:
                            if qg == qual_group:
                                if len(pl) >= 4:
                                    partner = pl[3]
                                break
                        if partner:
                            if len(group) <= 3 or group[3] is None:
                                # Проверяем конфликт
                                if first_player and first_player[3] == partner[3]:
                                    self.conflicts.append(f"Конфликт региона: {partner[1]} в группе {g_idx+1}")
                                group[3] = partner
                                # Удаляем партнера из списка
                                for i, (q, p) in enumerate(players):
                                    if p[0] == partner[0] and q == qual_group:
                                        del players[i]
                                        if i < idx:
                                            idx -= 1
                                        break
            if idx >= len(players):
                break
        self.current_player_idx = idx
        self.update_interface()
        if self.conflicts:
            QMessageBox.warning(self, "Конфликты", "\n".join(self.conflicts))
            self.conflicts = []

    def save_results(self):
        """Сохранение результатов в таблицы Choice, Game_list и Result."""
        try:
            # Определяем систему для полуфинала
            system = System.get_or_none(
                (System.title_id == self.title_id) &
                (System.stage == "Квалификация. 1-й полуфинал")
            )
            if not system:
                system = System.create(
                    title_id=self.title_id,
                    stage="Квалификация. 1-й полуфинал",
                    total_group=len(self.sf_groups[0]),
                    max_player=4,
                    type_table="Круговая",
                    score_flag=5
                )

            # Очищаем старые записи для этого этапа
            Game_list.delete().where(
                (Game_list.title_id == self.title_id) &
                (Game_list.system_id == system.id)
            ).execute()
            Choice.update(
                semi_final=None,
                posev_sf=None,
                sf_group=None
            ).where(
                (Choice.title_id == self.title_id) &
                (Choice.system_id == system.id)
            ).execute()

            # Сохраняем данные по всем полуфиналам
            for sf_idx, groups in enumerate(self.sf_groups):
                sf_num = sf_idx + 1
                for g_idx, group in enumerate(groups):
                    gr_num = g_idx + 1
                    for pos, athlete in enumerate(group, start=1):
                        if athlete:
                            # Обновляем Choice
                            choice = Choice.get_or_none(
                                (Choice.title_id == self.title_id) &
                                (Choice.player_choice_id == athlete[0])
                            )
                            if choice:
                                choice.semi_final = sf_num
                                choice.posev_sf = pos
                                choice.sf_group = f"{gr_num} группа"
                                choice.save()

                            # Создаём запись в Game_list
                            Game_list.create(
                                number_group=f"{gr_num} группа",
                                rank_num_player=pos,
                                player_group=athlete[0],
                                system_id=system.id,
                                title_id=self.title_id,
                                player_double_id=None,
                                team_id=None,
                                sex="man"
                            )

            # Создаём записи в Result (сыгранные матчи внутри каждой группы полуфинала)
            # Для каждой группы полуфинала создаём матчи между всеми игроками (круговая система)
            for sf_idx, groups in enumerate(self.sf_groups):
                sf_num = sf_idx + 1
                for g_idx, group in enumerate(groups):
                    players_in_group = [p for p in group if p is not None]
                    if len(players_in_group) < 2:
                        continue
                    # Все пары
                    for i in range(len(players_in_group)):
                        for j in range(i + 1, len(players_in_group)):
                            player1 = players_in_group[i]
                            player2 = players_in_group[j]
                            # Проверяем, нет ли уже такого матча в Result
                            existing = Result.get_or_none(
                                (Result.title_id == self.title_id) &
                                (Result.player1_id == player1[0]) &
                                (Result.player2_id == player2[0]) &
                                (Result.system_id == system.id)
                            )
                            if not existing:
                                Result.create(
                                    title_id=self.title_id,
                                    system_id=system.id,
                                    player1_id=player1[0],
                                    player2_id=player2[0],
                                    player1_score=0,
                                    player2_score=0,
                                    winner_id=None,
                                    status="pending"
                                )

            # Устанавливаем флаг выбора
            self.set_choice_flag_for_stage("Квалификация. 1-й полуфинал", flag=1)

            QMessageBox.information(self, "Успех",
                f"Результаты сохранены!\n"
                f"Создано {Game_list.select().where(Game_list.system_id == system.id).count()} записей в Game_list.\n"
                f"Создано {Result.select().where(Result.system_id == system.id).count()} матчей в Result.")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка сохранения: {str(e)}")

    def set_choice_flag_for_stage(self, stage, flag):
        """Установить флаг выбора для этапа."""
        try:
            system = System.get(
                (System.title_id == self.title_id) &
                (System.stage == stage)
            )
            system.choice_flag = flag
            system.save()
        except Exception as e:
            print(f"Ошибка установки флага: {e}")
# ========== ФУНКЦИИ ВЫЗОВА ==========
def choice_semifinal_manual(self, parent=None):
    """
    Запускает ручную жеребьёвку полуфиналов.
    Собирает данные из квалификационных групп и открывает диалог.
    """
    try:
        # Получаем систему квалификации
        system = System.get(
            (System.title_id == self.current_title_id) &
            (System.stage == "Квалификация")
        )
        # Собираем данные по группам
        groups_data = []
        for gr_num in range(1, system.total_group + 1):
            choices = Choice.select().where(
                (Choice.title_id == self.current_title_id) &
                (Choice.group == f"{gr_num} группа ")
            ).order_by(Choice.posev_group)
            athletes_in_group = []
            for ch in choices:
                player = Player.get_or_none(Player.id == ch.player_choice_id)
                if player:
                    athletes_in_group.append([player.id, player.fio, player.rank, player.region, player.coach_id])
            groups_data.append((gr_num, athletes_in_group))

        # Получаем всех спортсменов турнира (для справки)
        all_athletes = []
        for player in Player.select().where(Player.title_id == self.current_title_id):
            all_athletes.append([player.id, player.fio, player.rank, player.region, player.coach_id])

        dialog = SemiFinalManual(all_athletes, groups_data, self.current_title_id, parent)
        return dialog.exec_() == QDialog.Accepted
    except Exception as e:
        QMessageBox.warning(parent, "Ошибка", f"Ошибка подготовки данных: {str(e)}")
        return False

def choice_semifinal(self, title_id, parent=None):
    """
    Главная функция выбора типа жеребьёвки полуфиналов.
    Предлагает автоматическую или ручную.
    """
    # Проверяем, есть ли квалификация
    try:
        system = System.get(
            (System.title_id == title_id) &
            (System.stage == "Квалификация")
        )
    except:
        QMessageBox.warning(parent, "Ошибка", "Сначала проведите жеребьёвку квалификационных групп!")
        return False

    # Проверяем, есть ли игроки в группах
    if not Choice.select().where(Choice.title_id == title_id).exists():
        QMessageBox.warning(parent, "Ошибка", "Нет данных о распределении игроков по группам квалификации!")
        return False

    # Диалог выбора
    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout

    class ChoiceDialog(QDialog):
        def __init__(self):
            super().__init__(parent)
            self.setWindowTitle("Жеребьёвка полуфиналов")
            self.setModal(True)
            self.setFixedSize(400, 200)
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Выберите способ жеребьёвки полуфиналов:"))
            btn_layout = QHBoxLayout()
            btn_auto = QPushButton("Автоматическая")
            btn_auto.clicked.connect(lambda: self.done(1))
            btn_manual = QPushButton("Ручная")
            btn_manual.clicked.connect(lambda: self.done(2))
            btn_cancel = QPushButton("Отмена")
            btn_cancel.clicked.connect(lambda: self.done(0))
            btn_layout.addWidget(btn_auto)
            btn_layout.addWidget(btn_manual)
            btn_layout.addWidget(btn_cancel)
            layout.addLayout(btn_layout)

    choice_dlg = ChoiceDialog()
    result = choice_dlg.exec_()

    if result == 1:  # Автоматическая
        # Вызываем существующую функцию автоматической жеребьёвки (create_semi_final_1)
        return self.create_semi_final_1(1, system.total_group) is not None
    elif result == 2:  # Ручная
        return choice_semifinal_manual(self, title_id, parent)
    else:
        return False    

class PlayerItem(QListWidgetItem):
    """Элемент списка игроков с дополнительными данными"""
    def __init__(self, player_data):
        super().__init__()
        self.player_data = player_data
        self.setText(f"{player_data['name']} ({player_data['city']})")

#===========Ручная жеребьевка сетки
# class ManualNetDrawDialog(QDialog):
#     def __init__(self, parent=None, title_id=None, stage_name=None, sex=None):
#         super().__init__(parent)
#         self.parent = parent
#         self.title_id = title_id
#         self.stage_name = stage_name
#         self.sex = sex
#         self.current_system = None
#         self.current_player = None  # текущий игрок, который будет сеяться

#         self.players = []
#         self.net_positions = {}
#         self.max_players = 0
#         self.setWindowTitle(f"Ручная жеребьевка - {stage_name}")
#         self.setMinimumSize(1000, 850)
#         self.setModal(True)
#         self.init_ui()
#         self.load_stage_data()
# #====================
#     def init_ui(self):
#         main_layout = QVBoxLayout(self)

#         # Верхняя панель с информацией
#         top_panel = QHBoxLayout()
#         top_panel.addWidget(QLabel(f"Этап: {self.stage_name}"))
#         top_panel.addStretch()

#         # Статусная строка
#         self.status_label = QLabel("Загрузка данных...")
#         self.status_label.setStyleSheet("padding: 5px; background-color: #FFFFE0; border-top: 1px solid #ddd;font-size: 12px;")
#         top_panel.addWidget(self.status_label)
        

#         self.save_btn = QPushButton("💾 Сохранить жеребьевку")
#         self.save_btn.setEnabled(False)
#         self.save_btn.clicked.connect(self.save_drawing)
#         top_panel.addWidget(self.save_btn)
#         main_layout.addLayout(top_panel)

#         # Основной сплиттер (горизонтальный)
#         splitter = QSplitter(Qt.Horizontal)

#         # Левая панель
#         left_widget = QWidget()
#         left_layout = QVBoxLayout(left_widget)
#         left_layout.setContentsMargins(0, 0, 0, 0)

#         # Информация об игроке
#         info_group = QGroupBox("Текущий игрок")
#         info_group.setStyleSheet("""
#             QGroupBox {
#                 font-weight: bold;
#                 font-size: 12px;
#                 border: 2px solid #4CAF50;
#                 border-radius: 8px;
#                 margin-top: 10px;
#             }
#             QGroupBox::title {
#                 color: #4CAF50;
#                 subcontrol-origin: margin;
#                 left: 10px;
#                 padding: 0 8px 0 8px;
#             }
#         """)
#         info_layout = QFormLayout(info_group)
#         self.player_info = {
#             'name': QLabel("-"),
#             'city': QLabel("-"),
#             'region': QLabel("-"),
#             'coach': QLabel("-")
#         }
#         info_layout.addRow("ФИО:", self.player_info['name'])
#         info_layout.addRow("Город:", self.player_info['city'])
#         info_layout.addRow("Регион:", self.player_info['region'])
#         info_layout.addRow("Тренер:", self.player_info['coach'])
#         left_layout.addWidget(info_group)

#         # Список оставшихся игроков (растягивается)
#         list_group = QGroupBox("📝 Список игроков")
#         list_group.setStyleSheet("""
#             QGroupBox {
#                 font-weight: bold;
#                 font-size: 12px;
#                 border: 2px solid #2196F3;
#                 border-radius: 8px;
#                 margin-top: 10px;
#             }
#             QGroupBox::title {
#                 color: #2196F3;
#                 subcontrol-origin: margin;
#                 left: 10px;
#                 padding: 0 8px 0 8px;
#             }
#         """)
#         list_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         list_layout = QVBoxLayout(list_group)
#         list_layout.setContentsMargins(10, 15, 10, 10)
#         self.players_list = QListWidget()
#         list_layout.addWidget(self.players_list)
#         left_layout.addWidget(list_group)

#         splitter.addWidget(left_widget)

#         # Правая панель: сетка
#         right_widget = QWidget()
#         right_layout = QVBoxLayout(right_widget)
#         right_layout.setContentsMargins(0, 0, 0, 0)

#         self.net_table = QTableWidget()
#         self.net_table.setEditTriggers(QTableWidget.NoEditTriggers)
#         self.net_table.setSelectionBehavior(QTableWidget.SelectItems)
#         self.net_table.setAcceptDrops(True)
#         self.net_table.cellClicked.connect(self.on_net_cell_clicked)
#         self.net_table.setDragDropMode(QTableWidget.DropOnly)
#         self.net_table.setStyleSheet("""
#             QTableWidget {
#                 font-size: 11px;
#                 gridline-color: #ddd;
#             }
#             QTableWidget::item {
#                 padding: 4px;
#             }
#             QTableWidget::item:selected {
#                 background-color: #4CAF50;
#                 color: white;
#             }
#         """)
#         # Растягиваем сетку
#         self.net_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         right_layout.addWidget(self.net_table)

#         splitter.addWidget(right_widget)

#         # Устанавливаем пропорции (левая - 30%, правая - 70%)
#         splitter.setSizes([500, 500])

#         main_layout.addWidget(splitter)

      

#     def load_stage_data(self):
#         if not self.stage_name:
#             return
#         self.current_system = System.get_or_none(
#             (System.title_id == self.title_id) &
#             (System.stage == self.stage_name) &
#             (System.sex == self.sex)
#         )
#         if not self.current_system:
#             QMessageBox.warning(self, "Ошибка", f"Этап {self.stage_name} не найден")
#             self.close()
#             return
#         self.max_players = self.current_system.max_player
#         # Проверяем, есть ли уже жеребьёвка
#         existing = Game_list.select().where(
#             (Game_list.title_id == self.title_id) &
#             (Game_list.system_id == self.current_system.id)
#         ).count()
#         if existing > 0:
#             self._handle_existing_drawing()
#         else:
#             self.draw_net()
#             self.load_players()
#             self.save_btn.setEnabled(True)
#             self.status_label.setText(f"Загружен этап: {self.stage_name}. Игроков: {len(self.players) + 1}")

#     def _handle_existing_drawing(self):
#         reply = QMessageBox.question(
#             self,
#             "Жеребьёвка уже проведена",
#             "Для этого этапа уже есть жеребьёвка.\n"
#             "Загрузить существующую или сбросить и начать заново?",
#             QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
#             QMessageBox.Cancel
#         )
#         if reply == QMessageBox.Cancel:
#             self.close()
#             return
#         elif reply == QMessageBox.Yes:
#             # Загружаем существующую
#             self.load_players()
#             self.draw_net()
#             self.load_existing_net()
#             self.save_btn.setEnabled(True)
#             self.status_label.setText(f"Загружена существующая жеребьёвка для {self.stage_name}")
#         else:
#             # Сброс: удаляем старые записи
#             Game_list.delete().where(
#                 (Game_list.title_id == self.title_id) &
#                 (Game_list.system_id == self.current_system.id)
#             ).execute()
#             Choice.update(posev_final=0).where(
#                 (Choice.title_id == self.title_id) &
#                 (Choice.final == self.stage_name)
#             ).execute()
#             self.load_players()
#             self.draw_net()
#             self.save_btn.setEnabled(True)
#             self.status_label.setText(f"Старая жеребьёвка сброшена для {self.stage_name}")

#     def draw_net(self):
#         if not self.current_system:
#             return
#         max_pl = self.max_players
#         self.net_table.setRowCount(max_pl)
#         self.net_table.setColumnCount(2)
#         self.net_table.setHorizontalHeaderLabels(["№", "Игрок / Город"])
#         self.net_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
#         self.net_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
#         # Устанавливаем фиксированную высоту строк, чтобы поместилось 32 строки
#         if max_pl > 20:
#             self.net_table.verticalHeader().setDefaultSectionSize(18)
#         else:
#             self.net_table.verticalHeader().setDefaultSectionSize(24)

#         for pos in range(1, max_pl + 1):
#             # Номер посева
#             item = QTableWidgetItem(str(pos))
#             item.setTextAlignment(Qt.AlignCenter)
#             item.setFlags(item.flags() & ~Qt.ItemIsEditable)
#             self.net_table.setItem(pos - 1, 0, item)
#             # Ячейка для игрока
#             self.net_table.setItem(pos - 1, 1, QTableWidgetItem(""))

#         self.net_table.resizeColumnsToContents()
#         self.net_table.resizeRowsToContents()

#     def place_player(self, pos, player_data):
#         self.net_positions[pos] = {
#             'player_id': player_data['player_id'],
#             'name': player_data['name'],
#             'city': player_data['city'],
#             'choice_id': player_data['choice_id']
#         }

#         # Убираем игрока из списка
#         for i in range(self.players_list.count()):
#             item = self.players_list.item(i)
#             if item.player_data['player_id'] == player_data['player_id']:
#                 self.players_list.takeItem(i)
#                 break
#         self.update_net_display()
#         self.status_label.setText(f"Игрок {player_data['name']} размещён на позиции {pos}")
#         # Проверяем, все ли заполнены
#         if len(self.net_positions) == self.max_players:
#             self.status_label.setText(f"✅ Все {self.max_players} позиций заполнены!")
#             self.save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

#     def highlight_conflicts(self, selected_player=None):
#         """Подсвечивает игроков из того же региона или тренера, что и выбранный"""
#         # Сбрасываем подсветку
#         for row in range(self.net_table.rowCount()):
#             item = self.net_table.item(row, 1)
#             if item:
#                 item.setBackground(Qt.white)

#         if not selected_player:
#             return

#         region = selected_player.get('region', '')
#         coach = selected_player.get('coach', '')

#         # Получаем список размещённых игроков с регионами и тренерами
#         for pos, data in self.net_positions.items():
#             # Получаем полные данные игрока
#             player = Player.get_or_none(Player.id == data['player_id'])
#             if not player:
#                 continue
#             p_region = player.region or ''
#             p_coach = ''
#             if player.coach_id:
#                 coach_obj = Coach.get_or_none(Coach.id == player.coach_id)
#                 if coach_obj:
#                     p_coach = coach_obj.coach or ''

#             if region and p_region == region:
#                 row = pos - 1
#                 item = self.net_table.item(row, 1)
#                 if item:
#                     item.setBackground(QColor(244, 164, 96))
#             if coach and p_coach == coach:
#                 row = pos - 1
#                 item = self.net_table.item(row, 1)
#                 if item:
#                     item.setBackground(QColor(240, 128, 128))

#     def save_drawing(self):
#         """Сохранение жеребьёвки в БД"""
#         if len(self.net_positions) != self.max_players:
#             QMessageBox.warning(self, "Ошибка", f"Не все позиции заполнены. Осталось {self.max_players - len(self.net_positions)}")
#             return

#         reply = QMessageBox.question(
#             self,
#             "Подтверждение",
#             f"Сохранить жеребьёвку для {self.current_stage}?",
#             QMessageBox.Yes | QMessageBox.No
#         )
#         if reply != QMessageBox.Yes:
#             return

#         try:
#             # Удаляем старые записи в Game_list для этого этапа
#             Game_list.delete().where(
#                 (Game_list.title_id == self.title_id) &
#                 (Game_list.system_id == self.current_system.id)
#             ).execute()

#             # Сохраняем новые
#             for pos, data in self.net_positions.items():
#                 Game_list.create(
#                     number_group=self.stage_name,
#                     rank_num_player=pos,
#                     player_group_id=data['player_id'],
#                     system_id=self.current_system.id,
#                     title_id=self.title_id,
#                     sex=self.sex if self.sex else "man"
#                 )

#             # Обновляем Choice (posev_final)
#             Choice.update(posev_final=0).where(
#                 (Choice.title_id == self.title_id) &
#                 (Choice.sex == self.current_sex) &
#                 (Choice.final == self.stage_name)
#             ).execute()

#             for pos, data in self.net_positions.items():
#                 Choice.update(posev_final=pos).where(
#                     (Choice.title_id == self.title_id) &
#                     (Choice.sex == self.current_sex) &
#                     (Choice.player_choice == data['player_id'])
#                 ).execute()

#             # Устанавливаем флаг choice_flag для системы
#             System.update(choice_flag=1).where(System.id == self.current_system.id).execute()

#             QMessageBox.information(self, "Успех", f"Жеребьёвка для {self.current_stage} сохранена")
#             self.accept()

#         except Exception as e:
#             QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить жеребьёвку: {str(e)}")  

#     def load_players(self):
#         """Загрузка игроков для текущего финала с использованием real_place_for_final"""

#         if not self.current_system:
#             return

#         self.players.clear()
#         try:
#             self.players_list.clear()
#         except RuntimeError:
#             self.players_list = QListWidget()

#         # Получаем информацию о том, какие места выходят в этот финал
#         choice = Choice.get_or_none(
#             (Choice.title_id == self.title_id) &
#             (Choice.sex == self.sex)
#             )   
#         stage_exit = self.current_system.stage_exit

#         try:
#             final_info = self.parent.real_place_for_final(self.stage_name)
#             nums = final_info['place_stage']
#         except AttributeError:
#             QMessageBox.warning(self, "Ошибка", "Метод real_place_for_final не найден в родительском окне")
#             return

#         stage_sources = final_info['stage_exit']
#         if not stage_sources:
#             QMessageBox.warning(self, "Ошибка", f"Не указан источник для финала {self.stage_name}")
#             return

#         # Обрабатываем все источники (если их несколько)
#         players_data = []

#         # Определяем поля в зависимости от источника
#         if "полуфинал" in stage_exit.lower():
#             semi_num = 1 if "1-й" in stage_exit else 2
#             choices = Choice.select().where(
#                 (Choice.title_id == self.title_id) &
#                 (Choice.semi_final == semi_num)
#             )
#             group_field = 'sf_group'
#             pos_field = 'posev_sf'
#             place_field = 'mesto_semi_final'
#         else:
#             choices = Choice.select().where(
#                 (Choice.title_id == self.title_id) &
#                 (Choice.group.contains("группа"))
#             )
#             group_field = 'group'
#             pos_field = 'posev_group'
#             place_field = 'mesto_group'

#             # Фильтруем по полу
#             if self.sex:
#                 choices = choices.where(Choice.sex == self.sex)

#             # Собираем данные
#             for ch in choices:
#                 place = getattr(ch, place_field) or 0
#                 if place not in nums:
#                     continue
#                 player = Player.get_or_none(Player.id == ch.player_choice.id)
#                 if not player:
#                     continue
#                 group_name = getattr(ch, group_field)
#                 match = re.search(r'\d+', group_name)
#                 group_num = int(match.group()) if match else 0
#                 pos = getattr(ch, pos_field)

#                 coach_name = ""
#                 if player.coach_id:
#                     coach = Coach.get_or_none(Coach.id == player.coach_id)
#                     if coach:
#                         coach_name = coach.coach

#                 players_data.append({
#                     'choice_id': ch.id,
#                     'player_id': player.id,
#                     'name': player.fio or player.player,
#                     'city': player.city or "",
#                     'region': player.region or "",
#                     'rank': player.rank or 0,
#                     'group': group_num,
#                     'position': pos,
#                     'place': place,
#                     'coach': coach_name,
#                     'sex': player.sex or ""
#                 })

#         # Сортировка
#         if self.stage_name == "1-й финал":
#             players_data.sort(key=lambda x: (x['group'], x['place']))
#         else:
#             exit_count = self.current_system.mesta_exit or 1
#             if exit_count == 1:
#                 players_data.sort(key=lambda x: x['rank'], reverse=True)
#             else:
#                 players_data.sort(key=lambda x: (x['place'], -x['rank']))

#         self.players = players_data

#         # == копирует список не изменный
#         import copy

#         self.players_copy = copy.deepcopy(players_data)

#         # Берём первого как текущего
#         if self.players:
#             current_pl = self.players[0]
#             idx = self.players_copy.index(current_pl)
#             self.current_player = self.players.pop(0)
#             self.update_player_info(current_pl)
#             seed_positions = self.get_seed_positions(idx + 1)
#             self.highlight_posev(seed_positions)
#             self.highlight_conflicts(current_pl)
#         else:
#             self.current_player = None
#             self.update_player_info(None)
 
#         # Заполняем список
#         self.players_list.clear()
#         for p in players_data:
#             item = PlayerItem(p)
#             self.players_list.addItem(item)
# #=======================
#     def place_current_player(self, pos):
#         """Размещает текущего игрока на указанной позиции"""
#         player_data = self.current_player # Игрок, который сеятся
#         if not player_data:
#             return False
#         self.place_player(pos, player_data)
#         self.current_player = self.players[0]
#         # Удаляем из списка и переходим к следующему
#         idx = self.players.index(self.current_player)
#         index = self.players_copy.index(self.current_player)
#         self.players.pop(idx)
#         # обновляем отображение списка
#         self.update_players_list()  
#         self.update_player_info(self.current_player)

#         seed_positions = self.get_seed_positions(index + 1)
#         self.highlight_posev(seed_positions)
#         self.highlight_conflicts(self.current_player)
#         return True

#     def update_players_list(self):
#         """Обновляет список оставшихся игроков"""
#         self.players_list.clear()
#         for p in self.players:
#             item = PlayerItem(p)
#             self.players_list.addItem(item)

#     def update_net_display(self):
#         if not hasattr(self, 'net_table') or self.net_table is None:
#             return
        
#         for pos, data in self.net_positions.items():
#             row = pos - 1
#             # Формируем текст: фамилия + перенос + город
#             text = f"{data['name']}/ {data['city']}"
#             item = QTableWidgetItem(text)
#             item.setTextAlignment(Qt.AlignLeft)
#             self.net_table.setItem(row, 1, item)

#     def closeEvent(self, event):
#         if self.net_positions:
#             reply = QMessageBox.question(
#                 self,
#                 "Сохранение жеребьёвки",
#                 "Вы хотите сохранить текущую жеребьёвку?",
#                 QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
#             )
#             if reply == QMessageBox.Cancel:
#                 event.ignore()
#                 return
#             elif reply == QMessageBox.Yes:
#                 self.save_drawing()
#                 event.accept()
#             else:
#                 # Не сохраняем, просто закрываем
#                 event.accept()
#         else:
#             event.accept()

#     def load_existing_net(self):
#         """Загрузка уже размещённых игроков из Game_list"""
#         if not self.current_system:
#             return

#         game_players = Game_list.select().where(
#             (Game_list.title_id == self.title_id) &
#             (Game_list.system_id == self.current_system.id)
#         ).order_by(Game_list.rank_num_player)

#         self.net_positions = {}
#         for gp in game_players:
#             pos = gp.rank_num_player
#             player = Player.get_or_none(Player.id == gp.player_group.id)
#             if player:
#                 self.net_positions[pos] = {
#                     'player_id': player.id,
#                     'name': player.fio or player.player,
#                     'city': player.city or ""
#                 }
#                 # Удаляем игрока из списка, если он там есть
#                 for i in range(self.players_list.count()):
#                     item = self.players_list.item(i)
#                     if item.player_data['player_id'] == player.id:
#                         self.players_list.takeItem(i)
#                         break

#         self.update_net_display()

#     def update_player_info(self, player_data):
#         """Обновляет информацию о текущем игроке"""
#         if not player_data:
#             self.player_info['name'].setText("-")
#             self.player_info['city'].setText("-")
#             self.player_info['region'].setText("-")
#             self.player_info['coach'].setText("-")
#             return
#         self.player_info['name'].setText(player_data.get('name', "-"))
#         self.player_info['city'].setText(player_data.get('city', "-"))
#         self.player_info['region'].setText(player_data.get('region', "-"))
#         self.player_info['coach'].setText(player_data.get('coach', "-"))

#     def on_list_item_clicked(self, item):
#         if not item:
#             return
#         player_data = item.player_data
#         self.update_player_info(player_data)
#         self.highlight_conflicts(player_data)  

#     def save_drawing(self):
#         """Сохранение жеребьёвки в БД"""
#         if len(self.net_positions) != self.max_players:
#             QMessageBox.warning(self, "Ошибка", f"Не все позиции заполнены. Осталось {self.max_players - len(self.net_positions)}")
#             return

#         reply = QMessageBox.question(
#             self,
#             "Подтверждение",
#             f"Сохранить жеребьёвку для {self.current_stage}?",
#             QMessageBox.Yes | QMessageBox.No
#         )
#         if reply != QMessageBox.Yes:
#             return

#         try:
#             # Удаляем старые записи в Game_list для этого этапа
#             Game_list.delete().where(
#                 (Game_list.title_id == self.title_id) &
#                 (Game_list.system_id == self.current_system.id)
#             ).execute()

#             # Сохраняем новые
#             for pos, data in self.net_positions.items():
#                 Game_list.create(
#                     number_group=self.current_stage,
#                     rank_num_player=pos,
#                     player_group_id=data['player_id'],
#                     system_id=self.current_system.id,
#                     title_id=self.title_id,
#                     sex=self.sex if self.sex else "man"
#                 )

#             # Обновляем Choice (posev_final)
#             Choice.update(posev_final=0).where(
#                 (Choice.title_id == self.title_id) &
#                 (Choice.final == self.current_stage)
#             ).execute()

#             for pos, data in self.net_positions.items():
#                 Choice.update(posev_final=pos).where(
#                     (Choice.title_id == self.title_id) &
#                     (Choice.player_choice == data['player_id'])
#                 ).execute()

#             # Устанавливаем флаг choice_flag для системы
#             System.update(choice_flag=1).where(System.id == self.current_system.id).execute()

#             QMessageBox.information(self, "Успех", f"Жеребьёвка для {self.current_stage} сохранена")
#             self.accept()

#         except Exception as e:
#             QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить жеребьёвку: {str(e)}")

#     def get_seed_positions(self, player_index):
#         """
#         Возвращает список рекомендуемых позиций для игрока с номером player_index (начиная с 1).
#         """
#         if not hasattr(self.parent, 'setka_choice_number'):
#             return []
#         try:
#             count_exit = self.current_system.mesta_exit or 1
#             posev_structure = self.parent.setka_choice_number(self.stage_name, count_exit)
#             # posev_structure[0] - общее количество игроков
#             # posev_structure[1:] - списки групп для каждого уровня посева
#             # Игроки с индексом 1,2 относятся к 1-й группе посева, 3-4 ко 2-й, 5-8 к 3-й, 9-16 к 4-й, 17-32 к 5-й
#             # Но в структуре группы могут быть разного размера, поэтому нужно распределять игроков по группам
#             # Для простоты определим, к какой группе относится player_index
#             total_players = posev_structure[0]
#             if player_index > total_players:
#                 return []
#             # Собираем все группы в плоский список с указанием диапазона индексов игроков
#             groups = []
#             start_idx = 1
#             for level in posev_structure[1:]:
#                 for group in level:
#                     # group - список позиций (например, [1, 8])
#                     # Количество игроков в этой группе = len(group)
#                     end_idx = start_idx + len(group) - 1
#                     groups.append({
#                         'start': start_idx,
#                         'end': end_idx,
#                         'positions': group
#                     })
#                     start_idx = end_idx + 1
#             # Находим группу, в которую попадает player_index
#             for g in groups:
#                 if g['start'] <= player_index <= g['end']:
#                     return g['positions']
#             return []
#         except Exception as e:
#             print(f"Ошибка получения позиций посева: {e}")
#             return []

#     def highlight_posev(self, seed_positions):
#         """Подсвечивает номера посева"""
#         # Сбрасываем подсветку
#         for row in range(self.net_table.rowCount()):
#             item = self.net_table.item(row, 1)
#             if item:
#                 item.setBackground(Qt.white) 
#         for pos in seed_positions:
#             row = pos - 1
#             item = self.net_table.item(row, 0)
#             if item:
#                 item.setBackground(QColor(0, 255, 255))

#     def on_net_cell_clicked(self, row, col):
#         if not self.current_player:
#             QMessageBox.warning(self, "Ошибка", "Нет игроков для жеребьёвки")
#             return
#         pos = row + 1
#         if pos < 1 or pos > self.max_players:
#             return
#         self.place_current_player(pos)

# ========== new ==========
# import copy
# import re
# from PyQt5.QtWidgets import (
#     QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
#     QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
#     QSplitter, QMessageBox, QWidget, QListWidget, QListWidgetItem,
#     QAbstractItemView, QFormLayout
# )
# from PyQt5.QtCore import Qt, QSize
# from PyQt5.QtGui import QColor
# from models import System, Game_list, Choice, Player, Coach

class PlayerItem(QListWidgetItem):
    def __init__(self, player_data):
        super().__init__()
        self.player_data = player_data
        self.setText(f"{player_data['name']} ({player_data['city']})")


class ManualNetDrawDialog(QDialog):
    def __init__(self, parent=None, title_id=None, stage_name=None, sex=None):
        super().__init__(parent)
        self.parent = parent
        self.title_id = title_id
        self.stage_name = stage_name
        self.sex = sex
        self.current_system = None
        self.current_player = None
        self.players = []
        self.players_copy = []
        self.net_positions = {}
        self.max_players = 0
        self.all_players = []  # полный список для подсветки посева
        self.setWindowTitle(f"Ручная жеребьевка - {stage_name}")
        self.setMinimumSize(1000, 850)
        self.setModal(True)
        self.init_ui()
        self.load_stage_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Верхняя панель
        top_panel = QHBoxLayout()
        top_panel.addWidget(QLabel(f"Этап: {self.stage_name}"))
        top_panel.addStretch()
        self.status_label = QLabel("Загрузка данных...")
        self.status_label.setStyleSheet("padding: 5px; background-color: #FFFFE0; border-top: 1px solid #ddd; font-size: 12px;")
        top_panel.addWidget(self.status_label)
        self.save_btn = QPushButton("💾 Сохранить жеребьевку")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_drawing)
        top_panel.addWidget(self.save_btn)
        main_layout.addLayout(top_panel)

        # Основной сплиттер
        splitter = QSplitter(Qt.Horizontal)

        # Левая панель
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Информация об игроке
        info_group = QGroupBox("Текущий игрок")
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                color: #4CAF50;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }
        """)
        info_layout = QFormLayout(info_group)
        self.player_info = {
            'name': QLabel("-"),
            'city': QLabel("-"),
            'region': QLabel("-"),
            'coach': QLabel("-"),
            'group': QLabel("-"),
        }
        info_layout.addRow("ФИО:", self.player_info['name'])
        info_layout.addRow("Город:", self.player_info['city'])
        info_layout.addRow("Регион:", self.player_info['region'])
        info_layout.addRow("Тренер:", self.player_info['coach'])
        info_layout.addRow("Группа:", self.player_info['group'])
        left_layout.addWidget(info_group)

        # Список оставшихся игроков (растягивается)
        list_group = QGroupBox("📝 Список игроков")
        list_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #2196F3;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                color: #2196F3;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }
        """)
        list_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        list_layout = QVBoxLayout(list_group)
        list_layout.setContentsMargins(10, 15, 10, 10)
        self.players_list = QListWidget()
        self.players_list.itemClicked.connect(self.on_list_item_clicked)
        list_layout.addWidget(self.players_list)
        left_layout.addWidget(list_group)

        splitter.addWidget(left_widget)

        # Правая панель: сетка
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.net_table = QTableWidget()
        self.net_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.net_table.setSelectionBehavior(QTableWidget.SelectItems)
        self.net_table.setAcceptDrops(True)
        self.net_table.cellClicked.connect(self.on_net_cell_clicked)
        self.net_table.setDragDropMode(QTableWidget.DropOnly)
        self.net_table.setStyleSheet("""
            QTableWidget {
                font-size: 11px;
                gridline-color: #ddd;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)
        self.net_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout.addWidget(self.net_table)
        splitter.addWidget(right_widget)

        splitter.setSizes([500, 500])
        main_layout.addWidget(splitter)

    # ----------------------------------------------
    # Загрузка данных
    # ----------------------------------------------
    def load_stage_data(self):
        if not self.stage_name:
            return
        self.current_system = System.get_or_none(
            (System.title_id == self.title_id) &
            (System.stage == self.stage_name) &
            (System.sex == self.sex)
        )
        if not self.current_system:
            QMessageBox.warning(self, "Ошибка", f"Этап {self.stage_name} не найден")
            self.close()
            return
        self.max_players = self.current_system.max_player

        existing = Game_list.select().where(
            (Game_list.title_id == self.title_id) &
            (Game_list.system_id == self.current_system.id)
        ).count()
        if existing > 0:
            self._handle_existing_drawing()
        else:
            self.draw_net()
            self.load_players()
            self.save_btn.setEnabled(True)
            self.status_label.setText(f"Загружен этап: {self.stage_name}. Игроков: {len(self.players) + 1}")

    def _handle_existing_drawing(self):
        reply = QMessageBox.question(
            self,
            "Жеребьёвка уже проведена",
            "Для этого этапа уже есть жеребьёвка.\n"
            "Загрузить существующую или сбросить и начать заново?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Cancel
        )
        if reply == QMessageBox.Cancel:
            self.close()
            return
        elif reply == QMessageBox.Yes:
            self.draw_net()
            self.load_players()
            self.load_existing_net()
            self.save_btn.setEnabled(True)
            self.status_label.setText(f"Загружена существующая жеребьёвка для {self.stage_name}")
        else:
            # Сброс
            Game_list.delete().where(
                (Game_list.title_id == self.title_id) &
                (Game_list.system_id == self.current_system.id)
            ).execute()
            Choice.update(posev_final=0).where(
                (Choice.title_id == self.title_id) &
                (Choice.final == self.stage_name)
            ).execute()
            self.load_players()
            self.draw_net()
            self.save_btn.setEnabled(True)
            self.status_label.setText(f"Старая жеребьёвка сброшена для {self.stage_name}")
    # ----------------------------------------------
    # Загрузка игроков
    # ----------------------------------------------
    def load_players(self):
        """Загрузка игроков для текущего финала с использованием real_place_for_final"""
        if not self.current_system:
            return

        self.players.clear()
        try:
            self.players_list.clear()
        except RuntimeError:
            self.players_list = QListWidget()

        # Получаем информацию о том, какие места выходят в этот финал
        try:
            final_info = self.parent.real_place_for_final(self.stage_name)
            # final_info должно быть словарём {'stage_exit': ..., 'place_stage': [список мест]}
            if not final_info or 'place_stage' not in final_info:
                QMessageBox.warning(self, "Ошибка", "Некорректные данные от real_place_for_final")
                return
            nums = final_info['place_stage']
            stage_exit = final_info.get('stage_exit', '')
        except AttributeError:
            QMessageBox.warning(self, "Ошибка", "Метод real_place_for_final не найден в родительском окне")
            return

        if not nums:
            QMessageBox.warning(self, "Ошибка", f"Нет мест для финала {self.stage_name}")
            return

        # Определяем поля в зависимости от источника
        if "полуфинал" in stage_exit.lower():
            semi_num = 1 if "1-й" in stage_exit else 2
            choices = Choice.select().where(
                (Choice.title_id == self.title_id) &
                (Choice.semi_final == semi_num) &
                (Choice.sex == self.sex)
            )
            group_field = 'sf_group'
            pos_field = 'posev_sf'
            place_field = 'mesto_semi_final'
        else:
            choices = Choice.select().where(
                (Choice.title_id == self.title_id) &
                (Choice.group.contains("группа")) &
                (Choice.sex == self.sex)
            )
            group_field = 'group'
            pos_field = 'posev_group'
            place_field = 'mesto_group'

        # Собираем данные
        players_data = []
        for ch in choices:
            place = getattr(ch, place_field) or 0
            if place not in nums:
                continue
            player = Player.get_or_none(Player.id == ch.player_choice.id)
            if not player:
                continue
            group_name = getattr(ch, group_field)
            match = re.search(r'\d+', group_name)
            group_num = int(match.group()) if match else 0
            pos = getattr(ch, pos_field)

            coach_name = ""
            if player.coach_id:
                coach = Coach.get_or_none(Coach.id == player.coach_id)
                if coach:
                    coach_name = coach.coach

            players_data.append({
                'choice_id': ch.id,
                'player_id': player.id,
                'name': player.fio or player.player,
                'city': player.city or "",
                'region': player.region or "",
                'rank': player.rank or 0,
                'group': group_num,
                'position': pos,
                'place': place,
                'coach': coach_name,
                'sex': player.sex or ""
            })

        # Сортировка
        if self.stage_name == "1-й финал":
            players_data.sort(key=lambda x: (x['group'], x['place']))
        else:
            exit_count = self.current_system.mesta_exit or 1
            if exit_count == 1:
                players_data.sort(key=lambda x: x['rank'], reverse=True)
            else:
                players_data.sort(key=lambda x: (x['place'], -x['rank']))

        import copy

        self.all_players = copy.deepcopy(players_data)

        # Устанавливаем текущего игрока и список оставшихся
        if players_data:
            self.current_player = players_data[0]
            self.players = players_data[1:]  # остальные игроки
            self.update_player_info(self.current_player)
            self.update_players_list()
            self.highlight_posev()
            self.highlight_conflicts(self.current_player)         
        else:
            self.current_player = None
            self.players = []
            self.update_player_info(None)

    def update_players_list(self):
        """Обновляет список оставшихся игроков"""
        self.players_list.clear()
        for p in self.players:
            item = PlayerItem(p)
            self.players_list.addItem(item)
    # ----------------------------------------------
    # Отрисовка сетки
    # ----------------------------------------------
    def update_net_display(self):
        """Обновляет отображение сетки и подсветку"""
        if not hasattr(self, 'net_table') or self.net_table is None:
            return
        # Обновляем имена
        for pos, data in self.net_positions.items():
            row = pos - 1
            text = f"{data['name']} / {data['city']} - {data['group']} группа"
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignLeft)
            self.net_table.setItem(row, 1, item)
        # Подсветка
        self.highlight_conflicts(self.current_player)
        self.highlight_posev()

    def draw_net(self):
        if not self.current_system:
            return
        max_pl = self.max_players
        self.net_table.setRowCount(max_pl)
        self.net_table.setColumnCount(2)
        self.net_table.setHorizontalHeaderLabels(["№", "Игрок / Город"])
        self.net_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.net_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        # Высота строк
        if max_pl > 20:
            self.net_table.verticalHeader().setDefaultSectionSize(18)
        else:
            self.net_table.verticalHeader().setDefaultSectionSize(24)

        # Заполняем данными
        for pos in range(1, max_pl + 1):
            row = pos - 1
            item = QTableWidgetItem(str(pos))
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.net_table.setItem(row, 0, item)
            self.net_table.setItem(row, 1, QTableWidgetItem(""))

        # Устанавливаем делегат для отрисовки линий между четвертями
        quarter_size = max_pl // 4 if max_pl >= 8 else max_pl
        delegate = QuarterLineDelegate(self.net_table, quarter_size, max_pl)
        self.net_table.setItemDelegate(delegate)

        self.net_table.resizeColumnsToContents()
        self.net_table.resizeRowsToContents()
    # ----------------------------------------------
    # Размещение игрока
    # ----------------------------------------------
    def place_player(self, pos, player_data):
        """Размещает игрока на позиции (без удаления из списка)"""
        self.net_positions[pos] = {
            'player_id': player_data['player_id'],
            'name': player_data['name'],
            'city': player_data['city'],
            'group': player_data['group'],
            'choice_id': player_data['choice_id']
        }

    def place_current_player(self, pos):
        """Размещает текущего игрока на указанной позиции"""
        if not self.current_player:
            return False
        player_data = self.current_player
        self._place_player_on_position(pos, player_data)
        # Переходим к следующему игроку
        if self.players:
            self.current_player = self.players.pop(0)
            self.update_player_info(self.current_player)
            self.highlight_conflicts(self.current_player)
            self.get_seed_positions(pos)
            self.highlight_posev()
        else:
            self.current_player = None
            self.update_player_info(None)
        self.update_players_list()
        self.status_label.setText(f"Игрок {player_data['name']} размещён на позиции {pos}")
        return True
    # ----------------------------------------------
    # Обработчики событий
    # ----------------------------------------------
    def on_net_cell_clicked(self, row, col):
        if not self.current_player:
            QMessageBox.warning(self, "Ошибка", "Нет игроков для жеребьёвки")
            return
        pos = row + 1
        if pos < 1 or pos > self.max_players:
            return

        if pos in self.net_positions:
            # Позиция занята – меняем игроков
            old_player_data = self.net_positions[pos]
            # Удаляем старого с позиции
            del self.net_positions[pos]
            # Размещаем текущего на эту позицию
            self._place_player_on_position(pos, self.current_player)
            # Старый игрок становится текущим
            self.current_player = old_player_data
            # Обновляем список
            self.update_players_list()
            # Обновляем информацию и подсветку
            self.update_player_info(old_player_data)
            self.highlight_conflicts(old_player_data)
            self.status_label.setText(f"Замена: {old_player_data['name']} на позицию {pos}")
            return

        # Если позиция свободна
        self.place_current_player(pos)

    def on_list_item_clicked(self, item):
        if not item:
            return
        player_data = item.player_data
        # Делаем выбранного игрока текущим, а старого текущего возвращаем в список
        old_current = self.current_player
        if old_current:
            # Добавляем старого текущего в список (в начало)
            self.players.insert(0, old_current)
        self.current_player = player_data
        # Удаляем выбранного из списка
        for i, p in enumerate(self.players):
            if p['player_id'] == player_data['player_id']:
                self.players.pop(i)
                break
        self.update_player_info(self.current_player)
        self.update_players_list()
        self.update_net_display()
    # ----------------------------------------------
    # Подсветка
    # ----------------------------------------------
    def highlight_conflicts(self, selected_player=None):
        """Подсвечивает игроков из того же региона или тренера"""
        for row in range(self.net_table.rowCount()):
            item = self.net_table.item(row, 1)
            if item:
                item.setBackground(Qt.white)

        if not selected_player:
            return

        region = selected_player.get('region', '')
        coach = selected_player.get('coach', '')

        for pos, data in self.net_positions.items():
            player = Player.get_or_none(Player.id == data['player_id'])
            if not player:
                continue
            p_region = player.region or ''
            p_coach = ''
            if player.coach_id:
                coach_obj = Coach.get_or_none(Coach.id == player.coach_id)
                if coach_obj:
                    p_coach = coach_obj.coach or ''

            if region and p_region == region:
                row = pos - 1
                item = self.net_table.item(row, 1)
                if item:
                    item.setBackground(QColor(244, 164, 96))  # светло-оранжевый
            if coach and p_coach == coach:
                row = pos - 1
                item = self.net_table.item(row, 1)
                if item:
                    item.setBackground(QColor(240, 128, 128))  # светло-красный

    def highlight_posev(self):
        """Подсвечивает номера посева для текущего игрока"""
        # Сбрасываем подсветку в первом столбце
        for row in range(self.net_table.rowCount()):
            item = self.net_table.item(row, 0)
            if item:
                item.setBackground(Qt.white)

        if not self.current_player:
            return

        # Определяем номер текущего игрока в исходном списке (индекс + 1)
        # Для этого нужно знать полный список участников до сортировки
        # Мы сохраним его в self.all_players при загрузке
        if not hasattr(self, 'all_players'):
            return
        try:
            idx = self.all_players.index(self.current_player)
            player_index = idx + 1
            seed_positions = self.get_seed_positions(player_index)
            for pos in seed_positions:
                if pos not in self.net_positions:
                    row = pos - 1
                    item = self.net_table.item(row, 0)
                    if item:
                        item.setBackground(QColor(173, 216, 230))  # светло-голубой
        except ValueError:
            pass

    def get_seed_positions(self, player_index):
        if not hasattr(self.parent, 'setka_choice_number'):
            return []
        try:
            count_exit = self.current_system.mesta_exit or 1
            posev_structure = self.parent.setka_choice_number(self.stage_name, count_exit)
            if not posev_structure:
                return []
            total_players = posev_structure[0]
            if player_index > total_players:
                return []
            groups = []
            start_idx = 1
            for level in posev_structure[1:]:
                for group in level:
                    end_idx = start_idx + len(group) - 1
                    groups.append({
                        'start': start_idx,
                        'end': end_idx,
                        'positions': group
                    })
                    start_idx = end_idx + 1
            for g in groups:
                if g['start'] <= player_index <= g['end']:
                    return g['positions']
            return []
        except Exception as e:
            print(f"Ошибка получения позиций посева: {e}")
            return []
    # ----------------------------------------------
    # Информация об игроке
    # ----------------------------------------------
    def update_player_info(self, player_data):
        if not player_data:
            for key in self.player_info:
                self.player_info[key].setText("-")
            return
        self.player_info['name'].setText(player_data.get('name', "-"))
        self.player_info['city'].setText(player_data.get('city', "-"))
        self.player_info['region'].setText(player_data.get('region', "-"))
        self.player_info['coach'].setText(player_data.get('coach', "-"))
        self.player_info['group'].setText(str(player_data.get('group', "-")))
    # ----------------------------------------------
    # Загрузка существующей жеребьёвки
    # ----------------------------------------------
    def load_existing_net(self):
        if not self.current_system:
            return

        game_players = Game_list.select().where(
            (Game_list.title_id == self.title_id) &
            (Game_list.system_id == self.current_system.id)
        ).order_by(Game_list.rank_num_player)

        self.net_positions = {}
        for gp in game_players:
            pos = gp.rank_num_player
            player = Player.get_or_none(Player.id == gp.player_group.id)
            if player:
                self.net_positions[pos] = {
                    'player_id': player.id,
                    'name': player.fio or player.player,
                    'city': player.city or "",
                    'group': player.group
                }
                # Удаляем этого игрока из списка, если он там есть
                for i, p in enumerate(self.players):
                    if p['player_id'] == player.id:
                        self.players.pop(i)
                        break

        self.update_net_display()
    # ----------------------------------------------
    # Сохранение
    # ----------------------------------------------
    def save_drawing(self):
        if len(self.net_positions) != self.max_players:
            QMessageBox.warning(self, "Ошибка", f"Не все позиции заполнены. Осталось {self.max_players - len(self.net_positions)}")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Сохранить жеребьёвку для {self.stage_name}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            Game_list.delete().where(
                (Game_list.title_id == self.title_id) &
                (Game_list.system_id == self.current_system.id)
            ).execute()
            Result.delete().where(
                (Result.title_id == self.title_id) &
                (Result.system_id == self.current_system.id)
            ).execute()

            for pos, data in self.net_positions.items():
                Game_list.create(
                    number_group=self.stage_name,
                    rank_num_player=pos,
                    player_group_id=data['player_id'],
                    system_id=self.current_system.id,
                    title_id=self.title_id,
                    sex=self.sex if self.sex else "man"
                )

            Choice.update(posev_final=0, final="").where(
                (Choice.title_id == self.title_id) &
                (Choice.sex == self.sex) &
                (Choice.final == self.stage_name)
            ).execute()

            for pos, data in self.net_positions.items():
                Choice.update(posev_final=pos, final=self.stage_name).where(
                    (Choice.title_id == self.title_id) &
                    (Choice.sex == self.sex) & 
                    (Choice.player_choice == data['player_id'])
                ).execute()

            choices = Choice.select().where((Choice.title_id == self.title_id) &
                                            (Choice.final == self.stage_name) &
                                            (Choice.sex == self.sex)
                                            )
            
            posev_data = {} # окончательные посев номер в сетке - игрок/ город

            for i in self.net_positions.keys():
                id = self.net_positions[i]['player_id']
                if id == "X":
                    # Получаем ID игрока X
                    x_player_id = self.get_x_player_id()
                    posev_data[i] = {
                    'player_id':x_player_id,
                        'name_city':'X',
                        'name':'X'
                    }
                else:
                    # id = tmp_list[0]
                    pl_id = Player.get(Player.id == id)
                    family_city = pl_id.fio_city
                    family_shot = pl_id.fio
                    posev_data[i] = {
                    'player_id':id,
                        'name_city':family_city,
                        'name':family_shot
                    }
            # # 7. Создаём туры и матчи заполняем Results
            max_pl = self.max_players
            # число игр в сетке
            total_game = self.parent.number_game_of_net(self.stage_name)
            # =========== проба записи стадии ====
            # наивысшее место 
            highest_place = self.parent.get_final_start_place(self.stage_name)
            # определяет количество игр в сетке
            game = self.parent.number_game_of_net(self.stage_name)

            self.parent.get_match_title(i, game, highest_place, max_pl)
            # =======================
            # присваивает встречи 1-ого тура и записывает в тбл Results
            for i in range(1, max_pl // 2 + 1):   
                pl1 = posev_data[i * 2 - 1]['name_city']
                pl2 = posev_data[i * 2]['name_city']
                if pl1 is not None and pl2 is not None:
                    with db:
                        results = Result(number_group=self.stage_name, system_stage='финальный', player1=pl1, player2=pl2,
                                        tours=i, title_id=self.title_id,
                                        system_id=self.current_system.id, sex=self.sex).save()
            # дополняет номера будущих встреч            
            for i in range(max_pl // 2 + 1, total_game + 1): 
                with db:
                    results = Result(number_group=self.stage_name, system_stage="Финальный", player1="", player2="",
                                    tours=i, title_id=self.title_id,
                                    system_id=self.current_system.id, sex=self.sex).save()

            # записывает стадии сетки в Result
            stadia = self.parent.whrite_stadia_on_net(game, highest_place, max_pl)

            results_stadia = Result.select().where(
                (Result.title_id == self.title_id) &
                (Result.system_id == self.current_system.id))

            for k in results_stadia:
                num_game = int(k.tours)
                stadia_str = stadia[num_game]
                Result.update(stage_net=stadia_str).where(Result.id == k).execute()

            System.update(choice_flag=1).where(System.id == self.current_system.id).execute()

            QMessageBox.information(self, "Успех", f"Жеребьёвка для {self.stage_name} сохранена")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить жеребьёвку: {str(e)}")
    # ----------------------------------------------
    # Закрытие окна
    # ----------------------------------------------
    def closeEvent(self, event):
        if self.net_positions:
            reply = QMessageBox.question(
                self,
                "Сохранение жеребьёвки",
                "Вы хотите сохранить текущую жеребьёвку?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Cancel:
                event.ignore()
                return
            elif reply == QMessageBox.Yes:
                self.save_drawing()
                event.accept()
            else:
                event.accept()
        else:
            event.accept()
    # ----------------------------------------------
    # свободные номера в сетке
    # ----------------------------------------------
    def free_place_in_setka(self):
        """находит свободные места в сетке"""
        free_num = []
        for row in range(0, self.max_players):
            item = self.net_table.item(row, 1).text()
            if item == "":
                value = self.net_table.item(row, 0).text()
                free_num.append(int(value))

        # Получаем ID игрока X
        x_player_id = self.parent.get_x_player_id()

        # Создаем данные для игрока X
        x_player_data = {
            'player_id': x_player_id,  # id
            'name': "X",          # name
            'region': "",           # region
            'group_number': 0,            # group_number
            'group': "",           # group
            'city': "",           # city
            'rank': 0,            # rank
            'place': 0             # place
        }

        # Заполняем свободные места данными игрока X
        for pos in free_num:
            self.net_positions[pos] = x_player_data

    def fill_empty_positions_with_x(self):
            """Заполняет свободные позиции игроком X"""
            x_player_id = self.parent.get_x_player_id() if hasattr(self.parent, 'get_x_player_id') else None
            if not x_player_id:
                QMessageBox.warning(self, "Ошибка", "Не удалось получить ID игрока X")
                return

            # Находим свободные позиции
            free_positions = [pos for pos in range(1, self.max_players + 1) if pos not in self.net_positions]
            for pos in free_positions:
                self.net_positions[pos] = {
                    'player_id': x_player_id,
                    'name': 'X',
                    'city': '',
                    'choice_id': None,
                    'group': ''
                }
            self.update_net_display()
# ======new =====
    def _place_player_on_position(self, pos, player_data):
        """Размещает игрока на позиции, удаляя его из списка оставшихся"""
        # Добавляем в сетку
        self.net_positions[pos] = {
            'player_id': player_data['player_id'],
            'name': player_data['name'],
            'city': player_data['city'],
            'choice_id': player_data['choice_id'],
            'group': player_data['group']
        }
        # Удаляем из списка оставшихся
        for i in range(self.players_list.count()):
            item = self.players_list.item(i)
            if item.player_data['player_id'] == player_data['player_id']:
                self.players_list.takeItem(i)
                break
        # Удаляем из self.players, если он там ещё есть
        self.players = [p for p in self.players if p['player_id'] != player_data['player_id']]
        self.update_net_display()

    def update_players_list(self):
        self.players_list.clear()
        for p in self.players:
            item = PlayerItem(p)
            self.players_list.addItem(item)







    # ----------------------------------------------
    # Цвета четвертей у сетки
    # ----------------------------------------------
class QuarterLineDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, quarter_size=0, max_players=0):
        super().__init__(parent)
        self.quarter_size = quarter_size
        self.max_players = max_players

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        if self.quarter_size == 0 or self.max_players == 0:
            return

        row = index.row()
        # Проверяем, является ли строка последней в четверти
        # и не последняя ли это четверть в таблице
        if (row + 1) % self.quarter_size == 0 and row + 1 < self.max_players:
            painter.save()
            pen = QPen(QColor(210, 180, 140), 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawLine(option.rect.left(), option.rect.bottom(),
                             option.rect.right(), option.rect.bottom())
            painter.restore()