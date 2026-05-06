import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from models import *
from models import db

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
        # self.current_group_for_seed = self.find_next_group_for_seed()
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
        
    def initUI(self):
        self.setWindowTitle('Ручная жеребьевка спортсменов')
        self.setGeometry(100, 100, 1600, 720)
        
        main_layout = QVBoxLayout(self)
        
        title_label = QLabel("Ручная жеребьевка спортсменов")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        content_layout = QHBoxLayout()
        
        # ========== ЛЕВАЯ ПАНЕЛЬ ==========
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.StyledPanel)
        left_panel.setMaximumWidth(400)
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
        
        for g in range(self.num_groups):
            group_frame = QFrame()
            group_frame.setFrameStyle(QFrame.Box)
            group_frame.setMinimumWidth(300)
            group_frame.setMaximumWidth(400)
            group_layout = QVBoxLayout(group_frame)
            group_layout.setSpacing(5)
            
            header = QLabel(f"Группа {g+1}")
            header.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white; padding: 5px;")
            header.setAlignment(Qt.AlignCenter)
            group_layout.addWidget(header)
            
            table = QTableWidget()
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["№", "Участник (регион) рейтинг"])
            
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
                table.setRowHeight(row, 25)
            
            group_layout.addWidget(table)
            
            table_height = table.horizontalHeader().height() + 2
            table_height += self.max_rows_per_group * 25
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


def load_existing_draw_from_db(self):
    """Загрузка существующей жеребьевки из базы данных через Peewee"""
    choices = Choice.select().where(Choice.title_id == self)
    try:
        results = choices.select().order_by(Choice.group, Choice.posev_group)
        return list(results) if results.exists() else None
    except Exception as e:
        print(f"Ошибка при загрузке из базы данных: {e}")
        return None


def clear_db_before_choice(self):
    """очищает базу данных -Game_list- и -Result- перед повторной жеребьевкой групп"""

    systems = System.select().where((System.stage == "Предварительный") & (System.title_id == self)).get()
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


def choice_group_manual(athletes, num_groups, id_title, parent=None):
    """
    Функция для вызова ручной жеребьевки
    
    Args:
        athletes: список списков [id игрока, фамилия_имя, рейтинг, регион, тренер]
        num_groups: количество групп (от 2 до 32)
        parent: родительское окно
    
    Returns:
        list: список результатов или None если отмена
    """
    if num_groups < 2 or num_groups > 32:
        raise ValueError("Количество групп должно быть от 2 до 32")
    system = System.select().where((System.title_id == id_title) & (System.stage == "Предварительный")).get()  # находит system id последнего
    check_flag = system.choice_flag
    if check_flag is True:
        # Проверяем, есть ли уже жеребьевка в базе данных
        existing_data = load_existing_draw_from_db(id_title)
    
    if existing_data:
        # Создаем диалог выбора действия
        action_dialog = ChoiceActionDialog(parent)
        result = action_dialog.exec_()
        
        if result == 1:  # Сбросить
            # Очищаем таблицу в БД
            clear_db_before_choice(id_title)
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
    
    dialog = ChoiceGroupManual(athletes, num_groups, id_title, parent, existing_data)
    result_code = dialog.exec_()
    
    if result_code == QDialog.Accepted:
        return dialog.get_results()
    else:
        return None
