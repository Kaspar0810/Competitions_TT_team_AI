# main_AI.py
import sys
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTabWidget, QTableView, QMenuBar, QAction, QLabel,
    QFrame, QSizePolicy, QMessageBox, QListWidget, QListWidgetItem,
    QLineEdit, QDateEdit, QComboBox, QGroupBox, QFormLayout,
    QScrollArea, QSplitter, QInputDialog, QHeaderView, QAbstractItemView,
    QDialog, QProgressBar, QFileDialog, QMenu
)
from PyQt5.QtWidgets import QGridLayout  # Добавьте в импорт
from PyQt5.QtCore import Qt, QDate, QSize, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QCompleter
from PyQt5.QtCore import QStringListModel


from models import connect_db, close_db
from models import *
from models_qt import (
    PlayersTableModel, TeamsTableModel, ResultsTableModel, 
    DoublePlayersTableModel, TitlesTableModel, CoachesTableModel
)
from datetime import *
import pandas as pd

from datetime import datetime


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
        
        self.tab_context = {
            0: {"title": "Титул", "description": "Управление информацией о соревновании",
                "buttons": ["📋 Создать новое"]},
            1: {"title": "Участники", "description": "Управление списком участников",
                "buttons": [
                    ["➕ Добавить", "✏️ Редактировать"],
                    ["🗑️ Удалить", "🔍 Поиск"],
                    ["📤 Экспорт", "🗑️ Очистить"]
                ],
                "filters": ["Сортировка", "Фильтры", "Заявки"]},  # Добавлена секция заявок
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
        
        # Обновляем активность вкладок (по умолчанию все отключены)
        self.update_tabs_enabled()

    def showEvent(self, event):
        """Событие при первом отображении окна"""
        super().showEvent(event)
        QTimer.singleShot(100, lambda: self.set_tab_height(0))

    def set_tab_height(self, tab_index):
        """Устанавливает фиксированную высоту верхнего виджета в зависимости от вкладки"""
        if hasattr(self, 'top_widget') and hasattr(self, 'tab_heights'):
            height = self.tab_heights.get(tab_index, 200)
            self.top_widget.setFixedHeight(height)
            
            # Принудительно обновляем геометрию
            self.top_widget.updateGeometry()
            if hasattr(self, 'bottom_widget'):
                self.bottom_widget.updateGeometry()
            
            # Обновляем таблицу
            if hasattr(self, 'table_view'):
                self.table_view.updateGeometry()

    def resize_table_for_participants(self):
        """Устанавливает высоту для вкладки Участники"""
        self.set_tab_height(1)

    def resize_table_normal(self):
        """Восстанавливает нормальную высоту для текущей вкладки"""
        if hasattr(self, 'current_tab_index'):
            self.set_tab_height(self.current_tab_index)

    def resizeEvent(self, event):
        """Обработчик изменения размера окна"""
        super().resizeEvent(event)
        
        # Обновляем размеры при изменении окна
        if hasattr(self, 'current_tab_index') and hasattr(self, 'top_widget'):
            QTimer.singleShot(50, lambda: self.set_tab_height(self.current_tab_index))

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
        
        try:
            titles = Title.select().order_by(Title.data_start.desc())
            
            # Загружаем годы для фильтра (только один раз)
            if self.year_combo.count() <= 1:
                self.load_years_from_titles()
            
            if titles.count() == 0:
                item = QListWidgetItem("Нет доступных соревнований")
                item.setFlags(Qt.NoItemFlags)
                self.list_widget.addItem(item)
                return
            
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
            
            self.competitions_label.setText(f"🏆 Прошедшие соревнования ({titles.count()})")
            
        except Exception as e:
            print(f"Ошибка загрузки соревнований: {e}")
            item = QListWidgetItem(f"Ошибка загрузки: {e}")
            item.setFlags(Qt.NoItemFlags)
            self.list_widget.addItem(item)

    def init_ui(self):
        """Инициализация интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
#============ левая панель ===================        
        self.left_panel = QFrame()
        self.left_panel.setFrameShape(QFrame.StyledPanel)
        self.left_panel.setMinimumWidth(320)
        self.left_panel.setMaximumWidth(400)
        self.left_panel.setStyleSheet("background-color: #f5f5f5;")
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setAlignment(Qt.AlignTop)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        # Заголовок категорий участников
        category_label = QLabel("👥 Категория участников:")
        category_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #333; margin-top: 5px;")
        left_layout.addWidget(category_label)
        
        # Горизонтальный контейнер для кнопок Мальчики/Девочки
        self.gender_buttons_layout = QHBoxLayout()
        self.gender_buttons_layout.setSpacing(10)
        left_layout.addLayout(self.gender_buttons_layout)
        
        # Контейнер для возрастных кнопок (если есть несколько возрастных категорий)
        self.age_buttons_layout = QVBoxLayout()
        self.age_buttons_layout.setSpacing(8)
        left_layout.addLayout(self.age_buttons_layout)
        
        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #ccc; max-height: 2px; margin: 10px 0;")
        left_layout.addWidget(line)
# ===================================================        
        # Заголовок текущего действия
        self.action_title = QLabel("🔧 Действия")
        self.action_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #4CAF50; margin-top: 5px;")
        left_layout.addWidget(self.action_title)
        
        self.action_description = QLabel("Выберите вкладку для отображения действий")
        self.action_description.setStyleSheet("font-size: 11px; color: #666; margin-bottom: 10px;")
        self.action_description.setWordWrap(True)
        left_layout.addWidget(self.action_description)
        
        # Контейнер для кнопок действий
        self.dynamic_filters_widget = QWidget()
        self.dynamic_filters_layout = QVBoxLayout(self.dynamic_filters_widget)
        self.dynamic_filters_layout.setAlignment(Qt.AlignTop)
        self.dynamic_filters_layout.setSpacing(8)
        self.dynamic_filters_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.dynamic_filters_widget)        
        # ===== Контейнер для фильтров =====
        self.filters_widget = QWidget()
        filters_layout = QVBoxLayout(self.filters_widget)
        filters_layout.setSpacing(10)
        filters_layout.setContentsMargins(0, 10, 0, 0)
        
        # Заголовок фильтров
        filter_header = QLabel("🔍 Фильтры соревнований")
        filter_header.setStyleSheet("font-weight: bold; font-size: 13px; color: #2196F3;")
        filters_layout.addWidget(filter_header)
        
        # Поиск по названию
        search_label = QLabel("Поиск по названию:")
        search_label.setStyleSheet("font-size: 11px; font-weight: bold; margin-top: 5px;")
        filters_layout.addWidget(search_label)
        self.search_name_edit = QLineEdit()
        self.search_name_edit.setPlaceholderText("Введите название...")
        self.search_name_edit.setStyleSheet("""
            max-height: 32px; 
            min-height: 30px;
            padding: 5px; 
            font-size: 11px;
            border: 1px solid #ccc;
            border-radius: 4px;
        """)
        self.search_name_edit.textChanged.connect(self.filter_competitions)
        filters_layout.addWidget(self.search_name_edit)
        
        # Фильтр по году
        year_label = QLabel("Год:")
        year_label.setStyleSheet("font-size: 11px; font-weight: bold; margin-top: 5px;")
        filters_layout.addWidget(year_label)
        self.year_combo = QComboBox()

        # Заполним года позже, после загрузки данных
        self.year_combo.setStyleSheet("""
            max-height: 32px; 
            min-height: 30px;
            font-size: 11px;
            padding: 3px;
            border: 1px solid #ccc;
            border-radius: 4px;
        """)
        self.year_combo.currentTextChanged.connect(self.filter_competitions)
        filters_layout.addWidget(self.year_combo)
        
        # Фильтр по месяцу
        month_label = QLabel("Месяц:")
        month_label.setStyleSheet("font-size: 11px; font-weight: bold; margin-top: 5px;")
        filters_layout.addWidget(month_label)
        self.month_combo = QComboBox()
        self.month_combo.addItem("Все месяцы")
        months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        for month in months:
            self.month_combo.addItem(month)
        self.month_combo.setStyleSheet("""
            max-height: 32px; 
            min-height: 30px;
            font-size: 11px;
            padding: 3px;
            border: 1px solid #ccc;
            border-radius: 4px;
        """)
        self.month_combo.currentTextChanged.connect(self.filter_competitions)
        filters_layout.addWidget(self.month_combo)
        
        # Фильтр по категории "Среди"
        sredi_label = QLabel("Категория участников:")
        sredi_label.setStyleSheet("font-size: 11px; font-weight: bold; margin-top: 5px;")
        filters_layout.addWidget(sredi_label)
        self.sredi_combo = QComboBox()
        self.sredi_combo.addItem("Все категории")
        self.sredi_combo.addItems(["мальчики и девочки", "юноши и девушки", "юниоры и юниорки", "мужчины и женщины"])
        self.sredi_combo.setStyleSheet("""
            max-height: 32px; 
            min-height: 30px;
            font-size: 11px;
            padding: 3px;
            border: 1px solid #ccc;
            border-radius: 4px;
        """)
        self.sredi_combo.currentTextChanged.connect(self.filter_competitions)
        filters_layout.addWidget(self.sredi_combo)
        
        # Кнопка сброса фильтров
        reset_btn = QPushButton("🔄 Сбросить фильтры")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        reset_btn.clicked.connect(self.reset_filters_on_title_tab)
        filters_layout.addWidget(reset_btn)
        
        left_layout.addWidget(self.filters_widget)
       
        # ===== Контейнер для формы создания соревнования =====
        self.new_comp_widget = QWidget()
        self.new_comp_widget.setVisible(False)
        new_comp_layout = QVBoxLayout(self.new_comp_widget)
        new_comp_layout.setSpacing(10)
        new_comp_layout.setContentsMargins(0, 10, 0, 0)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        save_new_btn = QPushButton("💾 Сохранить")
        save_new_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                padding: 8px;
                font-size: 11px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        save_new_btn.clicked.connect(self.save_new_competition)
        cancel_new_btn = QPushButton("❌ Отмена")
        cancel_new_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336; 
                color: white; 
                padding: 8px;
                font-size: 11px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #d32f2f; }
        """)
        cancel_new_btn.clicked.connect(self.cancel_new_competition)
        btn_layout.addWidget(save_new_btn)
        btn_layout.addWidget(cancel_new_btn)
        new_comp_layout.addLayout(btn_layout)
        
        left_layout.addWidget(self.new_comp_widget)
        left_layout.addStretch()      
        # ========== Правая область ==========
        right_area = QWidget()
        right_layout = QVBoxLayout(right_area)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # Верхняя часть с вкладками
        self.top_widget = QWidget()
        self.top_widget.setMinimumHeight(140)
        self.top_widget.setMaximumHeight(400)
        top_layout = QHBoxLayout(self.top_widget)
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
        
        # Правая панель
        self.right_panel = QWidget()
        self.right_panel.setMaximumWidth(420)
        self.right_panel.setMinimumWidth(350)
        right_panel_layout = QVBoxLayout(self.right_panel)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        right_panel_layout.setSpacing(3)
        
        # В методе init_ui, после создания правой панели:
        self.competitions_label = QLabel("🏆 Прошедшие соревнования")
        self.competitions_label.setStyleSheet("""
            background-color: #4CAF50;
            color: white;
            padding: 6px;
            font-weight: bold;
            font-size: 11px;
            border-radius: 3px;
        """)
        self.competitions_label.setAlignment(Qt.AlignCenter)
        right_panel_layout.addWidget(self.competitions_label)

        # Список соревнований
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                font-size: 12px;
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
        """)
        self.list_widget.itemClicked.connect(self.on_title_selected)
        right_panel_layout.addWidget(self.list_widget)
        
        # Заголовок для поиска (вкладка Участники)
        self.search_label = QLabel("🔍 Поиск игроков в рейтингах")
        self.search_label.setStyleSheet("""
            background-color: #FF9800;
            color: white;
            padding: 6px;
            font-weight: bold;
            font-size: 11px;
            border-radius: 3px;
        """)
        self.search_label.setAlignment(Qt.AlignCenter)
        self.search_label.setVisible(False)
        right_panel_layout.addWidget(self.search_label)
      
        # Список результатов поиска
        self.search_results_list = QListWidget()
        self.search_results_list.setStyleSheet("""
            QListWidget {
                font-size: 12px;
                background-color: #fafafa;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #FF9800;
                color: white;
            }
        """)
        self.search_results_list.setVisible(False)
        self.search_results_list.itemClicked.connect(self.on_search_result_selected)
        right_panel_layout.addWidget(self.search_results_list)
        
        top_layout.addWidget(self.tab_widget)
        top_layout.addWidget(self.right_panel)
        top_layout.setStretch(0, 2)
        top_layout.setStretch(1, 1)


# =========== добавил
        self.list_widget.itemClicked.connect(self.on_title_selected)
        self.add_context_menu_to_list()  # Добавляем контекстное меню
        right_panel_layout.addWidget(self.list_widget)

        # ========== Нижняя часть с таблицей ==========
        self.bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(self.bottom_widget)
        bottom_layout.setContentsMargins(5, 5, 5, 5)
        bottom_layout.setSpacing(5)
        
        # Заголовок таблицы
        self.table_header = QLabel("👥 Список участников")
        self.table_header.setStyleSheet("""
            background-color: #2196F3;
            color: white;
            padding: 6px;
            font-weight: bold;
            font-size: 11px;
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
                font-size: 10px;
                gridline-color: #ddd;
                selection-background-color: #a0c4ff;
            }
            QTableView::item {
                padding: 2px;
            }
            QHeaderView::section {
                background-color: #2196F3;
                color: white;
                padding: 4px;
                font-weight: bold;
                font-size: 10px;
                border: none;
            }
        """)
        
        # Уменьшаем высоту строк
        self.table_view.verticalHeader().setDefaultSectionSize(22)
        self.table_view.verticalHeader().setMinimumSectionSize(18)
        
        # В методе init_ui, после установки модели:
        self.table_view.setModel(self.players_model)

        # Показываем первую колонку (№) и настраиваем её ширину
        self.table_view.setColumnHidden(0, False)  # Показываем колонку с номером
        self.table_view.setColumnWidth(0, 40)      # Ширина колонки №

        # Настройка остальных колонок
        self.table_view.setColumnWidth(1, 180)  # ФИО
        self.table_view.setColumnWidth(2, 90)   # Дата рождения
        self.table_view.setColumnWidth(3, 60)   # Рейтинг
        self.table_view.setColumnWidth(4, 120)  # Город
        self.table_view.setColumnWidth(5, 120)  # Регион
        self.table_view.setColumnWidth(6, 90)   # Разряд
        self.table_view.setColumnWidth(7, 150)  # Тренер

        # Растягиваем последнюю колонку
        self.table_view.horizontalHeader().setStretchLastSection(True)

        # В init_ui, после создания table_view:
        self.table_view.setSelectionMode(QTableView.ExtendedSelection)  # Множественное выделение
        self.table_view.setSelectionBehavior(QTableView.SelectRows)  # Выделение строк

        bottom_layout.addWidget(self.table_view)
        
        # Добавляем виджеты в правую область
        right_layout.addWidget(self.top_widget)
        right_layout.addWidget(self.bottom_widget)
        
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(right_area, 1)
        
        self.create_menu_bar()
        self.update_left_panel_for_tab(0)
        
        # Словарь для хранения высот верхней части для каждой вкладки
        self.tab_heights = {
            0: 600,  # Титул
            1: 180,  # Участники
            2: 180,  # Команды
            3: 180,  # Пары
            4: 220,  # Система
            5: 220,  # Результаты
            6: 180,  # Рейтинг
            7: 200   # Дополнительно
        }
        
        # Устанавливаем начальную высоту
        self.set_tab_height(0)
        
        # Загружаем список соревнований для вкладки Титул
        self.load_titles_list()

        # Загружаем последнее соревнование
        self.load_last_competition()
        
        # В конце метода, после создания всех виджетов, показываем фильтры
        self.filters_widget.setVisible(True)     

    def create_category_buttons(self):
        """Создание кнопок для переключения между категориями участников (только man/woman)"""
        # Очищаем существующие кнопки
        for i in reversed(range(self.gender_buttons_layout.count())):
            widget = self.gender_buttons_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        if not self.current_title_id:
            return
        
        try:
            current_title = Title.get_by_id(self.current_title_id)
            
            # Получаем данные из столбцов sredi и vozrast
            sredi = current_title.sredi if current_title.sredi else ""
            vozrast = current_title.vozrast if current_title.vozrast else ""
            
            # Преобразуем возраст в формат UXX
            age_short = self.format_age_to_u(vozrast)
            
            # Определяем надписи для кнопок
            if "юноши" in sredi.lower():
                men_text = f"Юноши {age_short}"
                women_text = f"Девушки {age_short}"
            elif "мальчики" in sredi.lower():
                men_text = f"Мальчики {age_short}"
                women_text = f"Девочки {age_short}"
            else:
                men_text = f"Мужчины {age_short}"
                women_text = f"Женщины {age_short}"
            
            # Создаем кнопку для мужчин (man)
            man_btn = QPushButton(men_text)
            man_btn.setMinimumHeight(40)
            man_btn.setCursor(Qt.PointingHandCursor)
            man_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            # Создаем кнопку для женщин (woman)
            woman_btn = QPushButton(women_text)
            woman_btn.setMinimumHeight(40)
            woman_btn.setCursor(Qt.PointingHandCursor)
            woman_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            # Определяем активную кнопку
            if self.current_sex == 'man':
                man_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4FC3F7;
                        color: white;
                        border: 2px solid #2E7D32;
                        border-radius: 8px;
                        padding: 10px;
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #29B6F6;
                    }
                """)
                woman_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FFB6C1;
                        color: #333;
                        border: 1px solid #ccc;
                        border-radius: 8px;
                        padding: 10px;
                        font-size: 13px;
                    }
                    QPushButton:hover {
                        background-color: #FF69B4;
                        border: 1px solid #2E7D32;
                    }
                """)
                self.left_panel.setStyleSheet("background-color: #ADD8E6;")
            else:
                man_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ADD8E6;
                        color: #333;
                        border: 1px solid #ccc;
                        border-radius: 8px;
                        padding: 10px;
                        font-size: 13px;
                    }
                    QPushButton:hover {
                        background-color: #87CEEB;
                        border: 1px solid #2E7D32;
                    }
                """)
                woman_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #F48FB1;
                        color: white;
                        border: 2px solid #2E7D32;
                        border-radius: 8px;
                        padding: 10px;
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #F06292;
                    }
                """)
                self.left_panel.setStyleSheet("background-color: #FFB6C1;")
            
            man_btn.clicked.connect(lambda: self.switch_gender_category('man'))
            woman_btn.clicked.connect(lambda: self.switch_gender_category('woman'))
            
            self.gender_buttons_layout.addWidget(man_btn)
            self.gender_buttons_layout.addWidget(woman_btn)
            
            # Обновляем заголовок таблицы
            self.update_table_header()
            
        except Exception as e:
            print(f"Ошибка создания кнопок категорий: {e}")

    def switch_competition_and_gender(self, title_id, sex):
        """Переключение между соревнованиями и полом"""
        if title_id != self.current_title_id:
            # Переключаем соревнование
            self.current_title_id = title_id
            title = Title.get_or_none(Title.id == title_id)
            if title:
                # Обновляем информацию на вкладке Титул
                self.comp_name_label.setText(title.name or "-")
                self.comp_short_name_label.setText(title.short_name_comp or "-")
                self.comp_full_name_label.setText(title.full_name_comp or "-")
                self.comp_sredi_label.setText(title.sredi or "-")
                self.comp_vozrast_label.setText(title.vozrast or "-")
                self.comp_type_info_label.setText(title.vid_turnira or "-")
                
                start = title.data_start.strftime("%d.%m.%Y") if title.data_start else "---"
                end = title.data_end.strftime("%d.%m.%Y") if title.data_end else "---"
                self.comp_dates_label.setText(f"{start} - {end}")
                self.comp_mesto_label.setText(title.mesto or "-")
                self.comp_referee_label.setText(title.referee or "-")
                self.comp_referee_category_label.setText(title.kat_ref or "-")
                self.comp_secretary_label.setText(title.secretary or "-")
                self.comp_secretary_category_label.setText(title.kat_sec or "-")
                
                # Обновляем активность вкладок
                self.update_tabs_enabled()
        
        # Переключаем пол
        if self.current_sex != sex:
            self.current_sex = sex
        
        # ЗАГРУЖАЕМ УЧАСТНИКОВ
        self.load_participants_for_title()
        
        # Обновляем кнопки
        self.create_category_buttons()

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
            'ВК': 'ССВК',
            '1К': '1 кат.',
            '2К': '2 кат',
            '3К': '3 кат',
        }
        return category_map.get(category_code, 'ССВК')

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
            self.competitions_label.setText(f"🏆 Текущее соревнование: {title_data['name'][:30]}...")
            self.competitions_label.setStyleSheet("""
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

    def create_title_tab(self):
        """Вкладка Титул - форма создания и информация о соревновании"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # ===== Форма создания нового соревнования (горизонтальная) =====
        self.new_comp_frame = QFrame()
        self.new_comp_frame.setStyleSheet("""
            QFrame {
                background-color: #f9f9f9;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 15px;
            }
            QLabel {
                font-size: 11px;
                font-weight: bold;
                color: #333;
            }
        """)
        self.new_comp_frame.setVisible(False)
        new_comp_layout = QVBoxLayout(self.new_comp_frame)
        new_comp_layout.setSpacing(12)
        
        # Заголовок
        new_comp_title = QLabel("✏️ Создание нового соревнования")
        new_comp_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50; margin-bottom: 10px;")
        new_comp_layout.addWidget(new_comp_title)
        
        # Ряд 1: Название
        row1 = QHBoxLayout()
        label_name = QLabel("Название:")
        label_name.setMinimumWidth(120)
        self.new_comp_name = QLineEdit()
        self.new_comp_name.setPlaceholderText("Введите название соревнования")
        self.new_comp_name.setStyleSheet("padding: 5px; font-size: 11px;")
        row1.addWidget(label_name)
        row1.addWidget(self.new_comp_name, 1)
        new_comp_layout.addLayout(row1)
        
        # Ряд 2: Категория, Возраст
        row2 = QHBoxLayout()
        label_sredi = QLabel("Категория:")
        label_sredi.setMinimumWidth(120)
        self.new_comp_sredi = QComboBox()
        self.new_comp_sredi.addItems(["мальчики и девочки", "юноши и девушки", "юниоры и юниорки", "мужчины и женщины"])
        self.new_comp_sredi.setStyleSheet("padding: 5px; font-size: 11px;")
        row2.addWidget(label_sredi)
        row2.addWidget(self.new_comp_sredi, 1)
        
        label_vozrast = QLabel("Возраст:")
        label_vozrast.setMinimumWidth(80)
        self.new_comp_vozrast = QComboBox()
        self.new_comp_vozrast.addItems(["до 12 лет", "до 14 лет", "до 16 лет", "до 18 лет", "до 20 лет", "до 22 лет", "22 года и старше"])
        self.new_comp_vozrast.setStyleSheet("padding: 5px; font-size: 11px;")
        row2.addWidget(label_vozrast)
        row2.addWidget(self.new_comp_vozrast, 1)
        new_comp_layout.addLayout(row2)
        
        # Ряд 3: Даты
        row3 = QHBoxLayout()
        label_start = QLabel("Дата начала:")
        label_start.setMinimumWidth(120)
        self.new_comp_start = QDateEdit()
        self.new_comp_start.setDate(QDate.currentDate())
        self.new_comp_start.setCalendarPopup(True)
        self.new_comp_start.setDisplayFormat("dd.MM.yyyy")
        self.new_comp_start.setStyleSheet("padding: 5px; font-size: 11px;")
        row3.addWidget(label_start)
        row3.addWidget(self.new_comp_start, 1)
        
        label_end = QLabel("Дата окончания:")
        label_end.setMinimumWidth(120)
        self.new_comp_end = QDateEdit()
        self.new_comp_end.setDate(QDate.currentDate().addDays(7))
        self.new_comp_end.setCalendarPopup(True)
        self.new_comp_end.setDisplayFormat("dd.MM.yyyy")
        self.new_comp_end.setStyleSheet("padding: 5px; font-size: 11px;")
        row3.addWidget(label_end)
        row3.addWidget(self.new_comp_end, 1)
        new_comp_layout.addLayout(row3)
        
        # Ряд 4: Место проведения
        row4 = QHBoxLayout()
        label_mesto = QLabel("Место проведения:")
        label_mesto.setMinimumWidth(120)
        self.new_comp_mesto = QLineEdit()
        self.new_comp_mesto.setPlaceholderText("Город, Спорткомплекс")
        self.new_comp_mesto.setStyleSheet("padding: 5px; font-size: 11px;")
        row4.addWidget(label_mesto)
        row4.addWidget(self.new_comp_mesto, 1)
        new_comp_layout.addLayout(row4)
        
        # Ряд 5: Главный судья и категория
        row5 = QHBoxLayout()
        label_referee = QLabel("Главный судья:")
        label_referee.setMinimumWidth(120)
        self.new_comp_referee = QLineEdit()
        self.new_comp_referee.setPlaceholderText("Фамилия И.О.")
        self.new_comp_referee.setStyleSheet("padding: 5px; font-size: 11px;")
        self.new_comp_referee.textChanged.connect(self.on_new_referee_text_changed)
        row5.addWidget(label_referee)
        row5.addWidget(self.new_comp_referee, 1)
        
        label_referee_cat = QLabel("Категория:")
        label_referee_cat.setMinimumWidth(80)
        self.new_comp_referee_cat = QComboBox()
        self.new_comp_referee_cat.addItems(["ВК", "1К", "2К", "3К"])
        self.new_comp_referee_cat.setStyleSheet("padding: 5px; font-size: 11px;")
        row5.addWidget(label_referee_cat)
        row5.addWidget(self.new_comp_referee_cat, 1)
        new_comp_layout.addLayout(row5)
        
        # Ряд 6: Главный секретарь и категория
        row6 = QHBoxLayout()
        label_secretary = QLabel("Главный секретарь:")
        label_secretary.setMinimumWidth(120)
        self.new_comp_secretary = QLineEdit()
        self.new_comp_secretary.setPlaceholderText("Фамилия И.О.")
        self.new_comp_secretary.setStyleSheet("padding: 5px; font-size: 11px;")
        self.new_comp_secretary.textChanged.connect(self.on_new_secretary_text_changed)
        row6.addWidget(label_secretary)
        row6.addWidget(self.new_comp_secretary, 1)
        
        label_secretary_cat = QLabel("Категория:")
        label_secretary_cat.setMinimumWidth(80)
        self.new_comp_secretary_cat = QComboBox()
        self.new_comp_secretary_cat.addItems(["ВК", "1К", "2К", "3К"])
        self.new_comp_secretary_cat.setStyleSheet("padding: 5px; font-size: 11px;")
        row6.addWidget(label_secretary_cat)
        row6.addWidget(self.new_comp_secretary_cat, 1)
        new_comp_layout.addLayout(row6)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Сохранить")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px 15px; font-size: 11px; font-weight: bold; border-radius: 4px;")
        save_btn.clicked.connect(self.save_new_competition)
        cancel_btn = QPushButton("❌ Отмена")
        cancel_btn.setStyleSheet("background-color: #f44336; color: white; padding: 8px 15px; font-size: 11px; font-weight: bold; border-radius: 4px;")
        cancel_btn.clicked.connect(self.cancel_new_competition)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        new_comp_layout.addLayout(btn_layout)
        
        layout.addWidget(self.new_comp_frame)
# =========================================================================        
        # ===== Информация о выбранном соревновании =====
        self.info_group = QGroupBox("📋 Информация о соревновании")
        self.info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                margin-top: 15px;
            }
            QGroupBox::title {
                color: #4CAF50;
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
            }
        """)
        info_layout = QFormLayout(self.info_group)
        info_layout.setSpacing(12)
        info_layout.setContentsMargins(15, 20, 15, 15)
        
        # Поля информации
        self.comp_name_label = QLabel("-")
        self.comp_short_name_label = QLabel("-")  # Добавляем короткое имя
        self.comp_full_name_label = QLabel("-")   # Добавляем полное имя
        self.comp_sredi_label = QLabel("-")
        self.comp_vozrast_label = QLabel("-")
        self.comp_dates_label = QLabel("-")
        self.comp_mesto_label = QLabel("-")
        self.comp_referee_label = QLabel("-")
        self.comp_referee_category_label = QLabel("-")
        self.comp_secretary_label = QLabel("-")
        self.comp_secretary_category_label = QLabel("-")
        self.comp_type_info_label = QLabel("-")
        
        for label in [self.comp_name_label, self.comp_short_name_label, self.comp_full_name_label,
                    self.comp_sredi_label, self.comp_vozrast_label,
                    self.comp_dates_label, self.comp_mesto_label,
                    self.comp_referee_label, self.comp_referee_category_label,
                    self.comp_secretary_label, self.comp_secretary_category_label,
                    self.comp_type_info_label]:
            label.setStyleSheet("""
                font-size: 11px; 
                padding: 6px; 
                background-color: #f9f9f9; 
                border-radius: 4px;
                border: 1px solid #e0e0e0;
            """)
            label.setWordWrap(True)
        
        info_layout.addRow("Название:", self.comp_name_label)
        info_layout.addRow("Короткое имя:", self.comp_short_name_label)
        info_layout.addRow("Полное имя:", self.comp_full_name_label)
        info_layout.addRow("Категория:", self.comp_sredi_label)
        info_layout.addRow("Возраст:", self.comp_vozrast_label)
        info_layout.addRow("Тип:", self.comp_type_info_label)
        info_layout.addRow("Даты:", self.comp_dates_label)
        info_layout.addRow("Место:", self.comp_mesto_label)
        info_layout.addRow("Главный судья:", self.comp_referee_label)
        info_layout.addRow("Категория судьи:", self.comp_referee_category_label)
        info_layout.addRow("Главный секретарь:", self.comp_secretary_label)
        info_layout.addRow("Категория секретаря:", self.comp_secretary_category_label)
        
        layout.addWidget(self.info_group)
        layout.addStretch()
        
        return tab_widget

    def on_razryad_changed(self, index):
        """Обработка изменения выбора в поле Разряд"""
        self.coach_edit.setFocus()

    def on_region_changed(self, index):
        """Обработка изменения выбора в поле Регион"""
        pass  # Можно оставить пустым

    def on_sex_changed(self, index):
        """Обработка изменения выбора в поле Пол"""
        pass  # Можно оставить пустым 

    def create_participants_tab(self):
        """Вкладка участников - с поиском по спискам и автодополнением"""
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setSpacing(3)
        main_layout.setContentsMargins(3, 3, 3, 3)
        
        # Стиль для полей ввода
        input_style = """
            QLineEdit, QDateEdit, QComboBox {
                max-height: 26px;
                min-height: 24px;
                padding: 2px 4px;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QLabel {
                font-size: 10px;
                font-weight: bold;
            }
        """
        
        form_widget = QWidget()
        form_widget.setMaximumHeight(350)
        form_layout = QGridLayout(form_widget)
        form_layout.setSpacing(4)
        form_layout.setContentsMargins(4, 4, 4, 4)
        
        # Ряд 1: ФИО
        label_fio = QLabel("ФИО:")
        label_fio.setStyleSheet("font-weight: bold; font-size: 10px;")
        form_layout.addWidget(label_fio, 0, 0)
        
        self.fio_edit = QLineEdit()
        self.fio_edit.setPlaceholderText("Введите фамилию для поиска...")
        self.fio_edit.setStyleSheet(input_style)
        self.fio_edit.textChanged.connect(self.on_fio_text_changed)
        self.fio_edit.returnPressed.connect(self.on_fio_enter_pressed)
        form_layout.addWidget(self.fio_edit, 0, 1, 1, 9)
        
        # Ряд 2: Отчество (с автодополнением)
        label_patronymic = QLabel("Отчество:")
        label_patronymic.setStyleSheet("font-weight: bold; font-size: 10px;")
        form_layout.addWidget(label_patronymic, 1, 0)
        
        self.patronymic_edit = QLineEdit()
        self.patronymic_edit.setPlaceholderText("Иванович")
        self.patronymic_edit.setStyleSheet(input_style)
        self.patronymic_edit.textChanged.connect(self.on_patronymic_text_changed)
        self.patronymic_edit.returnPressed.connect(self.on_patronymic_enter_pressed)
        form_layout.addWidget(self.patronymic_edit, 1, 1, 1, 3)
        
        # Создаем QCompleter для отчества
        self.patronymic_completer = QCompleter()
        self.patronymic_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.patronymic_completer.setFilterMode(Qt.MatchStartsWith)
        self.patronymic_completer.setCompletionMode(QCompleter.PopupCompletion)
        self.patronymic_edit.setCompleter(self.patronymic_completer)
        
        # Ряд 3: Дата рождения
        label_birth = QLabel("Дата рожд.:")
        label_birth.setStyleSheet("font-weight: bold; font-size: 10px;")
        form_layout.addWidget(label_birth, 1, 4)
        
        self.birth_date_edit = QLineEdit()
        self.birth_date_edit.setPlaceholderText("ДД.ММ.ГГГГ")
        self.birth_date_edit.setInputMask("99.99.9999")
        self.birth_date_edit.setStyleSheet(input_style)
        self.birth_date_edit.returnPressed.connect(self.on_birth_date_enter_pressed)
        form_layout.addWidget(self.birth_date_edit, 1, 5, 1, 2)
        
        # Рейтинг
        label_rank = QLabel("Рейт.:")
        label_rank.setStyleSheet("font-weight: bold; font-size: 10px;")
        form_layout.addWidget(label_rank, 1, 7)
        self.rank_edit = QLineEdit()
        self.rank_edit.setText("0")
        self.rank_edit.setMaximumWidth(60)
        self.rank_edit.setStyleSheet(input_style)
        self.rank_edit.setReadOnly(True)
        form_layout.addWidget(self.rank_edit, 1, 8)
        
        # Ряд 4: Город
        label_city = QLabel("Город:")
        label_city.setStyleSheet("font-weight: bold; font-size: 10px;")
        form_layout.addWidget(label_city, 3, 0)
        
        self.city_edit = QLineEdit()
        self.city_edit.setPlaceholderText("Москва")
        self.city_edit.setStyleSheet(input_style)
        self.city_edit.textChanged.connect(self.on_city_text_changed)
        self.city_edit.returnPressed.connect(self.on_city_enter_pressed)
        form_layout.addWidget(self.city_edit, 3, 1, 1, 4)
        
        # Создаем QCompleter для города
        self.city_completer = QCompleter()
        self.city_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.city_completer.setFilterMode(Qt.MatchStartsWith)
        self.city_completer.setCompletionMode(QCompleter.PopupCompletion)
        self.city_edit.setCompleter(self.city_completer)
        
        # Регион (ComboBox)
        label_region = QLabel("Регион:")
        label_region.setStyleSheet("font-weight: bold; font-size: 10px;")
        form_layout.addWidget(label_region, 3, 5)
        
        self.region_combo = QComboBox()
        self.region_combo.setStyleSheet(input_style)
        self.load_regions()
        self.region_combo.currentIndexChanged.connect(self.on_region_changed)
        form_layout.addWidget(self.region_combo, 3, 6, 1, 4)
        
        # Ряд 5: Разряд, Тренеры, Пол
        razryad_list = ["б/р", "3-юн", "2-юн", "1-юн", "3-р", "2-р", "1-р", "КМС", "МС", "МСМК"]
        label_razryad = QLabel("Разряд:")
        label_razryad.setStyleSheet("font-weight: bold; font-size: 10px;")
        form_layout.addWidget(label_razryad, 5, 0)
        self.razryad_combo = QComboBox()
        self.razryad_combo.addItems(razryad_list)
        self.razryad_combo.setStyleSheet(input_style)
        self.razryad_combo.currentIndexChanged.connect(self.on_razryad_changed)
        form_layout.addWidget(self.razryad_combo, 5, 1)
        
        label_coach = QLabel("Тренер:")
        label_coach.setStyleSheet("font-weight: bold; font-size: 10px;")
        form_layout.addWidget(label_coach, 5, 2)
        
        self.coach_edit = QLineEdit()
        self.coach_edit.setPlaceholderText("Иванов И.И.")
        self.coach_edit.setStyleSheet(input_style)
        self.coach_edit.textChanged.connect(self.on_coach_text_changed)
        self.coach_edit.returnPressed.connect(self.on_coach_enter_pressed)
        form_layout.addWidget(self.coach_edit, 5, 3, 1, 5)
        
        # Создаем QCompleter для тренера
        self.coach_completer = QCompleter()
        self.coach_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.coach_completer.setFilterMode(Qt.MatchStartsWith)
        self.coach_completer.setCompletionMode(QCompleter.PopupCompletion)
        self.coach_edit.setCompleter(self.coach_completer)
        
        label_sex = QLabel("Пол:")
        label_sex.setStyleSheet("font-weight: bold; font-size: 10px;")
        form_layout.addWidget(label_sex, 5, 8)
        self.sex_combo = QComboBox()
        self.sex_combo.addItems(["Мужской", "Женский"])
        self.sex_combo.setStyleSheet(input_style)
        self.sex_combo.currentIndexChanged.connect(self.on_sex_changed)
        form_layout.addWidget(self.sex_combo, 5, 9)
        
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
                # Проверяем количество соревнований на эту дату (без вывода сообщения)
                competitions_count = self.check_competitions_by_date(title)
                
                # Обновляем информацию на вкладке Титул
                self.comp_name_label.setText(title.name or "-")
                self.comp_short_name_label.setText(title.short_name_comp or "-")
                self.comp_full_name_label.setText(title.full_name_comp or "-")
                self.comp_sredi_label.setText(title.sredi or "-")
                self.comp_vozrast_label.setText(title.vozrast or "-")
                self.comp_type_info_label.setText(title.vid_turnira or "-")
                
                start = title.data_start.strftime("%d.%m.%Y") if title.data_start else "---"
                end = title.data_end.strftime("%d.%m.%Y") if title.data_end else "---"
                self.comp_dates_label.setText(f"{start} - {end}")
                self.comp_mesto_label.setText(title.mesto or "-")
                self.comp_referee_label.setText(title.referee or "-")
                self.comp_referee_category_label.setText(title.kat_ref or "-")
                self.comp_secretary_label.setText(title.secretary or "-")
                self.comp_secretary_category_label.setText(title.kat_sec or "-")
                
                # Определяем пол по умолчанию (man/woman)
                if "девушки" in title.name.lower() or "дев" in title.name.lower() or "woman" in title.name.lower():
                    self.current_sex = "woman"
                else:
                    self.current_sex = "man"
                
                # Обновляем активность вкладок
                self.update_tabs_enabled()
                
                # Обновляем кнопки категорий
                self.create_category_buttons()
                
                # Загружаем участников
                self.load_participants_for_title()
                
                # Обновляем заголовок списка
                self.competitions_label.setText(f"🏆 Текущее: {title.name[:40]}...")
                self.competitions_label.setStyleSheet("""
                    background-color: #2196F3;
                    color: white;
                    padding: 8px;
                    font-weight: bold;
                    font-size: 12px;
                    border-radius: 3px;
                """)
                
                # Сбрасываем цвет заголовка через 2 секунды
                from PyQt5.QtCore import QTimer
                def reset_label():
                    count = self.list_widget.count()
                    self.competitions_label.setText(f"🏆 Прошедшие соревнования ({count})")
                    self.competitions_label.setStyleSheet("""
                        background-color: #4CAF50;
                        color: white;
                        padding: 8px;
                        font-weight: bold;
                        font-size: 12px;
                        border-radius: 3px;
                    """)
                QTimer.singleShot(2000, reset_label)

    def on_tab_changed(self, index):
        """Смена вкладки"""
        self.current_tab_index = index
        
        # ОБНОВЛЯЕМ ЛЕВУЮ ПАНЕЛЬ ПРИ СМЕНЕ ВКЛАДКИ (очищаем и пересоздаем)
        self.update_left_panel_for_tab(index)
        
        # Управление отображением правой панели в зависимости от вкладки
        if index == 0:  # Вкладка Титул
            self.competitions_label.setVisible(True)
            self.list_widget.setVisible(True)
            self.search_label.setVisible(False)
            self.search_results_list.setVisible(False)
            self.filters_widget.setVisible(True)
            
            # Убеждаемся, что форма создания скрыта, а информация видна
            if hasattr(self, 'new_comp_frame'):
                self.new_comp_frame.setVisible(False)
            if hasattr(self, 'info_group'):
                self.info_group.setVisible(True)
            
            # Загружаем список соревнований
            self.load_titles_list()
            
        elif index == 1:  # Вкладка Участники
            self.competitions_label.setVisible(False)
            self.list_widget.setVisible(False)
            self.search_label.setVisible(True)
            self.search_results_list.setVisible(True)
            self.filters_widget.setVisible(False)
            
            # Активируем поле поиска
            if hasattr(self, 'fio_edit'):
                self.fio_edit.setEnabled(True)
            
            # Загружаем участников для текущего соревнования
            if self.current_title_id:
                self.load_participants_for_title()
            else:
                self.players_model.setData([])
                self.table_header.setText("👥 Список участников - выберите соревнование из списка справа")
            
            # Изменяем размеры для увеличения таблицы
            QTimer.singleShot(100, self.resize_table_for_participants)
            
        else:
            # Для всех остальных вкладок
            self.competitions_label.setVisible(True)
            self.list_widget.setVisible(True)
            self.search_label.setVisible(False)
            self.search_results_list.setVisible(False)
            self.filters_widget.setVisible(False)
            
            # Устанавливаем заголовки для разных вкладок
            tab_names = {
                2: "🏆 Команды",
                3: "🤝 Пары",
                4: "⚙️ Система",
                5: "📊 Результаты",
                6: "⭐ Рейтинг",
                7: "ℹ️ Дополнительно"
            }
            if index in tab_names:
                self.competitions_label.setText(tab_names[index])
            
            # Загружаем соответствующие данные
            if index == 2 and self.current_title_id:
                self.load_teams_for_title()
            elif index == 3 and self.current_title_id:
                self.load_doubles_for_title()
            elif index == 5 and self.current_title_id:
                self.load_results_for_title()
            else:
                self.list_widget.clear()
        
        # Устанавливаем высоту для текущей вкладки
        self.set_tab_height(index)

    def format_age_to_u(self, vozrast):
        """Преобразование возраста в формат UXX"""
        if not vozrast:
            return ""
        
        # Если уже в формате U16
        if vozrast.upper().startswith('U'):
            return vozrast.upper()
        
        # Если формат "до 16 лет"
        if 'до' in vozrast:
            import re
            match = re.search(r'(\d+)', vozrast)
            if match:
                return f"U{match.group(1)}"
        
        # Если просто число
        if vozrast.isdigit():
            return f"U{vozrast}"
        
        return vozrast

    def extract_age_number(self, vozrast):
        """Извлечение числового значения возраста для сортировки"""
        if not vozrast:
            return 0
        
        import re
        match = re.search(r'(\d+)', vozrast)
        if match:
            return int(match.group(1))
        return 0
 
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
            player = Player.get_by_id(player_id)
            
            self.fio_edit.setText(player.fio or player.player or "")
            
            patronymic_text = ""
            if player.patronymic_id:
                patronymic = Patronymic.get_or_none(Patronymic.id == player.patronymic_id)
                if patronymic:
                    patronymic_text = patronymic.patronymic
            self.patronymic_edit.setText(patronymic_text)
            
            self.rank_edit.setText(str(player.rank) if player.rank else "0")
            self.city_edit.setText(player.city or "")
            
            # Устанавливаем регион в comboBox
            if player.region:
                index = self.region_combo.findText(player.region)
                if index >= 0:
                    self.region_combo.setCurrentIndex(index)
            
            # Устанавливаем разряд
            index = self.razryad_combo.findText(player.razryad or "б/р")
            if index >= 0:
                self.razryad_combo.setCurrentIndex(index)
            
            coach_text = ""
            if player.coach_id:
                coach = Coach.get_or_none(Coach.id == player.coach_id)
                if coach:
                    coach_text = coach.coach
            self.coach_edit.setText(coach_text)
            
            # Устанавливаем дату рождения
            if player.bday:
                if isinstance(player.bday, date):
                    self.birth_date_edit.setText(player.bday.strftime("%d.%m.%Y"))
            
            sex_index = 0 if player.sex == "man" else 1
            self.sex_combo.setCurrentIndex(sex_index)
            
            self.editing_player_id = player_id
            QMessageBox.information(self, "Редактирование", f"Редактирование: {player.fio}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")

    def save_edited_player(self):
        """Сохранение отредактированного участника"""
        if not hasattr(self, 'editing_player_id') or not self.editing_player_id:
            QMessageBox.warning(self, "Ошибка", "Нет выбранного участника для редактирования")
            return
        
        fio_input = self.fio_edit.text().strip()
        if not fio_input:
            QMessageBox.warning(self, "Ошибка", "Введите ФИО участника")
            return
        
        city = self.city_edit.text().strip()
        if not city:
            QMessageBox.warning(self, "Ошибка", "Введите город участника")
            return
        
        # Форматируем ФИО
        player_name, full_name = self.format_player_name(fio_input)
        fio_city = self.format_fio_city(fio_input, city)
        
        # Отображаем в поле ввода правильный формат
        self.fio_edit.setText(full_name)
        
        patronymic_text = self.patronymic_edit.text().strip()
        region = self.region_combo.currentText()
        coach_text = self.coach_edit.text().strip()
        rank_text = self.rank_edit.text().strip()
        
        if not region:
            QMessageBox.warning(self, "Ошибка", "Введите регион участника")
            return
        
        if not rank_text:
            QMessageBox.warning(self, "Ошибка", "Введите рейтинг участника")
            return
        
        try:
            rank = int(rank_text)
        except:
            QMessageBox.warning(self, "Ошибка", "Рейтинг должен быть числом")
            return
        
        birth_date = self.parse_birth_date(self.birth_date_edit.text())
        if not birth_date:
            QMessageBox.warning(self, "Ошибка", "Введите корректную дату рождения")
            return
        
        # Получаем дату начала соревнования
        title = Title.get_by_id(self.current_title_id)
        competition_start_date = title.data_start
        current_date = QDate.currentDate().toPyDate()
        
        # Проверяем возраст участника
        age_check_result = self.check_player_age(birth_date, competition_start_date, title.vozrast)
        
        if age_check_result == "too_young":
            QMessageBox.warning(self, "Ошибка", 
                            f"Игроку нет 8 лет на дату начала соревнования ({competition_start_date.strftime('%d.%m.%Y')}).")
            return
        elif age_check_result == "too_old":
            QMessageBox.warning(self, "Ошибка", 
                            f"Игрок превышает возрастное ограничение ({title.vozrast}).")
            return
        
        # Определяем статус заявки
        if current_date == competition_start_date:
            application_status = "основная"
        else:
            application_status = "предварительная"
        
        try:
            sex = "woman" if self.sex_combo.currentText() == "Женский" else "man"
            razryad = self.razryad_combo.currentText()
            
            # Преобразуем отчество в ID
            patronymic_id = None
            if patronymic_text and patronymic_text != "-":
                patronymic, created = Patronymic.get_or_create(
                    patronymic=patronymic_text,
                    defaults={'sex': "w" if sex == "woman" else "m"}
                )
                patronymic_id = patronymic.id
            
            # Преобразуем тренера в ID
            coach_id = None
            if coach_text and coach_text != "-":
                coach, created = Coach.get_or_create(coach=coach_text)
                coach_id = coach.id
            
            # Обновляем данные участника в таблице Player
            update_data = {
                'player': player_name,
                'fio': full_name,
                'fio_city': fio_city,
                'bday': birth_date,
                'rank': rank,
                'city': city,
                'region': region,
                'razryad': razryad,
                'sex': sex,
                'application': application_status,
                'patronymic_id': patronymic_id,
                'coach_id': coach_id,
                'mesto': 0
            }
            
            query = Player.update(**update_data).where(Player.id == self.editing_player_id)
            query.execute()
            
            # СИНХРОНИЗАЦИЯ С TABLICA Players_full
            players_full_data = {
                'player': player_name,
                'bday': birth_date,
                'city': city,
                'region': region,
                'razryad': razryad,
                'coach_id': coach_id,
                'patronymic_id': patronymic_id,
                'sex': sex
            }
            self.sync_with_players_full(players_full_data)
            
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
        """Обновление левой панели в зависимости от вкладки (полная очистка)"""
        # ПОЛНОСТЬЮ ОЧИЩАЕМ ЛЕВУЮ ПАНЕЛЬ
        for i in reversed(range(self.dynamic_filters_layout.count())):
            item = self.dynamic_filters_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Очищаем вложенные layout
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
        
        context = self.tab_context.get(tab_index, self.tab_context[0])
        
        # Обновляем заголовок и описание
        self.action_title.setText(f"🔧 {context['title']}")
        self.action_description.setText(context['description'])
        
        buttons = context["buttons"]
        
        # Проверяем, является ли список кнопок двумерным (для рядов)
        if buttons and isinstance(buttons[0], list):
            # Создаем ряды кнопок
            for row_buttons in buttons:
                row_layout = QHBoxLayout()
                row_layout.setSpacing(10)
                
                for btn_text in row_buttons:
                    btn = QPushButton(btn_text)
                    btn.setMinimumHeight(35)
                    btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #4CAF50;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 8px;
                            font-size: 11px;
                            font-weight: bold;
                        }
                        QPushButton:hover { background-color: #45a049; }
                    """)
                    
                    # Привязываем функции для вкладки Участники
                    if tab_index == 1:
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
                        elif btn_text == "🗑️ Очистить":
                            btn.clicked.connect(self.clear_player_form)
                    # Для вкладки Титул
                    elif tab_index == 0:
                        if btn_text == "📋 Создать новое":
                            btn.clicked.connect(self.new_competition)
                    
                    row_layout.addWidget(btn)
                
                self.dynamic_filters_layout.addLayout(row_layout)
        else:
            # Обычное отображение (для других вкладок)
            for btn_text in buttons:
                btn = QPushButton(btn_text)
                btn.setMinimumHeight(32)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 11px;
                        font-weight: bold;
                        text-align: left;
                        padding-left: 12px;
                    }
                    QPushButton:hover { background-color: #45a049; }
                """)
                
                if tab_index == 0:  # Титул
                    if btn_text == "📋 Создать новое":
                        btn.clicked.connect(self.new_competition)
                elif tab_index == 2:  # Команды
                    if btn_text == "➕ Добавить":
                        btn.clicked.connect(self.add_team)
                    elif btn_text == "✏️ Редактировать":
                        btn.clicked.connect(self.edit_team)
                    elif btn_text == "🗑️ Удалить":
                        btn.clicked.connect(self.delete_team)
                    elif btn_text == "⭐ Рейтинг":
                        btn.clicked.connect(self.show_team_rating)
                elif tab_index == 3:  # Пары
                    if btn_text == "🎲 Сформировать":
                        btn.clicked.connect(self.generate_pairs)
                    elif btn_text == "🔄 Разбить":
                        btn.clicked.connect(self.break_pairs)
                    elif btn_text == "📊 Посев":
                        btn.clicked.connect(self.seeding_pairs)
                elif tab_index == 5:  # Результаты
                    if btn_text == "📥 Загрузить":
                        btn.clicked.connect(self.load_results)
                    elif btn_text == "📤 Экспорт":
                        btn.clicked.connect(self.export_results)
                    elif btn_text == "🗑️ Очистить":
                        btn.clicked.connect(self.clear_results)
                    elif btn_text == "🧮 Рассчитать":
                        btn.clicked.connect(self.calculate_results)
                
                self.dynamic_filters_layout.addWidget(btn)
        
        # Добавляем фильтры ТОЛЬКО для вкладки Участники
        if tab_index == 1:
            self.add_participant_filters()
    
        self.dynamic_filters_layout.addStretch()

    def add_player_from_form(self):
        """Добавление участника из формы на вкладке Участники"""
        if not self.current_title_id:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите соревнование из списка")
            return
        
        # Получаем данные из формы
        fio_input = self.fio_edit.text().strip()
        if not fio_input:
            QMessageBox.warning(self, "Ошибка", "Введите ФИО участника")
            return
        
        patronymic_text = self.patronymic_edit.text().strip()
        city = self.city_edit.text().strip()
        region = self.region_combo.currentText()
        coach_text = self.coach_edit.text().strip()
        rank_text = self.rank_edit.text().strip()
        
        # Форматируем ФИО
        fio_input =f"{fio_input} {patronymic_text}"
        formatted_fio = self.format_fio_for_display(fio_input)
        self.fio_edit.setText(formatted_fio)
        fio_input = formatted_fio

        # Получаем дату рождения из QLineEdit
        birth_date_str = self.birth_date_edit.text()
        birth_date = self.parse_birth_date(birth_date_str)
        
        if not birth_date:
            QMessageBox.warning(self, "Ошибка", "Введите корректную дату рождения в формате ДД.ММ.ГГГГ")
            return
        
        if not city:
            QMessageBox.warning(self, "Ошибка", "Введите город участника")
            return
        
        if not region:
            QMessageBox.warning(self, "Ошибка", "Введите регион участника")
            return
        
        if not rank_text:
            QMessageBox.warning(self, "Ошибка", "Введите рейтинг участника")
            return
        
        try:
            rank = int(rank_text)
        except:
            QMessageBox.warning(self, "Ошибка", "Рейтинг должен быть числом")
            return
        
        # Формируем ФИО для полей player и fio
        player_name, full_name = self.format_player_name(fio_input)
        fio_city = self.format_fio_city(fio_input, city)
        
        # Получаем дату начала соревнования
        title = Title.get_by_id(self.current_title_id)
        competition_start_date = title.data_start
        current_date = QDate.currentDate().toPyDate()
        
        # Проверяем возраст участника
        age_check_result = self.check_player_age(birth_date, competition_start_date, title.vozrast)
        
        if age_check_result == "too_young":
            QMessageBox.warning(self, "Ошибка", 
                            f"Игроку нет 8 лет на дату начала соревнования ({competition_start_date.strftime('%d.%m.%Y')}).\n"
                            f"Минимальный возраст для участия - 8 лет.")
            return
        elif age_check_result == "too_old":
            QMessageBox.warning(self, "Ошибка", 
                            f"Игрок превышает возрастное ограничение ({title.vozrast}).\n"
                            f"На год соревнования ({competition_start_date.strftime('%d.%m.%Y')}) игроку должно быть не более {self.get_max_age_from_text(title.vozrast)} лет.")
            return
        
        # Определяем статус заявки (application)
        if current_date == competition_start_date:
            application_status = "основная"
        else:
            application_status = "предварительная"
        
        try:
            sex = "woman" if self.sex_combo.currentText() == "Женский" else "man"
            razryad = self.razryad_combo.currentText()
            
            # Преобразуем отчество в ID через таблицу Patronymic
            patronymic_id = None
            if patronymic_text and patronymic_text != "-":
                patronymic, created = Patronymic.get_or_create(
                    patronymic=patronymic_text,
                    defaults={'sex': "w" if sex == "woman" else "m"}
                )
                patronymic_id = patronymic.id
            
            # Преобразуем тренера в ID через таблицу Coach
            coach_id = None
            if coach_text and coach_text != "-":
                coach, created = Coach.get_or_create(coach=coach_text)
                coach_id = coach.id
            
            # Проверяем, существует ли уже такой участник в текущем соревновании
            existing = Player.get_or_none(
                (Player.player == player_name) & 
                (Player.title_id == self.current_title_id)
            )
            
            if existing:
                reply = QMessageBox.question(self, "Внимание", 
                                            f"Участник {player_name} уже существует.\nОбновить данные?",
                                            QMessageBox.Yes | QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
                
                update_data = {
                    'player': player_name,
                    'fio': full_name,
                    'fio_city': fio_city,
                    'bday': birth_date,
                    'rank': rank,
                    'city': city,
                    'region': region,
                    'razryad': razryad,
                    'title_id': self.current_title_id,
                    'sex': sex,
                    'application': application_status,
                    'patronymic_id': patronymic_id,
                    'coach_id': coach_id,
                    'mesto': 0
                }
                query = Player.update(**update_data).where(Player.id == existing.id)
                query.execute()
            else:
                Player.create(
                    player=player_name,
                    fio=full_name,
                    fio_city=fio_city,
                    bday=birth_date,
                    rank=rank,
                    city=city,
                    region=region,
                    razryad=razryad,
                    title_id=self.current_title_id,
                    sex=sex,
                    total_game_player=0,
                    total_win_game=0,
                    coefficient_victories=0.0,
                    application=application_status,
                    comment="",
                    pay_rejting="",
                    patronymic_id=patronymic_id,
                    coach_id=coach_id,
                    mesto=0
                )
            
            # СИНХРОНИЗАЦИЯ С TABLICA Players_full
            players_full_data = {
                'player': player_name,
                'bday': birth_date,
                'city': city,
                'region': region,
                'razryad': razryad,
                'coach_id': coach_id,
                'patronymic_id': patronymic_id,
                'sex': sex
            }
            self.sync_with_players_full(players_full_data)
            
            # Обновляем таблицу
            self.load_participants_for_title()
            
            # Очищаем форму
            self.fio_edit.clear()
            self.patronymic_edit.clear()
            self.birth_date_edit.clear()
            self.city_edit.clear()
            self.rank_edit.setText("0")
            self.razryad_combo.setCurrentIndex(0)
            self.coach_edit.clear()
            self.sex_combo.setCurrentIndex(0)
            
            # Устанавливаем фокус на поле ФИО
            self.fio_edit.setFocus()
            
            QMessageBox.information(self, "Успех", 
                                f"Участник {player_name} успешно добавлен\n"
                                f"Статус заявки: {application_status}")
            
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
        
        # Получаем ФИО для подтверждения
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
                QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")

    def update_table_header(self):
        """Обновление заголовка таблицы с количеством игроков"""
        if self.current_title_id:
            title = Title.get_or_none(Title.id == self.current_title_id)
            if title:
                sex_text = "Женщины" if self.current_sex == "woman" else "Мужчины"
                count = self.players_model.rowCount()
                age_text = f" ({title.vozrast})" if title.vozrast else ""
                
                # Подсчитываем количество основных и предварительных заявок
                main_count = Player.select().where(
                    (Player.title_id == self.current_title_id) &
                    (Player.application == "основная")
                ).count()
                
                pre_count = Player.select().where(
                    (Player.title_id == self.current_title_id) &
                    (Player.application == "предварительная")
                ).count()
                
                self.table_header.setText(f"👥 {title.name}{age_text} - {sex_text} ({count} чел.) | Основные: {main_count} | Предварительные: {pre_count}")
            
    def search_players(self):
        """Поиск участников по ФИО, городу, региону или тренеру"""
        if not self.current_title_id:
            QMessageBox.warning(self, "Ошибка", "Выберите соревнование")
            return
        
        # Создаем диалог поиска
        dialog = QDialog(self)
        dialog.setWindowTitle("Поиск участников")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Поле для ввода поискового запроса
        label = QLabel("Введите текст для поиска (ФИО, город, регион, тренер):")
        layout.addWidget(label)
        
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("Например: Иванов или Москва")
        layout.addWidget(search_edit)
        
        # Выбор типа поиска
        search_type_label = QLabel("Тип поиска:")
        layout.addWidget(search_type_label)
        
        search_type_combo = QComboBox()
        search_type_combo.addItems(["Везде", "По ФИО", "По городу", "По региону", "По тренеру"])
        layout.addWidget(search_type_combo)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        search_btn = QPushButton("🔍 Найти")
        search_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet("background-color: #f44336; color: white; padding: 5px;")
        buttons_layout.addWidget(search_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)
        
        # Результаты поиска
        result_label = QLabel("Результаты поиска:")
        result_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(result_label)
        
        result_list = QListWidget()
        result_list.setStyleSheet("""
            QListWidget {
                min-height: 200px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)
        layout.addWidget(result_list)
        
        # Кнопка перехода к выбранному участнику
        go_to_btn = QPushButton("📌 Перейти к выбранному участнику")
        go_to_btn.setEnabled(False)
        go_to_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 5px;")
        layout.addWidget(go_to_btn)
        
        def perform_search():
            search_text = search_edit.text().strip()
            if not search_text:
                QMessageBox.warning(dialog, "Ошибка", "Введите текст для поиска")
                return
            
            search_type = search_type_combo.currentText()
            result_list.clear()
            
            try:
                query = Player.select().where(Player.title_id == self.current_title_id)
                
                if self.current_sex:
                    query = query.where(Player.sex == self.current_sex)
                
                results = []
                for player in query:
                    # Получаем тренера
                    coach_name = ""
                    if player.coach_id:
                        coach = Coach.get_or_none(Coach.id == player.coach_id)
                        if coach:
                            coach_name = coach.coach
                    
                    match = False
                    highlight_text = ""
                    
                    if search_type == "Везде":
                        if (search_text.lower() in player.player.lower() or
                            search_text.lower() in (player.city or "").lower() or
                            search_text.lower() in (player.region or "").lower() or
                            search_text.lower() in coach_name.lower()):
                            match = True
                            # Определяем что найдено
                            if search_text.lower() in player.player.lower():
                                highlight_text = f"ФИО: {player.player}"
                            elif search_text.lower() in (player.city or "").lower():
                                highlight_text = f"Город: {player.city}"
                            elif search_text.lower() in (player.region or "").lower():
                                highlight_text = f"Регион: {player.region}"
                            elif search_text.lower() in coach_name.lower():
                                highlight_text = f"Тренер: {coach_name}"
                    
                    elif search_type == "По ФИО":
                        if search_text.lower() in player.player.lower():
                            match = True
                            highlight_text = f"ФИО: {player.player}"
                    
                    elif search_type == "По городу":
                        if search_text.lower() in (player.city or "").lower():
                            match = True
                            highlight_text = f"Город: {player.city}"
                    
                    elif search_type == "По региону":
                        if search_text.lower() in (player.region or "").lower():
                            match = True
                            highlight_text = f"Регион: {player.region}"
                    
                    elif search_type == "По тренеру":
                        if search_text.lower() in coach_name.lower():
                            match = True
                            highlight_text = f"Тренер: {coach_name}"
                    
                    if match:
                        results.append({
                            'id': player.id,
                            'fio': player.fio,
                            'city': player.city or "",
                            'region': player.region or "",
                            'coach': coach_name,
                            'rank': player.rank or 0,
                            'razryad': player.razryad or "",
                            'highlight': highlight_text
                        })
                
                if results:
                    for r in results:
                        item_text = f"🏅 {r['fio']}\n   📍 {r['city']} | {r['region']}\n   🎽 {r['razryad']} | Рейтинг: {r['rank']}\n   👨‍🏫 {r['coach']}\n   🔍 Найдено по: {r['highlight']}"
                        item = QListWidgetItem(item_text)
                        item.setData(Qt.UserRole, r['id'])
                        result_list.addItem(item)
                    
                    result_label.setText(f"Результаты поиска: найдено {len(results)} участников")
                    go_to_btn.setEnabled(True)
                else:
                    result_list.addItem("Ничего не найдено")
                    result_label.setText("Результаты поиска: ничего не найдено")
                    go_to_btn.setEnabled(False)
                    
            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Ошибка поиска: {str(e)}")
        
        def go_to_player():
            current_item = result_list.currentItem()
            if current_item:
                player_id = current_item.data(Qt.UserRole)
                if player_id:
                    # Находим строку в таблице с этим ID
                    for row in range(self.players_model.rowCount()):
                        if self.players_model.get_id(row) == player_id:
                            # Выделяем строку
                            self.table_view.selectRow(row)
                            self.table_view.scrollTo(self.table_view.model().index(row, 0))
                            dialog.accept()
                            QMessageBox.information(self, "Успех", "Участник найден и выделен в таблице")
                            return
                    
                    QMessageBox.warning(self, "Ошибка", "Участник не найден в текущем списке")
        
        # Подключаем сигналы
        search_btn.clicked.connect(perform_search)
        cancel_btn.clicked.connect(dialog.reject)
        go_to_btn.clicked.connect(go_to_player)
        result_list.itemDoubleClicked.connect(go_to_player)
        search_edit.returnPressed.connect(perform_search)
        
        dialog.exec_()
        
    def clear_participant_form(self):
        """Очистка формы участника"""
        self.fio_edit.clear()
        self.patronymic_edit.clear()
        self.birth_date_edit.clear()
        self.city_edit.clear()
        self.region_combo.setCurrentIndex(0)
        self.razryad_combo.setCurrentIndex(0)
        self.coach_edit.clear()
        self.rank_edit.setText("0")
        self.sex_combo.setCurrentIndex(0)
        
        # Очищаем результаты поиска
        self.search_results_list.clear()
        
        # Сбрасываем заголовок поиска
        self.reset_search_label()
        
        # Устанавливаем фокус на поле ФИО
        self.fio_edit.setFocus()
    
    def new_competition(self):
        """Создание нового соревнования с выбором типа и загрузкой рейтингов"""
        # Сначала спрашиваем тип соревнования
        dialog_type = QDialog(self)
        dialog_type.setWindowTitle("Выбор типа соревнования")
        dialog_type.setModal(True)
        dialog_type.setFixedSize(300, 120)
        
        layout = QVBoxLayout(dialog_type)
        layout.addWidget(QLabel("Выберите тип соревнования:"))
        
        btn_layout = QHBoxLayout()
        personal_btn = QPushButton("🏆 Личные")
        personal_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-size: 12px;")
        team_btn = QPushButton("👥 Командные")
        team_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px; font-size: 12px;")
        
        self.selected_tournament_type = None
        
        def set_personal():
            self.selected_tournament_type = "Личные"
            dialog_type.accept()
        
        def set_team():
            self.selected_tournament_type = "Командные"
            dialog_type.accept()
        
        personal_btn.clicked.connect(set_personal)
        team_btn.clicked.connect(set_team)
        
        btn_layout.addWidget(personal_btn)
        btn_layout.addWidget(team_btn)
        layout.addLayout(btn_layout)
        
        if dialog_type.exec_() != QDialog.Accepted or not self.selected_tournament_type:
            return
        
        # Открываем диалог выбора файлов рейтинга
        dialog = RatingFileDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Получаем дату из загруженных файлов
            rating_date = QDate.currentDate()
            rating_date_str = rating_date.toString("yyyy_MM")
            
            # Проверяем на актуальность
            if not self.check_existing_rating(rating_date_str):
                return
            
               # Создаем запись в таблице Title с временными значениями
            current_date = QDate.currentDate().toPyDate()
            rating_date_str = QDate.currentDate().toString("yyyy_MM")
            
            # Временные значения для short_name и full_name
            temp_short_name = "Новое"
            temp_full_name = f"Новое соревнование.{rating_date_str}.не указано"
            
            title_data = {
                'name': "",
                'short_name_comp': temp_short_name,
                'full_name_comp': temp_full_name,
                'sredi': "",
                'vozrast': "",
                'data_start': current_date,
                'data_end': current_date,
                'mesto': "",
                'city': "",
                'referee': "",
                'kat_ref': "",
                'secretary': "",
                'kat_sec': "",
                'vid_turnira': self.selected_tournament_type,
                'tab_enabled': "1",
                'multiregion': 0,
                'perenos': 0,
                'otchestvo': 0,
                'r_date': rating_date_str
            }
            
            # Создаем запись в БД
            title = Title.create(**title_data)
            self.current_title_id = title.id
            
            # Очищаем информацию о соревновании
            for label in [self.comp_name_label, self.comp_sredi_label, self.comp_vozrast_label,
                        self.comp_dates_label, self.comp_mesto_label,
                        self.comp_referee_label, self.comp_referee_category_label,
                        self.comp_secretary_label, self.comp_secretary_category_label]:
                if label:
                    label.setText("-")
            
            # Скрываем информацию, показываем форму
            self.info_group.setVisible(False)
            self.new_comp_frame.setVisible(True)  # <--- ФОРМА ДОЛЖНА БЫТЬ ВИДНА
            
            # Очищаем поля формы (но не скрываем её!)
            self.new_comp_name.clear()
            self.new_comp_sredi.setCurrentIndex(0)
            self.new_comp_vozrast.setCurrentIndex(0)
            self.new_comp_start.setDate(QDate.currentDate())
            self.new_comp_end.setDate(QDate.currentDate().addDays(7))
            self.new_comp_mesto.clear()
            self.new_comp_referee.clear()
            self.new_comp_referee_cat.setCurrentIndex(0)
            self.new_comp_secretary.clear()
            self.new_comp_secretary_cat.setCurrentIndex(0)
            
            # Устанавливаем фокус на поле название
            self.new_comp_name.setFocus()
            
            QMessageBox.information(self, "Успех", 
                                f"✅ Рейтинги успешно загружены!\n"
                                f"📅 Дата рейтинга: {rating_date_str}\n"
                                f"🏆 Тип соревнования: {self.selected_tournament_type}\n\n"
                                f"Теперь заполните информацию о соревновании.")
      
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

    def filter_by_alphabet(self):
        """Сортировка по алфавиту"""
        if not self.current_title_id:
            return
        
        try:
            query = Player.select().where(Player.title_id == self.current_title_id)
            if self.current_sex:
                query = query.where(Player.sex == self.current_sex)
            query = query.order_by(Player.player.asc())
            
            participants_data = []
            for player in query:
                # Получаем данные из связанных таблиц
                coach_name = ""
                if player.coach_id:
                    coach = Coach.get_or_none(Coach.id == player.coach_id)
                    if coach:
                        coach_name = coach.coach
                
                # Сохраняем coaches_data для фильтрации
                if not hasattr(self, 'coaches_data'):
                    self.coaches_data = {}
                self.coaches_data[player.id] = coach_name

                participants_data.append({
                    'id': player.id,
                    'fio': player.fio or "",
                    'birth_date': player.bday,
                    'rank': player.rank or 0,
                    'city': player.city or "",
                    'region': player.region or "",
                    'razryad': player.razryad or "",
                    'coach': coach_name,
                    'sex': player.sex or ""
                })
            self.players_model.setData(participants_data)
            QMessageBox.information(self, "Сортировка", "Список отсортирован по алфавиту")
        except Exception as e:
            print(f"Ошибка сортировки: {e}")

    def filter_by_rating(self):
        """Сортировка по убыванию рейтинга"""
        if not self.current_title_id:
            return
        
        try:
            query = Player.select().where(Player.title_id == self.current_title_id)
            if self.current_sex:
                query = query.where(Player.sex == self.current_sex)
            query = query.order_by(Player.rank.desc())
            
            participants_data = []
            for player in query:
                # Получаем данные из связанных таблиц
                coach_name = ""
                if player.coach_id:
                    coach = Coach.get_or_none(Coach.id == player.coach_id)
                    if coach:
                        coach_name = coach.coach
                
                # Сохраняем coaches_data для фильтрации
                if not hasattr(self, 'coaches_data'):
                    self.coaches_data = {}
                self.coaches_data[player.id] = coach_name

                participants_data.append({
                    'id': player.id,
                    'fio': player.fio or "",
                    'birth_date': player.bday,
                    'rank': player.rank or 0,
                    'city': player.city or "",
                    'region': player.region or "",
                    'razryad': player.razryad or "",
                    'coach': coach_name,
                    'sex': player.sex or ""
                })

            self.players_model.setData(participants_data)
            QMessageBox.information(self, "Сортировка", "Список отсортирован по рейтингу")
        except Exception as e:
            print(f"Ошибка сортировки: {e}")

    def filter_by_region(self):
        """Фильтр по регионам"""
        if not self.current_title_id:
            return
        
        region, ok = QInputDialog.getText(self, "Фильтр по региону", "Введите регион:")
        if ok and region:
            try:
                query = Player.select().where(
                    (Player.title_id == self.current_title_id) &
                    (Player.region.contains(region))
                )
                if self.current_sex:
                    query = query.where(Player.sex == self.current_sex)
                
                participants_data = []
                for player in query:
                    coach_name = ""
                    if player.coach_id:
                        coach = Coach.get_or_none(Coach.id == player.coach_id)
                        if coach:
                            coach_name = coach.coach
                    
                    participants_data.append({
                        'id': player.id,
                        'fio': player.fio or "",
                        'birth_date': player.bday,
                        'rank': player.rank or 0,
                        'city': player.city or "",
                        'region': player.region or "",
                        'razryad': player.razryad or "",
                        'coach': coach_name,
                        'sex': player.sex or ""
                    })
                self.players_model.setData(participants_data)
                QMessageBox.information(self, "Фильтр", f"Найдено {len(participants_data)} участников")
            except Exception as e:
                print(f"Ошибка: {e}")

    def filter_by_city(self):
        """Фильтр по городам"""
        if not self.current_title_id:
            return
        
        city, ok = QInputDialog.getText(self, "Фильтр по городу", "Введите город:")
        if ok and city:
            try:
                query = Player.select().where(
                    (Player.title_id == self.current_title_id) &
                    (Player.city.contains(city))
                )
                if self.current_sex:
                    query = query.where(Player.sex == self.current_sex)
                
                participants_data = []
                for player in query:
                    coach_name = ""
                    if player.coach_id:
                        coach = Coach.get_or_none(Coach.id == player.coach_id)
                        if coach:
                            coach_name = coach.coach
                    
                    participants_data.append({
                        'id': player.id,
                        'fio': player.fio or "",
                        'birth_date': player.bday,
                        'rank': player.rank or 0,
                        'city': player.city or "",
                        'region': player.region or "",
                        'razryad': player.razryad or "",
                        'coach': coach_name,
                        'sex': player.sex or ""
                    })
                self.players_model.setData(participants_data)
                QMessageBox.information(self, "Фильтр", f"Найдено {len(participants_data)} участников")
            except Exception as e:
                print(f"Ошибка: {e}")

    def filter_by_coach(self):
        """Фильтр по тренерам"""
        if not self.current_title_id:
            return
        
        coach_name, ok = QInputDialog.getText(self, "Фильтр по тренеру", "Введите фамилию тренера:")
        if ok and coach_name:
            try:
                # Ищем ID тренера
                coach = Coach.get_or_none(Coach.coach.contains(coach_name))
                if coach:
                    query = Player.select().where(
                        (Player.title_id == self.current_title_id) &
                        (Player.coach_id == coach.id)
                    )
                    if self.current_sex:
                        query = query.where(Player.sex == self.current_sex)
                    
                    participants_data = []
                    for player in query:
                        participants_data.append({
                            'id': player.id,
                            'fio': player.fio or "",
                            'birth_date': player.bday,
                            'rank': player.rank or 0,
                            'city': player.city or "",
                            'region': player.region or "",
                            'razryad': player.razryad or "",
                            'coach': coach.coach,
                            'sex': player.sex or ""
                        })
                    self.players_model.setData(participants_data)
                    QMessageBox.information(self, "Фильтр", f"Найдено {len(participants_data)} участников")
                else:
                    QMessageBox.information(self, "Фильтр", f"Тренер {coach_name} не найден")
            except Exception as e:
                print(f"Ошибка: {e}")

    def reset_filters(self):
        """Сброс всех фильтров и сортировок"""
        if not self.current_title_id:
            return
        
        self.load_participants_for_title()
        QMessageBox.information(self, "Сброс фильтров", "Все фильтры сброшены")

    def on_fio_text_changed(self, text):
        """Обработчик изменения текста в поле ФИО - поиск в списках"""
        if len(text) >= 2:
            # Не форматируем при вводе, только при нажатии Enter
            self.search_in_r_lists(text)
        else:
            # Очищаем результаты поиска
            if hasattr(self, 'search_results_list'):
                self.search_results_list.clear()
            if hasattr(self, 'search_label'):
                self.reset_search_label()

    def search_in_r_lists(self, search_text):
        """Поиск в таблицах рейтинг-листа по фамилии и имени"""
        if not hasattr(self, 'search_results_list'):
            return
        
        self.search_results_list.clear()
        
        results = []
        current_source = None
        
        # Разбиваем поисковый запрос на части
        search_parts = search_text.strip().split()
        search_surname = search_parts[0] if search_parts else search_text
        search_name = search_parts[1] if len(search_parts) > 1 else ""
        
        # Функция для проверки совпадения ФИО
        def matches_fio(fio, surname, name):
            if not fio:
                return False
            fio_parts = fio.strip().split()
            if not fio_parts:
                return False
            
            # Проверяем фамилию (первая часть)
            fio_surname = fio_parts[0].lower()
            if not fio_surname.startswith(surname.lower()):
                return False
            
            # Если имя задано, проверяем вторую часть
            if name:
                if len(fio_parts) >= 2:
                    fio_name = fio_parts[1].lower()
                    return fio_name.startswith(name.lower())
                return False
            
            return True
        
        # Определяем, какой рейтинг искать в зависимости от current_sex
        if self.current_sex == "woman":
            # Ищем в женских рейтингах
            try:
                from models import R_list_d, R1_list_d
                
                # Поиск в текущем женском рейтинге
                all_items = list(R_list_d.select())
                for item in all_items:
                    if matches_fio(item.r_fname, search_surname, search_name):
                        results.append({
                            'source': 'r_list_d',
                            'source_name': '🏆 Текущий рейтинг (Ж)',
                            'fio': item.r_fname,
                            'birthday': item.r_bithday,
                            'city': item.r_city,
                            'region': item.r_region,
                            'district': item.r_district,
                            'number': item.r_number,
                            'list': item.r_list,
                            'sex': 'woman'
                        })
                        current_source = 'current'
                        if len(results) >= 30:
                            break
                
                # Если не найдено в текущем, ищем в январском
                if not results:
                    all_items = list(R1_list_d.select())
                    for item in all_items:
                        if matches_fio(item.r1_fname, search_surname, search_name):
                            results.append({
                                'source': 'r1_list_d',
                                'source_name': '📅 Январский рейтинг (Ж)',
                                'fio': item.r1_fname,
                                'birthday': item.r1_bithday,
                                'city': item.r1_city,
                                'region': item.r1_region,
                                'district': item.r1_district,
                                'number': item.r1_number,
                                'list': item.r1_list,
                                'sex': 'woman'
                            })
                            current_source = 'january'
                            if len(results) >= 30:
                                break
                        
            except Exception as e:
                print(f"Ошибка поиска в женских рейтингах: {e}")
        
        else:  # current_sex == "man"
            # Ищем в мужских рейтингах
            try:
                from models import R_list_m, R1_list_m
                
                # Поиск в текущем мужском рейтинге
                all_items = list(R_list_m.select())
                for item in all_items:
                    if matches_fio(item.r_fname, search_surname, search_name):
                        results.append({
                            'source': 'r_list_m',
                            'source_name': '🏆 Текущий рейтинг (М)',
                            'fio': item.r_fname,
                            'birthday': item.r_bithday,
                            'city': item.r_city,
                            'region': item.r_region,
                            'district': item.r_district,
                            'number': item.r_number,
                            'list': item.r_list,
                            'sex': 'man'
                        })
                        current_source = 'current'
                        if len(results) >= 30:
                            break
                
                # Если не найдено в текущем, ищем в январском
                if not results:
                    all_items = list(R1_list_m.select())
                    for item in all_items:
                        if matches_fio(item.r1_fname, search_surname, search_name):
                            results.append({
                                'source': 'r1_list_m',
                                'source_name': '📅 Январский рейтинг (М)',
                                'fio': item.r1_fname,
                                'birthday': item.r1_bithday,
                                'city': item.r1_city,
                                'region': item.r1_region,
                                'district': item.r1_district,
                                'number': item.r1_number,
                                'list': item.r1_list,
                                'sex': 'man'
                            })
                            current_source = 'january'
                            if len(results) >= 30:
                                break
                        
            except Exception as e:
                print(f"Ошибка поиска в мужских рейтингах: {e}")
        
        if results and hasattr(self, 'search_label'):
            # Меняем заголовок
            if self.current_sex == "woman":
                if current_source == 'current':
                    self.search_label.setText("🔍 Текущий рейтинг (Женщины)")
                else:
                    self.search_label.setText("🔍 Январский рейтинг (Женщины)")
            else:
                if current_source == 'current':
                    self.search_label.setText("🔍 Текущий рейтинг (Мужчины)")
                else:
                    self.search_label.setText("🔍 Январский рейтинг (Мужчины)")
            
            self.search_label.setStyleSheet("""
                background-color: #2196F3;
                color: white;
                padding: 6px;
                font-weight: bold;
                font-size: 11px;
                border-radius: 3px;
            """)
            
            for r in results[:30]:
                birthday_str = r['birthday'].strftime("%d.%m.%Y") if r['birthday'] else "---"
                position = f"№{r['list']}" if r['list'] else "---"
                
                # Формируем строку для отображения
                item_text = f"🏅 {r['fio']} | {birthday_str} | {r['city']} | {position}"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, r)
                self.search_results_list.addItem(item)
                
        elif hasattr(self, 'search_label'):
            self.search_results_list.clear()
            self.search_label.setText("🔍 Ничего не найдено. Введите нового игрока вручную.")
            self.search_label.setStyleSheet("""
                background-color: #f44336;
                color: white;
                padding: 6px;
                font-weight: bold;
                font-size: 11px;
                border-radius: 3px;
            """)
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(3000, self.reset_search_label)

    def on_suggestion_selected(self, item):
        """Выбор предложения из списка - заполнение формы"""
        data = item.data(Qt.UserRole)
        if data:
            self.fio_edit.setText(data['fio'])
            
            # Устанавливаем дату рождения
            if data['birthday']:
                if isinstance(data['birthday'], date):
                    self.birth_date_edit.setText(data['birthday'].strftime("%d.%m.%Y"))
                elif isinstance(data['birthday'], str):
                    try:
                        d = datetime.strptime(data['birthday'], "%Y-%m-%d").date()
                        self.birth_date_edit.setText(d.strftime("%d.%m.%Y"))
                    except:
                        pass
            
            # Устанавливаем город
            self.city_edit.setText(data['city'] or "")
            
            # Устанавливаем регион в comboBox
            if data.get('region'):
                index = self.region_combo.findText(data['region'])
                if index >= 0:
                    self.region_combo.setCurrentIndex(index)
            
            # Устанавливаем пол
            if data['sex'] == 'man':
                self.sex_combo.setCurrentIndex(0)
            else:
                self.sex_combo.setCurrentIndex(1)
            
            self.suggestions_list.clear()
            self.suggestions_list.setVisible(False)
            self.patronymic_edit.setFocus()
            
    def focusOutEvent(self, event):
        """Событие потери фокуса - скрываем список предложений"""
        super().focusOutEvent(event)
        if hasattr(self, 'suggestions_list'):
            QTimer.singleShot(200, lambda: self.suggestions_list.setVisible(False))
            
    def on_search_result_selected(self, item):
        """Выбор результата поиска - заполнение формы"""
        data = item.data(Qt.UserRole)
        if data:
            # ФОРМАТИРУЕМ И ЗАПОЛНЯЕМ ФИО
            raw_fio = data['fio']
            # Разбиваем ФИО на части
            fio_parts = raw_fio.split()
            if len(fio_parts) >= 2:
                # Фамилия заглавными, имя с заглавной
                formatted_fio = f"{fio_parts[0].upper()} {fio_parts[1].capitalize()}"
                if len(fio_parts) >= 3:
                    formatted_fio += f" {fio_parts[2].capitalize()}"
            else:
                formatted_fio = raw_fio.capitalize()
            
            self.fio_edit.setText(formatted_fio)
            
            # Устанавливаем дату рождения
            birth_date = None
            if data['birthday']:
                if isinstance(data['birthday'], date):
                    birth_date = data['birthday']
                    self.birth_date_edit.setText(birth_date.strftime("%d.%m.%Y"))
                elif isinstance(data['birthday'], str):
                    try:
                        for fmt in ["%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d"]:
                            try:
                                birth_date = datetime.strptime(data['birthday'], fmt).date()
                                self.birth_date_edit.setText(birth_date.strftime("%d.%m.%Y"))
                                break
                            except:
                                continue
                    except:
                        pass
            
            # Устанавливаем город
            city = data['city'] if data['city'] else ""
            self.city_edit.setText(city)
            
            # Устанавливаем регион в ComboBox
            region = data['region'] if data['region'] else ""
            if region:
                index = self.region_combo.findText(region)
                if index >= 0:
                    self.region_combo.setCurrentIndex(index)
                else:
                    # Если регион не найден в списке, добавляем его
                    self.region_combo.addItem(region)
                    self.region_combo.setCurrentIndex(self.region_combo.count() - 1)
            
            # Устанавливаем пол
            player_sex = 'man' if (data['sex'] == 'man' or data['sex'] == 'man') else 'woman'
            if player_sex == 'man':
                self.sex_combo.setCurrentIndex(0)
                if self.current_sex == "woman":
                    QMessageBox.warning(self, "Внимание", 
                                    "Найден спортсмен мужского пола, но выбран фильтр 'Женщины'.\n"
                                    "Пожалуйста, переключите фильтр на 'Мужчины' для добавления.")
            else:
                self.sex_combo.setCurrentIndex(1)
                if self.current_sex == "man":
                    QMessageBox.warning(self, "Внимание", 
                                    "Найден спортсмен женского пола, но выбран фильтр 'Мужчины'.\n"
                                    "Пожалуйста, переключите фильтр на 'Женщины' для добавления.")
            
            # Устанавливаем рейтинг (если есть)
            if data.get('list'):
                self.rank_edit.setText(str(data['list']))
            
            # ПОИСК В ТАБЛИЦЕ Players_full
            if birth_date and city:
                existing_player = self.find_player_in_players_full(formatted_fio, birth_date, city)
                
                if existing_player:
                    # Заполняем недостающие поля из найденной записи
                    print(f"Найден игрок в Players_full: {existing_player.player}")
                    
                    # Отчество
                    if existing_player.patronymic_id:
                        patronymic = Patronymic.get_or_none(Patronymic.id == existing_player.patronymic_id)
                        if patronymic:
                            self.patronymic_edit.setText(patronymic.patronymic)
                    
                    # Разряд
                    if existing_player.razryad:
                        index = self.razryad_combo.findText(existing_player.razryad)
                        if index >= 0:
                            self.razryad_combo.setCurrentIndex(index)
                    
                    # Тренер
                    if existing_player.coach_id:
                        coach = Coach.get_or_none(Coach.id == existing_player.coach_id)
                        if coach:
                            self.coach_edit.setText(coach.coach)
                    
                    # Город (если в Players_full есть более точный город)
                    if existing_player.city:
                        self.city_edit.setText(existing_player.city)
                        # Обновляем регион для нового города
                        city_obj = City.get_or_none(City.city == existing_player.city)
                        if city_obj:
                            index = self.region_combo.findData(city_obj.region_id)
                            if index >= 0:
                                self.region_combo.setCurrentIndex(index)
                    
                    QMessageBox.information(self, "Найдено в базе", 
                                        f"Данные игрока найдены в общей базе.\n"
                                        f"Заполнены поля: Отчество, Разряд, Тренер")
                else:
                    # Предлагаем внести недостающие данные
                    reply = QMessageBox.question(self, "Новый игрок", 
                                                f"Игрок {formatted_fio} не найден в общей базе.\n"
                                                f"Внесите дополнительные данные (Отчество, Разряд) вручную?",
                                                QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        self.patronymic_edit.setFocus()
                    else:
                        # Заполняем минимальными значениями
                        if not self.patronymic_edit.text():
                            self.patronymic_edit.setText("-")
                        if not self.razryad_combo.currentText():
                            self.razryad_combo.setCurrentText("б/р")
            
            # Очищаем список результатов поиска
            self.search_results_list.clear()
            
            # Устанавливаем фокус на поле "Отчество"
            self.patronymic_edit.setFocus()
            # self.fio_edit.clear()

    def reset_search_label(self):
        """Сброс заголовка поиска"""
        if hasattr(self, 'current_tab_index') and self.current_tab_index == 1:
            if hasattr(self, 'search_label'):
                self.search_label.setText("🔍 Поиск игроков в рейтингах")
                self.search_label.setStyleSheet("""
                    background-color: #FF9800;
                    color: white;
                    padding: 6px;
                    font-weight: bold;
                    font-size: 11px;
                    border-radius: 3px;
                """)

    def filter_competitions(self):
        """Фильтрация списка соревнований по критериям"""
        if not hasattr(self, 'search_name_edit'):
            return
        
        search_text = self.search_name_edit.text().strip().lower()
        year_filter = self.year_combo.currentText()
        month_filter = self.month_combo.currentText()
        sredi_filter = self.sredi_combo.currentText()
        
        self.list_widget.clear()
        
        try:
            titles = Title.select().order_by(Title.data_start.desc())
            
            filtered_titles = []
            
            for title in titles:
                # Фильтр по названию
                if search_text and search_text not in title.name.lower():
                    continue
                
                # Фильтр по категории "Среди"
                if sredi_filter != "Все категории" and title.sredi != sredi_filter:
                    continue
                
                # Фильтр по году и месяцу
                if title.data_start:
                    if year_filter != "Все годы" and str(title.data_start.year) != year_filter:
                        continue
                    if month_filter != "Все месяцы":
                        month_num = self.get_month_number(month_filter)
                        if title.data_start.month != month_num:
                            continue
                else:
                    if year_filter != "Все годы" or month_filter != "Все месяцы":
                        continue
                
                filtered_titles.append(title)
            
            # Отображаем отфильтрованные соревнования
            for title in filtered_titles:
                start_date = title.data_start.strftime("%d.%m.%Y") if title.data_start else "---"
                
                item_text = f"""🏆 {title.name}
    📅 {start_date} | {title.mesto}
    👥 {title.sredi} | {title.vozrast}
    🏷️ {title.vid_turnira}"""
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, title.id)
                item.setSizeHint(QSize(0, 65))
                self.list_widget.addItem(item)
            
            # Показываем количество найденных
            count = len(filtered_titles)
            self.competitions_label.setText(f"🏆 Прошедшие соревнования ({count})")
            
        except Exception as e:
            print(f"Ошибка фильтрации: {e}")
            self.load_titles_list()

    def get_month_number(self, month_name):
        """Преобразование названия месяца в номер"""
        months = {
            "Январь": 1, "Февраль": 2, "Март": 3, "Апрель": 4,
            "Май": 5, "Июнь": 6, "Июль": 7, "Август": 8,
            "Сентябрь": 9, "Октябрь": 10, "Ноябрь": 11, "Декабрь": 12
        }
        return months.get(month_name, 0)

    def reset_filters_on_title_tab(self):
        """Сброс всех фильтров на вкладке Титул"""
        self.search_name_edit.clear()
        self.year_combo.setCurrentIndex(0)
        self.month_combo.setCurrentIndex(0)
        self.sredi_combo.setCurrentIndex(0)
        self.load_titles_list()

    def save_new_competition(self):
        """Сохранение нового соревнования"""
        name = self.new_comp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название соревнования")
            return
        
        # Запрашиваем короткое имя
        short_name, ok = QInputDialog.getText(self, "Короткое имя соревнования", 
                                            "Введите короткое имя соревнования:",
                                            text=name[:20] if len(name) > 20 else name)
        
        if not ok or not short_name.strip():
            reply = QMessageBox.question(self, "Внимание", 
                                        "Короткое имя не введено. Использовать полное название?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                short_name = name[:30]
            else:
                return
        
        # Формируем полное имя
        start_date = self.new_comp_start.date().toPyDate()
        date_str = start_date.strftime("%Y-%m-%d")
        category = self.new_comp_sredi.currentText()
        full_name = f"{name}.{date_str}.{category}"
        
        try:
            from models import Referee, Title
            
            # Сохраняем главного судью
            referee_name = self.new_comp_referee.text().strip()
            if referee_name:
                referee, created = Referee.get_or_create(
                    family=referee_name,
                    defaults={
                        'city': '',
                        'category': self.new_comp_referee_cat.currentText(),
                        'signature': None
                    }
                )
            
            # Сохраняем главного секретаря
            secretary_name = self.new_comp_secretary.text().strip()
            if secretary_name:
                secretary, created = Referee.get_or_create(
                    family=secretary_name,
                    defaults={
                        'city': '',
                        'category': self.new_comp_secretary_cat.currentText(),
                        'signature': None
                    }
                )
            
            rating_date_str = QDate.currentDate().toString("yyyy_MM")
            
            if not self.current_title_id:
                # Создаем новое соревнование
                title = Title.create(
                    name=name,
                    short_name_comp=short_name.strip(),
                    full_name_comp=full_name,
                    sredi=self.new_comp_sredi.currentText(),
                    vozrast=self.new_comp_vozrast.currentText(),
                    data_start=start_date,
                    data_end=self.new_comp_end.date().toPyDate(),
                    mesto=self.new_comp_mesto.text().strip(),
                    city="",
                    referee=referee_name,
                    kat_ref=self.new_comp_referee_cat.currentText(),
                    secretary=secretary_name,
                    kat_sec=self.new_comp_secretary_cat.currentText(),
                    vid_turnira=self.selected_tournament_type if hasattr(self, 'selected_tournament_type') else "Личные",
                    tab_enabled="Титул Участники",  # Сразу активируем вкладку Участники
                    multiregion=0,
                    perenos=0,
                    otchestvo=0,
                    r_date=rating_date_str
                )
                self.current_title_id = title.id
            else:
                # Обновляем существующее
                title = Title.get_by_id(self.current_title_id)
                title.name = name
                title.short_name_comp = short_name.strip()
                title.full_name_comp = full_name
                title.sredi = self.new_comp_sredi.currentText()
                title.vozrast = self.new_comp_vozrast.currentText()
                title.data_start = start_date
                title.data_end = self.new_comp_end.date().toPyDate()
                title.mesto = self.new_comp_mesto.text().strip()
                title.referee = referee_name
                title.kat_ref = self.new_comp_referee_cat.currentText()
                title.secretary = secretary_name
                title.kat_sec = self.new_comp_secretary_cat.currentText()
                title.tab_enabled = "Титул Участники"  # Активируем вкладку Участники
                title.save()

            # Обновляем активность вкладок
            self.update_tabs_enabled()
            
            # Скрываем форму и показываем информацию
            self.new_comp_frame.setVisible(False)
            self.info_group.setVisible(True)
            
            # Обновляем информацию
            self.comp_name_label.setText(name)
            self.comp_sredi_label.setText(title.sredi)
            self.comp_vozrast_label.setText(title.vozrast)
            self.comp_dates_label.setText(f"{title.data_start.strftime('%d.%m.%Y')} - {title.data_end.strftime('%d.%m.%Y')}")
            self.comp_mesto_label.setText(title.mesto)
            self.comp_referee_label.setText(referee_name or "-")
            self.comp_referee_category_label.setText(title.kat_ref)
            self.comp_secretary_label.setText(secretary_name or "-")
            self.comp_secretary_category_label.setText(title.kat_sec)
            
            # Обновляем список годов и соревнований
            self.load_years_from_titles()
            self.filter_competitions()
            
            # Переключаемся на вкладку Участники
            self.tab_widget.setCurrentIndex(1)
            
            # Загружаем участников
            self.load_participants_for_title()
            
            # АКТИВИРУЕМ ПОЛЕ ПОИСКА СПОРТСМЕНА
            self.fio_edit.setEnabled(True)
            self.fio_edit.setFocus()
            
            QMessageBox.information(self, "Успех", 
                                f"✅ Соревнование '{name}' сохранено!\n"
                                f"🏆 Тип: {title.vid_turnira}\n"
                                f"📅 Дата рейтинга: {title.r_date}\n"
                                f"📝 Короткое имя: {title.short_name_comp}\n"
                                f"📋 Полное имя: {title.full_name_comp}\n\n"
                                f"Теперь можно добавлять участников")
            
            # Очищаем форму
            self.new_comp_name.clear()
            self.new_comp_sredi.setCurrentIndex(0)
            self.new_comp_vozrast.setCurrentIndex(0)
            self.new_comp_start.setDate(QDate.currentDate())
            self.new_comp_end.setDate(QDate.currentDate().addDays(7))
            self.new_comp_mesto.clear()
            self.new_comp_referee.clear()
            self.new_comp_referee_cat.setCurrentIndex(0)
            self.new_comp_secretary.clear()
            self.new_comp_secretary_cat.setCurrentIndex(0)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить соревнование: {str(e)}")    

    def cancel_new_competition(self):
        """Отмена создания нового соревнования (только при нажатии кнопки Отмена)"""
        # Очищаем форму
        self.new_comp_name.clear()
        self.new_comp_sredi.setCurrentIndex(0)
        self.new_comp_vozrast.setCurrentIndex(0)
        self.new_comp_start.setDate(QDate.currentDate())
        self.new_comp_end.setDate(QDate.currentDate().addDays(7))
        self.new_comp_mesto.clear()
        self.new_comp_referee.clear()
        self.new_comp_referee_cat.setCurrentIndex(0)
        self.new_comp_secretary.clear()
        self.new_comp_secretary_cat.setCurrentIndex(0)
        
        # Скрываем форму, показываем информацию
        self.new_comp_frame.setVisible(False)
        self.info_group.setVisible(True)
        
        # Сбрасываем фокус
        self.new_comp_name.clearFocus()
        
        # Если есть временная запись с пустым названием, удаляем её
        if self.current_title_id:
            try:
                title = Title.get_by_id(self.current_title_id)
                if not title.name or title.name == "":  # Временная запись
                    title.delete_instance()
                    self.current_title_id = None
            except:
                pass

    def load_years_from_titles(self):
        """Загрузка годов из существующих соревнований для фильтра"""
        try:
            # Получаем уникальные годы из таблицы Title
            years = set()
            
            titles = Title.select(Title.data_start).where(Title.data_start.is_null(False))
            for title in titles:
                if title.data_start:
                    years.add(str(title.data_start.year))
            
            # Сортируем годы
            sorted_years = sorted(list(years), key=lambda x: int(x) if x.isdigit() else 0)
            
            # Обновляем comboBox
            self.year_combo.clear()
            self.year_combo.addItem("Все годы")
            for year in sorted_years:
                self.year_combo.addItem(year)
            
            # Устанавливаем первый год из списка (самый ранний)
            if sorted_years:
                self.year_combo.setCurrentText(sorted_years[0])
                
        except Exception as e:
            print(f"Ошибка загрузки годов: {e}")
            # Если ошибка, добавляем стандартные годы
            self.year_combo.clear()
            self.year_combo.addItem("Все годы")
            current_year = QDate.currentDate().year()
            for year in range(current_year - 5, current_year + 2):
                self.year_combo.addItem(str(year))

    def on_new_referee_text_changed(self, text):
        """Поиск судьи при вводе текста"""
        if len(text) >= 3:
            self.find_referee_in_db(text, self.new_comp_referee_cat)

    def on_new_secretary_text_changed(self, text):
        """Поиск секретаря при вводе текста"""
        if len(text) >= 3:
            self.find_referee_in_db(text, self.new_comp_secretary_cat)

    def find_referee_in_db(self, search_text, category_combo):
        """Поиск судьи в базе данных"""
        try:
            from models import Referee
            referees = Referee.select().where(Referee.family.contains(search_text))
            
            if referees.count() > 0:
                referee = referees.first()
                # Устанавливаем категорию
                index = category_combo.findText(referee.category)
                if index >= 0:
                    category_combo.setCurrentIndex(index)
        except Exception as e:
            print(f"Ошибка поиска судьи: {e}")

    def check_rating_date(self, new_date):
        """Проверка актуальности даты рейтинга"""
        if self.current_title_id:
            title = Title.get_by_id(self.current_title_id)
            if title.r_date:
                reply = QMessageBox.question(self, "Подтверждение", 
                                            f"Рейтинг уже загружен ({title.r_date}).\nЗаменить на {new_date}?",
                                            QMessageBox.Yes | QMessageBox.No)
                return reply == QMessageBox.Yes
        return True

    def check_existing_rating(self, rating_date):
        """Проверка существования рейтинга с указанной датой"""
        existing = Title.select().where(Title.r_date == rating_date)
        if existing.count() > 0:
            reply = QMessageBox.question(self, "Внимание", 
                                        f"Рейтинг за {rating_date} уже существует.\n"
                                        f"Заменить на новый?",
                                        QMessageBox.Yes | QMessageBox.No)
            return reply == QMessageBox.Yes
        return True

    def setup_enter_navigation(self):
        """Настройка навигации по полям формы с помощью Enter"""
        # Название -> Категория
        self.new_comp_name.returnPressed.connect(lambda: self.new_comp_sredi.setFocus())
        
        # Категория -> Возраст
        self.new_comp_sredi.activated.connect(lambda: self.new_comp_vozrast.setFocus())
        
        # Возраст -> Дата начала
        self.new_comp_vozrast.activated.connect(lambda: self.new_comp_start.setFocus())
        
        # Дата начала -> Дата окончания
        self.new_comp_start.dateChanged.connect(lambda: self.new_comp_end.setFocus())
        
        # Дата окончания -> Место проведения
        self.new_comp_end.dateChanged.connect(lambda: self.new_comp_mesto.setFocus())
        
        # Место проведения -> Главный судья
        self.new_comp_mesto.returnPressed.connect(lambda: self.new_comp_referee.setFocus())
        
        # Главный судья -> Категория судьи
        self.new_comp_referee.returnPressed.connect(lambda: self.new_comp_referee_cat.setFocus())
        
        # Категория судьи -> Главный секретарь
        self.new_comp_referee_cat.activated.connect(lambda: self.new_comp_secretary.setFocus())
        
        # Главный секретарь -> Категория секретаря
        self.new_comp_secretary.returnPressed.connect(lambda: self.new_comp_secretary_cat.setFocus())

    def set_rating_date_to_form(self, rating_date):
        """Установка даты рейтинга в форму"""
        try:
            # Парсим дату из формата yyyy_MM
            year = int(rating_date.split('_')[0])
            month = int(rating_date.split('_')[1])
            
            # Устанавливаем дату начала на первое число месяца рейтинга
            start_date = QDate(year, month, 1)
            self.new_comp_start.setDate(start_date)
            
            # Устанавливаем дату окончания на последний день месяца рейтинга
            if month == 12:
                end_date = QDate(year + 1, 1, 1).addDays(-1)
            else:
                end_date = QDate(year, month + 1, 1).addDays(-1)
            self.new_comp_end.setDate(end_date)
            
        except Exception as e:
            print(f"Ошибка установки даты рейтинга: {e}")

    def update_tabs_enabled(self):
        """Обновление активности вкладок в зависимости от tab_enabled"""
        tab_dict = {'Титул': 0,
                    'Участники': 1,
                    'Команды': 2,
                    'Пары': 3,
                    'Система': 4,
                    'Результаты': 5,
                    'Рейтинг': 6,
                    'Дополнительно': 7}

        if not self.current_title_id:
            # Если нет выбранного соревнования, отключаем все вкладки кроме Титул
            for i in range(self.tab_widget.count()):
                self.tab_widget.setTabEnabled(i, False)
            self.tab_widget.setTabEnabled(0, True)  # Титул всегда активен
            return
        
        try:
            title = Title.get_by_id(self.current_title_id)
            tab_enabled = title.tab_enabled if title.tab_enabled else "Титул"
            
            # Вкладка Титул всегда активна (индекс 0)
            self.tab_widget.setTabEnabled(0, True)
            
            result = tab_enabled.split()

            for i in result:
                idx = tab_dict[i]
                self.tab_widget.setTabEnabled(idx, True)

            # Если текущая вкладка неактивна, переключаемся на Титул
            if not self.tab_widget.isTabEnabled(self.tab_widget.currentIndex()):
                self.tab_widget.setCurrentIndex(0)
            
        except Exception as e:
            print(f"Ошибка обновления вкладок: {e}")
            # По умолчанию активируем только Титул
            for i in range(self.tab_widget.count()):
                self.tab_widget.setTabEnabled(i, False)
            self.tab_widget.setTabEnabled(0, True)

    def find_similar_competitions(self, name, start_date, end_date):
        """Поиск похожих соревнований для группировки"""
        similar = Title.select().where(
            (Title.name == name) &
            (Title.data_start == start_date) &
            (Title.data_end == end_date)
        )
        return list(similar)
    
    def show_competitions_by_date(self, date):
        """Показать все соревнования на указанную дату"""
        try:
            competitions = Title.select().where(Title.data_start == date)
            
            if competitions.count() > 0:
                comp_list = []
                for comp in competitions:
                    comp_list.append(f"🏆 {comp.name}\n   📅 {comp.data_start.strftime('%d.%m.%Y')} | {comp.vozrast} | {comp.sredi}\n")
                
                comps_text = "\n".join(comp_list)
                
                QMessageBox.information(self, f"Соревнования на {date.strftime('%d.%m.%Y')}", comps_text)
        except Exception as e:
            print(f"Ошибка: {e}")

    def check_competitions_by_date(self, title):
        """Проверка сколько соревнований на ту же дату (без вывода сообщения)"""
        try:
            # Ищем все соревнования с такими же датами
            same_date_competitions = Title.select().where(
                (Title.data_start == title.data_start) &
                (Title.data_end == title.data_end)
            )
            return same_date_competitions.count()
        except Exception as e:
            print(f"Ошибка проверки дат: {e}")
            return 0

    def find_similar_by_name_and_date(self, title):
        """Поиск соревнований с похожим названием и датой"""
        try:
            # Ищем соревнования с таким же названием и датами
            similar = Title.select().where(
                (Title.name == title.name) &
                (Title.data_start == title.data_start) &
                (Title.data_end == title.data_end)
            )
            return list(similar)
        except Exception as e:
            print(f"Ошибка поиска похожих: {e}")
            return []

    def add_context_menu_to_list(self):
        """Добавление контекстного меню к списку соревнований"""
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_list_context_menu)

    def show_list_context_menu(self, position):
        """Показать контекстное меню для списка соревнований"""
        item = self.list_widget.itemAt(position)
        if not item:
            return
        
        title_id = item.data(Qt.UserRole)
        if not title_id:
            return
        
        title = Title.get_or_none(Title.id == title_id)
        if not title:
            return
        
        menu = QMenu()
        
        # Действие: показать все соревнования на эту дату
        show_date_action = QAction(f"📅 Показать все соревнования на {title.data_start.strftime('%d.%m.%Y')}", self)
        show_date_action.triggered.connect(lambda: self.show_competitions_by_date(title.data_start))
        menu.addAction(show_date_action)
        
        # Действие: найти похожие соревнования
        similar_action = QAction("🔍 Найти похожие соревнования", self)
        similar_action.triggered.connect(lambda: self.show_similar_competitions(title))
        menu.addAction(similar_action)
        
        menu.exec_(self.list_widget.mapToGlobal(position))

    def show_similar_competitions(self, title):
        """Показать похожие соревнования"""
        similar = self.find_similar_by_name_and_date(title)
        
        if len(similar) > 1:
            comp_list = []
            for comp in similar:
                comp_list.append(f"🏆 {comp.name}\n   👥 {comp.sredi} | {comp.vozrast}\n   🏷️ {comp.vid_turnira}\n")
            
            comps_text = "\n".join(comp_list)
            QMessageBox.information(self, f"Похожие соревнования ({len(similar)})", comps_text)
        else:
            QMessageBox.information(self, "Похожие соревнования", "Нет других соревнований с таким же названием и датами")

    def create_date_group_buttons(self):
        """Создание кнопок для группировки соревнований по датам"""
        try:
            # Получаем уникальные даты
            dates = Title.select(Title.data_start).distinct().order_by(Title.data_start.desc())
            
            # Очищаем существующие кнопки
            for i in reversed(range(self.date_buttons_layout.count())):
                widget = self.date_buttons_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()
            
            for date in dates:
                if date.data_start:
                    btn = QPushButton(date.data_start.strftime("%d.%m.%Y"))
                    btn.setMinimumHeight(30)
                    btn.clicked.connect(lambda checked, d=date.data_start: self.filter_by_date(d))
                    self.date_buttons_layout.addWidget(btn)
                    
        except Exception as e:
            print(f"Ошибка создания кнопок по датам: {e}")

    def filter_by_date(self, date):
        """Фильтрация соревнований по дате"""
        self.list_widget.clear()
        
        try:
            titles = Title.select().where(Title.data_start == date).order_by(Title.name)
            
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
            
            self.competitions_label.setText(f"🏆 Соревнования на {date.strftime('%d.%m.%Y')} ({titles.count()})")
            
        except Exception as e:
            print(f"Ошибка фильтрации: {e}")

    def switch_gender_category(self, sex):
        """Переключение между man и woman"""
        if self.current_sex == sex:
            return
        
        self.current_sex = sex
        
        # Перезагружаем участников с фильтром по полу
        self.load_participants_for_title()
        
        # Обновляем кнопки
        self.create_category_buttons()
        
        # Обновляем заголовок таблицы
        if self.current_title_id:
            title = Title.get_or_none(Title.id == self.current_title_id)
            if title:
                sex_text = "Женщины" if sex == "woman" else "Мужчины"
                count = self.players_model.rowCount()
                age_text = f" ({title.vozrast})" if title.vozrast else ""
                self.table_header.setText(f"👥 {title.name}{age_text} - {sex_text} ({count} чел.)")
        
        # Очищаем результаты поиска при смене пола
        self.search_results_list.clear()
        
        # Сбрасываем заголовок поиска
        self.reset_search_label()
        
        # # Показываем сообщение о смене рейтинга
        # if sex == "woman":
        #     QMessageBox.information(self, "Поиск", "Теперь поиск будет выполняться в женских рейтинг-листах")
        # else:
        #     QMessageBox.information(self, "Поиск", "Теперь поиск будет выполняться в мужских рейтинг-листах")

    def load_participants_for_title(self):
        """Загрузка участников для выбранного соревнования"""
        if not self.current_title_id:
            self.players_model.setData([])
            self.table_header.setText("👥 Список участников - выберите соревнование")
            return
        
        try:
            # Базовый запрос
            query = Player.select().where(Player.title_id == self.current_title_id)
            
            # Применяем фильтр по полу
            if self.current_sex == "woman":
                query = query.where(Player.sex == "woman")
            elif self.current_sex == "man":
                query = query.where(Player.sex == "man")
            
            # Сортируем по рейтингу
            query = query.order_by(Player.rank.desc())
            
            participants_data = []
            for player in query:
                coach_name = ""
                if player.coach_id:
                    coach = Coach.get_or_none(Coach.id == player.coach_id)
                    if coach:
                        coach_name = coach.coach
                
                participants_data.append({
                    'id': player.id,
                    'fio': player.fio or player.player or "",
                    'birth_date': player.bday,
                    'rank': player.rank or 0,
                    'city': player.city or "",
                    'region': player.region or "",
                    'razryad': player.razryad or "",
                    'coach': coach_name,
                    'sex': player.sex or "",
                    'application': player.application or "предварительная"
                })
            
            self.players_model.setData(participants_data)
            self.update_table_header()
            
        except Exception as e:
            print(f"Ошибка загрузки участников: {e}")
            self.players_model.setData([])

    def load_last_competition(self):
        """Загрузка последнего соревнования по умолчанию"""
        try:
            last_title = Title.select().order_by(Title.data_start.desc()).first()
            
            if last_title:
                self.current_title_id = last_title.id
                
                self.comp_name_label.setText(last_title.name or "-")
                self.comp_short_name_label.setText(last_title.short_name_comp or "-")
                self.comp_full_name_label.setText(last_title.full_name_comp or "-")
                self.comp_sredi_label.setText(last_title.sredi or "-")
                self.comp_vozrast_label.setText(last_title.vozrast or "-")
                self.comp_type_info_label.setText(last_title.vid_turnira or "-")
                
                start = last_title.data_start.strftime("%d.%m.%Y") if last_title.data_start else "---"
                end = last_title.data_end.strftime("%d.%m.%Y") if last_title.data_end else "---"
                self.comp_dates_label.setText(f"{start} - {end}")
                self.comp_mesto_label.setText(last_title.mesto or "-")
                self.comp_referee_label.setText(last_title.referee or "-")
                self.comp_referee_category_label.setText(last_title.kat_ref or "-")
                self.comp_secretary_label.setText(last_title.secretary or "-")
                self.comp_secretary_category_label.setText(last_title.kat_sec or "-")
                
                if "девушки" in last_title.name.lower() or "дев" in last_title.name.lower():
                    self.current_sex = "woman"
                else:
                    self.current_sex = "man"
                
                self.update_tabs_enabled()
                self.create_category_buttons()
                self.load_participants_for_title()
                
                for i in range(self.list_widget.count()):
                    item = self.list_widget.item(i)
                    if item.data(Qt.UserRole) == last_title.id:
                        self.list_widget.setCurrentItem(item)
                        break
                        
        except Exception as e:
            print(f"Ошибка загрузки последнего соревнования: {e}")

    def reset_search_label(self):
        """Сброс заголовка поиска"""
        if hasattr(self, 'current_tab_index') and self.current_tab_index == 1:
            if hasattr(self, 'search_label'):
                if self.current_sex == "woman":
                    self.search_label.setText("🔍 Поиск игроков в женских рейтингах")
                else:
                    self.search_label.setText("🔍 Поиск игроков в мужских рейтингах")
                self.search_label.setStyleSheet("""
                    background-color: #FF9800;
                    color: white;
                    padding: 6px;
                    font-weight: bold;
                    font-size: 11px;
                    border-radius: 3px;
                """)    

    def check_player_age(self, birth_date, competition_start_date, age_limit_text):
        """Проверка возраста участника"""
        if not birth_date or not competition_start_date:
            return "ok"
        
        # Вычисляем возраст на дату начала соревнования
        age_at_competition = competition_start_date.year - birth_date.year
        # Корректировка, если день рождения еще не наступил
        if (competition_start_date.month, competition_start_date.day) < (birth_date.month, birth_date.day):
            age_at_competition -= 1
        
        # Проверяем минимальный возраст (8 лет)
        if age_at_competition < 8:
            return "too_young"
        
        # Получаем максимальный возраст из текста ограничения
        max_age = self.get_max_age_from_text(age_limit_text)
        
        # Проверяем максимальный возраст
        if max_age is not None and age_at_competition >= max_age:
            return "too_old"
        
        return "ok"

    def get_max_age_from_text(self, age_text):
        """Извлечение максимального возраста из текста (например 'до 16 лет' -> 16, 'U16' -> 16)"""
        if not age_text:
            return None
        
        import re
        
        # Формат "до X лет"
        match = re.search(r'до (\d+)', age_text)
        if match:
            return int(match.group(1))
        
        # Формат "UXX"
        match = re.search(r'U(\d+)', age_text.upper())
        if match:
            return int(match.group(1))
        
        # Формат "XX лет"
        match = re.search(r'(\d+) лет', age_text)
        if match:
            return int(match.group(1))
        
        # Если число простое
        if age_text.isdigit():
            return int(age_text)
        
        return None

    def get_min_age_from_text(self, age_text):
        """Извлечение минимального возраста из текста (обычно 8 лет по умолчанию)"""
        return 8  # Минимальный возраст для всех соревнований

    def clear_participant_form_on_error(self):
        """Очистка формы при ошибке (поля ФИО остаются для исправления)"""
        self.patronymic_edit.clear()
        self.birth_date.setDate(QDate.currentDate().addYears(-18))
        self.city_edit.clear()
        self.region_edit.clear()
        self.razryad_combo.setCurrentIndex(0)
        self.coach_edit.clear()
        self.rank_edit.clear()
        self.sex_combo.setCurrentIndex(0)
        self.fio_edit.setFocus()

    def clear_player_form(self):
        """Очистка формы участника (вызывается по кнопке на левой панели)"""
        reply = QMessageBox.question(self, "Подтверждение", 
                                    "Очистить все поля формы?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.fio_edit.clear()
            self.patronymic_edit.clear()
            # self.birth_date.setDate(QDate.currentDate().addYears(-18))
            self.birth_date_edit.clear()
            self.city_edit.clear()
            self.region_combo.setCurrentIndex(0)
            self.razryad_combo.setCurrentIndex(0)
            self.coach_edit.clear()
            self.rank_edit.clear()
            self.sex_combo.setCurrentIndex(0)
            
            # Очищаем результаты поиска
            self.search_results_list.clear()
            
            # Сбрасываем заголовок поиска
            self.reset_search_label()
            
            # Устанавливаем фокус на поле ФИО
            self.fio_edit.setFocus()
            
            QMessageBox.information(self, "Очистка", "Форма очищена")
            
    def format_full_name(self, player):
        """Форматирование ФИО: первая буква заглавная, остальные строчные"""
        if not player:
            return ""
        
        # Разбиваем на части
        parts = player.strip().split()
        formatted_parts = []
        
        # Делаем первую букву заглавной, остальные строчными
        formatted_parts = f"{parts[0].upper()} {parts[1].capitalize()}"

        return formatted_parts
    
    def find_player_in_players_full(self, player, birth_date, city):
        """Поиск игрока в таблице players_full по ФИО, дате рождения и городу"""
        try:
            # Форматируем ФИО для поиска
            player_normalized = self.format_full_name(player)
            
            # Ищем игрока по ФИО и дате рождения
            query = Players_full.select().where(
                (Players_full.player == player_normalized) &
                (Players_full.bday == birth_date) &
                (Players_full.city == city)
            )
            
            if query.count() > 0:
                return query.first()
            
            # Если не нашли по полному совпадению, ищем по ФИО и дате рождения (без города)
            query2 = Players_full.select().where(
                (Players_full.player == player_normalized) &
                (Players_full.bday == birth_date)
            )
            
            if query2.count() > 0:
                return query2.first()
            
            return None
        except Exception as e:
            print(f"Ошибка поиска в players_full: {e}")
            return None 

    def add_team(self):
        QMessageBox.information(self, "Добавление", "Добавление команды")

    def edit_team(self):
        QMessageBox.information(self, "Редактирование", "Редактирование команды")

    def delete_team(self):
        QMessageBox.information(self, "Удаление", "Удаление команды")

    def show_team_rating(self):
        QMessageBox.information(self, "Рейтинг", "Рейтинг команд")

    def generate_pairs(self):
        QMessageBox.information(self, "Пары", "Формирование пар")

    def break_pairs(self):
        QMessageBox.information(self, "Пары", "Разбивка пар")

    def seeding_pairs(self):
        QMessageBox.information(self, "Пары", "Посев пар")

    def system_settings(self):
        QMessageBox.information(self, "Система", "Настройки системы")

    def system_parameters(self):
        QMessageBox.information(self, "Система", "Параметры системы")

    def system_reset(self):
        QMessageBox.information(self, "Система", "Сброс настроек")

    def load_results(self):
        QMessageBox.information(self, "Результаты", "Загрузка результатов")

    def export_results(self):
        QMessageBox.information(self, "Результаты", "Экспорт результатов")

    def clear_results(self):
        QMessageBox.information(self, "Результаты", "Очистка результатов")

    def calculate_results(self):
        QMessageBox.information(self, "Результаты", "Расчет результатов")

    def update_rating(self):
        QMessageBox.information(self, "Рейтинг", "Обновление рейтинга")

    def show_top10(self):
        QMessageBox.information(self, "Рейтинг", "Топ-10 рейтинга")

    def calculate_rating(self):
        QMessageBox.information(self, "Рейтинг", "Расчет рейтинга")

    def show_notes(self):
        QMessageBox.information(self, "Заметки", "Показать заметки")

    def show_help(self):
        QMessageBox.information(self, "Справка", "Справка по программе")           

    def get_players_count_by_status(self, title_id, status=None):
        """Получение количества игроков по статусу заявки"""
        try:
            query = Player.select().where(Player.title_id == title_id)
            if status:
                query = query.where(Player.application == status)
            return query.count()
        except Exception as e:
            print(f"Ошибка подсчета игроков: {e}")
            return 0
    
    def format_player_name(self, fio):
        """Форматирование имени игрока:
        - player: ИВАНОВ Иван (фамилия ЗАГЛАВНЫМИ, имя с заглавной)
        - fio: ИВАНОВ Иван Иванович (фамилия ЗАГЛАВНЫМИ, имя и отчество с заглавной)
        - fio_city: ИВАНОВ Иван Иванович/Москва
        """
        if not fio:
            return "", "", ""
        
        # Разбиваем строку на части
        parts = fio.strip().split()
        
        if len(parts) == 1:
            surname = parts[0].upper()
            name = ""
            patronymic = ""
        elif len(parts) == 2:
            surname = parts[0].upper()
            name = parts[1].capitalize()
            patronymic = ""
        else:
            surname = parts[0].upper()
            name = parts[1].capitalize()
            patronymic = parts[2].capitalize()
        
        # Формируем player (ИВАНОВ Иван)
        player_name = f"{surname} {name}".strip()
        
        # Формируем fio (ИВАНОВ Иван Иванович)
        if patronymic:
            full_name = f"{surname} {name} {patronymic}".strip()
        else:
            full_name = f"{surname} {name}".strip()
        
        return player_name, full_name

    def format_fio_city(self, fio, city):
        """Форматирование поля fio_city: ИВАНОВ Иван Иванович/Москва"""
        if not fio:
            return ""
        
        # Форматируем ФИО
        _, full_name = self.format_player_name(fio)
        
        # Добавляем город
        if city:
            return f"{full_name}/{city}"
        else:
            return full_name

    def filter_preliminary_applications(self):
        """Фильтрация предварительных заявок"""
        if not self.current_title_id:
            return
        
        if self.btn_filter_preliminary.isChecked():
            try:
                query = Player.select().where(
                    (Player.title_id == self.current_title_id) &
                    (Player.application == "предварительная")
                )
                
                if self.current_sex == "woman":
                    query = query.where(Player.sex == "woman")
                elif self.current_sex == "man":
                    query = query.where(Player.sex == "man")
                
                query = query.order_by(Player.rank.desc())
                
                participants_data = []
                for player in query:
                    coach_name = ""
                    if player.coach_id:
                        coach = Coach.get_or_none(Coach.id == player.coach_id)
                        if coach:
                            coach_name = coach.coach
                    
                    participants_data.append({
                        'id': player.id,
                        'fio': player.fio or player.player or "",
                        'birth_date': player.bday,
                        'rank': player.rank or 0,
                        'city': player.city or "",
                        'region': player.region or "",
                        'razryad': player.razryad or "",
                        'coach': coach_name,
                        'sex': player.sex or "",
                        'application': player.application or "предварительная"
                    })
                
                self.players_model.setData(participants_data)
                self.update_table_header()
                QMessageBox.information(self, "Фильтр", f"Показано {len(participants_data)} предварительных заявок")
                
            except Exception as e:
                print(f"Ошибка фильтрации: {e}")
        else:
            self.reset_application_filter()

    def reset_application_filter(self):
        """Сброс фильтра заявок и показ всех участников"""
        if not self.current_title_id:
            return
        
        self.btn_filter_preliminary.setChecked(False)
        self.load_participants_for_title()
        QMessageBox.information(self, "Сброс фильтра", "Показаны все заявки")

    def confirm_selected_applications(self):
        """Подтверждение выбранных заявок (перевод из предварительной в основную)"""
        selection = self.table_view.selectionModel().selectedRows()
        if not selection:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одного участника для подтверждения")
            return
        
        # Собираем ID выбранных участников
        selected_ids = []
        for index in selection:
            row = index.row()
            player_id = self.players_model.get_id(row)
            if player_id:
                selected_ids.append(player_id)
        
        if not selected_ids:
            return
        
        # Запрашиваем подтверждение
        reply = QMessageBox.question(self, "Подтверждение", 
                                    f"Подтвердить заявки {len(selected_ids)} участников?\n"
                                    f"Статус изменится с 'предварительная' на 'основная'.",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                # Обновляем статус заявок
                for player_id in selected_ids:
                    Player.update(application="основная").where(Player.id == player_id).execute()
                
                # Обновляем таблицу
                if self.btn_filter_preliminary.isChecked():
                    self.filter_preliminary_applications()
                else:
                    self.load_participants_for_title()
                
                QMessageBox.information(self, "Успех", f"Подтверждено {len(selected_ids)} заявок")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось подтвердить заявки: {str(e)}")

    def on_patronymic_text_changed(self, text):
        """Обработчик изменения текста в поле Отчество - обновление списка для QCompleter"""
        if len(text) >= 2:
            self.update_patronymic_completer(text)
        else:
            self.patronymic_completer.setModel(QStringListModel([]))
        
    def on_patronymic_enter_pressed(self):
        """Обработка Enter в поле Отчество"""
        text = self.patronymic_edit.text().strip()
        if text:
            # Добавляем отчество в таблицу Patronymic, если его там нет
            patronymic, created = Patronymic.get_or_create(
                patronymic=text,
                defaults={'sex': "М"}  # По умолчанию мужской род
            )
        self.birth_date.setFocus()
        self.birth_date.selectAll()

    def on_coach_text_changed(self, text):
        """Обработчик изменения текста в поле Тренер - обновление списка для QCompleter"""
        if len(text) >= 2:
            self.update_coach_completer(text)
        else:
            self.coach_completer.setModel(QStringListModel([]))

    def on_coach_enter_pressed(self):
        """Обработка Enter в поле Тренер"""
        self.sex_combo.setFocus()

    def on_fio_enter_pressed(self):
        """Обработка Enter в поле ФИО - форматирование фамилии и имени"""
        text = self.fio_edit.text().strip()
        if not text:
            self.patronymic_edit.setFocus()
            return
        
        # Форматируем ФИО
        formatted_text = self.format_fio_for_display(text)
        self.fio_edit.setText(formatted_text)
        
        # Если есть текст, выполняем поиск в рейтинг-листе
        if len(text) >= 2:
            self.search_in_r_lists(text)
        
        # Переход к полю Отчество
        self.patronymic_edit.setFocus()

    def on_birth_date_enter_pressed(self):
        """Обработка Enter в поле Дата рождения"""
        self.city_edit.setFocus()

    def on_rank_enter_pressed(self):
        """Обработка Enter в поле Рейтинг"""
        self.city_edit.setFocus()

    def on_region_enter_pressed(self):
        """Обработка Enter в поле Регион"""
        self.razryad_combo.setFocus()

    def on_razryad_enter_pressed(self):
        """Обработка Enter в поле Разряд"""
        self.coach_edit.setFocus()

    def starts_with_ignore_case(self, text, prefix):
        """Проверка, начинается ли строка с префикса (без учета регистра)"""
        if not text or not prefix:
            return False
        return text.lower().startswith(prefix.lower())

    def format_fio_for_display(self, fio_text):
        """Форматирование ФИО: фамилия ЗАГЛАВНЫМИ, имя с заглавной буквы"""
        if not fio_text:
            return ""
        
        # Разбиваем строку на части
        parts = fio_text.strip().split()
        
        if len(parts) == 1:
            # Только фамилия
            return parts[0].upper()
        
        elif len(parts) == 2:
            # Фамилия и имя
            surname = parts[0].upper()
            name = parts[1].capitalize()
            return f"{surname} {name}"
        
        else:
            # Фамилия, имя, отчество
            surname = parts[0].upper()
            name = parts[1].capitalize()
            patronymic = parts[2].capitalize()
            return f"{surname} {name} {patronymic}"

    def on_city_text_changed(self, text):
        """Обработчик изменения текста в поле Город - обновление списка для QCompleter"""
        if len(text) >= 2:
            self.update_city_completer(text)
        else:
            self.city_completer.setModel(QStringListModel([]))

    def on_birth_date_enter_pressed(self):
        """Обработка Enter в поле Дата рождения"""
        date_text = self.birth_date_edit.text()
        # Проверка корректности даты
        try:
            day, month, year = map(int, date_text.split('.'))
            if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2024:
                # Дата корректна
                pass
            else:
                QMessageBox.warning(self, "Ошибка", "Введите корректную дату в формате ДД.ММ.ГГГГ")
                self.birth_date_edit.setFocus()
                return
        except:
            QMessageBox.warning(self, "Ошибка", "Введите дату в формате ДД.ММ.ГГГГ")
            self.birth_date_edit.setFocus()
            return
        
        self.rank_edit.setFocus()

    def on_rank_enter_pressed(self):
        """Обработка Enter в поле Рейтинг"""
        self.city_edit.setFocus()

    def parse_birth_date(self, date_str):
        """Преобразование строки даты в объект date"""
        try:
            day, month, year = map(int, date_str.split('.'))
            return date(year, month, day)
        except:
            return None

    def on_razryad_activated(self):
        """Обработка выбора в поле Разряд"""
        self.coach_edit.setFocus()

    def on_sex_activated(self):
        """Обработка выбора в поле Пол (последнее поле)"""
        # Можно оставить пустым или добавить автоматическое добавление
        pass

    def on_patronymic_enter_pressed(self):
        """Обработка Enter в поле Отчество"""
        text = self.patronymic_edit.text().strip()
        if text and text.startswith('+ Добавить'):
            # Извлекаем текст для добавления
            new_text = text.replace('+ Добавить \'', '').replace('\'', '')
            self.patronymic_edit.setText(new_text)
            Patronymic.get_or_create(patronymic=new_text, defaults={'sex': "ьфт"})
        
        self.birth_date_edit.setFocus()
        self.birth_date_edit.selectAll()

    def on_birth_date_enter_pressed(self):
        """Обработка Enter в поле Дата рождения"""
        date_text = self.birth_date_edit.text()
        import re
        if re.match(r'\d{2}\.\d{2}\.\d{4}', date_text):
            try:
                day, month, year = map(int, date_text.split('.'))
                if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2024:
                    # Автоматически подставляем рейтинг 0
                    self.rank_edit.setText("0")
                    self.city_edit.setFocus()
                    return
            except:
                pass
        QMessageBox.warning(self, "Ошибка", "Введите корректную дату в формате ДД.ММ.ГГГГ")
        self.birth_date_edit.setFocus()
        self.birth_date_edit.selectAll()

    def on_rank_enter_pressed(self):
        """Обработка Enter в поле Рейтинг"""
        self.city_edit.setFocus()

    def on_region_enter_pressed(self):
        """Обработка Enter в поле Регион (ComboBox)"""
        self.razryad_combo.setFocus()

    def on_coach_enter_pressed(self):
        """Обработка Enter в поле Тренер"""
        text = self.coach_edit.text().strip()
        if text and text.startswith('+ Добавить'):
            new_text = text.replace('+ Добавить \'', '').replace('\'', '')
            self.coach_edit.setText(new_text)
            Coach.get_or_create(coach=new_text)
        
        self.sex_combo.setFocus()

    def on_region_enter_pressed(self):
        """Обработка Enter в поле Регион (ComboBox)"""
        self.razryad_combo.setFocus()

    def focusOutEvent(self, event):
        """Событие потери фокуса - скрываем списки предложений"""
        super().focusOutEvent(event)
        
        # Скрываем список предложений для отчества
        if hasattr(self, 'patronymic_suggestions'):
            QTimer.singleShot(200, lambda: self.patronymic_suggestions.setVisible(False))
        
        # Скрываем список предложений для города
        if hasattr(self, 'city_suggestions'):
            QTimer.singleShot(200, lambda: self.city_suggestions.setVisible(False))
        
        # Скрываем список предложений для тренера
        if hasattr(self, 'coach_suggestions'):
            QTimer.singleShot(200, lambda: self.coach_suggestions.setVisible(False))

    def update_coach_completer(self, search_text):
        """Обновление списка подсказок для тренера"""
        try:
            query = Coach.select().where(
                Coach.coach.startswith(search_text)
            ).limit(20)
            
            items = [item.coach for item in query]
            
            if not items:
                items = [f"+ Добавить '{search_text}'"]
            
            model = QStringListModel(items)
            self.coach_completer.setModel(model)
            
        except Exception as e:
            print(f"Ошибка обновления списка тренеров: {e}")

    def update_patronymic_completer(self, search_text):
        """Обновление списка подсказок для отчества с фильтрацией по полу"""
        try:
            from models import Patronymic
            
            # Определяем пол текущего соревнования
            if self.current_sex == "woman":
                sex_filter = "w"
            else:
                sex_filter = "m"
            
            # Ищем отчества, начинающиеся с введенного текста, и соответствующие полу
            query = Patronymic.select().where(
                (Patronymic.patronymic.startswith(search_text)) &
                (Patronymic.sex == sex_filter)
            ).limit(20)
            
            items = [item.patronymic for item in query]
            
            # Добавляем предложение добавить новое, если ничего не найдено
            if not items:
                items = [f"+ Добавить '{search_text}'"]
            
            model = QStringListModel(items)
            self.patronymic_completer.setModel(model)
            
        except Exception as e:
            print(f"Ошибка обновления списка отчеств: {e}")

    def update_city_completer(self, search_text):
        """Обновление списка подсказок для города"""
        try:
            from models import City, Region
            query = City.select().where(
                City.city.startswith(search_text)
            ).limit(20)
            
            items = []
            for city in query:
                items.append(f"{city.city}")
            
            if not items:
                items = [f"+ Добавить '{search_text}'"]
            
            model = QStringListModel(items)
            self.city_completer.setModel(model)
            
        except Exception as e:
            print(f"Ошибка обновления списка городов: {e}")

    def update_coach_completer(self, search_text):
        """Обновление списка подсказок для тренера"""
        try:
            from models import Coach
            query = Coach.select().where(
                Coach.coach.startswith(search_text)
            ).limit(20)
            
            items = [item.coach for item in query]
            
            if not items:
                items = [f"+ Добавить '{search_text}'"]
            
            model = QStringListModel(items)
            self.coach_completer.setModel(model)
            
        except Exception as e:
            print(f"Ошибка обновления списка тренеров: {e}")

    def on_patronymic_enter_pressed(self):
        """Обработка Enter в поле Отчество"""
        text = self.patronymic_edit.text().strip()
        if text and text.startswith('+ Добавить'):
            # Извлекаем текст для добавления
            new_text = text.replace('+ Добавить \'', '').replace('\'', '')
            self.patronymic_edit.setText(new_text)
            
            # Определяем пол для нового отчества
            if self.current_sex == "woman":
                sex_value = "w"
            else:
                sex_value = "m"
            
            from models import Patronymic
            Patronymic.get_or_create(patronymic=new_text, defaults={'sex': sex_value})
        
        self.birth_date_edit.setFocus()
        self.birth_date_edit.selectAll()

    def on_city_enter_pressed(self):
        """Обработка Enter в поле Город"""
        city_text = self.city_edit.text().strip()
        if not city_text:
            self.region_combo.setFocus()
            return
        
        try:
            from models import City, Region
            
            # Ищем город в базе данных (без учета регистра)
            city = City.get_or_none(City.city ** city_text)
            
            if city:
                # Город найден, подставляем регион
                print(f"Город найден: {city.city}, region_id={city.region_id}")
                
                # Ищем регион по ID в comboBox
                region_found = False
                for i in range(self.region_combo.count()):
                    item_data = self.region_combo.itemData(i)
                    if item_data == city.region_id:
                        self.region_combo.setCurrentIndex(i)
                        region_found = True
                        QMessageBox.information(self, "Информация", 
                                            f"Город '{city_text}' найден.\nРегион: {self.region_combo.currentText()}")
                        break
                
                if not region_found:
                    # Если не нашли по data, пробуем найти по названию региона
                    region = Region.get_or_none(Region.id == city.region_id)
                    if region:
                        for i in range(self.region_combo.count()):
                            if self.region_combo.itemText(i) == region.region:
                                self.region_combo.setCurrentIndex(i)
                                region_found = True
                                break
                    
                    if not region_found:
                        QMessageBox.warning(self, "Ошибка", f"Регион для города '{city_text}' не найден в списке")
            else:
                # Город не найден, предлагаем создать новый
                reply = QMessageBox.question(self, "Новый город", 
                                            f"Город '{city_text}' не найден в базе данных.\n"
                                            f"Создать новый город с выбором региона?",
                                            QMessageBox.Yes | QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    # Открываем диалог выбора региона
                    dialog = QDialog(self)
                    dialog.setWindowTitle("Выбор региона")
                    dialog.setModal(True)
                    dialog.setFixedSize(400, 150)
                    
                    layout = QVBoxLayout(dialog)
                    layout.addWidget(QLabel(f"Выберите регион для города '{city_text}':"))
                    
                    region_combo = QComboBox()
                    # Загружаем все регионы
                    regions = Region.select().order_by(Region.region)
                    for region in regions:
                        region_combo.addItem(region.region, region.id)
                    
                    layout.addWidget(region_combo)
                    
                    btn_layout = QHBoxLayout()
                    ok_btn = QPushButton("OK")
                    ok_btn.clicked.connect(dialog.accept)
                    cancel_btn = QPushButton("Отмена")
                    cancel_btn.clicked.connect(dialog.reject)
                    btn_layout.addWidget(ok_btn)
                    btn_layout.addWidget(cancel_btn)
                    layout.addLayout(btn_layout)
                    
                    if dialog.exec_() == QDialog.Accepted:
                        region_id = region_combo.currentData()
                        if region_id:
                            # Получаем название региона
                            region = Region.get_or_none(Region.id == region_id)
                            region_name = region.region if region else ""
                            
                            # Создаем новый город
                            City.create(city=city_text, region_id=region_id)
                            
                            # Обновляем регион в основном comboBox
                            region_found = False
                            for i in range(self.region_combo.count()):
                                if self.region_combo.itemData(i) == region_id:
                                    self.region_combo.setCurrentIndex(i)
                                    region_found = True
                                    break
                            
                            if not region_found:
                                # Если не нашли, добавляем новый регион в comboBox
                                self.region_combo.addItem(region_name, region_id)
                                self.region_combo.setCurrentIndex(self.region_combo.count() - 1)
                            
                            QMessageBox.information(self, "Успех", 
                                                f"Город '{city_text}' добавлен в базу данных\n"
                                                f"Регион: {region_name}")
                        else:
                            QMessageBox.warning(self, "Ошибка", "Регион не выбран")
                else:
                    # Пользователь отказался создавать новый город
                    QMessageBox.information(self, "Информация", 
                                        f"Город '{city_text}' не будет добавлен.\n"
                                        f"Выберите регион вручную из списка.")
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Ошибка при обработке города: {e}")
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")
        
        # Переход к следующему полю
        self.region_combo.setFocus()

    def on_coach_enter_pressed(self):
        """Обработка Enter в поле Тренер"""
        text = self.coach_edit.text().strip()
        if text and text.startswith('+ Добавить'):
            new_text = text.replace('+ Добавить \'', '').replace('\'', '')
            self.coach_edit.setText(new_text)
            from models import Coach
            Coach.get_or_create(coach=new_text)
        
        self.sex_combo.setFocus() 

    def on_patronymic_text_changed(self, text):
        """Обработчик изменения текста в поле Отчество - обновление списка для QCompleter"""
        if len(text) >= 2:
            self.update_patronymic_completer(text)
        else:
            self.patronymic_completer.setModel(QStringListModel([]))

    def on_city_text_changed(self, text):
        """Обработчик изменения текста в поле Город - обновление списка для QCompleter"""
        if len(text) >= 2:
            self.update_city_completer(text)
        else:
            self.city_completer.setModel(QStringListModel([]))

    def on_coach_text_changed(self, text):
        """Обработчик изменения текста в поле Тренер - обновление списка для QCompleter"""
        if len(text) >= 2:
            self.update_coach_completer(text)
        else:
            self.coach_completer.setModel(QStringListModel([]))           

    def load_regions(self):
        """Загрузка регионов в comboBox"""
        self.region_combo.clear()
        try:
            from models import Region
            regions = Region.select().order_by(Region.region)
            for region in regions:
                self.region_combo.addItem(region.region, region.id)
            print(f"Загружено {regions.count()} регионов")  # Отладка
        except Exception as e:
            print(f"Ошибка загрузки регионов: {e}")

    def sync_with_players_full(self, player_data):
        """Синхронизация данных с таблицей Players_full"""
        try:
            from models import Players_full, Patronymic, Coach
            
            # Получаем или создаем запись в Players_full
            players_full, created = Players_full.get_or_create(
                player=player_data['player'],
                bday=player_data['bday'],
                defaults={
                    'city': player_data['city'],
                    'region': player_data['region'],
                    'razryad': player_data['razryad'],
                    'coach_id': player_data.get('coach_id'),
                    'patronymic_id': player_data.get('patronymic_id'),
                    'sex': player_data['sex']
                }
            )
            
            if not created:
                # Обновляем существующую запись
                players_full.city = player_data['city']
                players_full.region = player_data['region']
                players_full.razryad = player_data['razryad']
                players_full.coach_id = player_data.get('coach_id')
                players_full.patronymic_id = player_data.get('patronymic_id')
                players_full.sex = player_data['sex']
                players_full.save()
                print(f"Обновлена запись в Players_full для {player_data['player']}")
            else:
                print(f"Создана новая запись в Players_full для {player_data['player']}")
            
            return players_full
            
        except Exception as e:
            print(f"Ошибка синхронизации с Players_full: {e}")
            return None
        
    def add_participant_filters(self):
        """Добавление фильтров для вкладки Участники"""
        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #ccc; max-height: 1px; margin: 10px 0;")
        self.dynamic_filters_layout.addWidget(line)
        
        # Создаем контейнер для фильтров
        filters_container = QWidget()
        filters_layout = QVBoxLayout(filters_container)
        filters_layout.setSpacing(8)
        
        # Заголовок фильтров
        filter_title = QLabel("📊 Сортировка")
        filter_title.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 5px;")
        filters_layout.addWidget(filter_title)
        
        # Строка с кнопками сортировки
        sort_layout = QHBoxLayout()
        sort_layout.setSpacing(10)
        
        btn_sort_alpha = QPushButton("🔤 По алфавиту (А-Я)")
        btn_sort_alpha.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        btn_sort_alpha.clicked.connect(self.filter_by_alphabet)
        sort_layout.addWidget(btn_sort_alpha)
        
        btn_sort_rating = QPushButton("📊 По убыванию рейтинга")
        btn_sort_rating.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        btn_sort_rating.clicked.connect(self.filter_by_rating)
        sort_layout.addWidget(btn_sort_rating)
        
        filters_layout.addLayout(sort_layout)
        
        # Заголовок фильтров
        filter_title2 = QLabel("🎯 Фильтры")
        filter_title2.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 5px;")
        filters_layout.addWidget(filter_title2)
        
        # Строка с кнопками фильтров
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        
        btn_filter_region = QPushButton("🗺️ По регионам")
        btn_filter_region.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        btn_filter_region.clicked.connect(self.filter_by_region)
        filter_layout.addWidget(btn_filter_region)
        
        btn_filter_city = QPushButton("🏙️ По городам")
        btn_filter_city.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        btn_filter_city.clicked.connect(self.filter_by_city)
        filter_layout.addWidget(btn_filter_city)
        
        btn_filter_coach = QPushButton("👨‍🏫 По тренерам")
        btn_filter_coach.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        btn_filter_coach.clicked.connect(self.filter_by_coach)
        filter_layout.addWidget(btn_filter_coach)
        
        filters_layout.addLayout(filter_layout)
        
        # Кнопка сброса фильтров
        btn_reset = QPushButton("🔄 Сбросить все фильтры")
        btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #D32F2F; }
        """)
        btn_reset.clicked.connect(self.reset_filters)
        filters_layout.addWidget(btn_reset)
        
        self.dynamic_filters_layout.addWidget(filters_container)
        
        # Разделитель перед кнопками заявок
        line4 = QFrame()
        line4.setFrameShape(QFrame.HLine)
        line4.setFrameShadow(QFrame.Sunken)
        line4.setStyleSheet("background-color: #ccc; max-height: 1px; margin: 10px 0;")
        self.dynamic_filters_layout.addWidget(line4)
        
        # Заголовок секции заявок
        filter_title3 = QLabel("📋 Управление заявками")
        filter_title3.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 5px;")
        self.dynamic_filters_layout.addWidget(filter_title3)
        
        # Горизонтальные кнопки для фильтрации и подтверждения заявок
        application_layout = QHBoxLayout()
        application_layout.setSpacing(10)
        
        # Кнопка фильтрации предварительных заявок
        self.btn_filter_preliminary = QPushButton("📝 Предварительные")
        self.btn_filter_preliminary.setCheckable(True)
        self.btn_filter_preliminary.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #F57C00; }
            QPushButton:checked { background-color: #E65100; }
        """)
        self.btn_filter_preliminary.clicked.connect(self.filter_preliminary_applications)
        application_layout.addWidget(self.btn_filter_preliminary)
        
        # Кнопка подтверждения выбранных заявок
        btn_confirm = QPushButton("✅ Подтвердить выбранные")
        btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        btn_confirm.clicked.connect(self.confirm_selected_applications)
        application_layout.addWidget(btn_confirm)
        
        self.dynamic_filters_layout.addLayout(application_layout)
        
        # Кнопка сброса фильтра заявок
        btn_reset_application = QPushButton("🔄 Показать все заявки")
        btn_reset_application.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        btn_reset_application.clicked.connect(self.reset_application_filter)
        self.dynamic_filters_layout.addWidget(btn_reset_application)

    def search_players_dialog(self):
        """Поиск участников - вызов диалога"""
        self.search_players()  # вызываем существующий метод
# =================================
class RatingLoaderThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    file_progress = pyqtSignal(int, str)  # (progress, filename)
    
    def __init__(self, file_path, table_name, file_index, total_files, rating_date=None):
        super().__init__()
        self.file_path = file_path
        self.table_name = table_name
        self.rating_date = rating_date
        self.file_index = file_index
        self.total_files = total_files
        self._is_running = True
    
    def stop(self):
        self._is_running = False
    
    def run(self):
        try:
            # Общий прогресс для всех файлов
            base_progress = (self.file_index - 1) * (100 // self.total_files)
            
            self.status.emit(f"📥 Загрузка файла {self.file_index}/{self.total_files}: {os.path.basename(self.file_path)}")
            
            if not os.path.exists(self.file_path):
                self.finished.emit(False, f"Файл не найден: {self.file_path}")
                return
            
            # Читаем Excel файл
            df = pd.read_excel(self.file_path)
            total_rows = len(df)
            
            # # Выводим первые 5 строк для отладки
            # print(f"Первые 5 строк файла {self.table_name}:")
            # print(df.head())
            
            # Определяем колонки
            column_mapping = self.get_column_mapping(df)
            
            records = []
            for idx, row in df.iterrows():
                if not self._is_running:
                    self.finished.emit(False, "Загрузка прервана")
                    return
                
                # Прогресс в пределах текущего файла
                file_progress = int((idx + 1) / total_rows * 100)
                # Общий прогресс
                total_progress = base_progress + int(file_progress / self.total_files)
                
                self.progress.emit(total_progress)
                self.file_progress.emit(file_progress, os.path.basename(self.file_path))
                
                # Парсим строку
                record = self.parse_row(row, idx, column_mapping)
                records.append(record)
            
            # Загружаем данные в БД
            self.load_to_database(records)
            
            # Завершаем загрузку файла
            self.progress.emit(base_progress + (100 // self.total_files))
            self.file_progress.emit(100, os.path.basename(self.file_path))
            
            self.finished.emit(True, f"✅ {os.path.basename(self.file_path)}: загружено {len(records)} записей")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(False, f"Ошибка: {str(e)}")
        
        self.quit()
        self.wait()
    
    def get_column_mapping(self, df):
        """Определение соответствия колонок"""
        column_mapping = {
            'r_number': None,
            'r_list': None,
            'r_fname': None,
            'r_bithday': None,
            'r_city': None,
            'r_region': None,
            'r_district': None
        }
        
        for col in df.columns:
            col_lower = str(col).lower()
            
            if 'место' in col_lower:
                if column_mapping['r_number'] is None:
                    column_mapping['r_number'] = col
                    
            if 'рейтинг' in col_lower:
                if column_mapping['r_list'] is None:
                    column_mapping['r_list'] = col
            
            if 'фамилия имя' in col_lower:
                if column_mapping['r_fname'] is None:
                    column_mapping['r_fname'] = col
            
            if 'дата рождения' in col_lower:
                if column_mapping['r_bithday'] is None:
                    column_mapping['r_bithday'] = col
            
            if 'населенный пункт' in col_lower:
                if column_mapping['r_city'] is None:
                    column_mapping['r_city'] = col
            
            if 'субъект рф' in col_lower:
                if column_mapping['r_region'] is None:
                    column_mapping['r_region'] = col
            
            if 'федеральный округ' in col_lower:
                if column_mapping['r_district'] is None:
                    column_mapping['r_district'] = col
        
        return column_mapping
    #===================
    def parse_row(self, row, idx, column_mapping):
        """Парсинг строки Excel"""
        # Место (позиция в рейтинге)
        place = idx + 1  # По умолчанию
        if column_mapping['r_number'] is not None:
            try:
                val = row[column_mapping['r_number']]
                if pd.notna(val):
                    # Пробуем преобразовать в целое число
                    if isinstance(val, (int, float)):
                        place = int(val)
                    elif isinstance(val, str):
                        # Убираем пробелы и точку в конце
                        val = val.strip().rstrip('.')
                        if val.isdigit():
                            place = int(val)
            except:
                place = idx + 1
        
        # Рейтинг (очки)
        rating = 0
        if column_mapping['r_list'] is not None:
            try:
                val = row[column_mapping['r_list']]
                if pd.notna(val):
                    if isinstance(val, (int, float)):
                        rating = int(val)
                    elif isinstance(val, str):
                        # Убираем пробелы и запятые
                        val = val.strip().replace(',', '').replace(' ', '')
                        if val.isdigit():
                            rating = int(val)
            except:
                rating = 0
        
        # ФИО
        fio = ""
        if column_mapping['r_fname'] is not None:
            fio = str(row[column_mapping['r_fname']]) if pd.notna(row[column_mapping['r_fname']]) else ""
            fio = fio.replace('nan', '').replace('None', '').strip()
            if not fio:
                fio = f"Игрок {idx + 1}"
        
        # Дата рождения
        birth_date = None
        if column_mapping['r_bithday'] is not None:
            try:
                val = row[column_mapping['r_bithday']]
                if pd.notna(val):
                    if isinstance(val, (pd.Timestamp, datetime)):
                        birth_date = val.date()
                    else:
                        birth_date = pd.to_datetime(val).date()
            except:
                birth_date = None
        
        # Город
        city = ""
        if column_mapping['r_city'] is not None:
            city = str(row[column_mapping['r_city']]) if pd.notna(row[column_mapping['r_city']]) else ""
            city = city.replace('nan', '').replace('None', '').strip()
        
        # Регион
        region = ""
        if column_mapping['r_region'] is not None:
            region = str(row[column_mapping['r_region']]) if pd.notna(row[column_mapping['r_region']]) else ""
            region = region.replace('nan', '').replace('None', '').strip()
        
        # Округ
        district = ""
        if column_mapping['r_district'] is not None:
            district = str(row[column_mapping['r_district']]) if pd.notna(row[column_mapping['r_district']]) else ""
            district = district.replace('nan', '').replace('None', '').strip()
        
        return {
            'r_number': place,      # Место (позиция)
            'r_list': rating,       # Рейтинг (очки)
            'r_fname': fio,         # ФИО
            'r_bithday': birth_date, # Дата рождения
            'r_city': city,         # Город
            'r_region': region,     # Регион
            'r_district': district  # Округ
        }
    # =======================================
    def load_to_database(self, records):
        """Загрузка данных в соответствующую таблицу"""
        try:
            if self.table_name == 'r_list_m':
                R_list_m.delete().execute()
                for record in records:
                    R_list_m.create(**{
                        'r_number': record['r_number'],  # Место
                        'r_list': record['r_list'],      # Рейтинг
                        'r_fname': record['r_fname'],
                        'r_bithday': record['r_bithday'],
                        'r_city': record['r_city'],
                        'r_region': record['r_region'],
                        'r_district': record['r_district']
                    })
                print(f"Загружено {len(records)} записей в r_list_m")
                
            elif self.table_name == 'r_list_d':
                R_list_d.delete().execute()
                for record in records:
                    R_list_d.create(**{
                        'r_number': record['r_number'],
                        'r_list': record['r_list'],
                        'r_fname': record['r_fname'],
                        'r_bithday': record['r_bithday'],
                        'r_city': record['r_city'],
                        'r_region': record['r_region'],
                        'r_district': record['r_district']
                    })
                print(f"Загружено {len(records)} записей в r_list_d")
                
            elif self.table_name == 'r1_list_m':
                R1_list_m.delete().execute()
                for record in records:
                    R1_list_m.create(**{
                        'r1_number': record['r_number'],
                        'r1_list': record['r_list'],
                        'r1_fname': record['r_fname'],
                        'r1_bithday': record['r_bithday'],
                        'r1_city': record['r_city'],
                        'r1_region': record['r_region'],
                        'r1_district': record['r_district']
                    })
                print(f"Загружено {len(records)} записей в r1_list_m")
                
            elif self.table_name == 'r1_list_d':
                R1_list_d.delete().execute()
                for record in records:
                    R1_list_d.create(**{
                        'r1_number': record['r_number'],
                        'r1_list': record['r_list'],
                        'r1_fname': record['r_fname'],
                        'r1_bithday': record['r_bithday'],
                        'r1_city': record['r_city'],
                        'r1_region': record['r_region'],
                        'r1_district': record['r_district']
                    })
                print(f"Загружено {len(records)} записей в r1_list_d")
                
        except Exception as e:
            print(f"Ошибка загрузки в БД: {e}")
            raise

class RatingFileDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Загрузка рейтингов")
        self.setModal(True)
        self.setMinimumWidth(700)
        
        layout = QVBoxLayout(self)
        
        # Информация
        info_label = QLabel("Выберите файлы рейтингов в следующем порядке:")
        info_label.setStyleSheet("font-weight: bold; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # Список файлов
        self.files_info = []
        file_names = [
            ("1. Текущий рейтинг (мужчины)", "r_list_m", "m"),
            ("2. Текущий рейтинг (женщины)", "r_list_d", "w"),
            ("3. Январский рейтинг (мужчины)", "r1_list_m", "m"),
            ("4. Январский рейтинг (женщины)", "r1_list_d", "w")
        ]
        
        self.loader_threads = []
        self.selected_count = 0
        
        for idx, (name, table, gender) in enumerate(file_names, 1):
            file_frame = QFrame()
            file_frame.setStyleSheet("QFrame { background-color: #f5f5f5; border-radius: 5px; margin: 2px; }")
            file_layout = QHBoxLayout(file_frame)
            file_layout.setContentsMargins(10, 5, 10, 5)
            
            # Название
            file_label = QLabel(f"{name}:")
            file_label.setMinimumWidth(250)
            file_label.setStyleSheet("font-size: 11px; font-weight: bold;")
            file_layout.addWidget(file_label)
            
            # Статус
            file_path_label = QLabel("❌ Файл не выбран")
            file_path_label.setStyleSheet("color: red; font-size: 10px;")
            file_path_label.setMinimumWidth(300)
            file_layout.addWidget(file_path_label, 1)
            
            # Прогресс для файла
            file_progress = QProgressBar()
            file_progress.setVisible(False)
            file_progress.setMaximumWidth(100)
            file_progress.setMaximumHeight(20)
            file_progress.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
            file_layout.addWidget(file_progress)
            
            # Кнопка выбора
            select_btn = QPushButton("📂 Выбрать")
            select_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 5px 10px;
                    font-size: 10px;
                    border-radius: 3px;
                }
                QPushButton:hover { background-color: #45a049; }
            """)
            # ИСПРАВЛЕНО: передаем все необходимые аргументы в лямбду
            select_btn.clicked.connect(lambda checked, t=table, lbl=file_path_label, g=gender, btn=select_btn, prog=file_progress: 
                                       self.select_file(t, lbl, g, btn, prog))
            file_layout.addWidget(select_btn)
            
            layout.addWidget(file_frame)
            
            self.files_info.append({
                'table': table,
                'path': None,
                'label': file_path_label,
                'gender': gender,
                'frame': file_frame,
                'button': select_btn,
                'progress': file_progress,
                'index': idx
            })
        
        # Общий прогресс бар
        self.total_progress_label = QLabel("Общий прогресс:")
        self.total_progress_label.setStyleSheet("font-size: 11px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(self.total_progress_label)
        
        self.total_progress_bar = QProgressBar()
        self.total_progress_bar.setVisible(False)
        self.total_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ccc;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:0.5 #8BC34A, stop:1 #4CAF50);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.total_progress_bar)
        
        # Статус
        self.status_label = QLabel("✅ Готов к загрузке")
        self.status_label.setStyleSheet("font-size: 11px; color: green; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.load_btn = QPushButton("🚀 Загрузить все")
        self.load_btn.setEnabled(False)
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 15px;
                font-size: 11px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.load_btn.clicked.connect(self.start_loading)
        
        cancel_btn = QPushButton("❌ Отмена")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 15px;
                font-size: 11px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #d32f2f; }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.current_index = 0
        self.setMinimumHeight(500)
    
    def select_file(self, table, label, gender, button, progress):
        """Выбор файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            f"Выберите файл для {table}", 
            "", 
            "Excel files (*.xlsx)"
        )
        
        if file_path:
            file_name = os.path.basename(file_path).lower()
            
            if not file_name.endswith('.xlsx'):
                QMessageBox.warning(self, "Ошибка", "Можно загружать только файлы с расширением .xlsx")
                return
            
            name_part = file_name.replace('.xlsx', '')
            if gender == 'm' and 'm' not in name_part and 'муж' not in name_part:
                QMessageBox.warning(self, "Ошибка", f"Файл должен содержать 'm' или 'муж' в названии")
                return
            
            if gender == 'w' and 'w' not in name_part and 'жен' not in name_part:
                QMessageBox.warning(self, "Ошибка", f"Файл должен содержать 'w' или 'жен' в названии")
                return
            
            label.setText(f"✅ {os.path.basename(file_path)}")
            label.setStyleSheet("color: green; font-size: 10px; font-weight: bold;")
            
            button.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    padding: 5px 10px;
                    font-size: 10px;
                    border-radius: 3px;
                }
                QPushButton:hover { background-color: #F57C00; }
            """)
            button.setText("🔄 Изменить")
            
            for info in self.files_info:
                if info['table'] == table:
                    info['path'] = file_path
                    break
            
            self.selected_count = sum(1 for info in self.files_info if info['path'] is not None)
            self.status_label.setText(f"📁 Выбрано файлов: {self.selected_count} из {len(self.files_info)}")
            
            all_selected = all(info['path'] for info in self.files_info)
            self.load_btn.setEnabled(all_selected)
            
            if all_selected:
                self.status_label.setText("✅ Все файлы выбраны! Нажмите 'Загрузить все'")
                self.status_label.setStyleSheet("font-size: 11px; color: #4CAF50; font-weight: bold;")
    
    def start_loading(self):
        """Начало загрузки всех файлов"""
        self.load_btn.setEnabled(False)
        self.total_progress_bar.setVisible(True)
        self.total_progress_bar.setValue(0)
        self.current_index = 0
        self.loader_threads = []
        
        # Показываем прогресс-бары для каждого файла
        for info in self.files_info:
            info['progress'].setVisible(True)
            info['progress'].setValue(0)
            info['button'].setEnabled(False)
            # Сбрасываем статус текста
            if info['path']:
                info['label'].setText(f"⏳ Ожидание загрузки...")
                info['label'].setStyleSheet("color: gray; font-size: 10px;")
        
        self.status_label.setText("⏳ Начинаем загрузку рейтингов...")
        self.load_next_file()
    
    def load_next_file(self):
        """Загрузка следующего файла"""
        if self.current_index >= len(self.files_info):
            self.total_progress_bar.setValue(100)
            self.status_label.setText("✅ Все рейтинги успешно загружены!")
            QMessageBox.information(self, "Успех", "Все рейтинги успешно загружены!")
            self.accept()
            return
        
        info = self.files_info[self.current_index]
        
        if info['path'] is None:
            # Пропускаем файл, если он не выбран
            info['progress'].setVisible(False)
            info['label'].setText("⏭️ Пропущен")
            info['label'].setStyleSheet("color: gray; font-size: 10px;")
            self.current_index += 1
            self.load_next_file()
            return
        
        info['progress'].setValue(0)
        info['label'].setText(f"⏳ Загрузка {os.path.basename(info['path'])}...")
        info['label'].setStyleSheet("color: orange; font-size: 10px;")
        
        self.current_loader = RatingLoaderThread(
            info['path'], 
            info['table'],
            self.current_index + 1,
            len([f for f in self.files_info if f['path'] is not None])  # Только выбранные файлы
        )
        self.current_loader.progress.connect(self.total_progress_bar.setValue)
        self.current_loader.file_progress.connect(self.update_file_progress)
        self.current_loader.status.connect(self.status_label.setText)
        self.current_loader.finished.connect(self.on_file_loaded)
        self.current_loader.start()
        
        self.loader_threads.append(self.current_loader)

    def update_file_progress(self, progress, filename):
        """Обновление прогресса текущего файла"""
        for info in self.files_info:
            if info['path'] and os.path.basename(info['path']) == filename:
                info['progress'].setValue(progress)
                if progress == 100:
                    info['label'].setText(f"✅ Загружено: {filename}")
                    info['label'].setStyleSheet("color: green; font-size: 10px;")
                break

    def on_file_loaded(self, success, msg):
        """Обработка завершения загрузки одного файла"""
        if success:
            info = self.files_info[self.current_index]
            info['label'].setText(f"✅ ЗАГРУЖЕНО: {os.path.basename(info['path'])}")
            info['label'].setStyleSheet("color: #4CAF50; font-size: 10px; font-weight: bold;")
            
            self.current_index += 1
            self.load_next_file()
        else:
            QMessageBox.critical(self, "Ошибка загрузки", 
                               f"Ошибка при загрузке {self.files_info[self.current_index]['table']}:\n{msg}")
            self.reject()
    
    def reject(self):
        """Отмена загрузки"""
        # Останавливаем все потоки
        for thread in self.loader_threads:
            if hasattr(thread, 'isRunning') and thread.isRunning():
                thread.stop()
                thread.quit()
                thread.wait()
        super().reject()

    def check_loaded_ratings(self):
        """Проверка загруженных рейтингов"""
        try:
            r_list_m_count = R_list_m.select().count()
            r_list_d_count = R_list_d.select().count()
            r1_list_m_count = R1_list_m.select().count()
            r1_list_d_count = R1_list_d.select().count()
            
            print(f"Текущий рейтинг (мужчины): {r_list_m_count} записей")
            print(f"Текущий рейтинг (женщины): {r_list_d_count} записей")
            print(f"Январский рейтинг (мужчины): {r1_list_m_count} записей")
            print(f"Январский рейтинг (женщины): {r1_list_d_count} записей")
            
            return {
                'current_m': r_list_m_count,
                'current_w': r_list_d_count,
                'january_m': r1_list_m_count,
                'january_w': r1_list_d_count
            }
        except Exception as e:
            print(f"Ошибка проверки: {e}")
            return None

    def find_similar_competitions(self, name, start_date, end_date):
        """Поиск похожих соревнований для группировки"""
        similar = Title.select().where(
            (Title.name == name) &
            (Title.data_start == start_date) &
            (Title.data_end == end_date)
        )
        return list(similar)

    def switch_gender_category(self, sex):
        """Переключение между мальчиками и девочками"""
        if self.current_sex == sex:
            return
        
        self.current_sex = sex
        
        # Перезагружаем участников с фильтром по полу
        self.load_participants_for_title()
        
        # Обновляем кнопки
        self.create_category_buttons()
        
        # Обновляем заголовок таблицы
        if self.current_title_id:
            title = Title.get_or_none(Title.id == self.current_title_id)
            if title:
                sex_text = "Девочки" if sex == "woman" else "Мальчики"
                count = self.players_model.rowCount()
                age_text = f" ({title.vozrast})" if title.vozrast else ""
                self.table_header.setText(f"👥 {title.name}{age_text} - {sex_text} ({count} чел.)")




def main():
    app = QApplication(sys.argv)
    window = MainWindow()

    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()