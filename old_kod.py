import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTabWidget, QTableView, QMenuBar, QAction, QLabel,
    QFrame, QSizePolicy, QMessageBox, QListWidget, QListWidgetItem,
    QLineEdit, QDateEdit, QComboBox, QGroupBox, QFormLayout,
    QScrollArea, QSplitter, QInputDialog, QHeaderView, QAbstractItemView
)
from PyQt5.QtWidgets import QGridLayout  # Добавьте в импорт
from PyQt5.QtCore import Qt, QDate, QSize
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import QTimer

from models import connect_db, close_db
from models import *
from models_qt import (
    PlayersTableModel, TeamsTableModel, ResultsTableModel, 
    DoublePlayersTableModel, TitlesTableModel, CoachesTableModel
)
from datetime import datetime
from datetime import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Панель управления соревнованиями")
        self.setGeometry(100, 100, 1500, 780)
        self.setMinimumSize(1200, 600)
        
        # Подключение к БД
        self.db = connect_db()
        
        # Текущее соревнование
        self.current_title_id = None
        self.current_sex = None
        
        # Загрузка моделей
        self.players_model = PlayersTableModel()
        self.teams_model = TeamsTableModel()
        self.results_model = ResultsTableModel()
        self.double_players_model = DoublePlayersTableModel()
        
        # Данные для comboBox
        self.load_combo_data()
        self.load_referees_list()
        
        # Контекст левой панели с действиями для каждой вкладки
        self.tab_context = {
            0: {"title": "Титул", "description": "Управление информацией о соревновании",
                "buttons": ["💾 Сохранить", "🗑️ Очистить", "📋 Создать новое"]},
            1: {"title": "Участники", "description": "Управление списком участников",
                "buttons": ["➕ Добавить", "✏️ Редактировать", "🗑️ Удалить", "🔍 Поиск", "📤 Экспорт"]},
            2: {"title": "Команды", "description": "Управление командами",
                "buttons": ["➕ Добавить", "✏️ Редактировать", "🗑️ Удалить", "⭐ Рейтинг"]},
            3: {"title": "Пары", "description": "Формирование пар",
                "buttons": ["🎲 Сформировать", "🔄 Разбить", "📊 Посев"]},
            4: {"title": "Система", "description": "Настройки системы проведения",
                "buttons": ["⚙️ Настройки", "📐 Параметры", "🔄 Сброс"]},
            5: {"title": "Результаты", "description": "Ввод и просмотр результатов",
                "buttons": ["📥 Загрузить", "📤 Экспорт", "🗑️ Очистить", "🧮 Рассчитать"]},
            6: {"title": "Рейтинг", "description": "Рейтинг участников",
                "buttons": ["🔄 Обновить", "🏆 Топ-10", "📊 Расчёт"]},
            7: {"title": "Дополнительно", "description": "Дополнительные настройки",
                "buttons": ["📝 Заметки", "❓ Справка", "ℹ️ О программе"]},
        }
        
        self.current_competition_buttons = []
        self.current_tab_index = 0
        self.is_fullscreen = False
        
        # Для редактирования участников
        self.editing_player_id = None
        # Инициализация интерфейса
        self.init_ui()
        
        # Загрузка списка соревнований
        self.load_titles_list()

    def resize_table_for_participants(self):
        """Увеличивает таблицу до 85% высоты для вкладки Участники"""
        if hasattr(self, 'main_splitter'):
            # Получаем общую высоту сплиттера
            total_height = self.main_splitter.height()
            if total_height > 0:
                # Устанавливаем: верхняя часть 15%, таблица 85% (ещё больше места для таблицы)
                self.main_splitter.setSizes([int(total_height * 0.15), int(total_height * 0.85)])
                # Принудительно обновляем
                self.main_splitter.update()
                self.main_splitter.setCollapsible(0, False)  # Запрещаем сворачивание верхней части
                self.main_splitter.setCollapsible(1, False)  # Запрещаем сворачивание таблицы
                
                # Обновляем заголовок таблицы
                if self.current_title_id:
                    title = Title.get_or_none(Title.id == self.current_title_id)
                    if title:
                        sex_text = "Девушки" if self.current_sex == "Ж" else "Юноши" if self.current_sex == "М" else "Все участники"
                        count = self.players_model.rowCount()
                        self.table_header.setText(f"👥 {title.name} - {sex_text} ({count} чел.)")
                self.table_header.setVisible(True)
                
                # Настраиваем таблицу для лучшего отображения
                self.table_view.setMinimumHeight(int(total_height * 0.8))

    def resize_table_normal(self):
        """Восстанавливает нормальные размеры сплиттера для других вкладок"""
        if hasattr(self, 'main_splitter'):
            total_height = self.main_splitter.height()
            if total_height > 0:
                # Устанавливаем: верхняя часть 40%, таблица 60%
                self.main_splitter.setSizes([int(total_height * 0.4), int(total_height * 0.6)])
                self.main_splitter.update()
                self.main_splitter.setCollapsible(0, True)
                self.main_splitter.setCollapsible(1, True)
                
                # Сбрасываем минимальную высоту таблицы
                self.table_view.setMinimumHeight(0)

    def resizeEvent(self, event):
        """Обработчик изменения размера окна - сохраняем пропорции при изменении размера"""
        super().resizeEvent(event)
        
        # Если текущая вкладка - Участники, обновляем пропорции сплиттера
        if hasattr(self, 'current_tab_index'):
            if self.current_tab_index == 1 and hasattr(self, 'main_splitter'):
                total_height = self.main_splitter.height()
                if total_height > 0:
                    self.main_splitter.setSizes([int(total_height * 0.15), int(total_height * 0.85)])
            elif hasattr(self, 'main_splitter'):
                total_height = self.main_splitter.height()
                if total_height > 0:
                    self.main_splitter.setSizes([int(total_height * 0.4), int(total_height * 0.6)])

    def load_teams_for_title(self):
        """Загрузка команд для выбранного соревнования"""
        if not self.current_title_id:
            self.teams_model.setData([])
            return
        
        try:
            query = Team.select().where(Team.title_id == self.current_title_id)
            teams_data = []
            for team in query:
                teams_data.append({
                    'id': team.id,
                    'team_name': team.team_name or "",
                    'region': team.region or "",
                    'coach_team': team.coach_team or "",
                    'r_sum': team.r_sum or 0
                })
            self.teams_model.setData(teams_data)
            self.table_view.setModel(self.teams_model)
            self.table_header.setText(f"🏆 Команды - {len(teams_data)} шт.")
        except Exception as e:
            print(f"Ошибка загрузки команд: {e}")

    def load_doubles_for_title(self):
        """Загрузка пар для выбранного соревнования"""
        if not self.current_title_id:
            self.double_players_model.setData([])
            return
        
        try:
            query = Players_double.select().where(Players_double.title_id == self.current_title_id)
            doubles_data = []
            for double in query:
                doubles_data.append({
                    'id': double.id,
                    'player1': double.player_1 or "",
                    'player2': double.player_2 or "",
                    'region': double.region_main or "",
                    'r_sum': double.r_sum or 0,
                    'posev': double.posev or 0,
                    'mesto': double.mesto or 0
                })
            self.double_players_model.setData(doubles_data)
            self.table_view.setModel(self.double_players_model)
            self.table_header.setText(f"🤝 Пары - {len(doubles_data)} шт.")
        except Exception as e:
            print(f"Ошибка загрузки пар: {e}")

    def load_results_for_title(self):
        """Загрузка результатов для выбранного соревнования"""
        if not self.current_title_id:
            self.results_model.setData([])
            return
        
        try:
            query = Result.select().where(Result.title_id == self.current_title_id)
            results_data = []
            for result in query:
                results_data.append({
                    'id': result.id,
                    'player1': result.player1 or "",
                    'player2': result.player2 or "",
                    'winner': result.winner or "",
                    'score': result.score_in_game or "",
                    'round': result.round or ""
                })
            self.results_model.setData(results_data)
            self.table_view.setModel(self.results_model)
            self.table_header.setText(f"📊 Результаты - {len(results_data)} записей")
        except Exception as e:
            print(f"Ошибка загрузки результатов: {e}")

    def load_combo_data(self):
        """Загрузка данных для comboBox"""
        self.coaches_list = [(c.id, c.coach) for c in Coach.select().order_by(Coach.coach)]
        self.patronymics_list = [(p.id, p.patronymic, p.sex) for p in Patronymic.select().order_by(Patronymic.patronymic)]
        self.regions_list = [(r.id, r.region) for r in Region.select().order_by(Region.region)]
    
    def load_referees_list(self):
        """Загрузка списка судей из БД"""
        try:
            from models import Referee
            referees = Referee.select().order_by(Referee.family)
            self.referees_list = [(r.id, r.family, r.category) for r in referees]
        except:
            # Тестовые данные
            self.referees_list = [
                (1, "Иванов И.И.", "ВК"),
                (2, "Петров П.П.", "1К"),
                (3, "Сидоров С.С.", "2К"),
                (4, "Кузнецова А.А.", "1К"),
                (5, "Смирнова Е.В.", "ВК"),
            ]
    
    def load_titles_list(self):
        """Загрузка списка соревнований в QListWidget"""
        self.list_widget.clear()
        titles = Title.select().order_by(Title.data_start.desc())
        for title in titles:
            start_date = title.data_start.strftime("%d.%m.%Y") if title.data_start else "---"
            
            item_text = f"""🏆 {title.name}
   📅 {start_date} | {title.mesto}
   👥 {title.sredi} | {title.vozrast}
   🏷️ {title.vid_turnira}"""
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, title.id)
            item.setSizeHint(QSize(0, 65))
            self.list_widget.addItem(item)

    def init_ui(self):
        """Инициализация интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ========== Левая панель ==========
        self.left_panel = QFrame()
        self.left_panel.setFrameShape(QFrame.StyledPanel)
        self.left_panel.setMinimumWidth(280)
        self.left_panel.setMaximumWidth(350)
        self.left_panel.setStyleSheet("background-color: #f5f5f5;")
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setAlignment(Qt.AlignTop)
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(8, 8, 8, 8)
        
        # Кнопки соревнований (девушки/юноши)
        comp_label = QLabel("🏅 Тип соревнования:")
        comp_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #333;")
        left_layout.addWidget(comp_label)
        
        self.competition_buttons_layout = QHBoxLayout()
        self.competition_buttons_layout.setAlignment(Qt.AlignLeft)
        self.competition_buttons_layout.setSpacing(5)
        left_layout.addLayout(self.competition_buttons_layout)
        
        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #ccc; max-height: 1px;")
        left_layout.addWidget(line)
        
        # Заголовок текущего действия
        self.action_title = QLabel("🔧 Действия")
        self.action_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #4CAF50; margin-top: 5px;")
        left_layout.addWidget(self.action_title)
        
        self.action_description = QLabel("Выберите вкладку для отображения действий")
        self.action_description.setStyleSheet("font-size: 10px; color: #666; margin-bottom: 10px;")
        self.action_description.setWordWrap(True)
        left_layout.addWidget(self.action_description)
        
        # Контейнер для кнопок действий
        self.dynamic_filters_widget = QWidget()
        self.dynamic_filters_layout = QVBoxLayout(self.dynamic_filters_widget)
        self.dynamic_filters_layout.setAlignment(Qt.AlignTop)
        self.dynamic_filters_layout.setSpacing(6)
        self.dynamic_filters_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.dynamic_filters_widget)
        left_layout.addStretch()
        
        # ========== Правая область ==========
        right_area = QWidget()
        right_layout = QVBoxLayout(right_area)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # Верхняя часть с вкладками и списком
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(5, 5, 5, 5)
        top_layout.setSpacing(5)
        
        # Вкладки
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { 
                border: 1px solid #ccc; 
                top: -1px;
                background-color: white;
            }
            QTabBar::tab { 
                padding: 4px 10px; 
                margin-right: 2px; 
                font-size: 11px;
                min-width: 70px;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
        """)
        
        # Создаем все вкладки
        title_tab = self.create_title_tab()
        participants_tab = self.create_participants_tab()
        teams_tab = self.create_teams_tab()
        doubles_tab = self.create_doubles_tab()
        system_tab = self.create_system_tab()
        results_tab = self.create_results_tab()
        rating_tab = self.create_rating_tab()
        extra_tab = self.create_extra_tab()
        
        # Добавляем вкладки
        self.tab_widget.addTab(title_tab, "📋 Титул")
        self.tab_widget.addTab(participants_tab, "👥 Участники")
        self.tab_widget.addTab(teams_tab, "🏆 Команды")
        self.tab_widget.addTab(doubles_tab, "🤝 Пары")
        self.tab_widget.addTab(system_tab, "⚙️ Система")
        self.tab_widget.addTab(results_tab, "📊 Результаты")
        self.tab_widget.addTab(rating_tab, "⭐ Рейтинг")
        self.tab_widget.addTab(extra_tab, "ℹ️ Дополнительно")
        
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        top_layout.addWidget(self.tab_widget)
        
        # Правая панель со списком соревнований
        right_panel = QWidget()
        right_panel.setMaximumWidth(380)
        right_panel.setMinimumWidth(320)
        right_panel_layout = QVBoxLayout(right_panel)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        right_panel_layout.setSpacing(3)
        
        # Подпись к списку
        self.list_label = QLabel("🏆 Прошедшие соревнования")
        self.list_label.setStyleSheet("""
            background-color: #4CAF50;
            color: white;
            padding: 6px;
            font-weight: bold;
            font-size: 11px;
            border-radius: 3px;
        """)
        self.list_label.setAlignment(Qt.AlignCenter)
        right_panel_layout.addWidget(self.list_label)
        
        # Список соревнований
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                font-size: 10px;
                font-family: Segoe UI, Consolas;
                background-color: #fafafa;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e0e0e0;
            }
        """)
        self.list_widget.itemClicked.connect(self.on_title_selected)
        right_panel_layout.addWidget(self.list_widget)
        
        top_layout.addWidget(self.tab_widget)
        top_layout.addWidget(right_panel)
        top_layout.setStretch(0, 1)  # Вкладки занимают 2 части
        top_layout.setStretch(1, 2)  # Список занимает 1 часть
        
        # ========== Нижняя часть с таблицей ==========
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(5, 5, 5, 5)
        bottom_layout.setSpacing(5)
        
        # Заголовок таблицы
        self.table_header = QLabel("👥 Список участников")
        self.table_header.setStyleSheet("""
            background-color: #2196F3;
            color: white;
            padding: 8px;
            font-weight: bold;
            font-size: 12px;
            border-radius: 3px;
        """)
        bottom_layout.addWidget(self.table_header)
        
        # Таблица участников
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setShowGrid(True)
        self.table_view.setStyleSheet("""
            QTableView {
                font-size: 11px;
                gridline-color: #ddd;
                selection-background-color: #a0c4ff;
            }
            QTableView::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                font-weight: bold;
                font-size: 11px;
                border: none;
            }
            QHeaderView::section:hover {
                background-color: #1976D2;
            }
        """)
        
        # Устанавливаем модель
        self.table_view.setModel(self.players_model)
        
        # Настройка колонок
        self.table_view.setColumnHidden(0, True)  # Скрываем ID
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.verticalHeader().setDefaultSectionSize(28)
        
        # Устанавливаем ширину колонок
        self.table_view.setColumnWidth(1, 180)  # ФИО
        self.table_view.setColumnWidth(2, 120)  # Отчество
        self.table_view.setColumnWidth(3, 100)  # Дата рождения
        self.table_view.setColumnWidth(4, 70)   # Рейтинг
        self.table_view.setColumnWidth(5, 120)  # Город
        self.table_view.setColumnWidth(6, 120)  # Регион
        self.table_view.setColumnWidth(7, 100)  # Разряд
        self.table_view.setColumnWidth(8, 150)  # Тренер
        
        bottom_layout.addWidget(self.table_view)
        
        # Создаем сплиттер и сохраняем ссылки на виджеты
        self.main_splitter = QSplitter(Qt.Vertical)
        self.main_splitter.addWidget(top_widget)
        self.main_splitter.addWidget(bottom_widget)
        self.main_splitter.setSizes([300, 480])  # Начальные размеры
        self.main_splitter.setHandleWidth(3)
        
        # Сохраняем ссылки на виджеты для доступа из других методов
        self.top_widget = top_widget
        self.bottom_widget = bottom_widget
        self.top_layout = top_layout
        
        right_layout.addWidget(self.main_splitter)
        
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(right_area, 1)
        
        self.create_menu_bar()
        self.update_left_panel_for_tab(0)

    def create_title_tab(self):
        """Вкладка Титул с полной информацией о соревновании"""
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Стиль для полей
        input_style = """
            QLineEdit, QComboBox, QDateEdit {
                max-height: 28px;
                padding: 3px 5px;
                font-size: 10px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                border: 1px solid #4CAF50;
            }
        """
        
        # Группа 1: Основная информация
        main_group = QGroupBox()
        main_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #4CAF50;
                border-radius: 5px;
                margin-top: 12px;
                background-color: #f9f9f9;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #4CAF50;
            }
        """)
        main_group.setTitle("📋 Основная информация")
        main_group_layout = QFormLayout(main_group)
        main_group_layout.setSpacing(8)
        main_group_layout.setContentsMargins(10, 15, 10, 10)
        
        self.comp_name_edit = QLineEdit()
        self.comp_name_edit.setPlaceholderText("Введите название соревнования")
        self.comp_name_edit.setStyleSheet(input_style)
        main_group_layout.addRow("Название соревнования:", self.comp_name_edit)
        
        self.comp_sredi_combo = QComboBox()
        self.comp_sredi_combo.addItems(["мальчики и девочки", "юноши и девушки", "юниоры и юниорки", "мужчины и женщины"])
        self.comp_sredi_combo.setStyleSheet(input_style)
        main_group_layout.addRow("Среди:", self.comp_sredi_combo)
        
        self.comp_vozrast_combo = QComboBox()
        self.comp_vozrast_combo.addItems(["до 12 лет", "до 14 лет", "до 16 лет", "до 18 лет", "до 20 лет", "до 22 лет", "22 года и старше"])
        self.comp_vozrast_combo.setStyleSheet(input_style)
        main_group_layout.addRow("Возраст участников:", self.comp_vozrast_combo)
        
        main_layout.addWidget(main_group)
        
        # Группа 2: Сроки проведения
        dates_group = QGroupBox()
        dates_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #FF9800;
                border-radius: 5px;
                margin-top: 12px;
                background-color: #f9f9f9;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #FF9800;
            }
        """)
        dates_group.setTitle("📅 Сроки проведения")
        dates_group_layout = QFormLayout(dates_group)
        dates_group_layout.setSpacing(8)
        dates_group_layout.setContentsMargins(10, 15, 10, 10)
        
        self.comp_start_date = QDateEdit()
        self.comp_start_date.setDate(QDate.currentDate())
        self.comp_start_date.setCalendarPopup(True)
        self.comp_start_date.setDisplayFormat("dd.MM.yyyy")
        self.comp_start_date.setStyleSheet(input_style)
        dates_group_layout.addRow("Дата начала:", self.comp_start_date)
        
        self.comp_end_date = QDateEdit()
        self.comp_end_date.setDate(QDate.currentDate().addDays(7))
        self.comp_end_date.setCalendarPopup(True)
        self.comp_end_date.setDisplayFormat("dd.MM.yyyy")
        self.comp_end_date.setStyleSheet(input_style)
        dates_group_layout.addRow("Дата окончания:", self.comp_end_date)
        
        main_layout.addWidget(dates_group)
        
        # Группа 3: Место проведения
        place_group = QGroupBox()
        place_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #2196F3;
                border-radius: 5px;
                margin-top: 12px;
                background-color: #f9f9f9;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #2196F3;
            }
        """)
        place_group.setTitle("📍 Место проведения")
        place_group_layout = QFormLayout(place_group)
        place_group_layout.setSpacing(8)
        place_group_layout.setContentsMargins(10, 15, 10, 10)
        
        self.comp_city_edit = QLineEdit()
        self.comp_city_edit.setPlaceholderText("Введите город")
        self.comp_city_edit.setStyleSheet(input_style)
        place_group_layout.addRow("Город:", self.comp_city_edit)
        
        self.comp_mesto_edit = QLineEdit()
        self.comp_mesto_edit.setPlaceholderText("Название спорткомплекса / зала")
        self.comp_mesto_edit.setStyleSheet(input_style)
        place_group_layout.addRow("Место проведения:", self.comp_mesto_edit)
        
        main_layout.addWidget(place_group)
        
        # Группа 4: Судейская коллегия
        referees_group = QGroupBox()
        referees_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #9C27B0;
                border-radius: 5px;
                margin-top: 12px;
                background-color: #f9f9f9;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #9C27B0;
            }
        """)
        referees_group.setTitle("⚖️ Главная судейская коллегия")
        referees_group_layout = QFormLayout(referees_group)
        referees_group_layout.setSpacing(8)
        referees_group_layout.setContentsMargins(10, 15, 10, 10)
        
        # Главный судья - QLineEdit с автоподстановкой
        self.main_referee_edit = QLineEdit()
        self.main_referee_edit.setPlaceholderText("Введите фамилию и инициалы главного судьи")
        self.main_referee_edit.setStyleSheet(input_style)
        self.main_referee_edit.textChanged.connect(self.on_referee_text_changed)
        referees_group_layout.addRow("Главный судья:", self.main_referee_edit)
        
        # Категория судьи (автоматически подставляется)
        self.referee_category_combo = QComboBox()
        self.referee_category_combo.addItems(["ВК (Всероссийская категория)", "1К (Первая категория)", "2К (Вторая категория)", "3К (Третья категория)"])
        self.referee_category_combo.setStyleSheet(input_style)
        referees_group_layout.addRow("Категория судьи:", self.referee_category_combo)
        
        # Главный секретарь - QLineEdit с автоподстановкой
        self.main_secretary_edit = QLineEdit()
        self.main_secretary_edit.setPlaceholderText("Введите фамилию и инициалы главного секретаря")
        self.main_secretary_edit.setStyleSheet(input_style)
        self.main_secretary_edit.textChanged.connect(self.on_secretary_text_changed)
        referees_group_layout.addRow("Главный секретарь:", self.main_secretary_edit)
        
        # Категория секретаря (автоматически подставляется)
        self.secretary_category_combo = QComboBox()
        self.secretary_category_combo.addItems(["ВК (Всероссийская категория)", "1К (Первая категория)", "2К (Вторая категория)", "3К (Третья категория)"])
        self.secretary_category_combo.setStyleSheet(input_style)
        referees_group_layout.addRow("Категория секретаря:", self.secretary_category_combo)
        
        main_layout.addWidget(referees_group)
        main_layout.addStretch()
        
        return tab_widget

    def on_referee_text_changed(self, text):
        """Поиск судьи в БД при вводе текста"""
        if len(text) >= 3:  # Начинаем поиск после 3 символов
            self.find_referee_in_db(text, self.referee_category_combo)

    def on_secretary_text_changed(self, text):
        """Поиск секретаря в БД при вводе текста"""
        if len(text) >= 3:
            self.find_referee_in_db(text, self.secretary_category_combo)

    def find_referee_in_db(self, search_text, category_combo):
        """Поиск судьи в базе данных"""
        try:
            from models import Referee
            
            # Ищем судью по фамилии (частичное совпадение)
            referees = Referee.select().where(Referee.family.contains(search_text))
            
            if referees.count() > 0:
                # Нашли судью, подставляем его категорию
                referee = referees.first()
                
                # Устанавливаем категорию в comboBox
                category_text = self.get_category_display(referee.category)
                index = category_combo.findText(category_text)
                if index >= 0:
                    category_combo.setCurrentIndex(index)
                
                # Показываем подсказку
                self.show_referee_tooltip(referee.family, referee.category)
            else:
                # Не нашли - сбрасываем категорию
                category_combo.setCurrentIndex(0)
                
        except Exception as e:
            print(f"Ошибка поиска судьи: {e}")

    def get_category_display(self, category_code):
        """Преобразование кода категории в отображаемый текст"""
        category_map = {
            'ВК': 'ВК (Всероссийская категория)',
            '1К': '1К (Первая категория)',
            '2К': '2К (Вторая категория)',
            '3К': '3К (Третья категория)',
            'Всероссийская': 'ВК (Всероссийская категория)',
            'Первая': '1К (Первая категория)',
            'Вторая': '2К (Вторая категория)',
            'Третья': '3К (Третья категория)'
        }
        return category_map.get(category_code, 'ВК (Всероссийская категория)')

    def get_category_code(self, display_text):
        """Преобразование отображаемого текста в код категории"""
        code_map = {
            'ВК (Всероссийская категория)': 'ВК',
            '1К (Первая категория)': '1К',
            '2К (Вторая категория)': '2К',
            '3К (Третья категория)': '3К'
        }
        return code_map.get(display_text, 'ВК')

    def show_referee_tooltip(self, full_name, category):
        """Показать всплывающую подсказку с информацией о найденном судье"""
        # Можно показать временное сообщение или установить tooltip
        pass  # Опционально

    def save_title_info(self):
        """Сохранение информации о соревновании"""
        if not self.comp_name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите название соревнования")
            return
        
        if not self.comp_city_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите город проведения")
            return
        
        # Получаем данные из формы
        title_data = {
            'name': self.comp_name_edit.text().strip(),
            'sredi': self.comp_sredi_combo.currentText(),
            'vozrast': self.comp_vozrast_combo.currentText(),
            'data_start': self.comp_start_date.date().toPyDate(),
            'data_end': self.comp_end_date.date().toPyDate(),
            'mesto': self.comp_mesto_edit.text().strip(),
            'city': self.comp_city_edit.text().strip(),
            'referee': self.main_referee_edit.text().strip(),
            'kat_ref': self.get_category_code(self.referee_category_combo.currentText()),
            'secretary': self.main_secretary_edit.text().strip(),
            'kat_sec': self.get_category_code(self.secretary_category_combo.currentText()),
            'vid_turnira': "Личное",
            'full_name_comp': self.comp_name_edit.text().strip(),
            'short_name_comp': self.comp_name_edit.text().strip()[:50],
            'tab_enabled': "1",
            'multiregion': 0,
            'perenos': 0,
            'otchestvo': 0,
            'r_date': ""
        }
        
        try:
            # Сохраняем или обновляем судью в базе данных
            self.save_or_update_referee(
                self.main_referee_edit.text().strip(),
                self.get_category_code(self.referee_category_combo.currentText())
            )
            self.save_or_update_referee(
                self.main_secretary_edit.text().strip(),
                self.get_category_code(self.secretary_category_combo.currentText())
            )
            
            if self.current_title_id:
                # Обновляем существующее соревнование
                query = Title.update(**title_data).where(Title.id == self.current_title_id)
                query.execute()
                QMessageBox.information(self, "Успех", "Информация о соревновании обновлена")
            else:
                # Создаем новое соревнование
                title = Title.create(**title_data)
                self.current_title_id = title.id
                QMessageBox.information(self, "Успех", f"Соревнование '{title_data['name']}' создано")
                
            # Обновляем список соревнований
            self.load_titles_list()
            
            # Обновляем отображение в списке
            self.list_label.setText(f"🏆 Текущее соревнование: {title_data['name'][:30]}...")
            self.list_label.setStyleSheet("""
                background-color: #2196F3;
                color: white;
                padding: 6px;
                font-weight: bold;
                font-size: 11px;
                border-radius: 3px;
            """)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить данные: {str(e)}")

    def save_or_update_referee(self, full_name, category):
        """Сохраняет или обновляет судью в базе данных"""
        if not full_name:
            return None
        
        try:
            from models import Referee
            
            # Ищем судью по фамилии
            referee = Referee.get_or_none(Referee.family == full_name)
            
            if referee:
                # Обновляем категорию, если она изменилась
                if referee.category != category:
                    referee.category = category
                    referee.save()
                return referee.id
            else:
                # Создаем нового судью
                new_referee = Referee.create(
                    family=full_name,
                    city="",
                    category=category,
                    signature=None
                )
                return new_referee.id
        except Exception as e:
            print(f"Ошибка сохранения судьи: {e}")
            return None

    def load_title_data(self):
        """Загрузка данных соревнования для редактирования"""
        try:
            title = Title.get_or_none(Title.id == self.current_title_id)
            if title:
                self.comp_name_edit.setText(title.name or "")
                
                # Устанавливаем значение в comboBox "Среди"
                index = self.comp_sredi_combo.findText(title.sredi or "")
                if index >= 0:
                    self.comp_sredi_combo.setCurrentIndex(index)
                
                # Устанавливаем значение в comboBox "Возраст"
                index = self.comp_vozrast_combo.findText(title.vozrast or "")
                if index >= 0:
                    self.comp_vozrast_combo.setCurrentIndex(index)
                
                # Устанавливаем даты
                if title.data_start:
                    self.comp_start_date.setDate(QDate(
                        title.data_start.year,
                        title.data_start.month,
                        title.data_start.day
                    ))
                if title.data_end:
                    self.comp_end_date.setDate(QDate(
                        title.data_end.year,
                        title.data_end.month,
                        title.data_end.day
                    ))
                # === исправил загрузку города и места ====
                mesto_txt = title.mesto
                mark = mesto_txt.find("/")
                
                if mark == -1:
                    self.comp_city_edit.setText(mesto_txt or "")
                else: 
                    mesto = mesto_txt[mark + 1:]
                    city = mesto_txt[:mark] 
                    self.comp_city_edit.setText(city or "")                 
                    self.comp_mesto_edit.setText(mesto or "")
                
                # Загрузка главного судьи
                self.main_referee_edit.setText(title.referee or "")
                
                # Загрузка категории судьи
                category_text = self.get_category_display(title.kat_ref or "ВК")
                index = self.referee_category_combo.findText(category_text)
                if index >= 0:
                    self.referee_category_combo.setCurrentIndex(index)
                
                # Загрузка главного секретаря
                self.main_secretary_edit.setText(title.secretary or "")
                
                # Загрузка категории секретаря
                category_text = self.get_category_display(title.kat_sec or "ВК")
                index = self.secretary_category_combo.findText(category_text)
                if index >= 0:
                    self.secretary_category_combo.setCurrentIndex(index)
                    
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")

    def clear_title_form(self):
        """Очистка формы титула"""
        self.comp_name_edit.clear()
        self.comp_sredi_combo.setCurrentIndex(0)
        self.comp_vozrast_combo.setCurrentIndex(0)
        self.comp_start_date.setDate(QDate.currentDate())
        self.comp_end_date.setDate(QDate.currentDate().addDays(7))
        self.comp_city_edit.clear()
        self.comp_mesto_edit.clear()
        self.main_referee_edit.clear()
        self.main_secretary_edit.clear()
        self.referee_category_combo.setCurrentIndex(0)
        self.secretary_category_combo.setCurrentIndex(0) 

    def create_participants_tab(self):
        """Вкладка участников - компактное расположение полей в 3 ряда, грид 3x5"""
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Стиль для полей ввода
        input_style = """
            QLineEdit, QDateEdit {
                max-height: 28px;
                min-height: 24px;
                padding: 2px 4px;
                font-size: 10px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QLabel {
                font-size: 10px;
                font-weight: bold;
            }
        """
        
        # Создаем форму с сеткой 3x5
        form_widget = QWidget()
        form_widget.setMaximumHeight(140)
        form_layout = QGridLayout(form_widget)
        form_layout.setSpacing(6)
        form_layout.setContentsMargins(5, 5, 5, 5)
        
        # ========== Ряд 1 ==========
        # ФИО (занимает 2 столбца)
        label_fio = QLabel("ФИО:")
        label_fio.setStyleSheet("font-weight: bold;")
        form_layout.addWidget(label_fio, 0, 0)
        self.fio_edit = QLineEdit()
        self.fio_edit.setPlaceholderText("Иванов Иван")
        self.fio_edit.setStyleSheet(input_style)
        form_layout.addWidget(self.fio_edit, 0, 1, 1, 2)  # spans 2 columns
        
        # Отчество (занимает 2 столбца)
        label_patronymic = QLabel("Отчество:")
        label_patronymic.setStyleSheet("font-weight: bold;")
        form_layout.addWidget(label_patronymic, 0, 3)
        self.patronymic_edit = QLineEdit()  # Заменяем QComboBox на QLineEdit
        self.patronymic_edit.setPlaceholderText("Иванович")
        self.patronymic_edit.setStyleSheet(input_style)
        form_layout.addWidget(self.patronymic_edit, 0, 4, 1, 2)  # spans 2 columns
        
        # Дата рождения (1 столбец)
        label_birth = QLabel("Дата рожд.:")
        label_birth.setStyleSheet("font-weight: bold;")
        form_layout.addWidget(label_birth, 0, 6)
        self.birth_date = QDateEdit()
        self.birth_date.setDate(QDate.currentDate().addYears(-18))
        self.birth_date.setCalendarPopup(True)
        self.birth_date.setDisplayFormat("dd.MM.yyyy")
        self.birth_date.setStyleSheet(input_style)
        form_layout.addWidget(self.birth_date, 0, 7)
        
        # ========== Ряд 2 ==========
        # Рейтинг (1 столбец)
        label_rank = QLabel("Рейтинг:")
        label_rank.setStyleSheet("font-weight: bold;")
        form_layout.addWidget(label_rank, 1, 0)
        self.rank_edit = QLineEdit()
        self.rank_edit.setPlaceholderText("0")
        self.rank_edit.setStyleSheet(input_style)
        form_layout.addWidget(self.rank_edit, 1, 1)
        
        # Город (2 столбца)
        label_city = QLabel("Город:")
        label_city.setStyleSheet("font-weight: bold;")
        form_layout.addWidget(label_city, 1, 2)
        self.city_edit = QLineEdit()
        self.city_edit.setPlaceholderText("Москва")
        self.city_edit.setStyleSheet(input_style)
        form_layout.addWidget(self.city_edit, 1, 3, 1, 2)  # spans 2 columns
        
        # Регион (2 столбца)
        label_region = QLabel("Регион:")
        label_region.setStyleSheet("font-weight: bold;")
        form_layout.addWidget(label_region, 1, 5)
        self.region_edit = QLineEdit()  # Заменяем QComboBox на QLineEdit
        self.region_edit.setPlaceholderText("Московская область")
        self.region_edit.setStyleSheet(input_style)
        form_layout.addWidget(self.region_edit, 1, 6, 1, 2)  # spans 2 columns
        
        # ========== Ряд 3 ==========
        # Разряд (1 столбец)
        label_razryad = QLabel("Разряд:")
        label_razryad.setStyleSheet("font-weight: bold;")
        form_layout.addWidget(label_razryad, 2, 0)
        self.razryad_edit = QLineEdit()
        self.razryad_edit.setPlaceholderText("КМС")
        self.razryad_edit.setStyleSheet(input_style)
        form_layout.addWidget(self.razryad_edit, 2, 1)
        
        # Тренеры (3 столбца)
        label_coach = QLabel("Тренеры:")
        label_coach.setStyleSheet("font-weight: bold;")
        form_layout.addWidget(label_coach, 2, 2)
        self.coach_edit = QLineEdit()  # Заменяем QComboBox на QLineEdit
        self.coach_edit.setPlaceholderText("Иванов И.И., Петров П.П.")
        self.coach_edit.setStyleSheet(input_style)
        form_layout.addWidget(self.coach_edit, 2, 3, 1, 3)  # spans 3 columns
        
        # Пол (1 столбец)
        label_sex = QLabel("Пол:")
        label_sex.setStyleSheet("font-weight: bold;")
        form_layout.addWidget(label_sex, 2, 6)
        self.sex_combo = QComboBox()
        self.sex_combo.addItems(["Мужской", "Женский"])
        self.sex_combo.setStyleSheet(input_style)
        form_layout.addWidget(self.sex_combo, 2, 7)
        
        # Настройка растяжения колонок
        form_layout.setColumnStretch(1, 1)  # Рейтинг
        form_layout.setColumnStretch(2, 0)  # Метка города
        form_layout.setColumnStretch(4, 1)  # Город (часть)
        form_layout.setColumnStretch(6, 0)  # Метка региона
        form_layout.setColumnStretch(7, 1)  # Регион
        
        main_layout.addWidget(form_widget)
        main_layout.addStretch()
        
        return tab_widget

    def create_teams_tab(self):
        """Вкладка команд"""
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        input_style = """
            QLineEdit, QComboBox {
                max-height: 26px;
                padding: 3px 5px;
                font-size: 10px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QLabel {
                font-size: 10px;
            }
        """
        
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(8)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        self.team_name_edit = QLineEdit()
        self.team_name_edit.setPlaceholderText("Название команды")
        self.team_name_edit.setMaximumHeight(26)
        self.team_name_edit.setStyleSheet(input_style)
        form_layout.addRow("Название:", self.team_name_edit)
        
        self.team_region_combo = QComboBox()
        self.team_region_combo.addItem("", None)
        for rid, rname in self.regions_list:
            self.team_region_combo.addItem(rname, rid)
        self.team_region_combo.setMaximumHeight(26)
        self.team_region_combo.setStyleSheet(input_style)
        form_layout.addRow("Регион:", self.team_region_combo)
        
        self.team_coach_edit = QLineEdit()
        self.team_coach_edit.setPlaceholderText("ФИО тренера")
        self.team_coach_edit.setMaximumHeight(26)
        self.team_coach_edit.setStyleSheet(input_style)
        form_layout.addRow("Тренер:", self.team_coach_edit)
        
        main_layout.addWidget(form_widget)
        main_layout.addStretch()
        
        return tab_widget

    def create_doubles_tab(self):
        """Вкладка пар"""
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        input_style = """
            QLineEdit, QComboBox {
                max-height: 26px;
                padding: 3px 5px;
                font-size: 10px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QLabel {
                font-size: 10px;
            }
        """
        
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(8)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        self.player1_edit = QLineEdit()
        self.player1_edit.setPlaceholderText("ФИО первого игрока")
        self.player1_edit.setMaximumHeight(26)
        self.player1_edit.setStyleSheet(input_style)
        form_layout.addRow("Игрок 1:", self.player1_edit)
        
        self.player2_edit = QLineEdit()
        self.player2_edit.setPlaceholderText("ФИО второго игрока")
        self.player2_edit.setMaximumHeight(26)
        self.player2_edit.setStyleSheet(input_style)
        form_layout.addRow("Игрок 2:", self.player2_edit)
        
        self.double_region_combo = QComboBox()
        self.double_region_combo.addItem("", None)
        for rid, rname in self.regions_list:
            self.double_region_combo.addItem(rname, rid)
        self.double_region_combo.setMaximumHeight(26)
        self.double_region_combo.setStyleSheet(input_style)
        form_layout.addRow("Регион:", self.double_region_combo)
        
        self.double_vid_combo = QComboBox()
        self.double_vid_combo.addItems(["Мужская", "Женская", "Смешанная"])
        self.double_vid_combo.setMaximumHeight(26)
        self.double_vid_combo.setStyleSheet(input_style)
        form_layout.addRow("Вид пары:", self.double_vid_combo)
        
        main_layout.addWidget(form_widget)
        main_layout.addStretch()
        
        return tab_widget

    def create_system_tab(self):
        """Вкладка Система"""
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        input_style = """
            QLineEdit, QComboBox {
                max-height: 26px;
                padding: 3px 5px;
                font-size: 10px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        
        group = QGroupBox("⚙️ Настройки системы проведения")
        group_layout = QFormLayout(group)
        group_layout.setSpacing(8)
        group_layout.setContentsMargins(10, 15, 10, 10)
        
        self.system_stage = QComboBox()
        self.system_stage.addItems(["Олимпийская", "Круговая", "Смешанная", "Швейцарская"])
        self.system_stage.setStyleSheet(input_style)
        group_layout.addRow("Система проведения:", self.system_stage)
        
        self.total_groups = QLineEdit()
        self.total_groups.setPlaceholderText("Количество групп")
        self.total_groups.setStyleSheet(input_style)
        group_layout.addRow("Количество групп:", self.total_groups)
        
        self.max_players = QLineEdit()
        self.max_players.setPlaceholderText("Максимум участников в группе")
        self.max_players.setStyleSheet(input_style)
        group_layout.addRow("Максимум участников:", self.max_players)
        
        main_layout.addWidget(group)
        main_layout.addStretch()
        
        return tab_widget

    def create_results_tab(self):
        """Вкладка Результаты"""
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        input_style = """
            QLineEdit, QComboBox {
                max-height: 26px;
                padding: 3px 5px;
                font-size: 10px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        
        group = QGroupBox("📊 Ввод результатов матча")
        group_layout = QFormLayout(group)
        group_layout.setSpacing(8)
        group_layout.setContentsMargins(10, 15, 10, 10)
        
        self.result_player1 = QLineEdit()
        self.result_player1.setPlaceholderText("Игрок 1")
        self.result_player1.setStyleSheet(input_style)
        group_layout.addRow("Игрок 1:", self.result_player1)
        
        self.result_score1 = QLineEdit()
        self.result_score1.setPlaceholderText("Счёт")
        self.result_score1.setStyleSheet(input_style)
        group_layout.addRow("Счёт 1:", self.result_score1)
        
        self.result_player2 = QLineEdit()
        self.result_player2.setPlaceholderText("Игрок 2")
        self.result_player2.setStyleSheet(input_style)
        group_layout.addRow("Игрок 2:", self.result_player2)
        
        self.result_score2 = QLineEdit()
        self.result_score2.setPlaceholderText("Счёт")
        self.result_score2.setStyleSheet(input_style)
        group_layout.addRow("Счёт 2:", self.result_score2)
        
        main_layout.addWidget(group)
        main_layout.addStretch()
        
        return tab_widget

    def create_rating_tab(self):
        """Вкладка Рейтинг"""
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        input_style = """
            QComboBox {
                max-height: 26px;
                padding: 3px 5px;
                font-size: 10px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        
        group = QGroupBox("⭐ Параметры рейтинга")
        group_layout = QFormLayout(group)
        group_layout.setSpacing(8)
        group_layout.setContentsMargins(10, 15, 10, 10)
        
        self.rating_type = QComboBox()
        self.rating_type.addItems(["Общий рейтинг", "По возрастным группам", "По регионам", "По городам"])
        self.rating_type.setStyleSheet(input_style)
        group_layout.addRow("Тип рейтинга:", self.rating_type)
        
        self.rating_limit = QComboBox()
        self.rating_limit.addItems(["Топ 10", "Топ 20", "Топ 50", "Топ 100", "Все"])
        self.rating_limit.setStyleSheet(input_style)
        group_layout.addRow("Показывать:", self.rating_limit)
        
        main_layout.addWidget(group)
        main_layout.addStretch()
        
        return tab_widget

    def create_extra_tab(self):
        """Вкладка Дополнительно"""
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        input_style = """
            QLineEdit, QTextEdit {
                padding: 3px 5px;
                font-size: 10px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        
        # Группа заметок
        notes_group = QGroupBox("📝 Заметки")
        notes_layout = QVBoxLayout(notes_group)
        notes_layout.setContentsMargins(10, 15, 10, 10)
        
        self.notes_text = QLineEdit()
        self.notes_text.setPlaceholderText("Добавить заметку о соревновании...")
        self.notes_text.setStyleSheet(input_style)
        notes_layout.addWidget(self.notes_text)
        
        main_layout.addWidget(notes_group)
        
        # Группа информации
        info_group = QGroupBox("ℹ️ Информация о программе")
        info_layout = QVBoxLayout(info_group)
        info_layout.setContentsMargins(10, 15, 10, 10)
        
        info_label = QLabel(
            "Версия: 3.0\n"
            "Разработчик: AI Assistant\n"
            "База данных: MySQL\n"
            "Год создания: 2024\n\n"
            "Функционал:\n"
            "• Управление соревнованиями\n"
            "• Ведение списка участников\n"
            "• Формирование пар и команд\n"
            "• Расчёт рейтинга\n"
            "• Экспорт данных"
        )
        info_label.setStyleSheet("font-size: 10px; padding: 5px;")
        info_layout.addWidget(info_label)
        
        main_layout.addWidget(info_group)
        main_layout.addStretch()
        
        return tab_widget
  
    def save_title_info(self):
        """Сохранение информации о соревновании"""
        if not self.comp_name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите название соревнования")
            return
        
        title_data = {
            'name': self.comp_name_edit.text().strip(),
            'sredi': self.comp_sredi_combo.currentText(),
            'vozrast': self.comp_vozrast_combo.currentText(),
            'data_start': self.comp_start_date.date().toPyDate(),
            'data_end': self.comp_end_date.date().toPyDate(),
            'mesto': self.comp_mesto_edit.text().strip(),
            'city': self.comp_city_edit.text().strip(),
            'referee': self.main_referee_edit.currentText(),
            'kat_ref': self.referee_category_combo.currentText(),
            'secretary': self.main_secretary_edit.text().strip(),
            'kat_sec': self.secretary_category_combo.currentText(),
            'vid_turnira': "Личное",
            'full_name_comp': self.comp_name_edit.text().strip(),
            'short_name_comp': self.comp_name_edit.text().strip()[:50],
            'tab_enabled': "1",
            'multiregion': 0,
            'perenos': 0,
            'otchestvo': 0,
            'r_date': ""
        }
        
        try:
            if self.current_title_id:
                query = Title.update(**title_data).where(Title.id == self.current_title_id)
                query.execute()
                QMessageBox.information(self, "Успех", "Информация о соревновании обновлена")
            else:
                title = Title.create(**title_data)
                self.current_title_id = title.id
                QMessageBox.information(self, "Успех", f"Соревнование '{title_data['name']}' создано")
            
            self.load_titles_list()
            self.load_title_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить данные: {str(e)}")
    
    
        """Загрузка данных соревнования для редактирования"""
        try:
            title = Title.get_or_none(Title.id == self.current_title_id)
            if title:
                self.comp_name_edit.setText(title.name or "")
                
                index = self.comp_sredi_combo.findText(title.sredi or "")
                if index >= 0:
                    self.comp_sredi_combo.setCurrentIndex(index)
                
                index = self.comp_vozrast_combo.findText(title.vozrast or "")
                if index >= 0:
                    self.comp_vozrast_combo.setCurrentIndex(index)
                
                if title.data_start:
                    self.comp_start_date.setDate(QDate(title.data_start.year, title.data_start.month, title.data_start.day))
                if title.data_end:
                    self.comp_end_date.setDate(QDate(title.data_end.year, title.data_end.month, title.data_end.day))
                # === исправил загрузку города и места ====
                mesto_txt = title.mesto
                mark = mesto_txt.find("/")
                
                if mark == -1:
                    self.comp_city_edit.setText(mesto_txt or "")
                else: 
                    mesto = mesto_txt[mark + 1:]
                    city = mesto_txt[:mark] 
                    self.comp_city_edit.setText(city or "")                 
                    self.comp_mesto_edit.setText(mesto or "")
                # ======= загрузка ГСК =======
                main_referee = title.referee
                main_secretary = title.secretary
                self.main_referee_combo.setCurrentText(main_referee)
                self.referee_category_combo.setCurrentText(main_secretary)
                # =============
                # index = self.main_referee_combo.findText(title.referee or "")
                # if index >= 0:
                #     self.main_referee_combo.setCurrentIndex(index)
                
                # index = self.main_secretary_combo.findText(title.secretary or "")
                # if index >= 0:
                #     self.main_secretary_combo.setCurrentIndex(index)
                
                index = self.referee_category_combo.findText(title.kat_ref or "")
                if index >= 0:
                    self.referee_category_combo.setCurrentIndex(index)
                
                index = self.secretary_category_combo.findText(title.kat_sec or "")
                if index >= 0:
                    self.secretary_category_combo.setCurrentIndex(index)
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
    
    def clear_title_form(self):
        """Очистка формы титула"""
        self.comp_name_edit.clear()
        self.comp_sredi_combo.setCurrentIndex(0)
        self.comp_vozrast_combo.setCurrentIndex(0)
        self.comp_start_date.setDate(QDate.currentDate())
        self.comp_end_date.setDate(QDate.currentDate().addDays(7))
        self.comp_city_edit.clear()
        self.comp_mesto_edit.clear()
        self.main_referee_combo.setCurrentIndex(0)
        self.main_secretary_combo.setCurrentIndex(0)
        self.referee_category_combo.setCurrentIndex(0)
        self.secretary_category_combo.setCurrentIndex(0)
    
    def on_title_selected(self, item):
        """Выбор соревнования из списка"""
        title_id = item.data(Qt.UserRole)
        if title_id:
            self.current_title_id = title_id
            title = Title.get_or_none(Title.id == title_id)
            if title:
                self.load_title_data()
                
                # Загружаем участников для выбранного соревнования
                self.load_participants_for_title()
                
                # Обновляем заголовок списка
                self.list_label.setText(f"🏆 Текущее соревнование: {title.name[:30]}...")
                self.list_label.setStyleSheet("""
                    background-color: #2196F3;
                    color: white;
                    padding: 6px;
                    font-weight: bold;
                    font-size: 11px;
                    border-radius: 3px;
                """)
                
                # Переключаемся на вкладку Участники
                self.tab_widget.setCurrentIndex(1)

    def on_tab_changed(self, index):
        """Смена вкладки"""
        self.current_tab_index = index
        self.update_left_panel_for_tab(index)
        
        # Меняем заголовок списка в зависимости от вкладки
        tab_titles = [
            "🏆 Прошедшие соревнования",
            "👥 Список участников",
            "🏆 Список команд",
            "🤝 Список пар",
            "⚙️ Настройки системы",
            "📊 Результаты соревнований",
            "⭐ Рейтинг участников",
            "ℹ️ Дополнительная информация"
        ]
        
        if index < len(tab_titles):
            self.list_label.setText(tab_titles[index])
        
        # Специальная обработка для вкладки "Участники" (индекс 1)
        if index == 1:
            # Очищаем QListWidget
            self.list_widget.clear()
            
            # Загружаем участников для текущего соревнования
            if self.current_title_id:
                self.load_participants_for_title()
            else:
                self.players_model.setData([])
                self.table_header.setText("👥 Список участников - выберите соревнование из списка справа")
            
            # Изменяем размеры сплиттера для увеличения таблицы
            QTimer.singleShot(100, self.resize_table_for_participants)
        
        # Для вкладки "Титул" (индекс 0) загружаем список соревнований
        elif index == 0:
            self.load_titles_list()
            
            QTimer.singleShot(100, self.resize_table_normal)
        
        # Для остальных вкладок
        else:
            QTimer.singleShot(100, self.resize_table_normal)
            
            # Загружаем соответствующие данные
            if index == 2 and self.current_title_id:  # Команды
                self.load_teams_for_title()
                self.table_header.setText(f"🏆 Команды")
            elif index == 3 and self.current_title_id:  # Пары
                self.load_doubles_for_title()
                self.table_header.setText(f"🤝 Пары")
            elif index == 5 and self.current_title_id:  # Результаты
                self.load_results_for_title()
                self.table_header.setText(f"📊 Результаты")

    def set_competition_buttons(self, count):
        """Установка кнопок соревнований"""
        for i in reversed(range(self.competition_buttons_layout.count())):
            widget = self.competition_buttons_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        titles = [("👧 Девушки", "Ж"), ("👦 Юноши", "М"), 
                  ("👧 Девушки U16", "Ж"), ("👦 Юноши U16", "М")]
        
        for i in range(min(count, 4)):
            btn_text, gender = titles[i]
            btn = QPushButton(btn_text)
            btn.setMaximumHeight(28)
            btn.setMinimumHeight(24)
            btn.setFont(QFont("", 9))
            color = "#FFB6C1" if gender == "Ж" else "#ADD8E6"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    font-size: 10px;
                    padding: 3px 6px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {'#FF69B4' if gender == 'Ж' else '#87CEEB'};
                }}
            """)
            btn.clicked.connect(lambda checked, g=gender: self.on_competition_type_clicked(g))
            self.competition_buttons_layout.addWidget(btn)
    
    def on_competition_type_clicked(self, gender):
        """Выбор типа соревнования (девушки/юноши)"""
        self.current_sex = gender
        
        # Меняем цвет левой панели
        color = "#FFF0F5" if gender == "Ж" else "#F0F8FF"
        self.left_panel.setStyleSheet(f"background-color: {color};")
        
        # Перезагружаем участников с фильтром по полу
        self.load_participants_for_title()
        
        # Показываем сообщение
        sex_text = "девушек" if gender == "Ж" else "юношей"
        QMessageBox.information(self, "Фильтр", f"Показаны {sex_text}")

    def edit_player(self):
        """Редактирование выбранного участника"""
        selection = self.table_view.selectedIndexes()
        if not selection:
            QMessageBox.warning(self, "Ошибка", "Выберите участника для редактирования")
            return
        
        row = selection[0].row()
        player_id = self.players_model.get_id(row)
        if not player_id:
            return
        
        try:
            # Получаем данные участника из БД
            player = Player.get_by_id(player_id)
            
            # Заполняем форму редактирования
            self.fio_edit.setText(player.player or "")
            patronymics = Patronymic.select().where(Patronymic.id == player.patronymic_id).get()
            patronymic = patronymics.patronymic
            self.patronymic_edit.setText(patronymic or "")  # Отчество теперь не хранится в отдельной таблице
            self.rank_edit.setText(str(player.rank) if player.rank else "")
            self.city_edit.setText(player.city or "")
            self.region_edit.setText(player.region or "")
            self.razryad_edit.setText(player.razryad or "")
            coaches = Coach.select().where(Coach.id == player.coach_id).get()
            coach = coaches.coach
            self.coach_edit.setText(coach or "")  # Тренер теперь не хранится в отдельной таблице
            
            # Устанавливаем дату рождения
            if player.bday:
                if isinstance(player.bday, date):
                    self.birth_date.setDate(QDate(player.bday.year, player.bday.month, player.bday.day))
                elif isinstance(player.bday, str):
                    for fmt in ["%Y-%m-%d", "%d.%m.%Y"]:
                        try:
                            d = datetime.strptime(player.bday, fmt).date()
                            self.birth_date.setDate(QDate(d.year, d.month, d.day))
                            break
                        except:
                            pass
            
            # Устанавливаем пол
            sex_index = 0 if player.sex == "М" else 1
            self.sex_combo.setCurrentIndex(sex_index)
            
            # Сохраняем ID редактируемого участника
            self.editing_player_id = player_id
            
            # Показываем сообщение
            QMessageBox.information(self, "Редактирование", 
                                f"Редактирование участника: {player.player}\n"
                                f"После внесения изменений нажмите 'Сохранить'")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные участника: {str(e)}")

    def save_edited_player(self):
        """Сохранение отредактированного участника"""
        if not hasattr(self, 'editing_player_id') or not self.editing_player_id:
            QMessageBox.warning(self, "Ошибка", "Нет выбранного участника для редактирования")
            return
        
        fio = self.fio_edit.text().strip()
        if not fio:
            QMessageBox.warning(self, "Ошибка", "Введите ФИО участника")
            return
        
        try:
            # Получаем данные из формы
            patronymic_id = self.patronymic_combo.currentData()
            coach_id = self.coach_combo.currentData()
            sex = "Ж" if self.sex_combo.currentText() == "Женский" else "М"
            rank = int(self.rank_edit.text()) if self.rank_edit.text().isdigit() else 0
            
            # Обновляем данные участника
            update_data = {
                'player': fio,
                'patronymic_id': patronymic_id,
                'bday': self.birth_date.date().toPyDate(),
                'rank': rank,
                'city': self.city_edit.text().strip(),
                'region': self.region_combo.currentText(),
                'razryad': self.razryad_edit.text().strip(),
                'coach_id': coach_id,
                'sex': sex,
                'fio': fio,
                'fio_city': f"{fio} ({self.city_edit.text()})"
            }
            
            # Обновляем в БД
            query = Player.update(**update_data).where(Player.id == self.editing_player_id)
            query.execute()
            
            # Очищаем форму и сбрасываем ID редактирования
            self.clear_participant_form()
            delattr(self, 'editing_player_id')
            
            # Перезагружаем таблицу
            self.load_participants_for_title()
            
            QMessageBox.information(self, "Успех", "Данные участника успешно обновлены")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить изменения: {str(e)}")

    def export_players(self):
        """Экспорт списка участников в файл"""
        if not self.current_title_id:
            QMessageBox.warning(self, "Ошибка", "Нет выбранного соревнования")
            return
        
        from PyQt5.QtWidgets import QFileDialog
        
        # Диалог выбора файла
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Сохранить список участников", 
            f"participants_{self.current_title_id}.csv",
            "CSV files (*.csv);;All files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            import csv
            
            # Получаем данные из таблицы
            data = []
            for row in range(self.players_model.rowCount()):
                row_data = []
                for col in range(1, self.players_model.columnCount()):  # Пропускаем ID
                    index = self.players_model.index(row, col)
                    value = self.players_model.data(index)
                    row_data.append(value)
                data.append(row_data)
            
            # Заголовки
            headers = ['ФИО', 'Отчество', 'Дата рождения', 'Рейтинг', 'Город', 'Регион', 'Разряд', 'Тренер']
            
            # Сохраняем в CSV
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                writer.writerows(data)
            
            QMessageBox.information(self, "Успех", f"Список участников сохранён в файл:\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать данные: {str(e)}")

        def search_players(self):
            """Поиск участников по ФИО или городу"""
            if not self.current_title_id:
                QMessageBox.warning(self, "Ошибка", "Выберите соревнование")
                return
            
            from PyQt5.QtWidgets import QInputDialog
            
            search_text, ok = QInputDialog.getText(self, "Поиск участников", "Введите ФИО или город для поиска:")
            
            if ok and search_text:
                try:
                    # Ищем участников в текущем соревновании
                    query = Player.select().where(
                        (Player.title_id == self.current_title_id) &
                        ((Player.player.contains(search_text)) | 
                        (Player.city.contains(search_text)))
                    )
                    
                    # Применяем фильтр по полу, если выбран
                    if self.current_sex:
                        query = query.where(Player.sex == self.current_sex)
                    
                    # Преобразуем в список словарей
                    participants_data = []
                    for player in query:
                        # Получаем отчество
                        patronymic_text = ""
                        if player.patronymic_id:
                            patronymic = Patronymic.get_or_none(Patronymic.id == player.patronymic_id)
                            if patronymic:
                                patronymic_text = patronymic.patronymic
                        
                        # Получаем тренера
                        coach_text = ""
                        if player.coach_id:
                            coach_text = player.coach_id.coach or ""
                        
                        participants_data.append({
                            'id': player.id,
                            'fio': player.player or "",
                            'patronymic': patronymic_text,
                            'birth_date': player.bday,
                            'rank': player.rank or 0,
                            'city': player.city or "",
                            'region': player.region or "",
                            'razryad': player.razryad or "",
                            'coach': coach_text,
                            'sex': player.sex or ""
                        })
                    
                    # Обновляем модель
                    self.players_model.setData(participants_data)
                    
                    # Показываем результат
                    QMessageBox.information(self, "Результат поиска", f"Найдено {len(participants_data)} участников")
                    
                    # Кнопка для сброса поиска
                    reply = QMessageBox.question(self, "Сброс поиска", 
                                                "Показать всех участников?",
                                                QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        self.load_participants_for_title()
                        
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка поиска: {str(e)}")
    
    def update_left_panel_for_tab(self, tab_index):
        """Обновление левой панели в зависимости от вкладки"""
        for i in reversed(range(self.dynamic_filters_layout.count())):
            widget = self.dynamic_filters_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        context = self.tab_context.get(tab_index, self.tab_context[0])
        
        # Обновляем заголовок и описание
        self.action_title.setText(f"🔧 {context['title']}")
        self.action_description.setText(context['description'])
        
        # Создаем кнопки действий
        for btn_text in context["buttons"]:
            btn = QPushButton(btn_text)
            btn.setMinimumHeight(32)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px;
                    font-size: 10px;
                    font-weight: bold;
                    text-align: left;
                    padding-left: 10px;
                }
                QPushButton:hover { 
                    background-color: #45a049; 
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
            
            # Привязываем функции для вкладки Титул
            if tab_index == 0:
                if btn_text == "💾 Сохранить":
                    btn.clicked.connect(self.save_title_info)
                elif btn_text == "🗑️ Очистить":
                    btn.clicked.connect(self.clear_title_form)
                elif btn_text == "📋 Создать новое":
                    btn.clicked.connect(self.new_competition)
                else:
                    btn.clicked.connect(lambda checked, b=btn_text: 
                                    QMessageBox.information(self, context["title"], f"Нажата: {b}"))
            # Для вкладки Участники
            elif tab_index == 1:
                if btn_text == "➕ Добавить":
                    btn.clicked.connect(self.add_player_from_form)
                elif btn_text == "✏️ Редактировать":
                    btn.clicked.connect(self.edit_player)
                elif btn_text == "🗑️ Удалить":
                    btn.clicked.connect(self.delete_player_from_table)
                elif btn_text == "🔍 Поиск":
                    btn.clicked.connect(self.search_players)
                elif btn_text == "📤 Экспорт":
                    btn.clicked.connect(self.export_players)
                else:
                    btn.clicked.connect(lambda checked, b=btn_text: 
                                    QMessageBox.information(self, context["title"], f"Нажата: {b}"))
            else:
                btn.clicked.connect(lambda checked, b=btn_text: 
                                QMessageBox.information(self, context["title"], f"Нажата: {b}"))
            
            self.dynamic_filters_layout.addWidget(btn)
        
        self.dynamic_filters_layout.addStretch()
    
    def add_player_from_form(self):
        """Добавление участника из формы на вкладке Участники"""
        if not self.current_title_id:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите соревнование из списка")
            return
        
        fio = self.fio_edit.text().strip()
        if not fio:
            QMessageBox.warning(self, "Ошибка", "Введите ФИО участника")
            return
        
        try:
            # Получаем данные из формы (теперь все из QLineEdit)
            patronymic = self.patronymic_edit.text().strip()
            coach = self.coach_edit.text().strip()
            sex = "Ж" if self.sex_combo.currentText() == "Женский" else "М"
            rank = int(self.rank_edit.text()) if self.rank_edit.text().isdigit() else 0
            city = self.city_edit.text().strip()
            region = self.region_edit.text().strip()
            razryad = self.razryad_edit.text().strip()
            
            # Проверяем, существует ли уже такой участник в этом соревновании
            existing = Player.get_or_none(
                (Player.player == fio) & 
                (Player.title_id == self.current_title_id)
            )
            
            if existing:
                reply = QMessageBox.question(self, "Внимание", 
                                            f"Участник {fio} уже существует в этом соревновании.\nОбновить данные?",
                                            QMessageBox.Yes | QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
                player_id = existing.id
                
                # Обновляем существующего участника
                update_data = {
                    'player': fio,
                    'bday': self.birth_date.date().toPyDate(),
                    'rank': rank,
                    'city': city,
                    'region': region,
                    'razryad': razryad,
                    'title_id': self.current_title_id,
                    'sex': sex,
                    'fio': fio,
                    'fio_city': f"{fio} ({city})" if city else fio,
                    'patronymic_id': None,  # Теперь не используем ID
                    'coach_id': None  # Теперь не используем ID
                }
                query = Player.update(**update_data).where(Player.id == player_id)
                query.execute()
            else:
                # Создаем нового участника
                player = Player.create(
                    player=fio,
                    bday=self.birth_date.date().toPyDate(),
                    rank=rank,
                    city=city,
                    region=region,
                    razryad=razryad,
                    title_id=self.current_title_id,
                    sex=sex,
                    fio=fio,
                    fio_city=f"{fio} ({city})" if city else fio,
                    patronymic_id=None,
                    coach_id=None,
                    total_game_player=0,
                    total_win_game=0,
                    coefficient_victories=0.0,
                    application="",
                    comment="",
                    pay_rejting=""
                )
            
            # Обновляем таблицу
            self.load_participants_for_title()
            
            # Очищаем форму
            self.clear_participant_form()
            
            QMessageBox.information(self, "Успех", f"Участник {fio} успешно добавлен")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить участника: {str(e)}")

    def delete_player_from_table(self):
        """Удаление выбранного участника из таблицы"""
        selection = self.table_view.selectedIndexes()
        if not selection:
            QMessageBox.warning(self, "Ошибка", "Выберите участника для удаления")
            return
        
        row = selection[0].row()
        
        # Получаем ID участника из модели
        player_id = self.players_model.get_id(row)
        if not player_id:
            return
        
        # Подтверждение удаления
        fio = self.players_model.get_fio(row)
        reply = QMessageBox.question(self, "Подтверждение", 
                                    f"Удалить участника {fio}?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                Player.delete().where(Player.id == player_id).execute()
                self.load_participants_for_title()
                QMessageBox.information(self, "Успех", "Участник удалён")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить участника: {str(e)}")

    def load_participants_for_title(self):
        """Загрузка участников для выбранного соревнования"""
        if not self.current_title_id:
            self.players_model.setData([])
            return
        
        try:
            # Загружаем участников из таблицы Player для текущего соревнования
            query = Player.select().where(Player.title_id == self.current_title_id)
            
            # Применяем фильтр по полу, если выбран
            if self.current_sex:
                query = query.where(Player.sex == self.current_sex)
            
            # Сортируем по рейтингу
            query = query.order_by(Player.rank.desc())
            
            # Преобразуем в список словарей для модели
            participants_data = []
            for player in query:
                # Получаем отчество
                patronymic_text = ""
                if player.patronymic_id:
                    patronymic = Patronymic.get_or_none(Patronymic.id == player.patronymic_id)
                    if patronymic:
                        patronymic_text = patronymic.patronymic
                
                # Получаем тренера
                coach_text = ""
                if player.coach_id:
                    coach_text = player.coach_id.coach or ""
                
                participants_data.append({
                    'id': player.id,
                    'fio': player.player or "",
                    'patronymic': patronymic_text,
                    'birth_date': player.bday,
                    'rank': player.rank or 0,
                    'city': player.city or "",
                    'region': player.region or "",
                    'razryad': player.razryad or "",
                    'coach': coach_text,
                    'sex': player.sex or ""
                })
            
            # Обновляем модель
            self.players_model.setData(participants_data)
            
            # Обновляем заголовок таблицы
            title = Title.get_or_none(Title.id == self.current_title_id)
            if title:
                sex_text = "Девушки" if self.current_sex == "Ж" else "Юноши" if self.current_sex == "М" else "Все участники"
                self.table_header.setText(f"👥 {title.name} - {sex_text} ({len(participants_data)} чел.)")
            
        except Exception as e:
            print(f"Ошибка загрузки участников: {e}")
            self.players_model.setData([])

    def search_players(self):
        """Поиск игрока"""
        text, ok = QInputDialog.getText(self, "Поиск", "Введите ФИО или город:")
        if ok and text:
            QMessageBox.information(self, "Результат", f"Поиск: {text}")
    
    def clear_participant_form(self):
        """Очистка формы участника"""
        self.fio_edit.clear()
        self.patronymic_edit.clear()
        self.birth_date.setDate(QDate.currentDate().addYears(-18))
        self.city_edit.clear()
        self.region_edit.clear()
        self.razryad_edit.clear()
        self.coach_edit.clear()
        self.rank_edit.clear()
        self.sex_combo.setCurrentIndex(0)
    
    def new_competition(self):
        """Создание нового соревнования"""
        self.current_title_id = None
        self.clear_title_form()
        QMessageBox.information(self, "Новое соревнование", "Введите данные и нажмите Сохранить")
    
    def create_menu_bar(self):
        """Создание меню"""
        menubar = self.menuBar()
        menubar.setStyleSheet("QMenuBar { padding: 3px; } QMenuBar::item { padding: 3px 8px; font-size: 10px; }")
        
        competitions_menu = menubar.addMenu("Соревнования")
        new_comp_action = QAction("Новое соревнование", self)
        new_comp_action.triggered.connect(self.new_competition)
        competitions_menu.addAction(new_comp_action)
        competitions_menu.addSeparator()
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        competitions_menu.addAction(exit_action)
        
        edit_menu = menubar.addMenu("Редактировать")
        edit_action = QAction("Параметры", self)
        edit_action.triggered.connect(lambda: QMessageBox.information(self, "Редактировать", "Параметры"))
        edit_menu.addAction(edit_action)
        
        print_menu = menubar.addMenu("Печать")
        print_action = QAction("Предпросмотр", self)
        print_action.triggered.connect(lambda: QMessageBox.information(self, "Печать", "Печать"))
        print_menu.addAction(print_action)
        
        view_menu = menubar.addMenu("Просмотр")
        fullscreen_action = QAction("Полный экран", self)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        rating_menu = menubar.addMenu("Рейтинг")
        rating_action = QAction("Показать рейтинг", self)
        rating_action.triggered.connect(lambda: QMessageBox.information(self, "Рейтинг", "Рейтинг"))
        rating_menu.addAction(rating_action)
        
        help_menu = menubar.addMenu("Помощь")
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.about_dialog)
        help_menu.addAction(about_action)
    
    def toggle_fullscreen(self):
        """Полноэкранный режим"""
        if self.is_fullscreen:
            self.showNormal()
        else:
            self.showFullScreen()
        self.is_fullscreen = not self.is_fullscreen
    
    def about_dialog(self):
        """О программе"""
        QMessageBox.about(self, "О программе", 
                         "Панель управления соревнованиями\n"
                         "Версия 3.0\n\n"
                         "Работа с базой данных MySQL\n"
                         "© 2024")
    
    def closeEvent(self, event):
        close_db()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.set_competition_buttons(4)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()