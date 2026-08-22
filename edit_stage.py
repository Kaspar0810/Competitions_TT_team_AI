import sys
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QGroupBox, QSplitter, QMessageBox, QWidget, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QAbstractItemView, QMenu,
    QAction, QFileDialog, QProgressDialog, QSpinBox, QLineEdit,
    QFrame, QGridLayout, QFormLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QBrush, QFont, QDrag
from models import *
import datetime


class EditStagesDialog(QDialog):
    """
    Диалог для редактирования этапов:
    1. Добавление нового игрока в группу на выбранную позицию
    2. Перемещение игроков между группами в квалификации
    3. Перемещение игроков в полуфиналах (с учетом сыгранных матчей)
    4. Перемещение игроков в финалах
    """
    
    def __init__(self, parent=None, title_id=None, sex=None):
        super().__init__(parent)
        self.parent = parent
        self.title_id = title_id
        self.current_title = None
        self.current_stage = None
        self.current_sex = sex
        self.current_system = None
        self.drag_data = None
        
        self.setWindowTitle("Редактирование этапов")
        self.setMinimumSize(1200, 700)
        self.setModal(True)
        
        self.init_ui()
        self.load_title_info()
        self.load_stages()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Верхняя панель с информацией и выбором этапа
        top_panel = QHBoxLayout()
        
        # Информация о соревновании
        self.title_info_label = QLabel("Соревнование: не выбрано")
        self.title_info_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        top_panel.addWidget(self.title_info_label)
        
        top_panel.addStretch()
        
        # Выбор этапа
        top_panel.addWidget(QLabel("Этап:"))
        self.stage_combo = QComboBox()
        self.stage_combo.setMinimumWidth(250)
        self.stage_combo.currentTextChanged.connect(self.on_stage_changed)
        top_panel.addWidget(self.stage_combo)
        
        # Кнопка обновления
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(self.refresh_data)
        top_panel.addWidget(refresh_btn)
        
        main_layout.addLayout(top_panel)
        
        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #ccc; max-height: 1px; margin: 5px 0;")
        main_layout.addWidget(line)
        
        # Основная часть - вкладки
        self.tab_widget = QTabWidget()
        
        # Вкладка 1: Редактирование групп
        self.group_tab = self.create_group_edit_tab()
        self.tab_widget.addTab(self.group_tab, "📊 Группы")
        
        # Вкладка 2: Перемещение игроков
        self.move_tab = self.create_move_players_tab()
        self.tab_widget.addTab(self.move_tab, "🔄 Перемещение")
        
        # Вкладка 3: Добавление игрока
        self.add_tab = self.create_add_player_tab()
        self.tab_widget.addTab(self.add_tab, "➕ Добавить игрока")
        
        main_layout.addWidget(self.tab_widget, 1)
        
        # Нижняя панель с кнопками
        bottom_panel = QHBoxLayout()
        bottom_panel.addStretch()
        
        apply_btn = QPushButton("✅ Применить изменения")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        apply_btn.clicked.connect(self.apply_changes)
        bottom_panel.addWidget(apply_btn)
        
        close_btn = QPushButton("❌ Закрыть")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #d32f2f; }
        """)
        close_btn.clicked.connect(self.accept)
        bottom_panel.addWidget(close_btn)
        
        main_layout.addLayout(bottom_panel)
        
    def create_group_edit_tab(self):
        """Вкладка для редактирования групп"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Информация о выбранной группе
        info_panel = QHBoxLayout()
        info_panel.addWidget(QLabel("Группа:"))
        self.group_combo = QComboBox()
        self.group_combo.currentTextChanged.connect(self.on_group_changed)
        info_panel.addWidget(self.group_combo)
        info_panel.addStretch()
        
        # Кнопки управления
        self.add_player_btn = QPushButton("➕ Добавить игрока")
        self.add_player_btn.clicked.connect(self.add_player_to_group)
        self.add_player_btn.setEnabled(False)
        info_panel.addWidget(self.add_player_btn)
        
        self.remove_player_btn = QPushButton("🗑️ Удалить игрока")
        self.remove_player_btn.clicked.connect(self.remove_player_from_group)
        self.remove_player_btn.setEnabled(False)
        info_panel.addWidget(self.remove_player_btn)
        
        layout.addLayout(info_panel)
        
        # Таблица игроков в группе
        self.group_table = QTableWidget()
        self.group_table.setColumnCount(5)
        self.group_table.setHorizontalHeaderLabels(["№", "Игрок", "Город", "Регион", "Рейтинг"])
        self.group_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.group_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.group_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.group_table.setSelectionMode(QTableWidget.SingleSelection)
        self.group_table.setDragEnabled(True)
        self.group_table.setAcceptDrops(True)
        self.group_table.setDropIndicatorShown(True)
        self.group_table.setDragDropMode(QTableWidget.InternalMove)
        self.group_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                font-size: 12px;
            }
            QTableWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QTableWidget::item {
                padding: 4px;
            }
        """)
        self.group_table.itemSelectionChanged.connect(self.on_group_table_selection_changed)
        layout.addWidget(self.group_table, 1)
        
        return tab
    
    def create_move_players_tab(self):
        """Вкладка для перемещения игроков"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Инструкция
        info_label = QLabel("Перетащите игрока из одной группы в другую или выберите игроков для обмена местами (Ctrl+клик для выбора двух)")
        info_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(info_label)
        
        # Основной сплиттер для двух списков
        splitter = QSplitter(Qt.Horizontal)
        
        # Левая панель - список групп
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_label = QLabel("📋 Группы")
        left_label.setStyleSheet("font-weight: bold; font-size: 12px; padding: 5px; background-color: #e3f2fd;")
        left_layout.addWidget(left_label)
        
        self.groups_tree = QTreeWidget()
        self.groups_tree.setHeaderLabel("Группы")
        self.groups_tree.setDragEnabled(True)
        self.groups_tree.setAcceptDrops(True)
        self.groups_tree.setDropIndicatorShown(True)
        self.groups_tree.setDragDropMode(QTreeWidget.InternalMove)
        self.groups_tree.setSelectionMode(QTreeWidget.ExtendedSelection)  # <-- ВАЖНО: множественный выбор
        self.groups_tree.setStyleSheet("""
            QTreeWidget {
                font-size: 12px;
                border: 1px solid #ddd;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)
        self.groups_tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
        left_layout.addWidget(self.groups_tree)
    #===================================    
        splitter.addWidget(left_panel)
        
        # Правая панель - информация и кнопки
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Информация о выбранном игроке
        info_group = QGroupBox("Информация об игроке")
        info_layout = QVBoxLayout(info_group)
        
        self.player_info_label = QLabel("Выберите игрока в дереве")
        self.player_info_label.setWordWrap(True)
        self.player_info_label.setStyleSheet("padding: 5px; background-color: #f5f5f5; border-radius: 3px;")
        info_layout.addWidget(self.player_info_label)
        
        right_layout.addWidget(info_group)
        
        # Кнопки действий
        actions_group = QGroupBox("Действия")
        actions_layout = QVBoxLayout(actions_group)
        
        self.swap_players_btn = QPushButton("🔄 Обменять игроков местами")
        self.swap_players_btn.clicked.connect(self.swap_players)
        self.swap_players_btn.setEnabled(False)
        actions_layout.addWidget(self.swap_players_btn)
        
        self.move_to_group_btn = QPushButton("📤 Переместить в другую группу")
        self.move_to_group_btn.clicked.connect(self.move_player_to_group)
        self.move_to_group_btn.setEnabled(False)
        actions_layout.addWidget(self.move_to_group_btn)
        
        self.move_up_btn = QPushButton("⬆ Переместить выше")
        self.move_up_btn.clicked.connect(self.move_player_up)
        self.move_up_btn.setEnabled(False)
        actions_layout.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("⬇ Переместить ниже")
        self.move_down_btn.clicked.connect(self.move_player_down)
        self.move_down_btn.setEnabled(False)
        actions_layout.addWidget(self.move_down_btn)
        
        right_layout.addWidget(actions_group)
        
        # Информация о сыгранных матчах
        matches_group = QGroupBox("Сыгранные матчи")
        matches_layout = QVBoxLayout(matches_group)
        
        self.matches_info_label = QLabel("Нет выбранного игрока")
        self.matches_info_label.setWordWrap(True)
        self.matches_info_label.setStyleSheet("padding: 5px; background-color: #f5f5f5; border-radius: 3px; font-size: 10px;")
        matches_layout.addWidget(self.matches_info_label)
        
        right_layout.addWidget(matches_group)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([500, 300])
        
        layout.addWidget(splitter, 1)
        
        return tab
    
    def create_add_player_tab(self):
        """Вкладка для добавления нового игрока"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Группа выбора
        select_group = QGroupBox("Выбор игрока и места")
        select_layout = QGridLayout(select_group)
        select_layout.setSpacing(10)
        select_layout.setContentsMargins(10, 15, 10, 10)
        
        # Выбор игрока
        select_layout.addWidget(QLabel("Игрок:"), 0, 0)
        self.player_to_add_combo = QComboBox()
        self.player_to_add_combo.setEditable(True)
        self.player_to_add_combo.setMinimumWidth(300)
        select_layout.addWidget(self.player_to_add_combo, 0, 1, 1, 2)
        
        # Кнопка обновления списка игроков
        refresh_players_btn = QPushButton("🔄")
        refresh_players_btn.setMaximumWidth(30)
        refresh_players_btn.clicked.connect(self.load_players_for_add)
        select_layout.addWidget(refresh_players_btn, 0, 3)
        
        # Выбор группы
        select_layout.addWidget(QLabel("Группа:"), 1, 0)
        self.target_group_combo = QComboBox()
        self.target_group_combo.currentTextChanged.connect(self.on_target_group_changed)
        select_layout.addWidget(self.target_group_combo, 1, 1)
        
        # Выбор позиции
        select_layout.addWidget(QLabel("Позиция:"), 1, 2)
        self.target_position_combo = QComboBox()
        select_layout.addWidget(self.target_position_combo, 1, 3)
        
        layout.addWidget(select_group)
        
        # Информация об игроке
        info_group = QGroupBox("Информация об игроке")
        info_layout = QFormLayout(info_group)
        
        self.add_player_info_label = QLabel("Выберите игрока")
        self.add_player_info_label.setStyleSheet("padding: 5px; background-color: #f5f5f5; border-radius: 3px;")
        info_layout.addRow("Данные:", self.add_player_info_label)
        
        layout.addWidget(info_group)
        
        # Кнопка добавления
        add_btn = QPushButton("✅ Добавить игрока в группу")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        add_btn.clicked.connect(self.add_new_player_to_group)
        layout.addWidget(add_btn)
        
        layout.addStretch()
        
        return tab
    
    def load_title_info(self):
        """Загрузка информации о соревновании"""
        if self.title_id:
            try:
                self.current_title = Title.get_by_id(self.title_id)
                self.title_info_label.setText(f"Соревнование: {self.current_title.name}")
            except:
                self.title_info_label.setText("Соревнование: не найдено")
# ==========================    
    def load_stages(self):
        """Загрузка списка этапов"""
        self.stage_combo.clear()
        
        if not self.title_id:
            return
        
        try:
            stages = System.select().where((System.title_id == self.title_id) & (System.sex == self.current_sex)).order_by(System.id)
            for stage in stages:
                self.stage_combo.addItem(stage.stage, stage.id)
            
            if self.stage_combo.count() > 0:
                self.stage_combo.setCurrentIndex(0)
                
        except Exception as e:
            print(f"Ошибка загрузки этапов: {e}")

    def on_stage_changed(self, stage_name):
        self.current_stage = stage_name
        if not stage_name:
            return

        try:
            self.current_system = System.get_or_none(
                (System.title_id == self.title_id) &
                (System.stage == stage_name)
            )

            if self.current_system:
                self.load_groups()
                self.load_players_for_move_tab()
                self.load_players_for_add()
                self.update_add_player_tab()  # <-- добавить

                self.add_player_btn.setEnabled(True)

        except Exception as e:
            print(f"Ошибка загрузки этапа: {e}")
 # =======================   
    def load_groups(self):
        """Загрузка групп для текущего этапа"""
        if not self.current_system:
            return

        self.group_combo.clear()
        self.target_group_combo.clear()  # очищаем и для вкладки "Добавить игрока"

        try:
            if "Квалификация" in self.current_stage and "полуфинал" not in self.current_stage:
                groups = Game_list.select(
                    Game_list.number_group
                ).where(
                    (Game_list.title_id == self.title_id) &
                    (Game_list.system_id == self.current_system.id)
                ).distinct().order_by(Game_list.number_group)

                for group in groups:
                    self.group_combo.addItem(group.number_group)
                    self.target_group_combo.addItem(group.number_group)

            elif "полуфинал" in self.current_stage.lower():
                semi_num = 1 if "1-й" in self.current_stage else 2
                choices = Choice.select(
                    Choice.sf_group
                ).where(
                    (Choice.title_id == self.title_id) &
                    (Choice.semi_final == semi_num)
                ).distinct().order_by(Choice.sf_group)

                for choice in choices:
                    if choice.sf_group:
                        self.group_combo.addItem(choice.sf_group)
                        self.target_group_combo.addItem(choice.sf_group)

            else:
                # Финал или другая таблица
                self.group_combo.addItem(self.current_stage)
                self.target_group_combo.addItem(self.current_stage)

            if self.group_combo.count() > 0:
                self.group_combo.setCurrentIndex(0)
                # Обновляем позиции для вкладки "Добавить игрока"
                self.on_target_group_changed(self.target_group_combo.currentText())

        except Exception as e:
            print(f"Ошибка загрузки групп: {e}")

    def update_add_player_tab(self):
        """Обновление вкладки добавления игрока (группы и позиции)"""
        current_group = self.target_group_combo.currentText()
        if current_group:
            self.on_target_group_changed(current_group)

    def on_group_changed(self, group_name):
        """Обработка изменения группы"""
        if not group_name:
            return
        
        self.load_group_players(group_name)
    
    def load_group_players(self, group_name):
        """Загрузка игроков группы в таблицу"""
        if not self.current_system:
            return
        
        self.group_table.setRowCount(0)
        
        try:
            # Получаем игроков группы из Game_list
            query = Game_list.select().where(
                (Game_list.title_id == self.title_id) &
                (Game_list.system_id == self.current_system.id) &
                (Game_list.number_group == group_name)
            ).order_by(Game_list.rank_num_player)
            
            self.group_table.setRowCount(query.count())
            
            for row, gp in enumerate(query):
                player = Player.get_or_none(Player.id == gp.player_group.id)
                if not player:
                    continue
                
                # Номер позиции
                self.group_table.setItem(row, 0, QTableWidgetItem(str(gp.rank_num_player)))
                
                # Имя игрока
                name_item = QTableWidgetItem(player.fio or player.player)
                if player.fio == "X" or player.player == "X":
                    name_item.setBackground(QBrush(QColor(255, 200, 200)))
                    name_item.setForeground(QBrush(QColor(150, 0, 0)))
                self.group_table.setItem(row, 1, name_item)
                
                # Город
                self.group_table.setItem(row, 2, QTableWidgetItem(player.city or ""))
                
                # Регион
                self.group_table.setItem(row, 3, QTableWidgetItem(player.region or ""))
                
                # Рейтинг
                self.group_table.setItem(row, 4, QTableWidgetItem(str(player.rank) if player.rank else "0"))
                
            # Настраиваем внешний вид
            self.group_table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"Ошибка загрузки игроков группы: {e}")
    
    def load_players_for_move_tab(self):
        """Загрузка игроков для вкладки перемещения"""
        self.groups_tree.clear()
        
        if not self.current_system:
            return
        
        try:
            # Определяем, как получать данные в зависимости от этапа
            if "Квалификация" in self.current_stage and "полуфинал" not in self.current_stage:
                # Квалификация - из Game_list
                players = Game_list.select().where(
                    (Game_list.title_id == self.title_id) &
                    (Game_list.system_id == self.current_system.id)
                ).order_by(Game_list.number_group, Game_list.rank_num_player)
                
                groups = {}
                for gp in players:
                    group = gp.number_group
                    if group not in groups:
                        groups[group] = []
                    groups[group].append(gp)
                
                # Строим дерево
                for group_name in sorted(groups.keys()):
                    group_item = QTreeWidgetItem(self.groups_tree)
                    group_item.setText(0, f"📁 {group_name}")
                    group_item.setData(0, Qt.UserRole, {"type": "group", "name": group_name})
                    
                    for gp in groups[group_name]:
                        player = Player.get_or_none(Player.id == gp.player_group.id)
                        coach_id = player.coach_id
                        coaches = Coach.get_or_none(Coach.id == coach_id)
                        coach = coaches.coach
                        if player:
                            player_item = QTreeWidgetItem(group_item)
                            player_name = player.fio or player.player
                            if player_name == "X":
                                player_item.setText(0, f"❌ {player_name} (посев: {gp.rank_num_player})")
                                player_item.setForeground(0, QBrush(QColor(150, 0, 0)))
                            else:
                                player_item.setText(0, f"🏅 {player_name} (посев: {gp.rank_num_player} город: {player.city} тренер: {coach})")
                            player_item.setData(0, Qt.UserRole, {
                                "type": "player",
                                "id": player.id,
                                "game_id": gp.id,
                                "group": group_name,
                                "position": gp.rank_num_player,
                                "name": player_name,
                                "city":player.city,
                                "coach":coach
                            })
                            
            elif "полуфинал" in self.current_stage.lower():
                # Полуфинал - из Choice с semi_final
                semi_num = 1 if "1-й" in self.current_stage else 2
                choices = Choice.select().where(
                    (Choice.title_id == self.title_id) &
                    (Choice.semi_final == semi_num)
                ).order_by(Choice.sf_group, Choice.posev_sf)
                
                groups = {}
                for choice in choices:
                    group = choice.sf_group
                    if group not in groups:
                        groups[group] = []
                    groups[group].append(choice)
                
                for group_name in sorted(groups.keys()):
                    group_item = QTreeWidgetItem(self.groups_tree)
                    group_item.setText(0, f"📁 {group_name}")
                    group_item.setData(0, Qt.UserRole, {"type": "group", "name": group_name})
                    
                    for choice in groups[group_name]:
                        player = Player.get_or_none(Player.id == choice.player_choice.id)
                        if player:
                            player_item = QTreeWidgetItem(group_item)
                            player_name = player.fio or player.player
                            player_item.setText(0, f"🏅 {player_name} (посев: {choice.posev_sf} город: {player.city} тренер: {coach})")
                            player_item.setData(0, Qt.UserRole, {
                                "type": "player",
                                "id": player.id,
                                "choice_id": choice.id,
                                "group": group_name,
                                "position": choice.posev_sf,
                                "name": player_name
                            })
                            
            else:
                # Финал - из Game_list
                players = Game_list.select().where(
                    (Game_list.title_id == self.title_id) &
                    (Game_list.system_id == self.current_system.id)
                ).order_by(Game_list.rank_num_player)
                
                group_item = QTreeWidgetItem(self.groups_tree)
                group_item.setText(0, f"📁 {self.current_stage}")
                group_item.setData(0, Qt.UserRole, {"type": "group", "name": self.current_stage})
                
                for gp in players:
                    player = Player.get_or_none(Player.id == gp.player_group.id)
                    if player:
                        player_item = QTreeWidgetItem(group_item)
                        player_name = player.fio or player.player
                        if player_name == "X":
                            player_item.setText(0, f"❌ {player_name} (посев: {gp.rank_num_player})")
                            player_item.setForeground(0, QBrush(QColor(150, 0, 0)))
                        else:
                            player_item.setText(0, f"🏅 {player_name} (посев: {gp.rank_num_player})")
                        player_item.setData(0, Qt.UserRole, {
                            "type": "player",
                            "id": player.id,
                            "game_id": gp.id,
                            "group": self.current_stage,
                            "position": gp.rank_num_player,
                            "name": player_name
                        })
            
            self.groups_tree.expandAll()
            
        except Exception as e:
            print(f"Ошибка загрузки игроков для перемещения: {e}")
    
    def load_players_for_add(self):
        """Загрузка игроков для добавления"""
        self.player_to_add_combo.clear()
        
        if not self.title_id:
            return
        
        try:
            # Получаем всех игроков соревнования, которые еще не размещены
            existing_players = set()
            
            # Получаем уже размещенных игроков
            if self.current_system:
                game_players = Game_list.select().where(
                    (Game_list.title_id == self.title_id) &
                    (Game_list.system_id == self.current_system.id)
                )
                for gp in game_players:
                    if gp.player_group:
                        existing_players.add(gp.player_group.id)
            
            # Получаем всех игроков
            all_players = Player.select().where(Player.title_id == self.title_id)
            
            for player in all_players:
                if player.id not in existing_players and player.player != "X":
                    self.player_to_add_combo.addItem(
                        f"{player.fio or player.player} ({player.city or ''})",
                        player.id
                    )
            
            if self.player_to_add_combo.count() == 0:
                self.player_to_add_combo.addItem("Нет доступных игроков")
            
        except Exception as e:
            print(f"Ошибка загрузки игроков: {e}")
    
    def on_target_group_changed(self, group_name):
        """Обновление списка позиций при выборе группы"""
        self.target_position_combo.clear()
        
        if not group_name or not self.current_system:
            return
        
        try:
            # Получаем максимальную позицию в группе
            max_pos = Game_list.select().where(
                (Game_list.title_id == self.title_id) &
                (Game_list.system_id == self.current_system.id) &
                (Game_list.number_group == group_name)
            ).count()
            
            # Добавляем позиции от 1 до max_pos + 1 (для вставки в конец)
            for i in range(1, max_pos + 2):
                self.target_position_combo.addItem(str(i))
                
        except Exception as e:
            print(f"Ошибка загрузки позиций: {e}")
    
    def add_new_player_to_group(self):
        """Добавление нового игрока в группу"""
        if not self.current_system:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите этап")
            return
        
        player_id = self.player_to_add_combo.currentData()
        if not player_id:
            QMessageBox.warning(self, "Ошибка", "Выберите игрока для добавления")
            return
        
        group_name = self.target_group_combo.currentText()
        if not group_name:
            QMessageBox.warning(self, "Ошибка", "Выберите группу")
            return
        
        position_str = self.target_position_combo.currentText()
        if not position_str:
            QMessageBox.warning(self, "Ошибка", "Выберите позицию")
            return
        
        try:
            position = int(position_str)
        except:
            QMessageBox.warning(self, "Ошибка", "Некорректная позиция")
            return
        
        # Проверяем, не занята ли позиция
        existing = Game_list.get_or_none(
            (Game_list.title_id == self.title_id) &
            (Game_list.system_id == self.current_system.id) &
            (Game_list.number_group == group_name) &
            (Game_list.rank_num_player == position)
        )
        
        if existing:
            reply = QMessageBox.question(
                self,
                "Позиция занята",
                f"Позиция {position} в группе {group_name} уже занята.\n"
                f"Заменить игрока?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
            
            # Удаляем старого игрока
            existing.delete_instance()
            
            # Сдвигаем остальных игроков
            self.shift_players_after_insert(group_name, position, -1)
        
        # Добавляем нового игрока
        Game_list.create(
            number_group=group_name,
            rank_num_player=position,
            player_group=player_id,
            system_id=self.current_system.id,
            title_id=self.title_id,
            sex=self.current_system.sex
        )
        
        # Сдвигаем игроков после вставки
        self.shift_players_after_insert(group_name, position, 1)
        
        QMessageBox.information(self, "Успех", f"Игрок добавлен в группу {group_name} на позицию {position}")
        
        # Обновляем данные
        self.load_group_players(group_name)
        self.load_players_for_move_tab()
        self.load_players_for_add()
    
    def shift_players_after_insert(self, group_name, from_position, direction):
        """Сдвиг игроков после вставки/удаления"""
        try:
            # Получаем всех игроков группы с позициями >= from_position
            players = Game_list.select().where(
                (Game_list.title_id == self.title_id) &
                (Game_list.system_id == self.current_system.id) &
                (Game_list.number_group == group_name) &
                (Game_list.rank_num_player >= from_position)
            ).order_by(Game_list.rank_num_player)
            
            for gp in players:
                if gp.rank_num_player == from_position and direction == 1:
                    continue  # Это новый игрок
                gp.rank_num_player += direction
                gp.save()
                
        except Exception as e:
            print(f"Ошибка сдвига игроков: {e}")
    
    def add_player_to_group(self):
        """Добавить игрока в выбранную группу (из вкладки Группы)"""
        # Переключаемся на вкладку добавления
        self.tab_widget.setCurrentIndex(2)
        
        # Заполняем группу и позицию
        current_group = self.group_combo.currentText()
        if current_group:
            index = self.target_group_combo.findText(current_group)
            if index >= 0:
                self.target_group_combo.setCurrentIndex(index)
    
    def remove_player_from_group(self):
        """Удалить выбранного игрока из группы"""
        selected = self.group_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите игрока для удаления")
            return
        
        row = selected[0].row()
        group_name = self.group_combo.currentText()
        position = self.group_table.item(row, 0).text()
        
        try:
            pos = int(position)
            
            # Находим запись в Game_list
            gp = Game_list.get_or_none(
                (Game_list.title_id == self.title_id) &
                (Game_list.system_id == self.current_system.id) &
                (Game_list.number_group == group_name) &
                (Game_list.rank_num_player == pos)
            )
            
            if not gp:
                QMessageBox.warning(self, "Ошибка", "Игрок не найден в базе данных")
                return
            
            player_name = self.group_table.item(row, 1).text()
            
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Удалить игрока {player_name} из группы {group_name}?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                gp.delete_instance()
                
                # Сдвигаем остальных игроков
                self.shift_players_after_insert(group_name, pos + 1, -1)
                
                QMessageBox.information(self, "Успех", f"Игрок {player_name} удален из группы")
                
                # Обновляем данные
                self.load_group_players(group_name)
                self.load_players_for_move_tab()
                self.load_players_for_add()
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить игрока: {str(e)}")
    
    def on_group_table_selection_changed(self):
        """Обработка выбора строки в таблице группы"""
        self.remove_player_btn.setEnabled(len(self.group_table.selectedItems()) > 0)
    
    def on_tree_selection_changed(self):
        """Обработка выбора в дереве"""
        selected = self.groups_tree.selectedItems()
        if not selected:
            self.move_to_group_btn.setEnabled(False)
            self.swap_players_btn.setEnabled(False)
            self.move_up_btn.setEnabled(False)
            self.move_down_btn.setEnabled(False)
            return
        
        item = selected[0]
        data = item.data(0, Qt.UserRole)
        
        if data and data.get("type") == "player":
            self.move_to_group_btn.setEnabled(True)
            self.swap_players_btn.setEnabled(True)
            self.move_up_btn.setEnabled(True)
            self.move_down_btn.setEnabled(True)
            
            # Показываем информацию об игроке
            player_id = data.get("id")
            if player_id:
                player = Player.get_or_none(Player.id == player_id)
                if player:
                    info_text = f"""
                    👤 Игрок: {player.fio or player.player}
                    🏙️ Город: {player.city or '—'}
                    📍 Регион: {player.region or '—'}
                    📊 Рейтинг: {player.rank or 0}
                    🎯 Разряд: {player.razryad or '—'}
                    📁 Группа: {data.get('group', '—')}
                    📍 Позиция: {data.get('position', '—')}
                    """
                    self.player_info_label.setText(info_text)
                    
                    # Загружаем информацию о матчах
                    self.load_player_matches(player_id)
        else:
            self.move_to_group_btn.setEnabled(False)
            self.swap_players_btn.setEnabled(False)
            self.move_up_btn.setEnabled(False)
            self.move_down_btn.setEnabled(False)
            self.player_info_label.setText("Выберите игрока в дереве")
    
    def load_player_matches(self, player_id):
        """Загрузка информации о матчах игрока"""
        try:
            player = Player.get_by_id(player_id)
            player_fio = player.fio or player.player
            
            # Ищем матчи, где участвовал игрок
            matches = Result.select().where(
                (Result.title_id == self.title_id) &
                ((Result.player1.contains(player_fio)) | 
                 (Result.player2.contains(player_fio)))
            ).order_by(Result.number_group, Result.tours)
            
            if matches.count() == 0:
                self.matches_info_label.setText("Нет сыгранных матчей")
                return
            
            # Формируем список матчей
            match_text = ""
            for match in matches:
                opponent = match.player2 if player_fio in match.player1 else match.player1
                score = match.score_in_game if match.score_in_game else "—"
                winner = "✅" if match.winner and (player_fio in match.winner) else "❌"
                match_text += f"{match.number_group} | {winner} vs {opponent} | {score}\n"
            
            self.matches_info_label.setText(match_text)
            
        except Exception as e:
            print(f"Ошибка загрузки матчей: {e}")
            self.matches_info_label.setText("Ошибка загрузки матчей")
    
    def swap_players(self):
        """Обмен игроков местами"""
        selected = self.groups_tree.selectedItems()
        if len(selected) != 2:
            QMessageBox.warning(self, "Ошибка", "Выберите двух игроков для обмена (Ctrl+клик)")
            return
        
        try:
            # Получаем данные об игроках
            player1_data = selected[0].data(0, Qt.UserRole)
            player2_data = selected[1].data(0, Qt.UserRole)
            
            if not player1_data or not player2_data:
                QMessageBox.warning(self, "Ошибка", "Не удалось получить данные игроков")
                return
            
            if player1_data.get("type") != "player" or player2_data.get("type") != "player":
                QMessageBox.warning(self, "Ошибка", "Выберите двух игроков")
                return
            
            player1_id = player1_data.get("id")
            player2_id = player2_data.get("id")
            group1 = player1_data.get("group")
            group2 = player2_data.get("group")
            pos1 = player1_data.get("position")
            pos2 = player2_data.get("position")
            
            # Проверяем, что игроки не совпадают
            if player1_id == player2_id:
                QMessageBox.warning(self, "Ошибка", "Выбраны два одинаковых игрока")
                return
            
            # Подтверждение обмена
            reply = QMessageBox.question(
                self,
                "Подтверждение обмена",
                f"Обменять игроков местами?\n\n"
                f"1. {self.get_player_name(player1_id)} (Группа: {group1}, Позиция: {pos1})\n"
                f"2. {self.get_player_name(player2_id)} (Группа: {group2}, Позиция: {pos2})",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Меняем местами
                self.swap_players_in_db(player1_id, player2_id, group1, group2, pos1, pos2)

                # # дополняет номера будущих встреч            
                # for i in range(max_pl // 2 + 1, total_game + 1): 
                #     with db:
                #         results = Result(number_group=stage, system_stage="Финальный", player1="", player2="",
                #                         tours=i, title_id=self.current_title_id,
                #                         system_id=system.id, sex=self.current_sex).save()
                        
                QMessageBox.information(self, "Успех", "Игроки успешно обменяны местами")
                
                # Обновляем данные
                self.load_group_players(self.group_combo.currentText())
                self.load_players_for_move_tab()
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обменять игроков: {str(e)}")
    
    # def swap_players_in_db(self, player1_id, player2_id, group1, group2, pos1, pos2):
    #     """Обмен игроков в базе данных"""
    #     try:
    #         # Находим записи в Game_list
    #         gp1 = Game_list.get_or_none(
    #             (Game_list.title_id == self.title_id) &
    #             (Game_list.system_id == self.current_system.id) &
    #             (Game_list.player_group == player1_id) &
    #             (Game_list.number_group == group1)
    #         )
            
    #         gp2 = Game_list.get_or_none(
    #             (Game_list.title_id == self.title_id) &
    #             (Game_list.system_id == self.current_system.id) &
    #             (Game_list.player_group == player2_id) &
    #             (Game_list.number_group == group2)
    #         )
            
    #         if not gp1 or not gp2:
    #             # Пытаемся найти через Choice для полуфиналов
    #             if "полуфинал" in self.current_stage.lower():
    #                 semi_num = 1 if "1-й" in self.current_stage else 2
    #                 choice1 = Choice.get_or_none(
    #                     (Choice.title_id == self.title_id) &
    #                     (Choice.player_choice == player1_id) &
    #                     (Choice.semi_final == semi_num) &
    #                     (Choice.sf_group == group1)
    #                 )
    #                 choice2 = Choice.get_or_none(
    #                     (Choice.title_id == self.title_id) &
    #                     (Choice.player_choice == player2_id) &
    #                     (Choice.semi_final == semi_num) &
    #                     (Choice.sf_group == group2)
    #                 )
                    
    #                 if choice1 and choice2:
    #                     # Меняем местами в Choice
    #                     temp_group = choice1.sf_group
    #                     temp_pos = choice1.posev_sf
    #                     choice1.sf_group = choice2.sf_group
    #                     choice1.posev_sf = choice2.posev_sf
    #                     choice2.sf_group = temp_group
    #                     choice2.posev_sf = temp_pos
    #                     choice1.save()
    #                     choice2.save()
                        
    #                     # Обновляем также Game_list
    #                     gp1_alt = Game_list.get_or_none(
    #                         (Game_list.title_id == self.title_id) &
    #                         (Game_list.system_id == self.current_system.id) &
    #                         (Game_list.player_group == player1_id)
    #                     )
    #                     gp2_alt = Game_list.get_or_none(
    #                         (Game_list.title_id == self.title_id) &
    #                         (Game_list.system_id == self.current_system.id) &
    #                         (Game_list.player_group == player2_id)
    #                     )
                        
    #                     if gp1_alt and gp2_alt:
    #                         temp_pos_g = gp1_alt.rank_num_player
    #                         temp_group_g = gp1_alt.number_group
    #                         gp1_alt.number_group = gp2_alt.number_group
    #                         gp1_alt.rank_num_player = gp2_alt.rank_num_player
    #                         gp2_alt.number_group = temp_group_g
    #                         gp2_alt.rank_num_player = temp_pos_g
    #                         gp1_alt.save()
    #                         gp2_alt.save()
    #                     return
    #             else:
    #                 # Пытаемся найти через Choice для финалов
    #                 choice1 = Choice.get_or_none(
    #                     (Choice.title_id == self.title_id) &
    #                     (Choice.player_choice == player1_id)
    #                 )
    #                 choice2 = Choice.get_or_none(
    #                     (Choice.title_id == self.title_id) &
    #                     (Choice.player_choice == player2_id)
    #                 )
                    
    #                 if choice1 and choice2 and choice1.final == choice2.final:
    #                     # Меняем местами в Choice
    #                     temp_pos = choice1.posev_final
    #                     choice1.posev_final = choice2.posev_final
    #                     choice2.posev_final = temp_pos
    #                     choice1.save()
    #                     choice2.save()
                        
    #                     # Обновляем Game_list
    #                     gp1_alt = Game_list.get_or_none(
    #                         (Game_list.title_id == self.title_id) &
    #                         (Game_list.system_id == self.current_system.id) &
    #                         (Game_list.player_group == player1_id)
    #                     )
    #                     gp2_alt = Game_list.get_or_none(
    #                         (Game_list.title_id == self.title_id) &
    #                         (Game_list.system_id == self.current_system.id) &
    #                         (Game_list.player_group == player2_id)
    #                     )
                        
    #                     if gp1_alt and gp2_alt:
    #                         temp_pos_g = gp1_alt.rank_num_player
    #                         gp1_alt.rank_num_player = gp2_alt.rank_num_player
    #                         gp2_alt.rank_num_player = temp_pos_g
    #                         gp1_alt.save()
    #                         gp2_alt.save()
    #                     return
            
    #         # Стандартный обмен через Game_list
    #         temp_group = gp1.number_group
    #         temp_pos = gp1.rank_num_player
            
    #         gp1.number_group = gp2.number_group
    #         gp1.rank_num_player = gp2.rank_num_player
    #         gp2.number_group = temp_group
    #         gp2.rank_num_player = temp_pos
            
    #         gp1.save()
    #         gp2.save()
            
    #         # Если это полуфинал, обновляем также Choice
    #         if "полуфинал" in self.current_stage.lower():
    #             semi_num = 1 if "1-й" in self.current_stage else 2
    #             choice1 = Choice.get_or_none(
    #                 (Choice.title_id == self.title_id) &
    #                 (Choice.player_choice == player1_id) &
    #                 (Choice.semi_final == semi_num)
    #             )
    #             choice2 = Choice.get_or_none(
    #                 (Choice.title_id == self.title_id) &
    #                 (Choice.player_choice == player2_id) &
    #                 (Choice.semi_final == semi_num)
    #             )
                
    #             if choice1 and choice2:
    #                 temp_group_c = choice1.sf_group
    #                 temp_pos_c = choice1.posev_sf
    #                 choice1.sf_group = choice2.sf_group
    #                 choice1.posev_sf = choice2.posev_sf
    #                 choice2.sf_group = temp_group_c
    #                 choice2.posev_sf = temp_pos_c
    #                 choice1.save()
    #                 choice2.save()
            
    #     except Exception as e:
    #         print(f"Ошибка обмена игроков: {e}")
    #         raise

    #=============== 18 2020
    def swap_players_in_db(self, player1_id, player2_id, group1, group2, pos1, pos2):
        """Обмен игроков в базе данных с обновлением Game_list, Choice и Result"""
        try:
            # Получаем объекты игроков для их ФИО
            player1 = Player.get_or_none(Player.id == player1_id)
            player2 = Player.get_or_none(Player.id == player2_id)
            if not player1 or not player2:
                raise ValueError("Игроки не найдены")

            # Формируем старые и новые ФИО (с городом)
            old_fio1 = player1.fio_city or self.format_fio_city(player1.fio, player1.city)
            old_fio2 = player2.fio_city or self.format_fio_city(player2.fio, player2.city)

            # Начинаем транзакцию
            with db.atomic():
                # --- 1. Обновляем Game_list ---
                gp1 = Game_list.get_or_none(
                    (Game_list.title_id == self.title_id) &
                    (Game_list.system_id == self.current_system.id) &
                    (Game_list.player_group == player1_id) &
                    (Game_list.number_group == group1)
                )
                gp2 = Game_list.get_or_none(
                    (Game_list.title_id == self.title_id) &
                    (Game_list.system_id == self.current_system.id) &
                    (Game_list.player_group == player2_id) &
                    (Game_list.number_group == group2)
                )

                if not gp1 or not gp2:
                    # Пытаемся найти через Choice для полуфиналов или финалов (альтернативный путь)
                    # ... (существующий код для полуфиналов и финалов)
                    # В этом блоке также нужно обновить Result после обмена
                    # Для простоты, если мы попали в этот блок, то после обмена Choice и Game_list нужно вызвать обновление Result
                    # Но здесь мы оставим существующую логику, но добавим вызов обновления Result в конце
                    # Однако лучше унифицировать: сначала обновить Game_list и Choice, а потом Result
                    pass

                # Стандартный обмен через Game_list
                temp_group = gp1.number_group
                temp_pos = gp1.rank_num_player

                gp1.number_group = gp2.number_group
                gp1.rank_num_player = gp2.rank_num_player
                gp2.number_group = temp_group
                gp2.rank_num_player = temp_pos

                gp1.save()
                gp2.save()

                # --- 2. Обновляем Choice (посев) ---
                # Находим Choice для обоих игроков
                choice1 = Choice.get_or_none(
                    (Choice.title_id == self.title_id) &
                    (Choice.player_choice == player1_id)
                )
                choice2 = Choice.get_or_none(
                    (Choice.title_id == self.title_id) &
                    (Choice.player_choice == player2_id)
                )

                if choice1 and choice2:
                    # Меняем местами номера посева (posev_group, posev_final, posev_sf в зависимости от этапа)
                    if self.current_stage == "Квалификация":
                        temp_posev = choice1.posev_group
                        choice1.posev_group = choice2.posev_group
                        choice2.posev_group = temp_posev
                    elif "полуфинал" in self.current_stage.lower():
                        temp_posev = choice1.posev_sf
                        choice1.posev_sf = choice2.posev_sf
                        choice2.posev_sf = temp_posev
                        # Также обновляем sf_group
                        temp_group_c = choice1.sf_group
                        choice1.sf_group = choice2.sf_group
                        choice2.sf_group = temp_group_c
                    else:  # финал
                        temp_posev = choice1.posev_final
                        choice1.posev_final = choice2.posev_final
                        choice2.posev_final = temp_posev
                    choice1.save()
                    choice2.save()

                # --- 3. Обновляем Result (заменяем имена игроков) ---
                # Получаем новые ФИО (они не изменились, но для уверенности)
                new_fio1 = player1.fio_city or self.format_fio_city(player1.fio, player1.city)
                new_fio2 = player2.fio_city or self.format_fio_city(player2.fio, player2.city)

                # Заменяем в player1
                Result.update(player1=new_fio1).where(
                    (Result.title_id == self.title_id) &
                    (Result.player1 == old_fio1)
                ).execute()
                Result.update(player1=new_fio2).where(
                    (Result.title_id == self.title_id) &
                    (Result.player1 == old_fio2)
                ).execute()

                # Заменяем в player2
                Result.update(player2=new_fio1).where(
                    (Result.title_id == self.title_id) &
                    (Result.player2 == old_fio1)
                ).execute()
                Result.update(player2=new_fio2).where(
                    (Result.title_id == self.title_id) &
                    (Result.player2 == old_fio2)
                ).execute()

                # Заменяем в winner
                Result.update(winner=new_fio1).where(
                    (Result.title_id == self.title_id) &
                    (Result.winner == old_fio1)
                ).execute()
                Result.update(winner=new_fio2).where(
                    (Result.title_id == self.title_id) &
                    (Result.winner == old_fio2)
                ).execute()

                # Заменяем в loser
                Result.update(loser=new_fio1).where(
                    (Result.title_id == self.title_id) &
                    (Result.loser == old_fio1)
                ).execute()
                Result.update(loser=new_fio2).where(
                    (Result.title_id == self.title_id) &
                    (Result.loser == old_fio2)
                ).execute()

            # После транзакции можно обновить интерфейс (перезагрузить данные)
            QMessageBox.information(self, "Успех", "Игроки успешно обменяны местами с обновлением всех данных")

        except Exception as e:
            print(f"Ошибка обмена игроков: {e}")
            raise

#================================
    # def swap_players_in_db(self, player1_id, player2_id, group1, group2, pos1, pos2):
    #     """Обмен игроков в базе данных с полным обновлением сетки"""
    #     try:
    #         with db.atomic():
    #             # --- 1. Обмен в Game_list ---
    #             gp1 = Game_list.get_or_none(
    #                 (Game_list.title_id == self.title_id) &
    #                 (Game_list.system_id == self.current_system.id) &
    #                 (Game_list.player_group == player1_id) &
    #                 (Game_list.number_group == group1)
    #             )
    #             gp2 = Game_list.get_or_none(
    #                 (Game_list.title_id == self.title_id) &
    #                 (Game_list.system_id == self.current_system.id) &
    #                 (Game_list.player_group == player2_id) &
    #                 (Game_list.number_group == group2)
    #             )

    #             if gp1 and gp2:
    #                 # Стандартный обмен через Game_list
    #                 temp_group = gp1.number_group
    #                 temp_pos = gp1.rank_num_player
    #                 gp1.number_group = gp2.number_group
    #                 gp1.rank_num_player = gp2.rank_num_player
    #                 gp2.number_group = temp_group
    #                 gp2.rank_num_player = temp_pos
    #                 gp1.save()
    #                 gp2.save()

    #             # --- 2. Обмен в Choice (для полуфиналов и финалов) ---
    #             if "полуфинал" in self.current_stage.lower():
    #                 semi_num = 1 if "1-й" in self.current_stage else 2
    #                 choice1 = Choice.get_or_none(
    #                     (Choice.title_id == self.title_id) &
    #                     (Choice.player_choice == player1_id) &
    #                     (Choice.semi_final == semi_num)
    #                 )
    #                 choice2 = Choice.get_or_none(
    #                     (Choice.title_id == self.title_id) &
    #                     (Choice.player_choice == player2_id) &
    #                     (Choice.semi_final == semi_num)
    #                 )
    #                 if choice1 and choice2:
    #                     temp_group_c = choice1.sf_group
    #                     temp_pos_c = choice1.posev_sf
    #                     choice1.sf_group = choice2.sf_group
    #                     choice1.posev_sf = choice2.posev_sf
    #                     choice2.sf_group = temp_group_c
    #                     choice2.posev_sf = temp_pos_c
    #                     choice1.save()
    #                     choice2.save()
    #             else:
    #                 # Для финалов
    #                 choice1 = Choice.get_or_none(
    #                     (Choice.title_id == self.title_id) &
    #                     (Choice.player_choice == player1_id)
    #                 )
    #                 choice2 = Choice.get_or_none(
    #                     (Choice.title_id == self.title_id) &
    #                     (Choice.player_choice == player2_id)
    #                 )
    #                 if choice1 and choice2 and choice1.final == choice2.final:
    #                     temp_pos = choice1.posev_final
    #                     choice1.posev_final = choice2.posev_final
    #                     choice2.posev_final = temp_pos
    #                     choice1.save()
    #                     choice2.save()

    #             # --- 3. Пересоздание матчей для этапа (Result) ---
    #             # Это гарантирует, что все матчи в сетке существуют и соответствуют новому расположению игроков
    #             if hasattr(self.parent, 'recreate_matches_for_stage'):
    #                 self.parent.recreate_matches_for_stage(self.current_stage)
    #             else:
    #                 # Если родительский метод недоступен, используем собственный fallback
    #                 # (но в реальности он есть, так как EditStagesDialog всегда имеет parent)
    #                 system = System.get_or_none(
    #                     (System.title_id == self.title_id) &
    #                     (System.stage == self.current_stage)
    #                 )
    #                 if system:
    #                     game_players = Game_list.select().where(
    #                         (Game_list.title_id == self.title_id) &
    #                         (Game_list.system_id == system.id)
    #                     )
    #                     # Используем стандартную логику пересоздания матчей из родителя
    #                     if hasattr(self.parent, 'recreate_round_robin_matches'):
    #                         self.parent.recreate_round_robin_matches(system, game_players)
    #                     elif hasattr(self.parent, 'recreate_olympic_matches'):
    #                         self.parent.recreate_olympic_matches(system, game_players)

    #                     # # дополняет номера будущих встреч            
    #                     # for i in range(max_pl // 2 + 1, total_game + 1): 
    #                     #     with db:
    #                     #         results = Result(number_group=self.current_stage, system_stage="Финальный", player1="", player2="",
    #                     #                         tours=i, title_id=self.current_title_id,
    #                     #                         system_id=system.id, sex=self.current_sex).save()

    #             print(f"Обмен игроков {player1_id} и {player2_id} выполнен. Сетка обновлена.")

    #     except Exception as e:
    #         print(f"Ошибка обмена игроков: {e}")
    #         import traceback
    #         traceback.print_exc()
    #         raise

    #================
        
    def move_player_to_group(self):
        """Переместить игрока в другую группу"""
        selected = self.groups_tree.selectedItems()
        if not selected:
            return
        
        item = selected[0]
        data = item.data(0, Qt.UserRole)
        
        if not data or data.get("type") != "player":
            QMessageBox.warning(self, "Ошибка", "Выберите игрока")
            return
        
        player_id = data.get("id")
        current_group = data.get("group")
        current_pos = data.get("position")
        
        # Получаем список доступных групп
        groups = []
        for i in range(self.group_combo.count()):
            groups.append(self.group_combo.itemText(i))
        
        # Создаем диалог выбора группы
        from PyQt5.QtWidgets import QInputDialog
        target_group, ok = QInputDialog.getItem(
            self,
            "Выбор группы",
            "Выберите целевую группу:",
            groups,
            0,
            False
        )
        
        if not ok or not target_group or target_group == current_group:
            return
        
        # Выбираем позицию
        # Получаем количество игроков в целевой группе
        count = Game_list.select().where(
            (Game_list.title_id == self.title_id) &
            (Game_list.system_id == self.current_system.id) &
            (Game_list.number_group == target_group)
        ).count()
        
        positions = [str(i) for i in range(1, count + 2)]
        target_pos, ok2 = QInputDialog.getItem(
            self,
            "Выбор позиции",
            f"Выберите позицию в группе {target_group}:",
            positions,
            0,
            False
        )
        
        if not ok2 or not target_pos:
            return
        
        target_pos = int(target_pos)
        
        # Подтверждение перемещения
        player_name = self.get_player_name(player_id)
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Переместить игрока {player_name}\n"
            f"из группы {current_group} (поз. {current_pos})\n"
            f"в группу {target_group} (поз. {target_pos})?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.move_player_in_db(player_id, current_group, current_pos, target_group, target_pos)
            
            QMessageBox.information(self, "Успех", f"Игрок {player_name} перемещен")
            
            # Обновляем данные
            self.load_group_players(self.group_combo.currentText())
            self.load_players_for_move_tab()
    
    def move_player_in_db(self, player_id, from_group, from_pos, to_group, to_pos):
        """Перемещение игрока в базе данных"""
        try:
            # Находим запись в Game_list
            gp = Game_list.get_or_none(
                (Game_list.title_id == self.title_id) &
                (Game_list.system_id == self.current_system.id) &
                (Game_list.player_group == player_id) &
                (Game_list.number_group == from_group)
            )
            
            if not gp:
                QMessageBox.warning(self, "Ошибка", "Игрок не найден в базе данных")
                return
            
            # Сдвигаем игроков в целевой группе
            self.shift_players_after_insert(to_group, to_pos, 1)
            
            # Перемещаем игрока
            gp.number_group = to_group
            gp.rank_num_player = to_pos
            gp.save()
            
            # Сдвигаем игроков в исходной группе после удаления
            self.shift_players_after_insert(from_group, from_pos + 1, -1)
            
            # Если это полуфинал, обновляем Choice
            if "полуфинал" in self.current_stage.lower():
                semi_num = 1 if "1-й" in self.current_stage else 2
                choice = Choice.get_or_none(
                    (Choice.title_id == self.title_id) &
                    (Choice.player_choice == player_id) &
                    (Choice.semi_final == semi_num)
                )
                if choice:
                    choice.sf_group = to_group
                    choice.posev_sf = to_pos
                    choice.save()
            
            # Если это финал, обновляем Choice
            elif "финал" in self.current_stage.lower():
                choice = Choice.get_or_none(
                    (Choice.title_id == self.title_id) &
                    (Choice.player_choice == player_id)
                )
                if choice and choice.final == self.current_stage:
                    choice.posev_final = to_pos
                    choice.save()
                    
        except Exception as e:
            print(f"Ошибка перемещения игрока: {e}")
            raise
    
    def move_player_up(self):
        """Переместить игрока выше в группе"""
        self.move_player_vertical(-1)
    
    def move_player_down(self):
        """Переместить игрока ниже в группе"""
        self.move_player_vertical(1)
    
    def move_player_vertical(self, direction):
        """Перемещение игрока вверх или вниз в группе"""
        selected = self.groups_tree.selectedItems()
        if not selected:
            return
        
        item = selected[0]
        data = item.data(0, Qt.UserRole)
        
        if not data or data.get("type") != "player":
            return
        
        player_id = data.get("id")
        group = data.get("group")
        current_pos = data.get("position")
        new_pos = current_pos + direction
        
        if new_pos < 1:
            return
        
        # Проверяем, есть ли игрок на новой позиции
        other = Game_list.get_or_none(
            (Game_list.title_id == self.title_id) &
            (Game_list.system_id == self.current_system.id) &
            (Game_list.number_group == group) &
            (Game_list.rank_num_player == new_pos)
        )
        
        if other:
            # Меняем местами с соседним игроком
            other_id = other.player_group.id
            
            # Обмен через swap_players_in_db
            self.swap_players_in_db(player_id, other_id, group, group, current_pos, new_pos)
        else:
            # Просто меняем позицию
            gp = Game_list.get_or_none(
                (Game_list.title_id == self.title_id) &
                (Game_list.system_id == self.current_system.id) &
                (Game_list.player_group == player_id) &
                (Game_list.number_group == group)
            )
            if gp:
                gp.rank_num_player = new_pos
                gp.save()
        
        # Обновляем данные
        self.load_group_players(self.group_combo.currentText())
        self.load_players_for_move_tab()
    
    def get_player_name(self, player_id):
        """Получение имени игрока по ID"""
        try:
            player = Player.get_by_id(player_id)
            return player.fio or player.player
        except:
            return f"Игрок {player_id}"
    
    def refresh_data(self):
        """Обновление всех данных"""
        self.load_stages()
        
        if self.stage_combo.count() > 0:
            self.on_stage_changed(self.stage_combo.currentText())
    
    def apply_changes(self):
        """Применение всех изменений - перезапись Result и Choice"""
        try:
            # Подтверждение
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                "После применения изменений все матчи будут пересозданы.\n"
                "Текущие результаты будут сохранены, если игроки уже играли.\n\n"
                "Продолжить?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Пересоздаем матчи для текущего этапа
            if self.current_system:
                self.recreate_matches_for_stage(self.current_stage)
                
                # Обновляем выборы
                self.update_choice_after_changes()
                
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Изменения применены для этапа {self.current_stage}\n"
                    "Таблицы Result, Choice и Game_list обновлены."
                )
                
                # Обновляем данные
                self.refresh_data()
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось применить изменения: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def recreate_round_robin_matches(self, system, game_players):
        """Пересоздание матчей для круговой системы"""
        # Группируем игроков по группам
        groups = {}
        for gp in game_players:
            group = gp.number_group
            if group not in groups:
                groups[group] = []
            groups[group].append(gp)
        
        # Удаляем старые результаты для этого этапа
        if system.stage in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"]:
            Result.delete().where(
                (Result.title_id == self.title_id) &
                (Result.system_stage == system.stage)
            ).execute()
        else:
            Result.delete().where(
                (Result.title_id == self.title_id) &
                (Result.number_group == system.stage)
            ).execute()
        
        # Создаем новые матчи для каждой группы
        for group_name, players in groups.items():
            # Сортируем по позиции
            players.sort(key=lambda x: x.rank_num_player)
            
            # Создаем словарь для быстрого доступа к игрокам
            player_by_pos = {}
            for gp in players:
                player = Player.get_or_none(Player.id == gp.player_group.id)
                if player:
                    player_by_pos[gp.rank_num_player] = player
            
            total_players = len(players)
            if total_players < 2:
                continue
            
            # Получаем туры
            tours = self.get_tours_list(total_players)
            
            # Создаем матчи
            for tour_idx, matches in enumerate(tours, 1):
                for match in matches:
                    positions = match.split('-')
                    pos1 = int(positions[0])
                    pos2 = int(positions[1])
                    
                    if pos1 in player_by_pos and pos2 in player_by_pos:
                        player1 = player_by_pos[pos1]
                        player2 = player_by_pos[pos2]
                        
                        player1_name = f"{player1.fio or player1.player}/{player1.city or ''}" if player1.city else (player1.fio or player1.player)
                        player2_name = f"{player2.fio or player2.player}/{player2.city or ''}" if player2.city else (player2.fio or player2.player)
                        
                        # Проверяем, есть ли уже результат для этого матча (из старых данных)
                        existing_result = Result.get_or_none(
                            (Result.title_id == self.title_id) &
                            (Result.number_group == group_name) &
                            (Result.tours == match) &
                            (Result.system_stage == system.stage if system.stage in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else None)
                        )
                        
                        if existing_result:
                            # Сохраняем результат, если он есть
                            Result.create(
                                system_stage=system.stage if system.stage in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else "",
                                number_group=group_name,
                                tours=match,
                                player1=player1_name,
                                player2=player2_name,
                                winner=existing_result.winner,
                                points_win=existing_result.points_win,
                                score_in_game=existing_result.score_in_game,
                                score_win=existing_result.score_win,
                                loser=existing_result.loser,
                                points_loser=existing_result.points_loser,
                                score_loser=existing_result.score_loser,
                                title_id=self.title_id,
                                round=tour_idx,
                                system_id=system.id,
                                sex=system.sex
                            )
                        else:
                            # Создаем пустой матч
                            Result.create(
                                system_stage=system.stage if system.stage in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else "",
                                number_group=group_name,
                                tours=match,
                                player1=player1_name,
                                player2=player2_name,
                                title_id=self.title_id,
                                round=tour_idx,
                                system_id=system.id,
                                sex=system.sex
                            )
# =====================   
    # def recreate_olympic_matches(self, system, game_players):
    #     """Пересоздание матчей для олимпийской системы"""
    #     # Удаляем старые результаты
    #     if system.stage in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"]:
    #         Result.delete().where(
    #             (Result.title_id == self.title_id) &
    #             (Result.system_stage == system.stage)
    #         ).execute()
    #     else:
    #         Result.delete().where(
    #             (Result.title_id == self.title_id) &
    #             (Result.sex == self.current_sex) &
    #             (Result.number_group == system.stage)
    #         ).execute()
        
    #     # Получаем максимальное количество игроков в сетке
    #     max_player = system.max_player
    #     total_players = game_players.count()
    #     real_players = [gp for gp in game_players if gp.player_group and gp.player_group.player != "X"]
        
    #     # Создаем словарь игроков по позициям
    #     player_by_pos = {}
    #     for gp in game_players:
    #         player = Player.get_or_none(Player.id == gp.player_group.id)
    #         if player:
    #             player_by_pos[gp.rank_num_player] = player
        
    #     # Создаем матчи для первого раунда
    #     first_round_pairs = []
    #     for i in range(1, max_player // 2 + 1):
    #         pos1 = i * 2 - 1
    #         pos2 = i * 2
            
    #         player1 = player_by_pos.get(pos1)
    #         player2 = player_by_pos.get(pos2)
            
    #         if player1 and player2:
    #             player1_name = f"{player1.fio or player1.player}/{player1.city or ''}" if player1.city else (player1.fio or player1.player)
    #             player2_name = f"{player2.fio or player2.player}/{player2.city or ''}" if player2.city else (player2.fio or player2.player)
                
    #             first_round_pairs.append((pos1, pos2, player1_name, player2_name))
        
    #     # Создаем записи в Result для первого раунда
    #     for pair_idx, (pos1, pos2, p1_name, p2_name) in enumerate(first_round_pairs, 1):
    #         # Проверяем существующий результат
    #         existing = Result.get_or_none(
    #             (Result.title_id == self.title_id) &
    #             (Result.system_stage == system.stage if system.stage in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else None) &
    #             (Result.number_group == system.stage if system.stage not in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else None) &
    #             (Result.tours == str(pair_idx))
    #         )
            
    #         if existing:
    #             Result.create(
    #                 system_stage=system.stage if system.stage in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else "",
    #                 number_group=system.stage if system.stage not in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else "",
    #                 tours=str(pair_idx),
    #                 player1=p1_name,
    #                 player2=p2_name,
    #                 winner=existing.winner,
    #                 points_win=existing.points_win,
    #                 score_in_game=existing.score_in_game,
    #                 score_win=existing.score_win,
    #                 loser=existing.loser,
    #                 points_loser=existing.points_loser,
    #                 score_loser=existing.score_loser,
    #                 title_id=self.title_id,
    #                 round=1,
    #                 system_id=system.id,
    #                 sex=system.sex
    #             )
    #         else:
    #             Result.create(
    #                 system_stage=system.stage if system.stage in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else "",
    #                 number_group=system.stage if system.stage not in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else "",
    #                 tours=str(pair_idx),
    #                 player1=p1_name,
    #                 player2=p2_name,
    #                 title_id=self.title_id,
    #                 round=1,
    #                 system_id=system.id,
    #                 sex=system.sex
    #             )
        
    #     # Создаем пустые записи для последующих раундов
    #     total_games = self.number_game_of_net(system.stage)
    #     # total_games = self.get_total_olympic_games(max_player)
    #     for game_num in range(max_player // 2 + 1, total_games + 1):
    #         existing = Result.get_or_none(
    #             (Result.title_id == self.title_id) &
    #             (Result.system_stage == system.stage if system.stage in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else None) &
    #             (Result.number_group == system.stage if system.stage not in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else None) &
    #             (Result.tours == str(game_num))
    #         )
            
    #         if not existing:
    #             Result.create(
    #                 system_stage=system.stage if system.stage in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else "",
    #                 number_group=system.stage if system.stage not in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else "",
    #                 tours=str(game_num),
    #                 player1="",
    #                 player2="",
    #                 title_id=self.title_id,
    #                 round=1,
    #                 system_id=system.id,
    #                 sex=system.sex
    #             )


    def recreate_olympic_matches(self, system, game_players):
        """Пересоздание матчей для олимпийской системы с сохранением результатов"""
        if system.stage in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"]:
            Result.delete().where(
                (Result.title_id == self.title_id) &
                (Result.system_stage == system.stage)
            ).execute()
        else:
            Result.delete().where(
                (Result.title_id == self.title_id) &
                (Result.number_group == system.stage)
            ).execute()

        max_player = system.max_player
        total_players = game_players.count()
        real_players = [gp for gp in game_players if gp.player_group and gp.player_group.player != "X"]
        
        # Создаём словарь игроков по позициям
        player_by_pos = {}
        for gp in game_players:
            player = Player.get_or_none(Player.id == gp.player_group.id)
            if player:
                player_by_pos[gp.rank_num_player] = player

        # --- ПЕРВЫЙ РАУНД ---
        first_round_pairs = []
        for i in range(1, max_player // 2 + 1):
            pos1 = i * 2 - 1
            pos2 = i * 2
            player1 = player_by_pos.get(pos1)
            player2 = player_by_pos.get(pos2)
            if player1 and player2:
                player1_name = f"{player1.fio or player1.player}/{player1.city or ''}" if player1.city else (player1.fio or player1.player)
                player2_name = f"{player2.fio or player2.player}/{player2.city or ''}" if player2.city else (player2.fio or player2.player)
                first_round_pairs.append((pos1, pos2, player1_name, player2_name))

        for pair_idx, (pos1, pos2, p1_name, p2_name) in enumerate(first_round_pairs, 1):
            existing = Result.get_or_none(
                (Result.title_id == self.title_id) &
                (Result.system_stage == system.stage if system.stage in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else None) &
                (Result.number_group == system.stage if system.stage not in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else None) &
                (Result.tours == str(pair_idx))
            )
            if existing:
                Result.create(
                    system_stage=system.stage if system.stage in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else "",
                    number_group=system.stage if system.stage not in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else "",
                    tours=str(pair_idx),
                    player1=p1_name,
                    player2=p2_name,
                    winner=existing.winner,
                    points_win=existing.points_win,
                    score_in_game=existing.score_in_game,
                    score_win=existing.score_win,
                    loser=existing.loser,
                    points_loser=existing.points_loser,
                    score_loser=existing.score_loser,
                    title_id=self.title_id,
                    round=1,
                    system_id=system.id,
                    sex=system.sex
                )
            else:
                Result.create(
                    system_stage=system.stage if system.stage in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else "",
                    number_group=system.stage if system.stage not in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else "",
                    tours=str(pair_idx),
                    player1=p1_name,
                    player2=p2_name,
                    title_id=self.title_id,
                    round=1,
                    system_id=system.id,
                    sex=system.sex
                )

        # --- ПОСЛЕДУЮЩИЕ РАУНДЫ (ПУСТЫЕ ЗАПИСИ) ---
        # Используем корректное количество игр из number_game_of_net
        total_games = self.number_game_of_net(system.stage)
        for game_num in range(max_player // 2 + 1, total_games + 1):
            existing = Result.get_or_none(
                (Result.title_id == self.title_id) &
                (Result.system_stage == system.stage if system.stage in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else None) &
                (Result.number_group == system.stage if system.stage not in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else None) &
                (Result.tours == str(game_num))
            )
            if not existing:
                Result.create(
                    system_stage=system.stage if system.stage in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else "",
                    number_group=system.stage if system.stage not in ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"] else "",
                    tours=str(game_num),
                    player1="",
                    player2="",
                    title_id=self.title_id,
                    round=1,
                    system_id=system.id,
                    sex=system.sex
                )

        # записывает стадии сетки в Result
        highest_place = self.parent.get_final_start_place(system.stage)

        stadia = self.parent.whrite_stadia_on_net(total_games, highest_place, max_player)

        results_stadia = Result.select().where(
            (Result.title_id == self.title_id) &
            (Result.system_id == system.id))

        for k in results_stadia:
            num_game = int(k.tours)
            stadia_str = stadia[num_game]
            Result.update(stage_net=stadia_str).where(Result.id == k).execute()

    def number_game_of_net(self, stage):
        """Возвращает общее количество игр в олимпийской сетке для данного этапа.
        Использует родительский метод, если он доступен, иначе рассчитывает самостоятельно.
        """
        # Пытаемся вызвать родительский метод
        if hasattr(self.parent, 'number_game_of_net'):
            return self.parent.number_game_of_net(stage)
        
        # Fallback: рассчитываем вручную
        system = System.get_or_none(
            (System.title_id == self.title_id) &
            (System.stage == stage)
        )
        if not system:
            return 0
        
        max_player = system.max_player
        # Определяем степень двойки для сетки
        m = 0
        temp = max_player
        while temp > 1:
            temp //= 2
            m += 1
        # Минимальное количество игр в олимпийской системе
        total_games = m * (max_player // 2)
        
        # Если тип "Олимпийская (минус 2)", добавляем дополнительные игры
        if system.type_table == "Олимпийская (минус 2)":
            additional = 0
            for l in range(2, 17, 2):
                games = (max_player // l) // 2
                additional += games
                if games // 2 == 1:
                    break
            total_games += additional
        return total_games
    #======================
    
    # def get_tours_list(self, players_count):
    #     """Получение списка туров для круговой системы"""
    #     # Используем существующую функцию tours_list
    #     if hasattr(self.parent, 'tours_list'):
    #         return self.parent.tours_list(players_count)
        
    #     # fallback
    #     if players_count <= 3:
    #         return [['1-2'], ['1-3'], ['2-3']]
    #     elif players_count == 4:
    #         return [['1-2', '3-4'], ['1-3', '2-4'], ['1-4', '2-3']]
    #     elif players_count == 5:
    #         return [['1-2', '3-4'], ['1-3', '2-5'], ['1-4', '3-5'], ['1-5', '2-4'], ['2-3', '4-5']]
    #     elif players_count == 6:
    #         return [['1-2', '3-4', '5-6'], ['1-3', '2-5', '4-6'], ['1-4', '2-6', '3-5'], ['1-5', '2-4', '3-6'], ['1-6', '2-3', '4-5']]
    #     else:
    #         # Для большего количества игроков используем стандартный алгоритм
    #         tours = []
    #         players = list(range(1, players_count + 1))
    #         if players_count % 2 == 1:
    #             players.append(0)
    #             n = players_count + 1
    #         else:
    #             n = players_count
            
    #         for _ in range(n - 1):
    #             tour = []
    #             for i in range(n // 2):
    #                 p1 = players[i]
    #                 p2 = players[n - 1 - i]
    #                 if p1 != 0 and p2 != 0:
    #                     tour.append(f"{p1}-{p2}")
    #             tours.append(tour)
    #             players = [players[0]] + [players[-1]] + players[1:-1]
    #         return tours
    
    def update_choice_after_changes(self):
        """Обновление Choice после изменений"""
        if not self.current_system:
            return
        
        try:
            # Получаем всех игроков из Game_list
            game_players = Game_list.select().where(
                (Game_list.title_id == self.title_id) &
                (Game_list.system_id == self.current_system.id)
            )
            
            for gp in game_players:
                player = Player.get_or_none(Player.id == gp.player_group.id)
                if not player:
                    continue
                
                # Находим запись Choice
                choice = Choice.get_or_none(
                    (Choice.title_id == self.title_id) &
                    (Choice.player_choice == player.id)
                )
                
                if not choice:
                    continue
                
                # Обновляем в зависимости от этапа
                if "Квалификация" in self.current_stage and "полуфинал" not in self.current_stage:
                    choice.group = gp.number_group
                    choice.posev_group = gp.rank_num_player
                elif "полуфинал" in self.current_stage.lower():
                    semi_num = 1 if "1-й" in self.current_stage else 2
                    choice.semi_final = semi_num
                    choice.sf_group = gp.number_group
                    choice.posev_sf = gp.rank_num_player
                else:
                    choice.final = self.current_stage
                    choice.posev_final = gp.rank_num_player
                
                choice.save()
                
        except Exception as e:
            print(f"Ошибка обновления Choice: {e}")
# ==================
    def recreate_semifinal_matches(self, system, game_players, stage_name):
        """Пересоздание матчей для полуфинала с переносом результатов из квалификации"""
        # Группируем игроков по группам
        groups = {}
        for gp in game_players:
            group = gp.number_group
            if group not in groups:
                groups[group] = []
            groups[group].append(gp)

        # Формируем структуру sf_groups для родительского метода
        sf_groups = []
        for group_name, players in groups.items():
            players.sort(key=lambda x: x.rank_num_player)
            group_players = []
            for gp in players:
                player = Player.get_or_none(Player.id == gp.player_group.id)
                if player:
                    choice = Choice.get_or_none(
                        (Choice.title_id == self.title_id) &
                        (Choice.player_choice == player.id)
                    )
                    if choice:
                        group_players.append(choice)
            # Извлекаем номер группы
            import re
            match = re.search(r'(\d+)', group_name)
            group_num = int(match.group(1)) if match else 0
            sf_groups.append({
                'sf_group_num': group_num,
                'players': group_players,
                'from_groups': []   # не используется, но нужно для структуры
            })

        # Определяем номер полуфинала
        semi_num = 1 if "1-й" in stage_name else 2

        # Убеждаемся, что в родителе установлен правильный title_id
        if self.parent and hasattr(self.parent, 'current_title_id'):
            self.parent.current_title_id = self.title_id

        # Вызываем родительский метод, если он доступен
        if self.parent and hasattr(self.parent, 'create_matches_for_semi_final'):
            self.parent.create_matches_for_semi_final(1, sf_groups, stage_name)
        else:
            # Fallback – упрощённая версия (без переноса результатов)
            self.create_matches_for_semi_final_local(semi_num, sf_groups, stage_name)

        # Обновляем Choice после изменений
        self.update_choice_after_changes()

    def recreate_matches_for_stage(self, stage_name):
        """Пересоздание матчей для этапа после изменений"""
        system = System.get_or_none(
            (System.title_id == self.title_id) &
            (System.sex == self.current_sex) &
            (System.stage == stage_name)
        )
        if not system:
            return

        game_players = Game_list.select().where(
            (Game_list.title_id == self.title_id) &
            (Game_list.system_id == system.id)
        ).order_by(Game_list.number_group, Game_list.rank_num_player)

        if game_players.count() == 0:
            return

        # === НОВАЯ ПРОВЕРКА ДЛЯ ПОЛУФИНАЛОВ ===
        if "полуфинал" in stage_name.lower():
            self.recreate_semifinal_matches(system, game_players, stage_name)
            return

        # Остальной код для круговой/олимпийской системы
        type_table = system.type_table
        if "Круговая" in type_table or system.type_table == "Круговая":
            self.recreate_round_robin_matches(system, game_players)
        else:
            self.recreate_olympic_matches(system, game_players)
# =======================
def show_edit_stages_dialog(parent=None, title_id=None):
    """Функция для вызова диалога редактирования этапов"""
    dialog = EditStagesDialog(parent, title_id)
    return dialog.exec_()
# Добавляем в главное меню
def add_edit_stages_menu_item(menu_bar, parent_window):
    """Добавление пункта меню 'Редактирование этапов'"""
    edit_menu = menu_bar.addMenu("Редактировать")
    
    edit_stages_action = QAction("Редактирование этапов", parent_window)
    edit_stages_action.triggered.connect(
        lambda: show_edit_stages_dialog(parent_window, parent_window.current_title_id)
    )
    edit_menu.addAction(edit_stages_action)
    
    return edit_menu