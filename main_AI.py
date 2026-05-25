# main_AI.py
import sys
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTabWidget, QTableView, QMenuBar, QAction, QLabel,
    QFrame, QSizePolicy, QMessageBox, QListWidget, QListWidgetItem,
    QLineEdit, QDateEdit, QComboBox, QGroupBox, QFormLayout,
    QScrollArea, QSplitter, QInputDialog, QHeaderView, QAbstractItemView,
    QDialog, QProgressBar, QFileDialog, QMenu, QProgressDialog, QTextEdit, QSpinBox
)
from PyQt5.QtWidgets import QGridLayout  # Добавьте в импорт
from PyQt5.QtCore import Qt, QDate, QSize, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor, QIntValidator
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QCompleter
from PyQt5.QtCore import QStringListModel

from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import *
from reportlab.lib.styles import ParagraphStyle as PS
import tempfile

from models import connect_db, close_db
from models import *
from models_qt import (
    PlayersTableModel, TeamsTableModel, ResultsTableModel, 
    DoublePlayersTableModel, TitlesTableModel, CoachesTableModel
)
from datetime import *
import pandas as pd

from datetime import datetime

import manual_choice


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Панель управления соревнованиями")
        self.setGeometry(100, 100, 1500, 780)
        self.setMinimumSize(1200, 600)
        
        # Подключение к БД
        self.db = connect_db()

        # Создаем папку для бэкапов, если её нет
        if not os.path.exists("backup_db"):
            os.makedirs("backup_db") 
        if not os.path.isdir("table_pdf"):  # создает папку 
            os.mkdir("table_pdf")
        if not os.path.isdir("competition_pdf"):  # создает папку 
            os.mkdir("competition_pdf")
        if not os.path.isdir("sign"):  # создает папку 
            os.mkdir("sign")

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
                "filters": ["Сортировка", "Фильтры", "Заявки"]},
            2: {"title": "Команды", "description": "Управление командами",
                "buttons": ["➕ Добавить", "✏️ Редактировать", "🗑️ Удалить", "⭐ Рейтинг"]},
            3: {"title": "Пары", "description": "Формирование пар",
                "buttons": ["🎲 Сформировать", "🔄 Разбить", "📊 Посев"]},
            4: {"title": "Система", "description": "Настройки системы проведения",
                "buttons": [
                    ["🔍 Поиск в Choice", "📊 Статистика"],
                    ["🗑️ Очистить", "📋 Отчет"]
                ]},
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
        
        # Отключаем все вкладки кроме Титул при запуске
        for i in range(1, self.tab_widget.count()):
            self.tab_widget.setTabEnabled(i, False)
        self.tab_widget.setTabEnabled(0, True)  # Титул всегда активен
        
        # Устанавливаем текущую вкладку - Титул
        self.tab_widget.setCurrentIndex(0)
        
        # Загружаем последнее соревнование (если есть)
        self.load_last_competition()

    def showEvent(self, event):
        """Событие при первом отображении окна"""
        super().showEvent(event)
        QTimer.singleShot(100, lambda: self.set_tab_height(0))

    def set_tab_height(self, tab_index):
        """Устанавливает фиксированную высоту верхнего виджета в зависимости от вкладки"""
        if not hasattr(self, 'top_widget') or not hasattr(self, 'tab_heights'):
            return
        
        if self.top_widget is None:
            return
        
        try:
            height = self.tab_heights.get(tab_index, 200)
            self.top_widget.setFixedHeight(height)
            
            # Принудительно обновляем геометрию
            self.top_widget.updateGeometry()
            if hasattr(self, 'bottom_widget') and self.bottom_widget:
                self.bottom_widget.updateGeometry()
            
            # Обновляем таблицу
            if hasattr(self, 'table_view') and self.table_view:
                self.table_view.updateGeometry()
        except Exception as e:
            print(f"Ошибка set_tab_height: {e}")

    def resize_table_for_participants(self):
        """Устанавливает высоту для вкладки Участники"""
        if hasattr(self, 'set_tab_height'):
            self.set_tab_height(1)

    def resize_table_normal(self):
        """Восстанавливает нормальную высоту для текущей вкладки"""
        if hasattr(self, 'current_tab_index') and hasattr(self, 'set_tab_height'):
            self.set_tab_height(self.current_tab_index)

    def resizeEvent(self, event):
        """Обработчик изменения размера окна"""
        super().resizeEvent(event)
        
        # Обновляем размеры при изменении окна
        if hasattr(self, 'current_tab_index') and hasattr(self, 'top_widget'):
            if self.top_widget is not None:
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

    # ========== Левая панель ==========
        self.left_panel = QFrame()
        self.left_panel.setFrameShape(QFrame.StyledPanel)
        self.left_panel.setMinimumWidth(250)
        self.left_panel.setMaximumWidth(280)
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
        
        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #ccc; max-height: 2px; margin: 10px 0;")
        left_layout.addWidget(line)
        
        # === СЕКЦИЯ ДЛЯ СОЗДАНИЯ ЭТАПА ===
        self.stage_section = QGroupBox("🏆 Создание этапа")
        self.stage_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #4CAF50;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                color: #4CAF50;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        stage_layout = QVBoxLayout(self.stage_section)  # <-- stage_layout определяется здесь
        stage_layout.setSpacing(8)
        stage_layout.setContentsMargins(8, 12, 8, 8)
        
        # Кнопка параметров системы (ДОБАВИТЬ ЗДЕСЬ)
        params_btn = QPushButton("⚙️ Параметры системы")
        params_btn.setMinimumHeight(30)
        params_btn.setStyleSheet("""
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
        params_btn.clicked.connect(self.change_system_parameters)
        stage_layout.addWidget(params_btn)
        
        # Название этапа
        stage_name_layout = QHBoxLayout()
        stage_name_layout.addWidget(QLabel("Этап:"))
        self.system_stage = QComboBox()
        self.system_stage.addItems([
            "Одна таблица",
            "Квалификация",
            "Квалификация. 1-й полуфинал",
            "Квалификация. 2-й полуфинал",
            "Финал"
        ])
        self.system_stage.setEditable(True)
        self.system_stage.currentTextChanged.connect(self.on_stage_type_changed)
        stage_name_layout.addWidget(self.system_stage, 1)
        stage_layout.addLayout(stage_name_layout)
        
        # Тип таблицы
        table_type_layout = QHBoxLayout()
        table_type_layout.addWidget(QLabel("Тип таблицы:"))
        self.table_type = QComboBox()
        self.table_type.addItems([
            "Круговая",
            "Олимпийская (минус 2)",
            "Олимпийская (с розыгрышем всех мест)",
            "Олимпийская (за 1-3 место)"
        ])
        table_type_layout.addWidget(self.table_type, 1)
        stage_layout.addLayout(table_type_layout)
        
        # Количество групп (показывается только для квалификации)
        self.groups_widget = QWidget()
        groups_layout = QHBoxLayout(self.groups_widget)
        groups_layout.setContentsMargins(0, 0, 0, 0)
        groups_layout.addWidget(QLabel("Количество групп:"))
        self.total_groups = QLineEdit()
        self.total_groups.setPlaceholderText("кол-во")
        self.total_groups.setMaximumWidth(80)
        groups_layout.addWidget(self.total_groups)
        groups_layout.addWidget(QLabel("гр."))
        groups_layout.addStretch()
        stage_layout.addWidget(self.groups_widget)
        self.groups_widget.setVisible(False)  # Изначально скрыт
        
        # Количество партий
        parties_layout = QHBoxLayout()
        parties_layout.addWidget(QLabel("Количество партий:"))
        self.score_flag = QComboBox()
        self.score_flag.addItems(["3", "5", "7"])
        self.score_flag.setCurrentText("5")
        parties_layout.addWidget(self.score_flag)
        parties_layout.addStretch()
        stage_layout.addLayout(parties_layout)
        
        # Кнопка добавления этапа
        add_stage_btn = QPushButton("➕ Добавить этап")
        add_stage_btn.setMinimumHeight(30)
        add_stage_btn.clicked.connect(self.add_system_stage)
        stage_layout.addWidget(add_stage_btn)
        
        left_layout.addWidget(self.stage_section)

        # =============
        # Информация о посеве игроков
        self.seeding_info_label = QLabel("🎯 Посев игроков: 0 из 0 (0 осталось)")
        self.seeding_info_label.setStyleSheet("font-size: 11px; padding: 5px; background-color: #e0e0e0; border-radius: 3px;")
        left_layout.addWidget(self.seeding_info_label)

        # Разделитель
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        line2.setStyleSheet("background-color: #ccc; max-height: 2px; margin: 10px 0;")
        left_layout.addWidget(line2)
        
        
        # Контейнер для кнопок действий
        self.dynamic_filters_widget = QWidget()
        self.dynamic_filters_layout = QVBoxLayout(self.dynamic_filters_widget)
        self.dynamic_filters_layout.setAlignment(Qt.AlignTop)
        self.dynamic_filters_layout.setSpacing(8)
        self.dynamic_filters_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.dynamic_filters_widget)
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
        self.right_panel.setMaximumWidth(320)
        self.right_panel.setMinimumWidth(300)
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
            4: 600,  # Система
            5: 220,  # Результаты
            6: 180,  # Рейтинг
            7: 200   # Дополнительно
        }
        
        # Устанавливаем начальную высоту
        self.set_tab_height(0)
        
        # Загружаем список соревнований для вкладки Титул
        self.load_titles_list()

        # # Отключаем все вкладки кроме Титул при запуске
        # for i in range(1, self.tab_widget.count()):
        #     self.tab_widget.setTabEnabled(i, False)
        # self.tab_widget.setTabEnabled(0, True)  # Титул всегда активен
        
        # # Устанавливаем текущую вкладку - Титул
        # self.tab_widget.setCurrentIndex(0)
        
        # # Загружаем последнее соревнование (если есть)
        # self.load_last_competition()   

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
            'ВК (Всероссийская категория)': 'ССВК',
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
#=====================================
    def create_system_tab(self):
        """Вкладка Система"""
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        input_style = """
            QLineEdit, QComboBox {
                max-height: 32px;
                min-height: 30px;
                padding: 5px;
                font-size: 11px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QTextEdit {
                font-size: 11px;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        
        # Информационное окно для вывода этапов
        info_group = QGroupBox("📋 Информация о добавленных этапах")
        info_layout = QVBoxLayout(info_group)
        
        self.stages_info = QTextEdit()
        self.stages_info.setReadOnly(True)
        self.stages_info.setMaximumHeight(150)
        self.stages_info.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        info_layout.addWidget(self.stages_info)
        
        main_layout.addWidget(info_group)
        
        # Группа настройки системы
        group = QGroupBox("⚙️ Настройка этапа")
        group_layout = QFormLayout(group)
        group_layout.setSpacing(10)
        group_layout.setContentsMargins(10, 15, 10, 10)
        
        # Название этапа
        self.system_stage = QComboBox()
        self.system_stage.addItems([
            "Квалификация",
            "1-й полуфинал",
            "2-й полуфинал",
            "Финал",
            "Суперфинал"
        ])
        self.system_stage.setEditable(True)
        self.system_stage.setStyleSheet(input_style)
        group_layout.addRow("Название этапа:", self.system_stage)
        
        # Тип таблицы (вместо Тип системы)
        self.table_type = QComboBox()
        self.table_type.addItems([
            "Круговая",
            "Олимпийская (минус 2)",
            "Олимпийская (с розыгрышем всех мест)",
            "Олимпийская (за 1-3 место)"
        ])
        self.table_type.setStyleSheet(input_style)
        group_layout.addRow("Тип таблицы:", self.table_type)
        
        # Количество групп
        self.total_groups = QLineEdit()
        self.total_groups.setPlaceholderText("Количество групп")
        self.total_groups.setStyleSheet(input_style)
        group_layout.addRow("Количество групп:", self.total_groups)
        
        # Максимум участников
        self.max_players = QLineEdit()
        self.max_players.setPlaceholderText("Максимум участников в группе")
        self.max_players.setStyleSheet(input_style)
        group_layout.addRow("Максимум участников:", self.max_players)
        
        # Количество проходящих
        self.stage_exit = QLineEdit()
        self.stage_exit.setPlaceholderText("Количество проходящих в следующий этап")
        self.stage_exit.setStyleSheet(input_style)
        group_layout.addRow("Проходят в след. этап:", self.stage_exit)
        
        # Кнопка "Добавить этап"
        add_stage_btn = QPushButton("➕ Добавить этап")
        add_stage_btn.clicked.connect(self.add_system_stage)
        group_layout.addRow("", add_stage_btn)
        
        main_layout.addWidget(group)
        main_layout.addStretch()
        
        # Список для хранения добавленных этапов
        self.stages_list = []
        
        # Загружаем существующие данные
        self.load_system_data()
        
        return tab_widget
#=====================================
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
                # Если есть текущее соревнование, предлагаем его сохранить
                if self.current_title_id and self.current_title_id != title_id:
                    reply = QMessageBox.question(self, "Сохранение", 
                                                "Сохранить текущее соревнование перед переходом?",
                                                QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        self.save_current_competition()
                
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
                
                # Определяем пол по умолчанию
                if "девушки" in title.name.lower() or "дев" in title.name.lower():
                    self.current_sex = "woman"
                else:
                    self.current_sex = "man"

                # Обновляем меню финалов
                self.update_finals_menu_after_selection()

                # ОБНОВЛЯЕМ АКТИВНОСТЬ ВКЛАДОК (после выбора соревнования)
                self.update_tabs_enabled()
              
                # Обновляем кнопки категорий
                self.create_category_buttons()
                
                # Загружаем участников (если вкладка Участники активна)
                if self.tab_widget.isTabEnabled(1):
                    self.load_participants_for_title()
             
                # Если текущая вкладка - Система, обновляем информацию
                if self.current_tab_index == 4:
                    self.update_stages_info()
                    # Обновляем кнопки на левой панели (чтобы убрать дублирование)
                    self.update_left_panel_for_tab(4)
  
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
# ==================================================
    def update_finals_menu_after_selection(self):
        """Обновление меню финалов после выбора соревнования"""
        # Находим меню "Соревнования" -> "Жеребьевка" -> "Финалы"
        for action in self.menuBar().actions():
            if action.text() == "Соревнования":
                competitions_menu = action.menu()
                for sub_action in competitions_menu.actions():
                    if sub_action.text() == "🎲 Жеребьевка":
                        drawing_menu = sub_action.menu()
                        for final_sub_action in drawing_menu.actions():
                            if final_sub_action.text() == "Финалы":
                                finals_menu = final_sub_action.menu()
                                self.update_finals_menu(finals_menu)
                                break
                        break
                break
# ==================================================================
    def on_tab_changed(self, index):
        """Смена вкладки"""
        self.current_tab_index = index
        
        # ОБНОВЛЯЕМ ЛЕВУЮ ПАНЕЛЬ ПРИ СМЕНЕ ВКЛАДКИ
        self.update_left_panel_for_tab(index)
        
        # Управление отображением правой панели в зависимости от вкладки
        if index == 0:  # Вкладка Титул
            if hasattr(self, 'competitions_label'):
                self.competitions_label.setVisible(True)
            if hasattr(self, 'list_widget'):
                self.list_widget.setVisible(True)
            if hasattr(self, 'search_label'):
                self.search_label.setVisible(False)
            if hasattr(self, 'search_results_list'):
                self.search_results_list.setVisible(False)
            if hasattr(self, 'filters_widget'):
                self.filters_widget.setVisible(True)
            
            if hasattr(self, 'new_comp_frame'):
                self.new_comp_frame.setVisible(False)
            if hasattr(self, 'info_group'):
                self.info_group.setVisible(True)
            if hasattr(self, 'stage_section'):
                self.stage_section.setVisible(False)
            
            self.load_titles_list()
            
        elif index == 1:  # Вкладка Участники
            if hasattr(self, 'competitions_label'):
                self.competitions_label.setVisible(False)
            if hasattr(self, 'list_widget'):
                self.list_widget.setVisible(False)
            if hasattr(self, 'search_label'):
                self.search_label.setVisible(True)
            if hasattr(self, 'search_results_list'):
                self.search_results_list.setVisible(True)
            if hasattr(self, 'filters_widget'):
                self.filters_widget.setVisible(False)
            
            if hasattr(self, 'stage_section'):
                self.stage_section.setVisible(False)
            if hasattr(self, 'fio_edit'):
                self.fio_edit.setEnabled(True)
            
            if self.current_title_id:
                self.load_participants_for_title()
            else:
                if hasattr(self, 'players_model'):
                    self.players_model.setData([])
                if hasattr(self, 'table_header'):
                    self.table_header.setText("👥 Список участников - выберите соревнование из списка справа")
            
            QTimer.singleShot(100, self.resize_table_for_participants)
            
        elif index == 4:  # Вкладка Система
            if hasattr(self, 'competitions_label'):
                self.competitions_label.setVisible(True)
            if hasattr(self, 'list_widget'):
                self.list_widget.setVisible(True)
            if hasattr(self, 'search_label'):
                self.search_label.setVisible(False)
            if hasattr(self, 'search_results_list'):
                self.search_results_list.setVisible(False)
            if hasattr(self, 'filters_widget'):
                self.filters_widget.setVisible(False)
            if hasattr(self, 'competitions_label'):
                self.competitions_label.setText("⚙️ Система")
            
            # Показываем секцию создания этапа
            if hasattr(self, 'stage_section'):
                self.stage_section.setVisible(True)
            
            # Обновляем информацию о посеве
            self.update_seeding_info()
            
            # Обновляем информацию о системе
            if self.current_title_id:
                self.update_stages_info()
            else:
                if hasattr(self, 'list_widget'):
                    self.list_widget.clear()
                if hasattr(self, 'stages_info'):
                    self.stages_info.setText("Нет выбранного соревнования")
    # ========================================================                    
        elif index == 5:  # Вкладка Результаты
            if hasattr(self, 'competitions_label'):
                self.competitions_label.setVisible(True)
            if hasattr(self, 'list_widget'):
                self.list_widget.setVisible(True)
            if hasattr(self, 'search_label'):
                self.search_label.setVisible(False)
            if hasattr(self, 'search_results_list'):
                self.search_results_list.setVisible(False)
            if hasattr(self, 'filters_widget'):
                self.filters_widget.setVisible(False)
            if hasattr(self, 'competitions_label'):
                self.competitions_label.setText("📊 Результаты")
            
            if hasattr(self, 'stage_section'):
                self.stage_section.setVisible(False)
            
            if self.current_title_id:
                self.load_results_for_title()
            else:
                if hasattr(self, 'list_widget'):
                    self.list_widget.clear()
                    
        elif index == 6:  # Вкладка Рейтинг
            if hasattr(self, 'competitions_label'):
                self.competitions_label.setVisible(True)
            if hasattr(self, 'list_widget'):
                self.list_widget.setVisible(True)
            if hasattr(self, 'search_label'):
                self.search_label.setVisible(False)
            if hasattr(self, 'search_results_list'):
                self.search_results_list.setVisible(False)
            if hasattr(self, 'filters_widget'):
                self.filters_widget.setVisible(False)
            if hasattr(self, 'competitions_label'):
                self.competitions_label.setText("⭐ Рейтинг")
            
            if hasattr(self, 'stage_section'):
                self.stage_section.setVisible(False)
            
            if hasattr(self, 'list_widget'):
                self.list_widget.clear()
                
        elif index == 7:  # Вкладка Дополнительно
            if hasattr(self, 'competitions_label'):
                self.competitions_label.setVisible(True)
            if hasattr(self, 'list_widget'):
                self.list_widget.setVisible(True)
            if hasattr(self, 'search_label'):
                self.search_label.setVisible(False)
            if hasattr(self, 'search_results_list'):
                self.search_results_list.setVisible(False)
            if hasattr(self, 'filters_widget'):
                self.filters_widget.setVisible(False)
            if hasattr(self, 'competitions_label'):
                self.competitions_label.setText("ℹ️ Дополнительно")
            
            if hasattr(self, 'stage_section'):
                self.stage_section.setVisible(False)
            
            if hasattr(self, 'list_widget'):
                self.list_widget.clear()
        
        # Устанавливаем высоту для текущей вкладки
        self.set_tab_height(index)
# =======================================================
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
        # Сбрасываем флаг фильтров
        self._filters_added = False

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
                    
                    # Привязываем функции для разных вкладок
                    if tab_index == 1:  # Участники
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
                    
                    elif tab_index == 4:  # Система
                        if btn_text == "🔍 Поиск в Choice":
                            btn.clicked.connect(self.search_in_choice_table)
                        elif btn_text == "📊 Статистика":
                            btn.clicked.connect(self.show_choice_statistics)
                        elif btn_text == "🗑️ Очистить":
                            btn.clicked.connect(self.clear_choice_table)
                        elif btn_text == "📋 Отчет":
                            btn.clicked.connect(self.export_choice_report)
                    
                    elif tab_index == 0:  # Титул
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
                
                if tab_index == 2:  # Команды
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
        """Удаление выбранного участника с записью в таблицу Delete_player"""
        selection = self.table_view.selectedIndexes()
        if not selection:
            QMessageBox.warning(self, "Ошибка", "Выберите участника для удаления")
            return
        
        row = selection[0].row()
        
        # Получаем ID участника из модели
        player_id = self.players_model.get_id(row)
        if not player_id:
            return
        
        # Получаем данные игрока для подтверждения
        fio = self.players_model.get_fio(row)
        
        # Получаем полные данные игрока из таблицы Player
        try:
            player = Player.get_by_id(player_id)
            
            reply = QMessageBox.question(self, "Подтверждение", 
                                        f"Удалить участника {fio}?\n\n"
                                        f"Игрок будет перемещен в архив удаленных.\n"
                                        f"Вы сможете восстановить его позже.",
                                        QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # Создаем запись в таблице Delete_player
                Delete_player.create(
                    player=player.player,
                    bday=player.bday,
                    rank=player.rank,
                    city=player.city,
                    region=player.region,
                    razryad=player.razryad,
                    coach_id=player.coach_id,
                    full_name=player.fio,
                    title_id=self.current_title_id,
                    pay_rejting=player.pay_rejting or "",
                    comment=player.comment or "",
                    patronymic_id=player.patronymic_id.id if player.patronymic_id else None,
                    sex=player.sex
                )
                
                # Удаляем игрока из таблицы Player
                player.delete_instance()
                
                # Обновляем таблицу
                self.load_participants_for_title()
                
                # Обновляем количество игроков
                self.update_table_header()
                
                # Показываем сообщение с возможностью восстановления
                QMessageBox.information(self, "Успех", 
                                    f"Участник {fio} удален.\n"
                                    f"Данные сохранены в архиве.\n"
                                    f"Для восстановления используйте фильтр 'Удаленные'.")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")

    def update_table_header(self):
        """Обновление заголовка таблицы с количеством игроков"""
        if self.current_title_id:
            title = Title.get_or_none(Title.id == self.current_title_id)
            if title:
                sex_text = "Женщины" if self.current_sex == "woman" else "Мужчины"
                count = self.players_model.rowCount()
                age_text = f" ({title.vozrast})" if title.vozrast else ""

                age_text = f" ({title.vozrast})" if title.vozrast else ""
                self.table_header.setText(f"🗑️ УДАЛЕННЫЕ: {title.name}{age_text} - {sex_text} ({count} чел.)")
                self.table_header.setStyleSheet("""
                    background-color: #f44336;
                    color: white;
                    padding: 6px;
                    font-weight: bold;
                    font-size: 11px;
                    border-radius: 3px;
                """)
                
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
        # Если есть текущее соревнование, предлагаем его сохранить
        if self.current_title_id:
            reply = QMessageBox.question(self, "Сохранение", 
                                        "Сохранить текущее соревнование перед созданием нового?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.save_current_competition()
        # Сбрасываем параметры системы для нового соревнования
        if hasattr(self, 'system_tables'):
            delattr(self, 'system_tables')
        if hasattr(self, 'match_time'):
            delattr(self, 'match_time')
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
# ========= просмотр соревнований ============
    # def view_full_competition(self):
    #     pass

    # def view_player_listing(self):
    #     """просмотр списка в PDF"""
    #     from models import Player
    #     # if view_sort == "По рейтингу":
    #     player_list = Player.select().where(Player.title_id == self.current_title_id).order_by(Player.rank.desc())  # сортировка по рейтингу
    #         # elif view_sort == "По алфавиту": 
    #         #     player_list_x = Player.select().where(Player.title_id == self.title_current_id).order_by(Player.player) # сортировка по алфавиту
    #         # elif view_sort == "По месту":
    #         #     player_list_x = Player.select().where(Player.title_id == title_id()).order_by(Player.mesto)  # сортировка по месту
    #         # player_list = player_list_x.select().where(Player.player != "x")
    #     self.list_player_pdf(player_list)
#===========================
    def create_menu_bar(self):
        """Создание меню"""
        menubar = self.menuBar()
        menubar.setStyleSheet("QMenuBar { padding: 3px; } QMenuBar::item { padding: 3px 8px; font-size: 10px; }")
        
        # Соревнования
        competitions_menu = menubar.addMenu("Соревнования")
        
        new_comp_action = QAction("Новое соревнование", self)
        new_comp_action.triggered.connect(self.new_competition)
        competitions_menu.addAction(new_comp_action)
        
        open_comp_action = QAction("Открыть соревнование", self)
        open_comp_action.triggered.connect(self.open_competition)
        competitions_menu.addAction(open_comp_action)
        
        competitions_menu.addSeparator()
        
        # Жеребьевка - подменю
        drawing_menu = competitions_menu.addMenu("🎲 Жеребьевка")
        
        # Квалификация
        qualification_action = QAction("Квалификация", self)
        qualification_action.triggered.connect(lambda: self.run_drawing_for_stage("Квалификация"))
        drawing_menu.addAction(qualification_action)
        
        # Полуфиналы - подменю
        semifinals_menu = drawing_menu.addMenu("Полуфиналы")
        
        semifinal_1_action = QAction("1-й полуфинал", self)
        semifinal_1_action.triggered.connect(lambda: self.run_drawing_for_stage("1-й полуфинал"))
        semifinals_menu.addAction(semifinal_1_action)
        
        semifinal_2_action = QAction("2-й полуфинал", self)
        semifinal_2_action.triggered.connect(lambda: self.run_drawing_for_stage("2-й полуфинал"))
        semifinals_menu.addAction(semifinal_2_action)
        
        # Финалы - подменю
        finals_menu = drawing_menu.addMenu("Финалы")
        
        # Динамически добавляем финалы
        self.update_finals_menu(finals_menu)
        
        competitions_menu.addSeparator()
        
        # Система - подменю
        system_menu = competitions_menu.addMenu("⚙️ Система")
        
        create_system_action = QAction("Создать", self)
        create_system_action.triggered.connect(self.create_system_settings)
        system_menu.addAction(create_system_action)
        
        edit_system_action = QAction("Редактировать", self)
        edit_system_action.triggered.connect(self.edit_system_settings)
        system_menu.addAction(edit_system_action)
        
        competitions_menu.addSeparator()
        
        # Выход
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        competitions_menu.addAction(exit_action)
        
        # Редактировать
        edit_menu = menubar.addMenu("Редактировать")
        edit_action = QAction("Параметры", self)
        edit_action.triggered.connect(lambda: QMessageBox.information(self, "Редактировать", "Параметры"))
        edit_menu.addAction(edit_action)
        
        # Печать
        print_menu = menubar.addMenu("Печать")
        print_action = QAction("Предпросмотр", self)
        print_action.triggered.connect(lambda: QMessageBox.information(self, "Печать", "Печать"))
        print_menu.addAction(print_action)
        
        # Просмотр
        view_menu = menubar.addMenu("Просмотр")
    
        # Список участников
        participants_list_action = QAction("📋 Список участников (PDF)", self)
        participants_list_action.triggered.connect(self.export_participants_to_pdf)
        view_menu.addAction(participants_list_action)
        
        # Расписание (если есть система)
        schedule_action = QAction("📅 Расписание (PDF)", self)
        schedule_action.triggered.connect(self.export_schedule_to_pdf)
        view_menu.addAction(schedule_action)
        
        view_menu.addSeparator()
        
        fullscreen_action = QAction("Полный экран", self)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

# ====================================================        
        # Рейтинг
        rating_menu = menubar.addMenu("Рейтинг")
        rating_action = QAction("Показать рейтинг", self)
        rating_action.triggered.connect(lambda: QMessageBox.information(self, "Рейтинг", "Рейтинг"))
        rating_menu.addAction(rating_action)
        
        # База данных
        db_menu = menubar.addMenu("База данных")
        
        import_action = QAction("📥 Импортировать", self)
        import_action.triggered.connect(self.import_database)
        db_menu.addAction(import_action)
        
        export_action = QAction("📤 Экспортировать", self)
        export_action.triggered.connect(self.export_database)
        db_menu.addAction(export_action)
        
        db_menu.addSeparator()
        
        # Сохранить текущее соревнование
        save_competition_action = QAction("💾 Сохранить текущее соревнование", self)
        save_competition_action.triggered.connect(self.save_current_competition)
        db_menu.addAction(save_competition_action)
        
        # Помощь
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
                         "© 2026")
    
    def closeEvent(self, event):
        """Событие закрытия окна - сохранение базы данных"""
        try:
            # Спрашиваем пользователя о сохранении
            reply = QMessageBox.question(self, "Сохранение базы данных", 
                                        "Сохранить резервную копию базы данных перед выходом?",
                                        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            
            if reply == QMessageBox.Cancel:
                event.ignore()
                return
            
            if reply == QMessageBox.Yes:
                # Создаем папку backup_db, если её нет
                backup_dir = "backup_db"
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                
                # Формируем имя файла с текущей датой и временем
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                backup_file = os.path.join(backup_dir, f"backup_{timestamp}.sql")
                
                # Экспортируем базу данных
                self.export_database_internal(backup_file, None)
                
                QMessageBox.information(self, "Успех", f"База данных сохранена в:\n{backup_file}")
            
            # Закрываем соединение с БД
            close_db()
            event.accept()
            
        except Exception as e:
            print(f"Ошибка при сохранении БД: {e}")
            close_db()
            event.accept()
    #==============================================
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
        """Фильтр по тренерам (поиск по вхождению, учитывая нескольких тренеров)"""
        if not self.current_title_id:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите соревнование")
            return
        
        coach_name, ok = QInputDialog.getText(self, "Фильтр по тренеру", 
                                            "Введите фамилию тренера (или часть):")
        if ok and coach_name:
            coach_search = coach_name.strip().lower()
            
            try:
                # Получаем всех игроков в соревновании
                query = Player.select().where(Player.title_id == self.current_title_id)
                
                if self.current_sex == "woman":
                    query = query.where(Player.sex == "woman")
                elif self.current_sex == "man":
                    query = query.where(Player.sex == "man")
                
                filtered_players = []
                
                for player in query:
                    # Получаем имя тренера
                    coach_text = ""
                    if player.coach_id:
                        coach = Coach.get_or_none(Coach.id == player.coach_id)
                        if coach:
                            coach_text = coach.coach.lower()
                    
                    # Проверяем, содержится ли искомая строка в имени тренера
                    if coach_search in coach_text:
                        # Получаем данные для отображения
                        coach_name_display = ""
                        if player.coach_id:
                            coach_obj = Coach.get_or_none(Coach.id == player.coach_id)
                            if coach_obj:
                                coach_name_display = coach_obj.coach
                        
                        filtered_players.append({
                            'id': player.id,
                            'fio': player.fio or player.player or "",
                            'birth_date': player.bday,
                            'rank': player.rank or 0,
                            'city': player.city or "",
                            'region': player.region or "",
                            'razryad': player.razryad or "",
                            'coach': coach_name_display,
                            'sex': player.sex or "",
                            'application': player.application or "предварительная"
                        })
                
                if filtered_players:
                    self.players_model.setData(filtered_players)
                    self.update_table_header()
                    QMessageBox.information(self, "Фильтр", 
                                        f"Найдено {len(filtered_players)} участников\n"
                                        f"с тренером: {coach_name}")
                else:
                    QMessageBox.information(self, "Фильтр", 
                                        f"Участники с тренером '{coach_name}' не найдены")
                    
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка фильтрации: {str(e)}")

    def reset_filters(self):
        """Сброс всех фильтров и сортировок"""
        if not self.current_title_id:
            return
        
        # Сбрасываем фильтр удаленных
        if hasattr(self, 'btn_filter_deleted') and self.btn_filter_deleted is not None:
            if self.btn_filter_deleted.isChecked():
                self.btn_filter_deleted.setChecked(False)
                self.btn_filter_deleted.setText("📋 Показать удаленных")
        
        # Сбрасываем фильтр предварительных заявок
        if hasattr(self, 'btn_filter_preliminary') and self.btn_filter_preliminary is not None:
            if self.btn_filter_preliminary.isChecked():
                self.btn_filter_preliminary.setChecked(False)
        
        # Загружаем активных участников
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
        title_data = {
        # ... другие поля ...
        'tab_enabled': "Титул Участники",  # Начальное значение - только вкладка Титул активна
        # ... остальные поля ...
        }
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

                # Создаем начальную систему
                System.create(
                    title_id=self.current_title_id,
                    total_athletes=0,
                    total_group=1,
                    max_player=16,
                    stage="Квалификация",
                    type_table="Круговая",
                    page_vid="лист",
                    label_string="",
                    kol_game_string="",
                    choice_flag=False,
                    score_flag=0,
                    visible_game=True,
                    stage_exit="0",
                    mesta_exit=0,
                    no_game="",
                    sex=self.current_sex if self.current_sex else "man"
        )
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
        if not self.current_title_id:
            # Если нет выбранного соревнования, отключаем все вкладки кроме Титул
            for i in range(self.tab_widget.count()):
                self.tab_widget.setTabEnabled(i, False)
            self.tab_widget.setTabEnabled(0, True)  # Титул всегда активен
            self.tab_widget.setCurrentIndex(0)  # Переключаемся на Титул
            return
        
        try:
            title = Title.get_by_id(self.current_title_id)
            tab_enabled = title.tab_enabled if title.tab_enabled else "Титул"
            
            # Словарь соответствия названий вкладок их индексам
            tab_dict = {
                'Титул': 0,
                'Участники': 1,
                'Команды': 2,
                'Пары': 3,
                'Система': 4,
                'Результаты': 5,
                'Рейтинг': 6,
                'Дополнительно': 7
            }
            
            # Сначала отключаем все вкладки
            for i in range(self.tab_widget.count()):
                self.tab_widget.setTabEnabled(i, False)
            
            # Разбираем строку tab_enabled (формат: "Титул Участники Система")
            enabled_tabs = tab_enabled.split()
            
            # Активируем указанные вкладки
            for tab_name in enabled_tabs:
                if tab_name in tab_dict:
                    idx = tab_dict[tab_name]
                    self.tab_widget.setTabEnabled(idx, True)
            
            # Если ни одна вкладка не активирована, активируем только Титул
            if not any(self.tab_widget.isTabEnabled(i) for i in range(self.tab_widget.count())):
                self.tab_widget.setTabEnabled(0, True)
            
            # Если текущая вкладка неактивна, переключаемся на Титул
            if not self.tab_widget.isTabEnabled(self.tab_widget.currentIndex()):
                self.tab_widget.setCurrentIndex(0)
            
            print(f"Активированы вкладки: {enabled_tabs}")
            
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
                
                # Обновляем информацию на вкладке Титул (только если виджеты существуют)
                if hasattr(self, 'comp_name_label'):
                    self.comp_name_label.setText(last_title.name or "-")
                if hasattr(self, 'comp_short_name_label'):
                    self.comp_short_name_label.setText(last_title.short_name_comp or "-")
                if hasattr(self, 'comp_full_name_label'):
                    self.comp_full_name_label.setText(last_title.full_name_comp or "-")
                if hasattr(self, 'comp_sredi_label'):
                    self.comp_sredi_label.setText(last_title.sredi or "-")
                if hasattr(self, 'comp_vozrast_label'):
                    self.comp_vozrast_label.setText(last_title.vozrast or "-")
                if hasattr(self, 'comp_type_info_label'):
                    self.comp_type_info_label.setText(last_title.vid_turnira or "-")
                
                if hasattr(self, 'comp_dates_label') and last_title.data_start:
                    start = last_title.data_start.strftime("%d.%m.%Y") if last_title.data_start else "---"
                    end = last_title.data_end.strftime("%d.%m.%Y") if last_title.data_end else "---"
                    self.comp_dates_label.setText(f"{start} - {end}")
                if hasattr(self, 'comp_mesto_label'):
                    self.comp_mesto_label.setText(last_title.mesto or "-")
                if hasattr(self, 'comp_referee_label'):
                    self.comp_referee_label.setText(last_title.referee or "-")
                if hasattr(self, 'comp_referee_category_label'):
                    self.comp_referee_category_label.setText(last_title.kat_ref or "-")
                if hasattr(self, 'comp_secretary_label'):
                    self.comp_secretary_label.setText(last_title.secretary or "-")
                if hasattr(self, 'comp_secretary_category_label'):
                    self.comp_secretary_category_label.setText(last_title.kat_sec or "-")
                
                # Определяем пол по умолчанию
                if "девушки" in last_title.name.lower() or "дев" in last_title.name.lower():
                    self.current_sex = "woman"
                else:
                    self.current_sex = "man"
                
                # АКТИВИРУЕМ ВКЛАДКИ НА ОСНОВЕ tab_enabled
                self.update_tabs_enabled()
                
                # Обновляем кнопки категорий
                self.create_category_buttons()
                
                # Загружаем участников (если вкладка активна)
                if hasattr(self, 'tab_widget') and self.tab_widget.isTabEnabled(1):
                    self.load_participants_for_title()
                
                # Подсвечиваем последнее соревнование в списке
                if hasattr(self, 'list_widget'):
                    for i in range(self.list_widget.count()):
                        item = self.list_widget.item(i)
                        if item.data(Qt.UserRole) == last_title.id:
                            self.list_widget.setCurrentItem(item)
                            break
                            
                print(f"Загружено последнее соревнование: {last_title.name}")
                    
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
        
        if hasattr(self, 'btn_filter_preliminary'):
            self.btn_filter_preliminary.setChecked(False)
        
        # Проверяем, не включен ли фильтр удаленных
        if hasattr(self, 'btn_filter_deleted') and self.btn_filter_deleted.isChecked():
            self.load_deleted_players()
        else:
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
        # Проверяем, есть ли уже фильтры
        if hasattr(self, '_filters_added') and self._filters_added:
            return
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
        
        # Разделитель перед архивом
        line5 = QFrame()
        line5.setFrameShape(QFrame.HLine)
        line5.setFrameShadow(QFrame.Sunken)
        line5.setStyleSheet("background-color: #ccc; max-height: 1px; margin: 10px 0;")
        self.dynamic_filters_layout.addWidget(line5)
        
        # Заголовок архива
        filter_title_archive = QLabel("🗑️ Архив")
        filter_title_archive.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 5px;")
        self.dynamic_filters_layout.addWidget(filter_title_archive)
        
        # Горизонтальные кнопки для работы с архивом
        archive_layout = QHBoxLayout()
        archive_layout.setSpacing(10)
        
        # Кнопка фильтрации удаленных игроков
        self.btn_filter_deleted = QPushButton("📋 Показать удаленных")
        self.btn_filter_deleted.setCheckable(True)
        self.btn_filter_deleted.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #7B1FA2; }
            QPushButton:checked { background-color: #6A1B9A; }
        """)
        self.btn_filter_deleted.clicked.connect(self.toggle_deleted_filter)
        archive_layout.addWidget(self.btn_filter_deleted)
        
        # Кнопка восстановления выбранного игрока
        btn_restore = QPushButton("🔄 Восстановить выбранного")
        btn_restore.setStyleSheet("""
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
        btn_restore.clicked.connect(self.restore_deleted_player)
        archive_layout.addWidget(btn_restore)
        
        self.dynamic_filters_layout.addLayout(archive_layout)
        
        # Кнопка показа всех игроков
        btn_show_all = QPushButton("👥 Показать всех (активные)")
        btn_show_all.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        btn_show_all.clicked.connect(self.show_all_players)
        self.dynamic_filters_layout.addWidget(btn_show_all)

    def search_players_dialog(self):
        """Поиск участников - вызов диалога"""
        self.search_players()  # вызываем существующий метод

    def load_deleted_players(self):
        """Загрузка удаленных участников для текущего соревнования"""
        if not self.current_title_id:
            self.players_model.setData([])
            self.table_header.setText("👥 Список удаленных участников - выберите соревнование")
            return
        
        try:
            # Получаем удаленных игроков для текущего соревнования
            query = Delete_player.select().where(Delete_player.title_id == self.current_title_id)
            
            # Применяем фильтр по полу
            if self.current_sex == "woman":
                query = query.where(Delete_player.sex == "woman")
            elif self.current_sex == "man":
                query = query.where(Delete_player.sex == "man")
            
            # Сортируем
            query = query.order_by(Delete_player.rank.desc())
            
            participants_data = []
            for player in query:
                # Получаем тренера
                coach_name = ""
                if player.coach_id:
                    coach = Coach.get_or_none(Coach.id == player.coach_id.id if hasattr(player.coach_id, 'id') else player.coach_id)
                    if coach:
                        coach_name = coach.coach
                
                participants_data.append({
                    'id': player.id,
                    'fio': player.full_name or player.player or "",
                    'birth_date': player.bday,
                    'rank': player.rank or 0,
                    'city': player.city or "",
                    'region': player.region or "",
                    'razryad': player.razryad or "",
                    'coach': coach_name,
                    'sex': player.sex or "",
                    'is_deleted': True  # Маркер для удаленного игрока
                })
            
            self.players_model.setData(participants_data)
            self.update_table_header_deleted()
            
        except Exception as e:
            print(f"Ошибка загрузки удаленных участников: {e}")
            self.players_model.setData([])

    def update_table_header_deleted(self):
        """Обновление заголовка таблицы для удаленных игроков"""
        if self.current_title_id:
            title = Title.get_or_none(Title.id == self.current_title_id)
            if title:
                sex_text = "Женщины" if self.current_sex == "woman" else "Мужчины"
                count = self.players_model.rowCount()
                age_text = f" ({title.vozrast})" if title.vozrast else ""
                self.table_header.setText(f"🗑️ УДАЛЕННЫЕ: {title.name}{age_text} - {sex_text} ({count} чел.)")
                self.table_header.setStyleSheet("""
                    background-color: #f44336;
                    color: white;
                    padding: 6px;
                    font-weight: bold;
                    font-size: 11px;
                    border-radius: 3px;
                """)

    def restore_deleted_player(self):
        """Восстановление выбранного удаленного игрока"""
        selection = self.table_view.selectedIndexes()
        if not selection:
            QMessageBox.warning(self, "Ошибка", "Выберите участника для восстановления")
            return
        
        row = selection[0].row()
        player_id = self.players_model.get_id(row)
        if not player_id:
            return
        
        fio = self.players_model.get_fio(row)
        
        reply = QMessageBox.question(self, "Подтверждение", 
                                    f"Восстановить участника {fio}?\n\n"
                                    f"Игрок будет возвращен в основной список.",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                # Получаем данные из таблицы Delete_player
                deleted = Delete_player.get_by_id(player_id)
                
                # Восстанавливаем игрока в таблицу Player
                Player.create(
                    player=deleted.player,
                    fio=deleted.full_name,
                    bday=deleted.bday,
                    rank=deleted.rank,
                    city=deleted.city,
                    region=deleted.region,
                    razryad=deleted.razryad,
                    coach_id=deleted.coach_id.id if deleted.coach_id else None,
                    title_id=self.current_title_id,
                    sex=deleted.sex,
                    total_game_player=0,
                    total_win_game=0,
                    coefficient_victories=0.0,
                    application="предварительная",
                    comment=deleted.comment,
                    pay_rejting=deleted.pay_rejting,
                    patronymic_id=deleted.patronymic_id if deleted.patronymic_id else None,
                    mesto=0
                )
                
                # Удаляем запись из архива
                deleted.delete_instance()
                
                # Обновляем таблицу в зависимости от текущего режима
                if self.btn_filter_deleted.isChecked():
                    self.load_deleted_players()
                else:
                    self.load_participants_for_title()
                
                QMessageBox.information(self, "Успех", f"Участник {fio} восстановлен")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при восстановлении: {str(e)}")

    def toggle_deleted_filter(self):
        """Переключение фильтра удаленных игроков"""
        if self.btn_filter_deleted.isChecked():
            # Показываем удаленных игроков
            self.load_deleted_players()
            # Меняем стиль кнопок в левой панели
            self.btn_filter_deleted.setText("📋 Скрыть удаленных")
            # Отключаем другие фильтры сортировки
            QMessageBox.information(self, "Режим архива", 
                                "Показаны удаленные игроки.\n"
                                "Используйте кнопку 'Восстановить' для возврата игрока.")
        else:
            # Показываем активных игроков
            self.load_participants_for_title()
            self.btn_filter_deleted.setText("📋 Показать удаленных")
            # Восстанавливаем цвет заголовка
            self.table_header.setStyleSheet("""
                background-color: #2196F3;
                color: white;
                padding: 6px;
                font-weight: bold;
                font-size: 11px;
                border-radius: 3px;
            """)

    def show_all_players(self):
        """Показать всех активных игроков (сброс фильтров)"""
        # Сбрасываем фильтр удаленных
        if self.btn_filter_deleted.isChecked():
            self.btn_filter_deleted.setChecked(False)
            self.btn_filter_deleted.setText("📋 Показать удаленных")
        
        # Сбрасываем остальные фильтры
        self.reset_filters()
        
        # Загружаем активных участников
        self.load_participants_for_title()
        
        # Восстанавливаем цвет заголовка
        self.table_header.setStyleSheet("""
            background-color: #2196F3;
            color: white;
            padding: 6px;
            font-weight: bold;
            font-size: 11px;
            border-radius: 3px;
        """)
        
        QMessageBox.information(self, "Сброс фильтров", "Показаны все активные участники")
# ==========================
    def _export_database(self):
        """Экспорт базы данных в файл"""
        try:
            # Создаем диалог выбора места сохранения
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Экспорт базы данных",
                f"backup_db/backup_{QDate.currentDate().toString('yyyy_MM_dd')}.sql",
                "SQL files (*.sql);;All files (*.*)"
            )
            
            if not file_path:
                return
            
            # Убедимся, что папка существует
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Показываем прогресс-бар
            progress = QProgressDialog("Экспорт базы данных...", "Отмена", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            from models import db
            
            # Получаем параметры подключения
            # Для Peewee connection_params хранит параметры
            if hasattr(db, 'connection_params'):
                host = db.connection_params.get('host', 'localhost')
                user = db.connection_params.get('user', 'root')
                password = db.connection_params.get('password', '')
                port = db.connection_params.get('port', 3306)
                database = db.database
            else:
                # Альтернативный способ
                host = 'localhost'
                user = 'root'
                password = 'db_pass'
                port = 3306
                database = db.database
            
            progress.setValue(20)
            
            # Формируем команду mysqldump
            import subprocess
            
            cmd = [
                'mysqldump',
                f'--host={host}',
                f'--user={user}',
                f'--password={password}',
                f'--port={port}',
                database,
                '--result-file=' + file_path,
                '--skip-extended-insert',
                '--complete-insert'
            ]
            
            progress.setValue(50)
            
            # Выполняем команду
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            progress.setValue(100)
            
            if result.returncode == 0:
                QMessageBox.information(self, "Успех", 
                                    f"База данных успешно экспортирована в файл:\n{file_path}")
            else:
                QMessageBox.warning(self, "Предупреждение", 
                                f"Не удалось выполнить экспорт через mysqldump.\n"
                                f"Будет использован встроенный экспорт.\n\n"
                                f"Ошибка: {result.stderr}")
                # Если mysqldump не работает, используем встроенный экспорт
                self.export_database_internal(file_path, progress)
            
            progress.close()
            
        except Exception as e:
            progress.close()
            # Если произошла ошибка, пробуем встроенный экспорт
            self.export_database_internal(file_path, None)

    def export_database(self):
        """Экспорт базы данных в файл"""
        try:
            # Создаем диалог выбора места сохранения
            backup_dir = "backup_db"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            from datetime import datetime
            default_name = f"backup_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.sql"
            default_path = os.path.join(backup_dir, default_name)
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Экспорт базы данных",
                default_path,
                "SQL files (*.sql);;All files (*.*)"
            )
            
            if not file_path:
                return
            
            # Показываем прогресс-бар
            progress = QProgressDialog("Экспорт базы данных...", "Отмена", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            try:
                self.export_database_internal(file_path, progress)
                progress.setValue(100)
                QMessageBox.information(self, "Успех", 
                                    f"База данных успешно экспортирована в файл:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать базу данных: {str(e)}")
            finally:
                progress.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")
# =======================================
    def import_database(self):
        """Импорт базы данных из файла бэкапа"""
        try:
            # Создаем диалог выбора файла, по умолчанию открываем папку backup_db
            backup_dir = "backup_db"
            if os.path.exists(backup_dir):
                start_dir = backup_dir
            else:
                start_dir = ""
            
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Импорт базы данных",
                start_dir,
                "SQL files (*.sql);;All files (*.*)"
            )
            
            if not file_path:
                return
            
            # Запрашиваем подтверждение
            reply = QMessageBox.question(
                self, 
                "Подтверждение", 
                f"Импорт базы данных из файла:\n{file_path}\n\n"
                f"ВНИМАНИЕ! Текущие данные будут заменены!\n"
                f"Перед импортом рекомендуется сделать резервную копию.\n\n"
                f"Продолжить?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Показываем прогресс-бар
            progress = QProgressDialog("Импорт базы данных...", "Отмена", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # Читаем SQL файл
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            progress.setValue(30)
            
            # Подключаемся к БД и выполняем импорт
            from models import db
            
            # Закрываем текущее соединение
            if not db.is_closed():
                db.close()
            
            progress.setValue(50)
            
            # Открываем новое соединение
            db.connect()
            
            progress.setValue(70)
            
            # Разбиваем SQL на отдельные запросы
            import re
            # Убираем комментарии
            sql_content = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
            # Разбиваем по точкам с запятой
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            
            total = len(statements)
            for i, statement in enumerate(statements):
                if statement:
                    try:
                        db.execute_sql(statement)
                    except Exception as e:
                        print(f"Ошибка выполнения запроса: {e}")
                        print(f"Запрос: {statement[:100]}...")
                
                # Обновляем прогресс
                progress.setValue(70 + int((i + 1) / total * 30))
                
                if progress.wasCanceled():
                    break
            
            progress.setValue(100)
            
            QMessageBox.information(self, "Успех", 
                                f"База данных успешно импортирована из файла:\n{file_path}\n\n"
                                f"Рекомендуется перезапустить приложение для полного применения изменений.")
            
            progress.close()
            
            # Предлагаем перезапустить приложение
            restart_reply = QMessageBox.question(
                self,
                "Перезапуск",
                "Для полного применения изменений рекомендуется перезапустить приложение.\n"
                "Перезапустить сейчас?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if restart_reply == QMessageBox.Yes:
                # Перезапускаем приложение
                python = sys.executable
                os.execl(python, python, *sys.argv)
            
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Ошибка", f"Не удалось импортировать базу данных: {str(e)}")

    def open_competition(self):
        """Открыть существующее соревнование"""
        # Переключаемся на вкладку Титул, где отображаются все соревнования
        self.tab_widget.setCurrentIndex(0)
        QMessageBox.information(self, "Открытие соревнования", 
                            "Выберите соревнование из списка справа")
# ============================     
    def create_system_tab(self):
        """Вкладка Система - только отображение информации о этапах"""
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Информационное окно для вывода этапов
        info_group = QGroupBox("📋 Информация о добавленных этапах")
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(3)
        info_layout.setContentsMargins(5, 10, 5, 5)
        
        self.stages_info = QTextEdit()
        self.stages_info.setReadOnly(True)
        self.stages_info.setMinimumHeight(500)
        self.stages_info.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                font-family: Consolas, monospace;
                font-size: 12px;
                line-height: 1.4;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        info_layout.addWidget(self.stages_info)
        
        main_layout.addWidget(info_group)
        main_layout.addStretch()
        
        # Загружаем существующие данные
        self.load_system_data()
        
        return tab_widget
# ======================================
    def edit_system_settings(self):
        """Редактирование существующей системы проведения"""
        if not self.current_title_id:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите соревнование")
            return
        
        try:
            # Получаем выбранный этап
            if not hasattr(self, 'stages_list') or not self.stages_list:
                QMessageBox.warning(self, "Ошибка", "Нет добавленных этапов для редактирования")
                return
            
            # Создаем диалог выбора этапа
            dialog = QDialog(self)
            dialog.setWindowTitle("Выбор этапа для редактирования")
            dialog.setModal(True)
            dialog.setFixedSize(400, 200)
            
            layout = QVBoxLayout(dialog)
            layout.addWidget(QLabel("Выберите этап для редактирования:"))
            
            stage_combo = QComboBox()
            for i, stage in enumerate(self.stages_list, 1):
                stage_combo.addItem(f"{i}. {stage['stage_name']}")
            
            layout.addWidget(stage_combo)
            
            btn_layout = QHBoxLayout()
            ok_btn = QPushButton("Редактировать")
            ok_btn.clicked.connect(dialog.accept)
            cancel_btn = QPushButton("Отмена")
            cancel_btn.clicked.connect(dialog.reject)
            btn_layout.addWidget(ok_btn)
            btn_layout.addWidget(cancel_btn)
            layout.addLayout(btn_layout)
            
            if dialog.exec_() != QDialog.Accepted:
                return
            
            selected_index = stage_combo.currentIndex()
            selected_stage = self.stages_list[selected_index]
            
            # Открываем диалог редактирования
            edit_dialog = QDialog(self)
            edit_dialog.setWindowTitle(f"Редактирование этапа: {selected_stage['stage_name']}")
            edit_dialog.setModal(True)
            edit_dialog.setMinimumWidth(450)
            
            edit_layout = QVBoxLayout(edit_dialog)
            
            edit_group = QGroupBox("Параметры этапа")
            edit_group_layout = QFormLayout(edit_group)
            
            # Название этапа
            stage_edit = QComboBox()
            stage_edit.addItems([
                "Одна таблица",
                "Квалификация",
                "1-й полуфинал",
                "2-й полуфинал",
                "Финал",
                "Суперфинал"
            ])
            stage_edit.setEditable(True)
            stage_edit.setCurrentText(selected_stage['stage_name'])
            edit_group_layout.addRow("Название этапа:", stage_edit)
            
            # Тип таблицы
            table_type_edit = QComboBox()
            table_type_edit.addItems([
                "Круговая",
                "Олимпийская (минус 2)",
                "Олимпийская (с розыгрышем всех мест)",
                "Олимпийская (за 1-3 место)"
            ])
            table_type_edit.setCurrentText(selected_stage['table_type'])
            edit_group_layout.addRow("Тип таблицы:", table_type_edit)
            
            # Количество групп
            groups_edit = QLineEdit()
            groups_edit.setText(str(selected_stage['total_groups']))
            edit_group_layout.addRow("Количество групп:", groups_edit)
            
            # Максимум участников
            max_players_edit = QLineEdit()
            max_players_edit.setText(str(selected_stage['max_players']))
            edit_group_layout.addRow("Максимум участников:", max_players_edit)
            
            # Количество проходящих
            stage_exit_edit = QLineEdit()
            stage_exit_edit.setText(str(selected_stage['stage_exit']))
            edit_group_layout.addRow("Проходят в след. этап:", stage_exit_edit)
            
            edit_layout.addWidget(edit_group)
            
            btn_edit_layout = QHBoxLayout()
            save_btn = QPushButton("💾 Сохранить изменения")
            save_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
            cancel_edit_btn = QPushButton("❌ Отмена")
            cancel_edit_btn.setStyleSheet("background-color: #f44336; color: white; padding: 5px;")
            
            def save_changes():
                try:
                    # Обновляем данные в списке
                    selected_stage['stage_name'] = stage_edit.currentText()
                    selected_stage['table_type'] = table_type_edit.currentText()
                    selected_stage['total_groups'] = int(groups_edit.text()) if groups_edit.text().isdigit() else 1
                    selected_stage['max_players'] = int(max_players_edit.text()) if max_players_edit.text().isdigit() else 16
                    selected_stage['stage_exit'] = int(stage_exit_edit.text()) if stage_exit_edit.text().isdigit() else 0
                    
                    # Обновляем в базе данных
                    system = System.get_or_none(
                        (System.title_id == self.current_title_id) &
                        (System.stage == selected_stage['stage_name'])
                    )
                    
                    if system:
                        system.stage = selected_stage['stage_name']
                        if hasattr(system, 'type_table'):
                            system.type_table = selected_stage['table_type']
                        system.total_group = selected_stage['total_groups']
                        system.max_player = selected_stage['max_players']
                        system.mesta_exit = selected_stage['stage_exit']
                        system.save()
                    
                    # Обновляем информационное окно
                    self.update_stages_info()
                    
                    QMessageBox.information(edit_dialog, "Успех", "Изменения сохранены")
                    edit_dialog.accept()
                    
                except Exception as e:
                    QMessageBox.critical(edit_dialog, "Ошибка", f"Не удалось сохранить изменения: {str(e)}")
            
            save_btn.clicked.connect(save_changes)
            cancel_edit_btn.clicked.connect(edit_dialog.reject)
            
            btn_edit_layout.addWidget(save_btn)
            btn_edit_layout.addWidget(cancel_edit_btn)
            edit_layout.addLayout(btn_edit_layout)
            
            edit_dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")
       
    def system_settings(self):
        """Настройки системы (вызов из левой панели)"""
        # Создаем диалог выбора
        dialog = QDialog(self)
        dialog.setWindowTitle("Система проведения")
        dialog.setModal(True)
        dialog.setFixedSize(300, 150)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Выберите действие:"))
        
        btn_create = QPushButton("📝 Создать новую систему")
        btn_create.clicked.connect(lambda: [dialog.accept(), self.create_system_settings()])
        btn_create.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        
        btn_edit = QPushButton("✏️ Редактировать текущую систему")
        btn_edit.clicked.connect(lambda: [dialog.accept(), self.edit_system_settings()])
        btn_edit.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(dialog.reject)
        
        layout.addWidget(btn_create)
        layout.addWidget(btn_edit)
        layout.addWidget(btn_cancel)
        
        dialog.exec_()
#====================================
    def load_system_data(self):
        """Загрузка данных системы на вкладке Система"""
        if not self.current_title_id:
            return
        if not hasattr(self, 'system_stage') or not hasattr(self, 'table_type'):
            return
        try:
            from models import System
            
            # Обновляем информационное окно с существующими этапами
            self.update_stages_info()
            
            # Получаем последний добавленный этап для заполнения полей
            last_system = System.select().where(
                System.title_id == self.current_title_id
            ).order_by(System.id.desc()).first()
            
            if last_system:
                # Заполняем поля последним использованным значением
                index = self.system_stage.findText(last_system.stage)
                if index >= 0:
                    self.system_stage.setCurrentIndex(index)
                else:
                    self.system_stage.setCurrentText(last_system.stage)
                
                index = self.table_type.findText(last_system.type_table)
                if index >= 0:
                    self.table_type.setCurrentIndex(index)
                
                # Для квалификации заполняем количество групп
                if "Квалификация" in last_system.stage:
                    self.total_groups.setText(str(last_system.total_group))
                    self.total_groups.setEnabled(True)
                else:
                    # Для полуфиналов и финалов количество групп рассчитывается автоматически
                    self.total_groups.setText(str(last_system.total_group))
                    self.total_groups.setEnabled(False)
                    self.total_groups.setStyleSheet("background-color: #f0f0f0; color: #999;")
                
                self.score_flag.setCurrentText(str(last_system.score_flag) if last_system.score_flag else "5")
            else:
                # Очищаем поля, если этапов нет
                self.system_stage.setCurrentIndex(0)
                self.table_type.setCurrentIndex(0)
                self.total_groups.clear()
                self.total_groups.setEnabled(True)
                self.total_groups.setStyleSheet("")
                self.score_flag.setCurrentText("5")
                
        except Exception as e:
            print(f"Ошибка загрузки данных системы: {e}")
#===============================
    def add_system_stage(self):
        """Добавление этапа в список"""
        from models import System
        from PyQt5.QtWidgets import QSpinBox

        # Проверяем статус игроков перед созданием системы
        if not self.check_players_status():
            return
        
        # Запрашиваем параметры системы (только один раз)
        if not hasattr(self, 'system_tables') or not hasattr(self, 'match_time'):
            tables, match_time = self.get_system_parameters()
            if tables is None or match_time is None:
                return  # Пользователь отменил ввод параметров
            self.system_tables = tables
            self.match_time = match_time
        
        # Получаем данные из формы
        stage_name = self.system_stage.currentText().strip()
        if not stage_name:
            QMessageBox.warning(self, "Ошибка", "Введите название этапа")
            return
        
        table_type = self.table_type.currentText()
        score_flag = self.score_flag.currentText()
        total_players = Player.select().where(Player.title_id == self.current_title_id).count()
        
        # Получаем предыдущий этап
        previous_stage = System.select().where(
            System.title_id == self.current_title_id
        ).order_by(System.id.desc()).first()
        
        # Переменные для хранения информации об этапе
        total_groups = 1
        max_players = total_players
        stage_exit = 0
        choice_flag = 0
        label_string = ""
        kol_game_string = ""
        total_games_in_stage = 0
        
        # Получаем информацию о распределении игроков
        distribution = self.get_players_distribution_info()

        # === ОДНА ТАБЛИЦА ===
        if stage_name == "Одна таблица":
            if previous_stage:
                QMessageBox.warning(self, "Ошибка", "Этап 'Одна таблица' может быть только первым этапом")
                return
            
            total_groups = 1
            max_players = total_players
            stage_exit = 0
            
            # Расчет количества игр
            if table_type == "Круговая":
                total_games_in_stage = (total_players * (total_players - 1)) // 2
                kol_game_string = f"Всего игр: {total_games_in_stage}"
            else:
                total_games_in_stage = self.calculate_olympic_games(total_players)
                kol_game_string = f"Всего игр: {total_games_in_stage}"
            
            label_string = f"Одна таблица, {total_players} участников"
            choice_flag = 1
            
        # === КВАЛИФИКАЦИЯ ===
        elif "Квалификация" in stage_name and "полуфинал" not in stage_name:
            total_groups_text = self.total_groups.text().strip()
            if not total_groups_text or not total_groups_text.isdigit():
                QMessageBox.warning(self, "Ошибка", "Введите количество групп")
                return
            total_groups = int(total_groups_text)
            
            # Распределение участников по группам
            base = total_players // total_groups
            remainder = total_players % total_groups
            players_per_group = base + (1 if remainder > 0 else 0)
            max_players = players_per_group
            
            # Спрашиваем количество выходящих из каждой группы
            if previous_stage:
                exit_count, ok = QInputDialog.getInt(self, "Выход из групп", 
                                                    "Сколько участников выходит из каждой группы?",
                                                    2, 1, players_per_group)
                if not ok:
                    return
                stage_exit = exit_count
            else:
                stage_exit = 2
            
            # Расчет количества игр в квалификации
            group_sizes = self.calculate_group_sizes(total_players, total_groups)
            total_games_in_stage = 0
            games_info = []
            for i, gsize in enumerate(group_sizes, 1):
                if table_type == "Круговая":
                    games = (gsize * (gsize - 1)) // 2
                else:
                    games = self.calculate_olympic_games(gsize)
                total_games_in_stage += games
                games_info.append(f"Гр{i}: {games} игр")
            
            # kol_game_string = " | ".join(games_info)
            kol_game_string = str (f"{total_games_in_stage} игр.")
            # label_string = f"Квалификация: {total_groups} гр по {players_per_group} чел."
            label_string = ""
            choice_flag = 0
            source_stage = ""
            
        # === ПОЛУФИНАЛЫ ===
        elif "полуфинал" in stage_name.lower():
            if not previous_stage or "Квалификация" not in previous_stage.stage:
                QMessageBox.warning(self, "Ошибка", "Полуфинал может следовать только после квалификации")
                return
            
            # Количество групп полуфинала = количество групп квалификации / 2
            total_groups = max(1, previous_stage.total_group // 2)
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Настройка полуфинала")
            dialog.setModal(True)
            dialog.setMinimumWidth(400)
            
            layout = QVBoxLayout(dialog)
            layout.addWidget(QLabel(f"Из этапа '{previous_stage.stage}' в полуфинал переходят:"))
            
            exit_layout = QHBoxLayout()
            exit_layout.addWidget(QLabel("Количество участников из каждой группы:"))
            exit_spin = QSpinBox()
            exit_spin.setMinimum(1)
            exit_spin.setMaximum(previous_stage.max_player)
            exit_spin.setValue(previous_stage.mesta_exit if previous_stage.mesta_exit > 0 else 2)
            exit_layout.addWidget(exit_spin)
            layout.addLayout(exit_layout)
            
            info_label = QLabel()
            info_label.setStyleSheet("color: blue;")
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
            
            def update_semifinal_info():
                exit_val = exit_spin.value()
                players_per_group = exit_val * 2
                total_in_semifinal = previous_stage.total_group * exit_val
                info_label.setText(f"Всего в полуфинале: {total_in_semifinal} чел.\n"
                                f"Количество групп: {total_groups}\n"
                                f"Участников в группе: {players_per_group} чел.\n"
                                f"Всего игр: {self.calculate_semifinal_games_count(total_groups, players_per_group, previous_stage)}")
            
            exit_spin.valueChanged.connect(update_semifinal_info)
            update_semifinal_info()
            
            btn_layout = QHBoxLayout()
            ok_btn = QPushButton("OK")
            ok_btn.clicked.connect(dialog.accept)
            cancel_btn = QPushButton("Отмена")
            cancel_btn.clicked.connect(dialog.reject)
            btn_layout.addWidget(ok_btn)
            btn_layout.addWidget(cancel_btn)
            layout.addLayout(btn_layout)
            
            if dialog.exec_() != QDialog.Accepted:
                return
            
            stage_exit = exit_spin.value()
            max_players = stage_exit * 2
            choice_flag = 0
            
            # Расчет количества игр в полуфинале
            players_per_group = stage_exit * 2
            group_sizes = [players_per_group] * total_groups
            total_games_in_stage = 0
            games_info = []
            exit_count = previous_stage.mesta_exit
            for i, gsize in enumerate(group_sizes, 1):
                total_possible = (gsize * (gsize - 1)) // 2
                already_played = (exit_count * (exit_count - 1)) // 2 * 2
                games = total_possible - already_played
                total_games_in_stage += games
                games_info.append(f"Гр{i}: {games} игр")
            
            kol_game_string = f"{total_games_in_stage} игр."
            label_string = ""

            source_stage = "Квалификация"

        # === ФИНАЛ ===
        elif self.is_final_stage(stage_name):
            if not previous_stage:
                QMessageBox.warning(self, "Ошибка", "Финал не может быть первым этапом (используйте 'Одна таблица')")
                return
    
            # Получаем следующий номер финала
            final_number = len(distribution['finals']) + 1

            stage_name_with_number = f"{final_number}-й финал"
            stage_name = stage_name_with_number

            # Определяем, откуда будут браться игроки для следующего финала
            groups_list = []
            source_stage = None
            remaining_players = 0
            players_per_group = 0
            total_groups = 0
            players_in_final = 0

            already_in_finals = sum([f['players'] for f in distribution['finals']])

            # Сначала проверяем 1-й полуфинал (есть ли еще нераспределенные игроки)
            systems_sf = System.select().where((System.title_id == self.current_title_id) and (System.stage_exit == "Квалификация. 1-й полуфинал"))
            for sf in systems_sf:
                mesta_exit = sf.mesta_exit
                groups_list.append(mesta_exit)
            players_in_final = sum(groups_list)

            if distribution['semifinal_1']['players_per_group'] > players_in_final:
                source_stage = "Квалификация. 1-й полуфинал"
                # число участников в группе
                players_per_group = distribution['semifinal_1']['players_per_group']
                # число игроков еще не посеянных в финале
                if stage_name != "1-й финал":
                    remaining_players = players_per_group - distribution['semifinal_1']['exited_per_group']
                else:
                    remaining_players = players_per_group
                # число групп в полуфинале
                total_groups = distribution['semifinal_1']['total_groups']
            
            # Затем проверяем 2-й полуфинал
            if not source_stage and distribution['semifinal_2']['total_groups'] > 0:
                if already_in_finals < distribution['semifinal_2']['exited_total']:
                    source_stage = "Квалификация. 2-й полуфинал"
                    remaining_players = distribution['semifinal_2']['exited_total'] - already_in_finals
                    players_per_group = distribution['semifinal_2']['exited_per_group']
                    total_groups = distribution['semifinal_2']['total_groups']
            
            # Затем проверяем квалификацию (оставшиеся игроки, не ушедшие в полуфиналы)
            if not source_stage and distribution['qualification']['total_groups'] > 0:
                # Вычитаем уже ушедших в полуфиналы
                gone_to_semifinals = 0
                if distribution['semifinal_1']['exited_total'] > 0:
                    gone_to_semifinals += distribution['semifinal_1']['exited_total']
                if distribution['semifinal_2']['exited_total'] > 0:
                    gone_to_semifinals += distribution['semifinal_2']['exited_total']
                
                remaining_in_qualification = distribution['qualification']['remaining_total']
                
                if remaining_in_qualification > 0:
                    source_stage = "Квалификация"
                    remaining_players = remaining_in_qualification
                    players_per_group = distribution['qualification']['players_per_group'] - distribution['qualification']['exited_per_group']
                    total_groups = distribution['qualification']['total_groups']
            
            if not source_stage or remaining_players <= 0:
                QMessageBox.warning(self, "Ошибка", "Нет игроков для создания нового финала")
                return
    
# ==================================================================            
            # Диалог для финала
            dialog = QDialog(self)
            dialog.setWindowTitle("Настройка финала")
            dialog.setModal(True)
            dialog.setMinimumWidth(400)
            
            layout = QVBoxLayout(dialog)
            
            # Информация об источнике игроков
            info_label = QLabel(f"Из этапа '{source_stage}' в {stage_name} выходят:")
            info_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            layout.addWidget(info_label)
            
            layout.addSpacing(10)
            
            # Показываем оставшихся игроков
            # remaining_label = QLabel(f"Осталось нераспределенных игроков из {source_stage}: {remaining_players}")
            players_not_out = total_players - already_in_finals
            remaining_label = QLabel(f"Осталось всего нераспределенных игроков: {players_not_out}")
            remaining_label.setStyleSheet("color: brown; font-weight: bold;")
            layout.addWidget(remaining_label)
            
            # # Показываем сколько игроков уже в финалах из этого этапа
            # already_in_finals_from_source = already_in_finals
            # if source_stage == "Квалификация. 1-й полуфинал":
            #     already_in_finals_from_source = already_in_finals
            # elif source_stage == "Квалификация. 2-й полуфинал":
            #     already_in_finals_from_source = already_in_finals - distribution['semifinal_1']['exited_total'] if distribution['semifinal_1']['exited_total'] > 0 else already_in_finals
            # elif source_stage == "Квалификация":
            #     already_in_finals_from_source = already_in_finals - distribution['semifinal_1']['exited_total'] - distribution['semifinal_2']['exited_total'] if distribution['semifinal_2']['exited_total'] > 0 else already_in_finals
            
            # already_label = QLabel(f"Уже распределено в финалы из {source_stage}: {already_in_finals_from_source}")
            # already_label.setStyleSheet("color: blue;")
            # layout.addWidget(already_label)
            
            # layout.addSpacing(5)
# ===========================================            
            # Количество выходящих из каждой группы
            exit_layout = QHBoxLayout()
            exit_layout.addWidget(QLabel("Количество участников из каждой группы:"))
            exit_edit = QLineEdit()
            exit_edit.setPlaceholderText("число")
            exit_edit.setText(str(min(2, 1)))
            exit_edit.setValidator(QIntValidator(1, players_per_group))  # Только целые числа
            exit_edit.setMaximumWidth(80)
            exit_layout.addWidget(exit_edit)
            layout.addLayout(exit_layout)

            # Информация о финале
            finals_info_label = QLabel()
            finals_info_label.setStyleSheet("color: blue;")
            finals_info_label.setWordWrap(True)
            layout.addWidget(finals_info_label)

            # Информация о местах
            places_info_label = QLabel()
            places_info_label.setStyleSheet("color: green;")
            places_info_label.setWordWrap(True)
            layout.addWidget(places_info_label)

            # Расчет начальных позиций мест
            start_place = 1
            for final in distribution['finals']:
                start_place += final['players']

            # Переменные для хранения значений
            total_in_this_final = 0
            games_in_this_final = 0

            def update_finals_info():
                nonlocal total_in_this_final, games_in_this_final
                
                # Получаем значение из QLineEdit
                try:
                    exit_val = int(exit_edit.text())
                    if exit_val < 1:
                        exit_val = 1
                        exit_edit.setText("1")
                    if exit_val > players_per_group:
                        exit_val = players_per_group
                        exit_edit.setText(str(players_per_group))
                    
                except ValueError:
                    exit_val = min(2, players_per_group)
                    exit_edit.setText(str(exit_val))

                # # определяем число игроков в последнем финале               
                total_in_this_final = total_groups * exit_val

                if exit_val > remaining_players:
                    # Показываем предупреждение, не изменяя значение
                    finals_info_label.setText(f"⚠️ Недостаточно игроков! Максимум: {remaining_players} чел.\n"
                                            f"Текущее значение: {total_in_this_final} чел.")
                    return total_in_this_final, games_in_this_final
                
                # если в последнем финале игроков болше чем всех участников, то последнее место это количестов всех участников
                end_place = start_place + total_in_this_final - 1
                if total_players < end_place:
                    end_place = total_players
               
                # Показываем, из каких групп выходят игроки
                groups_info = []
                for i in range(total_groups):
                    groups_info.append(f"Группа {i+1}: {exit_val} чел.")
                
                finals_info_label.setText(f"✅ Всего в этом {stage_name}: {total_in_this_final} чел.\n"
                                        f"📌 Источник: {source_stage}")
                
                places_info_label.setText(f"Места с {start_place} по {end_place}")
                
                # Рассчитываем количество игр
                group_sizes = [total_in_this_final]
                games_in_this_final = self.calculate_total_games(
                    self.table_type.currentText(), 
                    total_in_this_final, 
                    1, 
                    group_sizes, 
                    stage_name, 
                    previous_stage
                )
                
                return total_in_this_final, games_in_this_final

            # Подключаем сигналы изменения текста
            def on_exit_text_changed():
                update_finals_info()

            exit_edit.textChanged.connect(on_exit_text_changed)

            # Вызываем функцию для начального расчета
            total_in_this_final, games_in_this_final = update_finals_info()

            layout.addSpacing(10)

            btn_layout = QHBoxLayout()
            ok_btn = QPushButton("OK")
            ok_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
            ok_btn.clicked.connect(dialog.accept)
            cancel_btn = QPushButton("Отмена")
            cancel_btn.setStyleSheet("background-color: #f44336; color: white; padding: 5px;")
            cancel_btn.clicked.connect(dialog.reject)
            btn_layout.addWidget(ok_btn)
            btn_layout.addWidget(cancel_btn)
            layout.addLayout(btn_layout)

            if dialog.exec_() != QDialog.Accepted:
                return

            # Получаем значение из QLineEdit после закрытия диалога
            try:
                stage_exit = int(exit_edit.text())
                if stage_exit < 1:
                    stage_exit = 1
                if stage_exit > players_per_group:
                    stage_exit = players_per_group
            except ValueError:
                stage_exit = min(2, players_per_group)

            max_players = total_in_this_final
            choice_flag = 0

            # Формируем строки для записи в БД
            label_string = places_info_label.text()
            kol_game_string = f"{games_in_this_final} игр."

            # После добавления финала, обновляем информацию о посеве
            self.update_seeding_info()

            # # Проверяем, все ли игроки распределены
            remaining_players = self.update_seeding_info()

            all_posev_player = total_in_this_final + remaining_players
            if total_players <= all_posev_player:
                self.fill_choice_table()
            # if total_players - already_in_finals - players_not_out  <= 1:
            # if total_players - remaining_players <= 1:
                reply = QMessageBox.question(self, "Завершение посева", 
                                            f"✅ Все {total_players} игроков распределены по финалам!\n\n"
                                            f"Провести жеребьевку квалификации сейчас?",
                                            QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.perform_drawing()
                  

            # Сохраняем информацию о финале
            self.current_finals_info = {
                'number': final_number,
                'players': total_in_this_final,
                'source': source_stage,
                'places': f"{start_place}-{start_place + total_in_this_final - 1}"
            }      
    # Продолжаем сохранение в БД...
        else:
            QMessageBox.warning(self, "Ошибка", f"Неизвестный тип этапа: {stage_name}")
            return
            
        # Сохраняем в базу данных
        try:
            
            system_data = {
                'title_id': self.current_title_id,
                'total_athletes': total_players,
                'total_group': total_groups,
                'max_player': max_players,
                'stage': stage_name,
                'stage_exit': source_stage if source_stage else "",
                'mesta_exit': stage_exit,
                'label_string': label_string,
                'kol_game_string': kol_game_string,
                'page_vid': "книжная",
                'choice_flag': choice_flag,
                'score_flag': int(score_flag),
                'visible_game': True,
                'no_game': "",
                'sex': self.current_sex if self.current_sex else "man"
            }
            
            if hasattr(System, 'type_table'):
                system_data['type_table'] = table_type
            
            system = System.create(**system_data)
            self.update_stages_info()

            # После добавления финала, обновляем информацию о посеве
            self.update_seeding_info()
            
            # Подсчет общей суммы игр
            total_all_games = 0
            all_systems = System.select().where(System.title_id == self.current_title_id)
            for s in all_systems:
                if s.kol_game_string:
                    # Извлекаем числа из строки
                    import re
                    numbers = re.findall(r'(\d+)', s.kol_game_string)
                    for num in numbers:
                        total_all_games += int(num)
            
            QMessageBox.information(self, "Успех", 
                                f"✅ Этап '{stage_name}' добавлен\n"
                                # f"📊 Игр в этапе: {total_games_in_stage}\n"
                                f"🏆 Всего на соревновании: {total_all_games} игр.")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить этап: {str(e)}")    
# ==================================
    def update_stages_info(self):
        """Обновление информационного окна со списком этапов (формат 2 строки с выравниванием)"""
        try:
            from models import System, Player, Title
            import math
            
            if not self.current_title_id:
                self.stages_info.setText("Нет выбранного соревнования")
                return
            
            title = Title.get_or_none(Title.id == self.current_title_id)
            title_name = title.name if title else "Неизвестное соревнование"
            
            systems = System.select().where(System.title_id == self.current_title_id).order_by(System.id)
            
            self.stages_info.clear()
            
            if systems.count() == 0:
                self.stages_info.setText(f"🏆 СОРЕВНОВАНИЕ: {title_name}\n\n{'=' * 60}\n\n❌ Нет добавленных этапов")
                return
            
            # Получаем параметры системы
            tables = getattr(self, 'system_tables', 4)
            match_time = getattr(self, 'match_time', 15)
            
            info_text = f"🏆 СОРЕВНОВАНИЕ: {title_name.upper()}. СИСТЕМА ПРОВЕДЕНИЯ. | 🏓 Столов: {tables} | ⏱️ Время на матч: {match_time} мин.\n"
            info_text += "=" * 110 + "\n\n"
            
            previous_stage = None
            current_place = 1
            total_all_games = 0
            total_time_minutes = 0
            
            # Определяем максимальную ширину для выравнивания
            max_games_width = 0
            
            # Первый проход: определяем максимальную ширину
            temp_games_list = []
            for system in systems:
                total_players = Player.select().where(Player.title_id == self.current_title_id).count()
                if total_players == 0:
                    temp_games_list.append(0)
                else:
                    groups_count = system.total_group if system.total_group else 1
                    if "полуфинал" in system.stage.lower() and previous_stage and "Квалификация" in previous_stage.stage:
                        players_in_semifinal = previous_stage.total_group * previous_stage.mesta_exit
                        players_per_group = previous_stage.mesta_exit * 2
                        games = self.calculate_semifinal_games_count(groups_count, players_per_group, previous_stage)
                    elif self.is_final_stage(system.stage):
                        if system.kol_game_string:
                            import re
                            games_match = re.search(r'(\d+)', system.kol_game_string)
                            games = int(games_match.group(1)) if games_match else 0
                        else:
                            if "Круговая" in system.type_table:
                                games = (system.max_player * (system.max_player - 1)) // 2
                            else:
                                games = self.calculate_olympic_games(system.max_player)
                    else:
                        group_sizes = self.calculate_group_sizes(total_players, groups_count)
                        games = self.calculate_total_games(
                            system.type_table, total_players, groups_count, group_sizes,
                            system.stage, previous_stage
                        )
                    temp_games_list.append(games)
                previous_stage = system
            
            # Определяем максимальную ширину для выравнивания
            max_games_width = max([len(str(g)) for g in temp_games_list]) if temp_games_list else 0
            max_games_width = max(max_games_width, 30)
            
            # Второй проход: выводим с выравниванием
            previous_stage = None
            for idx, system in enumerate(systems, 1):
                total_players = Player.select().where(Player.title_id == self.current_title_id).count()
                
                if total_players == 0:
                    distribution_text = "нет участников"
                    total_games = 0
                    stage_display = system.stage
                    places_display = ""
                    stage_time = "0 мин"
                else:
                    groups_count = system.total_group if system.total_group else 1
                    
                    # Для полуфинала
                    if "полуфинал" in system.stage.lower() and previous_stage and "Квалификация" in previous_stage.stage:
                        players_in_semifinal = previous_stage.total_group * previous_stage.mesta_exit
                        players_per_group = previous_stage.mesta_exit * 2
                        group_sizes = [players_per_group] * groups_count
                        distribution_text = self.calculate_group_distribution(players_in_semifinal, groups_count)
                        total_games = self.calculate_semifinal_games_count(groups_count, players_per_group, previous_stage)
                        stage_display = system.stage
                        places_display = ""
                        
                        # Расчет времени для полуфинала (с учетом туров)
                        max_tours = self.calculate_max_tours_in_stage(group_sizes)
                        tables_per_tour = self.calculate_tables_per_tour(group_sizes)
                        
                        if max_tours > 0 and tables > 0:
                            # Если столов меньше, чем нужно на тур, добавляем дополнительные туры
                            if tables_per_tour > tables:
                                actual_tours = max_tours * math.ceil(tables_per_tour / tables)
                            else:
                                actual_tours = max_tours
                            total_minutes = actual_tours * match_time
                            hours = total_minutes // 60
                            minutes = total_minutes % 60
                            if hours > 0:
                                stage_time = f"{hours} ч {minutes} мин"
                            else:
                                stage_time = f"{minutes} мин"
                        else:
                            stage_time = "0 мин"
                        
                    # Для финала
                    elif self.is_final_stage(system.stage):
                        players_in_final = system.max_player
                        start_place = current_place
                        end_place = current_place + players_in_final - 1
                        
                        distribution_text = f"{players_in_final} чел."
                        
                        if system.kol_game_string:
                            import re
                            games_match = re.search(r'(\d+)', system.kol_game_string)
                            total_games = int(games_match.group(1)) if games_match else 0
                        else:
                            if "Круговая" in system.type_table:
                                total_games = (players_in_final * (players_in_final - 1)) // 2
                            else:
                                total_games = self.calculate_olympic_games(players_in_final)
                        
                        stage_display = system.stage
                        places_display = f" | места {start_place}-{end_place}"
                        current_place += players_in_final
                        
                        # Расчет времени для финала
                        if "Круговая" in system.type_table:
                            # Для кругового финала используем туры
                            max_tours = self.calculate_tours_in_group(players_in_final)
                            tables_per_tour = players_in_final // 2
                            if max_tours > 0 and tables > 0:
                                if tables_per_tour > tables:
                                    actual_tours = max_tours * math.ceil(tables_per_tour / tables)
                                else:
                                    actual_tours = max_tours
                                total_minutes = actual_tours * match_time
                                hours = total_minutes // 60
                                minutes = total_minutes % 60
                                if hours > 0:
                                    stage_time = f"{hours} ч {minutes} мин"
                                else:
                                    stage_time = f"{minutes} мин"
                            else:
                                stage_time = "0 мин"
                        else:
                            # Для олимпийской системы
                            if tables > 0:
                                total_minutes = math.ceil(total_games / tables) * match_time
                                hours = total_minutes // 60
                                minutes = total_minutes % 60
                                if hours > 0:
                                    stage_time = f"{hours} ч {minutes} мин"
                                else:
                                    stage_time = f"{minutes} мин"
                            else:
                                stage_time = "0 мин"
                        
                    else:
                        # Для квалификации
                        group_sizes = self.calculate_group_sizes(total_players, groups_count)
                        distribution_text = self.calculate_group_distribution(total_players, groups_count)
                        total_games = self.calculate_total_games(
                            system.type_table, total_players, groups_count, group_sizes,
                            system.stage, previous_stage
                        )
                        stage_display = system.stage
                        places_display = ""
                        
                        # Расчет времени для квалификации (с учетом туров)
                        max_tours = self.calculate_max_tours_in_stage(group_sizes)
                        tables_per_tour = self.calculate_tables_per_tour(group_sizes)
                        
                        if max_tours > 0 and tables > 0:
                            # Если столов меньше, чем нужно на тур, добавляем дополнительные туры
                            if tables_per_tour > tables:
                                actual_tours = max_tours * math.ceil(tables_per_tour / tables)
                            else:
                                actual_tours = max_tours
                            total_minutes = actual_tours * match_time
                            hours = total_minutes // 60
                            minutes = total_minutes % 60
                            if hours > 0:
                                stage_time = f"{hours} ч {minutes} мин"
                            else:
                                stage_time = f"{minutes} мин"
                        else:
                            stage_time = "0 мин"
                
                # Подсчитываем общее количество игр
                total_all_games += total_games

                # # подсчитываем общее время игр
                # total_all_time += stage_time
                # Выравниваем количество игр по правому краю
                games_str = str(total_games)
                games_padded = games_str.rjust(max_games_width)
                
                # 1-я строка: номер этапа, название, места
                info_text += f"┌─ 📌 ЭТАП {idx}: {stage_display}{places_display}\n"
                # 2-я строка: тип таблицы, распределение, количество игр, время
                info_text += f"└─ 📊 {system.type_table} | {distribution_text} | {games_padded} игр | ⏱️ {stage_time}\n"
                
                # # Добавляем информацию о турах для групповых этапов
                # if "Круговая" in system.type_table and not self.is_final_stage(system.stage):
                #     if 'group_sizes' in locals():
                #         info_text += f"      🎯 Туров: {max_tours} | Столов в туре: {tables_per_tour}\n"
                
                previous_stage = system
            
            # Подсчет общего времени

            total_hours = total_time_minutes // 60
            total_minutes = total_time_minutes % 60
            if total_hours > 0:
                total_time_str = f"{total_hours} ч {total_minutes} мин"
            else:
                total_time_str = f"{total_minutes} мин"
            
            # Подчеркивание и сумма игр всех этапов
            info_text += "─" * 70 + "\n"
            info_text += f"🏆 ВСЕГО НА СОРЕВНОВАНИИ: {total_all_games} ИГР | ⏱️ ОБЩЕЕ ВРЕМЯ: {total_time_str}\n"
            
            self.stages_info.setText(info_text)
            
        except Exception as e:
            print(f"Ошибка обновления информации об этапах: {e}")
            import traceback
            traceback.print_exc()
            self.stages_info.setText(f"Ошибка: {str(e)}")
    # ===================================
    def calculate_group_sizes(self, players, groups):
        """Расчет количества участников в каждой группе"""
        if groups <= 0:
            return []
        
        if players == 0:
            return [0] * groups
        
        base = players // groups
        remainder = players % groups
        
        group_sizes = []
        for i in range(groups):
            if i < remainder:
                group_sizes.append(base + 1)
            else:
                group_sizes.append(base)
        
        return group_sizes
    # =============================
    def calculate_group_distribution(self, players, groups):
        """Расчет распределения участников по группам"""
        if groups <= 0:
            return "нет групп"
        
        if players == 0:
            return "нет участников"
        
        base = players // groups
        remainder = players % groups
        
        if remainder == 0:
            return f"{groups} гр по {base} чел."
        else:
            return f"{groups} гр ({remainder} гр по {base + 1} чел., {groups - remainder} гр по {base} чел.)"
#============
    def calculate_total_games(self, table_type, total_players, groups_count, group_sizes, stage_name=None, previous_stage=None):
        """Расчет общего количества игр с учетом типа этапа и уже сыгранных встреч"""
        if total_players == 0:
            return 0
        
        total_games = 0
        
        if "Круговая" in table_type:
            # Для финала (точно не полуфинал)
            if self.is_final_stage(stage_name) and previous_stage:
                # В финале играют участники из разных групп предыдущего этапа
                total_possible = (total_players * (total_players - 1)) // 2
                
                # Вычитаем игры, сыгранные внутри каждой группы предыдущего этапа
                already_played = 0
                # Количество участников из одной группы в финале
                players_per_previous_group = previous_stage.mesta_exit
                if players_per_previous_group > 1:
                    already_played = (players_per_previous_group * (players_per_previous_group - 1)) // 2 * previous_stage.total_group
                
                total_games = total_possible - already_played
            else:
                # Для остальных этапов (квалификация, полуфиналы)
                for group_size in group_sizes:
                    if group_size > 1:
                        total_games += (group_size * (group_size - 1)) // 2
        
        elif "Олимпийская" in table_type:
            for group_size in group_sizes:
                if group_size == 4:
                    total_games += 6
                elif group_size == 8:
                    total_games += 12
                elif group_size == 16:
                    total_games += 32
                elif group_size == 32:
                    total_games += 80
                else:
                    total_games += group_size - 1
        
        return total_games
  # ========================  
    def create_system_settings(self):
        """Создание новой системы проведения (вызывается из меню)"""
        # Переключаемся на вкладку Система
        self.tab_widget.setCurrentIndex(4)  # Индекс вкладки Система
        QMessageBox.information(self, "Создание системы", 
                            "Заполните параметры этапа и нажмите 'Добавить этап'")      

    def edit_system_settings(self):
        """Редактирование существующей системы проведения (вызывается из меню)"""
        # Переключаемся на вкладку Система
        self.tab_widget.setCurrentIndex(4)  # Индекс вкладки Система
        
        # Проверяем, есть ли добавленные этапы
        try:
            systems_count = System.select().where(System.title_id == self.current_title_id).count()
            if systems_count == 0:
                QMessageBox.information(self, "Редактирование системы", 
                                    "Нет добавленных этапов.\n"
                                    "Создайте новый этап с помощью кнопки 'Добавить этап'")
                return
            
            # Создаем диалог выбора этапа для редактирования
            dialog = QDialog(self)
            dialog.setWindowTitle("Выбор этапа для редактирования")
            dialog.setModal(True)
            dialog.setFixedSize(400, 200)
            
            layout = QVBoxLayout(dialog)
            layout.addWidget(QLabel("Выберите этап для редактирования:"))
            
            stage_combo = QComboBox()
            systems = System.select().where(System.title_id == self.current_title_id)
            for system in systems:
                stage_combo.addItem(f"{system.stage} (Групп: {system.total_group})", system.id)
            
            layout.addWidget(stage_combo)
            
            btn_layout = QHBoxLayout()
            ok_btn = QPushButton("Редактировать")
            ok_btn.clicked.connect(dialog.accept)
            cancel_btn = QPushButton("Отмена")
            cancel_btn.clicked.connect(dialog.reject)
            btn_layout.addWidget(ok_btn)
            btn_layout.addWidget(cancel_btn)
            layout.addLayout(btn_layout)
            
            if dialog.exec_() == QDialog.Accepted:
                system_id = stage_combo.currentData()
                self.edit_system_stage(system_id)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")
# =================================
    def edit_system_stage(self, system_id):
        """Редактирование выбранного этапа с очисткой связанных данных"""
        from models import System, Result, Game_list, Choice
        
        try:
            system = System.get_by_id(system_id)
            
            # Проверяем наличие связанных данных
            results_count = Result.select().where(Result.system_id == system_id).count()
            games_count = Game_list.select().where(Game_list.system_id == system_id).count()
            choices_count = Choice.select().where(Choice.title_id == self.current_title_id).count()
            
            total_count = results_count + games_count + choices_count
            
            if total_count > 0:
                message = f"Для этого этапа есть связанные данные:\n"
                if results_count > 0:
                    message += f"📊 Результаты: {results_count} записей\n"
                if games_count > 0:
                    message += f"🎮 Игры: {games_count} записей\n"
                if choices_count > 0:
                    message += f"🎯 Выборы: {choices_count} записей\n"
                message += f"\nПри изменении параметров этапа все эти данные будут удалены.\n\nПродолжить?"
                
                reply = QMessageBox.question(self, "Предупреждение", 
                                            message,
                                            QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    return
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Редактирование этапа: {system.stage}")
            dialog.setModal(True)
            dialog.setMinimumWidth(450)
            
            layout = QVBoxLayout(dialog)
            
            group = QGroupBox("Параметры этапа")
            group_layout = QFormLayout(group)
            group_layout.setSpacing(10)
            
            # Название этапа
            stage_edit = QComboBox()
            stage_edit.addItems([
                "Одна таблица",
                "Квалификация",
                "Квалификация. 1-й полуфинал",
                "Квалификация. 2-й полуфинал",
                "Финал",
                "Суперфинал"
            ])
            stage_edit.setEditable(True)
            stage_edit.setCurrentText(system.stage)
            group_layout.addRow("Название этапа:", stage_edit)
            
            # Тип таблицы
            table_type_edit = QComboBox()
            table_type_edit.addItems([
                "Круговая",
                "Олимпийская (минус 2)",
                "Олимпийская (с розыгрышем всех мест)",
                "Олимпийская (за 1-3 место)"
            ])
            if hasattr(system, 'type_table'):
                table_type_edit.setCurrentText(system.type_table)
            group_layout.addRow("Тип таблицы:", table_type_edit)
            
            # Количество групп
            groups_edit = QLineEdit()
            groups_edit.setText(str(system.total_group))
            group_layout.addRow("Количество групп:", groups_edit)
            
            # Максимум участников
            max_players_edit = QLineEdit()
            max_players_edit.setText(str(system.max_player) if system.max_player else "16")
            group_layout.addRow("Максимум участников:", max_players_edit)
            
            # Количество партий
            score_flag_edit = QComboBox()
            score_flag_edit.addItems(["3", "5", "7"])
            score_flag_edit.setCurrentText(str(system.score_flag) if system.score_flag else "5")
            group_layout.addRow("Количество партий:", score_flag_edit)
            
            # Количество проходящих
            stage_exit_edit = QLineEdit()
            stage_exit_edit.setText(str(system.mesta_exit) if system.mesta_exit else "0")
            group_layout.addRow("Проходят в след. этап:", stage_exit_edit)
            
            layout.addWidget(group)
            
            btn_layout = QHBoxLayout()
            save_btn = QPushButton("💾 Сохранить изменения")
            save_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
            cancel_btn = QPushButton("❌ Отмена")
            cancel_btn.setStyleSheet("background-color: #f44336; color: white; padding: 5px;")
            
            def save_changes():
                try:
                    # Удаляем связанные данные
                    if total_count > 0:
                        # Удаляем результаты
                        if results_count > 0:
                            deleted = Result.delete().where(Result.system_id == system_id).execute()
                            print(f"Удалено {deleted} записей результатов")
                        
                        # Удаляем игры
                        if games_count > 0:
                            deleted = Game_list.delete().where(Game_list.system_id == system_id).execute()
                            print(f"Удалено {deleted} записей игр")
                        
                        # Удаляем выборы
                        if choices_count > 0:
                            deleted = Choice.delete().where(Choice.title_id == self.current_title_id).execute()
                            print(f"Удалено {deleted} записей выборов")
                    
                    # Обновляем параметры этапа
                    system.stage = stage_edit.currentText()
                    if hasattr(system, 'type_table'):
                        system.type_table = table_type_edit.currentText()
                    system.total_group = int(groups_edit.text()) if groups_edit.text().isdigit() else 1
                    system.max_player = int(max_players_edit.text()) if max_players_edit.text().isdigit() else 16
                    system.score_flag = int(score_flag_edit.currentText())
                    system.mesta_exit = int(stage_exit_edit.text()) if stage_exit_edit.text().isdigit() else 0
                    system.save()
                    
                    # Сбрасываем флаг жеребьевки
                    system.choice_flag = 0
                    system.save()
                    
                    # Обновляем информационное окно
                    self.update_stages_info()
                    
                    QMessageBox.information(dialog, "Успех", "Изменения сохранены")
                    dialog.accept()
                    
                except Exception as e:
                    QMessageBox.critical(dialog, "Ошибка", f"Не удалось сохранить изменения: {str(e)}")
            
            save_btn.clicked.connect(save_changes)
            cancel_btn.clicked.connect(dialog.reject)
            
            btn_layout.addWidget(save_btn)
            btn_layout.addWidget(cancel_btn)
            layout.addLayout(btn_layout)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")
        
    def on_stage_changed(self, stage_name):
        """Обработка изменения этапа"""
        # Если этап "Финал" или "Суперфинал", отключаем поле "Группы"
        if stage_name in ["Финал", "Суперфинал"]:
            self.total_groups.setEnabled(False)
            self.total_groups.setText("1")
            self.total_groups.setStyleSheet("background-color: #f0f0f0; color: #999;")
        else:
            self.total_groups.setEnabled(True)
            self.total_groups.setStyleSheet("")

    def on_table_type_changed(self, table_type):
        """Обработка изменения типа таблицы"""
        # Если тип таблицы не "Круговая", то макс. участников может быть только 4, 8, 16, 32 или 64
        if table_type != "Круговая":
            self.max_players.setPlaceholderText("4, 8, 16, 32 или 64")
            # Проверяем текущее значение
            current_value = self.max_players.text()
            if current_value and current_value.isdigit():
                value = int(current_value)
                if value not in [4, 8, 16, 32, 64]:
                    self.max_players.setText("")
                    QMessageBox.warning(self, "Ошибка", 
                                    "Для олимпийской системы максимальное количество участников должно быть 4, 8, 16, 32 или 64")
        else:
            self.max_players.setPlaceholderText("чел.")
            self.max_players.setStyleSheet("")

    def on_max_players_changed(self, text):
        """Проверка вводимого значения макс. участников"""
        if self.table_type.currentText() != "Круговая":
            if text and text.isdigit():
                value = int(text)
                if value not in [4, 8, 16, 32, 64]:
                    # Показываем предупреждение, но не блокируем ввод
                    self.max_players.setStyleSheet("border: 1px solid red;")
                else:
                    self.max_players.setStyleSheet("")
            else:
                self.max_players.setStyleSheet("")

    def calculate_finals_info(self, total_players, max_players, table_type):
        """Расчет информации о финалах"""
        if table_type == "Круговая":
            # Для круговой системы финал один, если все игроки
            if total_players <= max_players:
                return {"count": 1, "has_number": False, "distribution": f"{total_players} игроков"}
            else:
                # Игроки разбиваются на группы
                groups = (total_players + max_players - 1) // max_players
                last_group_size = total_players % max_players
                if last_group_size == 0:
                    last_group_size = max_players
                
                distribution = f"{groups} финалов"
                if groups > 1:
                    distribution += f" (последний: {last_group_size} игр.)"
                return {"count": groups, "has_number": groups > 1, "distribution": distribution}
        
        else:  # Олимпийская система
            # Определяем размеры сеток
            valid_sizes = [4, 8, 16, 32, 64]
            remaining = total_players
            finals = []
            final_number = 1
            
            while remaining > 0:
                # Находим подходящий размер сетки
                grid_size = max([s for s in valid_sizes if s <= remaining], default=valid_sizes[0])
                if grid_size > remaining:
                    grid_size = valid_sizes[0]
                
                finals.append({
                    'number': final_number,
                    'size': grid_size,
                    'players': min(grid_size, remaining)
                })
                remaining -= grid_size
                final_number += 1
            
            if len(finals) == 1:
                return {"count": 1, "has_number": False, "distribution": f"{finals[0]['players']} игроков в сетке {finals[0]['size']}"}
            else:
                distribution = ", ".join([f"{f['number']}-й финал: {f['players']} игр." for f in finals])
                return {"count": len(finals), "has_number": True, "distribution": distribution}

    def calculate_empty_slots(self, total_players, max_players, table_type):
        """Расчет свободных мест в сетке"""
        if table_type == "Круговая":
            return 0
        
        valid_sizes = [4, 8, 16, 32, 64]
        remaining = total_players
        empty_slots = 0
        
        while remaining > 0:
            grid_size = max([s for s in valid_sizes if s <= remaining], default=valid_sizes[0])
            if grid_size > remaining:
                grid_size = valid_sizes[0]
            
            empty_slots += grid_size - min(grid_size, remaining)
            remaining -= grid_size
        
        return empty_slots
 #=================================================   
    def on_stage_selected(self, index):
        """Обработка выбора этапа для автоматического расчета"""
        stage_name = self.system_stage.currentText()
        
        previous_stages = System.select().where(
            System.title_id == self.current_title_id
        ).order_by(System.id)
        
        previous_stages_list = list(previous_stages)
        
        if not previous_stages_list:
            return
        
        last_stage = previous_stages_list[-1]
        
        # Логика для 1-го полуфинала после квалификации
        if "Квалификация" in last_stage.stage and "полуфинал" in stage_name.lower():
            # Количество групп полуфинала = количество групп квалификации / 2
            auto_groups = max(1, last_stage.total_group // 2)
            self.total_groups.setText(str(auto_groups))
            
            # Для полуфинала поле "Группы" делаем неактивным
            self.total_groups.setEnabled(False)
            self.total_groups.setStyleSheet("background-color: #f0f0f0; color: #999;")
            
            QMessageBox.information(self, "Автоматический расчет", 
                                f"На основе предыдущего этапа 'Квалификация' автоматически установлены:\n"
                                f"📦 Количество групп в полуфинале: {auto_groups}\n"
                                f"(Количество групп квалификации: {last_stage.total_group})")
        
        # Логика для 2-го полуфинала после 1-го полуфинала
        elif "1-й полуфинал" in last_stage.stage and "2-й полуфинал" in stage_name:
            # Количество групп 2-го полуфинала = количество групп 1-го полуфинала / 2
            auto_groups = max(1, last_stage.total_group // 2)
            self.total_groups.setText(str(auto_groups))
            
            # Для полуфинала поле "Группы" делаем неактивным
            self.total_groups.setEnabled(False)
            self.total_groups.setStyleSheet("background-color: #f0f0f0; color: #999;")
            
            QMessageBox.information(self, "Автоматический расчет", 
                                f"На основе предыдущего этапа '1-й полуфинал' автоматически установлены:\n"
                                f"📦 Количество групп во 2-м полуфинале: {auto_groups}\n"
                                f"(Количество групп в 1-м полуфинале: {last_stage.total_group})")
        
        # Логика для финала после полуфинала
        elif "полуфинал" in last_stage.stage and "Финал" in stage_name:
            # Для финала количество групп всегда 1
            self.total_groups.setText("1")
            self.total_groups.setEnabled(False)
            self.total_groups.setStyleSheet("background-color: #f0f0f0; color: #999;")
            
            # Количество участников финала = количество групп полуфинала * количество проходящих
            if last_stage.mesta_exit > 0:
                auto_players = last_stage.total_group * last_stage.mesta_exit
                QMessageBox.information(self, "Автоматический расчет", 
                                    f"На основе предыдущего этапа '{last_stage.stage}' автоматически установлены:\n"
                                    f"📦 Количество групп в финале: 1\n"
                                    f"👥 Количество участников финала: {auto_players} чел.\n"
                                    f"(Из {last_stage.total_group} групп выходит по {last_stage.mesta_exit} чел.)")
        
        # Логика для финала после квалификации (без полуфинала)
        elif "Квалификация" in last_stage.stage and "Финал" in stage_name:
            # Для финала количество групп всегда 1
            self.total_groups.setText("1")
            self.total_groups.setEnabled(False)
            self.total_groups.setStyleSheet("background-color: #f0f0f0; color: #999;")
            
            # Количество участников финала = количество групп квалификации * количество проходящих
            if last_stage.mesta_exit > 0:
                auto_players = last_stage.total_group * last_stage.mesta_exit
                QMessageBox.information(self, "Автоматический расчет", 
                                    f"На основе предыдущего этапа 'Квалификация' автоматически установлены:\n"
                                    f"📦 Количество групп в финале: 1\n"
                                    f"👥 Количество участников финала: {auto_players} чел.\n"
                                    f"(Из {last_stage.total_group} групп выходит по {last_stage.mesta_exit} чел.)")
 # ==================================                             
    def perform_drawing(self):
        """Проведение жеребьевки квалификации с выбором типа"""
        # Проверяем, есть ли этапы для жеребьевки
        stages = System.select().where(System.title_id == self.current_title_id)
        qualification = None
        
        for stage in stages:
            if "Квалификация" in stage.stage and "полуфинал" not in stage.stage:
                qualification = stage
                break
        
        if not qualification:
            QMessageBox.warning(self, "Ошибка", "Нет этапа квалификации для жеребьевки")
            return

        # Выбор типа жеребьевки
        drawing_type = self.get_drawing_type()
        if drawing_type is None:
            return  # Пользователь отменил
        
        if drawing_type == "auto":
            self.auto_drawing(qualification)
        else:
            self.hide()
            self.manual_drawing_for_stage(stage)
            self.show()

    def calculate_semifinal_games(self, groups_count, players_per_group, exit_count):
        """
        Расчет количества игр в полуфинале с учетом уже сыгранных встреч
        """
        if groups_count <= 0 or players_per_group <= 0 or exit_count <= 0:
            return 0, 0, 0
        
        # В полуфинале группы формируются путем слияния двух групп квалификации
        semifinal_groups = groups_count // 2
        
        # В каждой группе полуфинала будет 2 * exit_count игроков
        players_in_semifinal_group = exit_count * 2
        
        # Общее количество возможных игр в группе (если бы все встречались впервые)
        total_possible_games = (players_in_semifinal_group * (players_in_semifinal_group - 1)) // 2
        
        # Количество уже сыгранных игр:
        # В каждой группе квалификации сыграно (exit_count * (exit_count - 1)) // 2 игр между вышедшими
        # Таких групп в одной группе полуфинала - 2 (из двух групп квалификации)
        already_played = ((exit_count * (exit_count - 1)) // 2) * 2
        
        # Также нужно учесть, что игроки из одной группы квалификации уже играли между собой
        # Поэтому уникальных игр будет меньше
        unique_games = total_possible_games - already_played
        
        # Общее количество игр в полуфинале
        total_games = unique_games * semifinal_groups
        
        return total_games, unique_games, semifinal_groups
    
    def on_stage_type_changed(self, stage_name):
        """Обработка изменения типа этапа - показываем/скрываем поле количество групп"""
        print(f"Выбран этап: {stage_name}")  # Для отладки
        
        if "Квалификация" in stage_name and "полуфинал" not in stage_name:
            # Показываем поле для квалификации
            self.groups_widget.setVisible(True)
            self.total_groups.setEnabled(True)
            self.total_groups.setFocus()
            # print("Поле 'Количество групп' показано")
        else:
            # Скрываем поле для остальных этапов
            self.groups_widget.setVisible(False)
            self.total_groups.clear()
            self.total_groups.setEnabled(False)
            # print("Поле 'Количество групп' скрыто")

    def calculate_max_players_for_final(self, total_players):
        """Расчет максимального количества участников в одном финале"""
        # Стандартные размеры сеток для олимпийской системы
        valid_sizes = [4, 8, 16, 32, 64]
        
        # Находим ближайший подходящий размер
        for size in valid_sizes:
            if total_players <= size:
                return size
        
        # Если больше 64, берем 64
        return 64
    
    def calculate_olympic_games(self, players):
        """Расчет количества игр в олимпийской системе"""
        if players == 4:
            return 6
        elif players == 8:
            return 12
        elif players == 16:
            return 32
        elif players == 32:
            return 80
        else:
            return 192

    def calculate_finals_distribution(self, total_players, max_per_final):
        """Расчет распределения по финалам"""
        groups_list = ['Одна_таблица', 'Квалификация', 'Квалификация. 1-й полуфинал', 'Квалификация. 2-й полуфинал']
        final_list = []
        if max_per_final <= 0:
            return "ошибка"
        systems = System.select().where(System.title_id == self.current_title_id)
        for i in systems:
            stage = i.stage
            if stage not in groups_list:
                final_list.append(stage)
        finals_count = len(final_list)
 
        distribution = []
        remaining = total_players
        for i in range(finals_count):
            players = min(max_per_final, remaining)
            distribution.append(f"{i+1}-й финал: {players} чел.")
            remaining -= players
        
        return ", ".join(distribution)
        
    def calculate_semifinal_games_count(self, groups_count, players_per_group, previous_stage):
        """Расчет количества игр в полуфинале с учетом уже сыгранных"""
        # Всего возможных игр в группе (если все встречаются впервые)
        total_possible = (players_per_group * (players_per_group - 1)) // 2
        
        # Уже сыграно в квалификации между вышедшими участниками
        exit_count = previous_stage.mesta_exit
        already_played = (exit_count * (exit_count - 1)) // 2 * 2  # По 2 группы в одном полуфинале
        
        unique_games_per_group = total_possible - already_played
        total_games = unique_games_per_group * groups_count
        
        return total_games

    def delete_system_stage(self, system_id):
        """Удаление этапа с очисткой связанных данных"""
        from models import System, Result, Game_list, Choice
        
        try:
            system = System.get_by_id(system_id)
            
            # Проверяем наличие связанных данных
            results_count = Result.select().where(Result.system_id == system_id).count()
            games_count = Game_list.select().where(Game_list.system_id == system_id).count()
            choices_count = Choice.select().where(Choice.title_id == self.current_title_id).count()
            
            total_count = results_count + games_count + choices_count
            
            message = f"Удалить этап '{system.stage}'?"
            if total_count > 0:
                message += f"\n\nВнимание! Вместе с этапом будут удалены:\n"
                if results_count > 0:
                    message += f"📊 Результаты: {results_count} записей\n"
                if games_count > 0:
                    message += f"🎮 Игры: {games_count} записей\n"
                if choices_count > 0:
                    message += f"🎯 Выборы: {choices_count} записей\n"
            
            reply = QMessageBox.question(self, "Подтверждение", 
                                        message,
                                        QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # Удаляем связанные данные
                if results_count > 0:
                    deleted = Result.delete().where(Result.system_id == system_id).execute()
                    print(f"Удалено {deleted} записей результатов")
                
                if games_count > 0:
                    deleted = Game_list.delete().where(Game_list.system_id == system_id).execute()
                    print(f"Удалено {deleted} записей игр")
                
                if choices_count > 0:
                    deleted = Choice.delete().where(Choice.title_id == self.current_title_id).execute()
                    print(f"Удалено {deleted} записей выборов")
                
                # Удаляем этап
                system.delete_instance()
                self.update_stages_info()
                QMessageBox.information(self, "Успех", f"Этап '{system.stage}' удален")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка удаления: {str(e)}")

    def clear_stage_results(self, stage_name):
        """Очистка результатов для этапа с указанным именем"""
        from models import System, Result
        
        try:
            # Находим этап по имени
            system = System.get_or_none(
                (System.title_id == self.current_title_id) &
                (System.stage == stage_name)
            )
            
            if system:
                results_count = Result.select().where(Result.system_id == system.id).count()
                if results_count > 0:
                    reply = QMessageBox.question(self, "Предупреждение", 
                                                f"Для этапа '{stage_name}' уже есть результаты ({results_count} записей).\n"
                                                f"При замене этапа все результаты будут удалены.\n\n"
                                                f"Продолжить?",
                                                QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        Result.delete().where(Result.system_id == system.id).execute()
                        print(f"Удалены результаты для этапа {stage_name}")
                        return True
                    else:
                        return False
            return True
            
        except Exception as e:
            print(f"Ошибка при проверке результатов: {e}")
            return True

    def get_final_number(self, stage_name):
        """Извлечение номера финала из названия"""
        import re
        match = re.search(r'(\d+)', stage_name)
        if match:
            return int(match.group(1))
        return 1
    
    def is_final_stage(self, stage_name):
        """Проверка, является ли этап финалом (точно не полуфиналом)"""
        if not stage_name:
            return False
        # Если передан объект поля, получаем его значение
        if hasattr(stage_name, 'lower'):
            stage_str = stage_name
        else:
            stage_str = str(stage_name)
        
        stage_lower = stage_str.lower()
        return "финал" in stage_lower and "полуфинал" not in stage_lower and "квалификация" not in stage_lower

    def get_total_games_count(self):
        """Подсчет общего количества игр на соревновании"""
        try:
            total_games = 0
            systems = System.select().where(System.title_id == self.current_title_id)
            for system in systems:
                if system.kol_game_string:
                    import re
                    numbers = re.findall(r'(\d+)', system.kol_game_string)
                    for num in numbers:
                        total_games += int(num)
            return total_games
        except Exception as e:
            print(f"Ошибка подсчета игр: {e}")
            return 0

    def get_next_final_number(self):
        """Получение следующего номера финала"""
        try:
            from models import System
            existing_finals = System.select().where(
                (System.title_id == self.current_title_id) &
                (System.stage.contains("финал")) &
                (~System.stage.contains("полуфинал"))
            ).count()
            return existing_finals + 1
        except Exception as e:
            print(f"Ошибка получения номера финала: {e}")
            return 1
        
    def get_players_distribution_info(self):
        """Получение информации о распределении игроков по этапам"""
        from models import System
        
        systems = System.select().where(System.title_id == self.current_title_id).order_by(System.id)
        
        if len(systems) == 0:
            return
        
        distribution = {
            'qualification': {'total_groups': 0, 'players_per_group': 0, 'exited_per_group': 0, 'exited_total': 0, 'remaining_total': 0},
            'semifinal_1': {'total_groups': 0, 'players_per_group': 0, 'exited_per_group': 0, 'exited_total': 0, 'remaining_total': 0},
            'semifinal_2': {'total_groups': 0, 'players_per_group': 0, 'exited_per_group': 0, 'exited_total': 0, 'remaining_total': 0},
            'finals': []
        }
        
        previous_stage = None
        
        for system in systems:
            # Квалификация
            if "Квалификация" in system.stage and "полуфинал" not in system.stage:
                distribution['qualification']['total_groups'] = system.total_group
                distribution['qualification']['players_per_group'] = system.max_player
                distribution['qualification']['exited_per_group'] = system.mesta_exit
                # Фикс: оставшиеся в квалификации
                distribution['qualification']['remaining_total'] = (system.max_player) - distribution['qualification']['exited_per_group']
            
            # 1-й полуфинал
            elif "1-й полуфинал" in system.stage or ("полуфинал" in system.stage and previous_stage and "Квалификация" in previous_stage.stage):
                distribution['semifinal_1']['total_groups'] = system.total_group
                distribution['semifinal_1']['players_per_group'] = system.max_player
                distribution['semifinal_1']['exited_per_group'] = system.mesta_exit
                # Оставшиеся в полуфинале игроки (не вышедшие в финал)
                distribution['semifinal_1']['remaining_total'] = (system.max_player) - distribution['semifinal_1']['exited_per_group']
            
            # 2-й полуфинал
            elif "2-й полуфинал" in system.stage:
                distribution['semifinal_2']['total_groups'] = system.total_group
                distribution['semifinal_2']['players_per_group'] = system.max_player
                distribution['semifinal_2']['exited_per_group'] = system.mesta_exit
                distribution['semifinal_2']['remaining_total'] = (system.max_player) - distribution['semifinal_2']['exited_per_group']
            
            # Финал
            elif self.is_final_stage(system.stage):
                distribution['finals'].append({
                    'number': len(distribution['finals']) + 1,
                    'players': system.max_player,
                    'stage_name': system.stage
                })
            
            previous_stage = system
        
        return distribution
    
    def check_players_status(self):
        """Проверка статуса всех игроков перед созданием системы"""
        if not self.current_title_id:
            return False
        
        # Получаем всех игроков с неосновным статусом
        pending_players = Player.select().where(
            (Player.title_id == self.current_title_id) &
            (Player.application != "основная")
        )
        
        if pending_players.count() > 0:
            # Создаем диалог со списком неподтвержденных игроков
            dialog = QDialog(self)
            dialog.setWindowTitle("Неподтвержденные участники")
            dialog.setModal(True)
            dialog.setMinimumWidth(700)
            dialog.setMinimumHeight(500)
            
            layout = QVBoxLayout(dialog)
            
            info_label = QLabel("Следующие участники имеют статус 'предварительная' или другой:")
            info_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            layout.addWidget(info_label)
            
            layout.addSpacing(10)
            
            # Список неподтвержденных игроков с возможностью множественного выделения
            players_list = QListWidget()
            players_list.setSelectionMode(QListWidget.ExtendedSelection)  # Множественное выделение
            players_list.setStyleSheet("""
                QListWidget {
                    font-size: 11px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
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
            
            # Сохраняем ID игроков для быстрого доступа
            player_ids = []
            for player in pending_players:
                player_ids.append(player.id)
                item_text = f"🏅 {player.fio} | {player.city} | {player.razryad}"
                if player.coach_id:
                    coach = Coach.get_or_none(Coach.id == player.coach_id)
                    if coach:
                        item_text += f" | Тренер: {coach.coach}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, player.id)
                players_list.addItem(item)
            
            layout.addWidget(players_list)
            
            layout.addSpacing(10)
            
            # Кнопки управления
            buttons_layout = QHBoxLayout()
            buttons_layout.setSpacing(10)
            
            # Кнопка подтверждения выделенных
            confirm_selected_btn = QPushButton("✅ Подтвердить выделенных")
            confirm_selected_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 8px;
                    font-size: 11px;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            confirm_selected_btn.clicked.connect(lambda: self.confirm_selected_players(players_list, dialog))
            buttons_layout.addWidget(confirm_selected_btn)
            
            # Кнопка удаления выделенных
            delete_selected_btn = QPushButton("🗑️ Удалить выделенных")
            delete_selected_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    padding: 8px;
                    font-size: 11px;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            delete_selected_btn.clicked.connect(lambda: self.delete_selected_players(players_list, dialog))
            buttons_layout.addWidget(delete_selected_btn)
            
            # Кнопка подтверждения всех
            confirm_all_btn = QPushButton("✅ Подтвердить всех")
            confirm_all_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    padding: 8px;
                    font-size: 11px;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            confirm_all_btn.clicked.connect(lambda: self.confirm_all_players(dialog))
            buttons_layout.addWidget(confirm_all_btn)
            
            # Кнопка удаления всех неподтвержденных
            delete_all_btn = QPushButton("🗑️ Удалить всех")
            delete_all_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    padding: 8px;
                    font-size: 11px;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
            delete_all_btn.clicked.connect(lambda: self.delete_all_pending_players(dialog))
            buttons_layout.addWidget(delete_all_btn)
            
            layout.addLayout(buttons_layout)
            
            layout.addSpacing(5)
            
            # Кнопка закрытия
            close_btn = QPushButton("Закрыть")
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #9E9E9E;
                    color: white;
                    padding: 8px;
                    font-size: 11px;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #757575;
                }
            """)
            close_btn.clicked.connect(dialog.reject)
            layout.addWidget(close_btn)
            
            dialog.exec_()
            return False
        
        return True

    def confirm_selected_players(self, players_list, dialog):
        """Подтверждение выделенных игроков"""
        selected_items = players_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(dialog, "Ошибка", "Выберите игроков для подтверждения")
            return
        
        selected_ids = [item.data(Qt.UserRole) for item in selected_items]
        
        reply = QMessageBox.question(dialog, "Подтверждение", 
                                    f"Подтвердить заявки {len(selected_ids)} участников?\n"
                                    f"Статус изменится с 'предварительная' на 'основная'.",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                # Обновляем статус выбранных игроков
                for player_id in selected_ids:
                    Player.update(application="основная").where(Player.id == player_id).execute()
                
                # Обновляем список
                self.refresh_pending_players_list(players_list)
                
                # Проверяем, остались ли еще неподтвержденные
                remaining = Player.select().where(
                    (Player.title_id == self.current_title_id) &
                    (Player.application != "основная")
                ).count()
                
                if remaining == 0:
                    QMessageBox.information(dialog, "Успех", "Все участники подтверждены!")
                    dialog.accept()
                else:
                    QMessageBox.information(dialog, "Успех", f"Подтверждено {len(selected_ids)} участников")
                    
            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось подтвердить участников: {str(e)}")

    def delete_selected_players(self, players_list, dialog):
        """Удаление выделенных игроков"""
        selected_items = players_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(dialog, "Ошибка", "Выберите игроков для удаления")
            return
        
        selected_ids = [item.data(Qt.UserRole) for item in selected_items]
        
        # Получаем ФИО для отображения
        fios = []
        for player_id in selected_ids:
            player = Player.get_or_none(Player.id == player_id)
            if player:
                fios.append(player.fio)
        
        reply = QMessageBox.question(dialog, "Подтверждение", 
                                    f"Удалить {len(selected_ids)} участников?\n\n"
                                    f"{chr(10).join(fios[:5])}{chr(10) if len(fios) > 5 else ''}"
                                    f"{f'... и еще {len(fios) - 5}' if len(fios) > 5 else ''}\n\n"
                                    f"Игроки будут перемещены в архив удаленных.",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                for player_id in selected_ids:
                    player = Player.get_by_id(player_id)
                    
                    # Создаем запись в таблице Delete_player
                    Delete_player.create(
                        player=player.player,
                        bday=player.bday,
                        rank=player.rank,
                        city=player.city,
                        region=player.region,
                        razryad=player.razryad,
                        coach_id=player.coach_id,
                        full_name=player.fio,
                        title_id=self.current_title_id,
                        pay_rejting=player.pay_rejting or "",
                        comment=player.comment or "",
                        patronymic_id=player.patronymic_id.id if player.patronymic_id else None,
                        sex=player.sex
                    )
                    
                    # Удаляем игрока из таблицы Player
                    player.delete_instance()
                
                # Обновляем список
                self.refresh_pending_players_list(players_list)
                
                # Проверяем, остались ли еще неподтвержденные
                remaining = Player.select().where(
                    (Player.title_id == self.current_title_id) &
                    (Player.application != "основная")
                ).count()
                
                if remaining == 0:
                    QMessageBox.information(dialog, "Успех", "Все участники обработаны!")
                    dialog.accept()
                else:
                    QMessageBox.information(dialog, "Успех", f"Удалено {len(selected_ids)} участников")
                    
            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось удалить участников: {str(e)}")

    def confirm_all_players(self, dialog):
        """Подтверждение всех неподтвержденных игроков"""
        reply = QMessageBox.question(dialog, "Подтверждение", 
                                    "Подтвердить заявки ВСЕХ участников?\n"
                                    "Статус изменится с 'предварительная' на 'основная'.",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                # Обновляем статус всех игроков
                Player.update(application="основная").where(
                    (Player.title_id == self.current_title_id) &
                    (Player.application != "основная")
                ).execute()
                
                QMessageBox.information(dialog, "Успех", "Все участники подтверждены")
                dialog.accept()
                
            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось подтвердить участников: {str(e)}")

    def delete_all_pending_players(self, dialog):
        """Удаление всех неподтвержденных игроков"""
        pending_count = Player.select().where(
            (Player.title_id == self.current_title_id) &
            (Player.application != "основная")
        ).count()
        
        reply = QMessageBox.question(dialog, "Подтверждение", 
                                    f"Удалить ВСЕХ неподтвержденных участников ({pending_count} чел.)?\n\n"
                                    f"Игроки будут перемещены в архив удаленных.",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                pending_players = Player.select().where(
                    (Player.title_id == self.current_title_id) &
                    (Player.application != "основная")
                )
                
                for player in pending_players:
                    # Создаем запись в таблице Delete_player
                    Delete_player.create(
                        player=player.player,
                        bday=player.bday,
                        rank=player.rank,
                        city=player.city,
                        region=player.region,
                        razryad=player.razryad,
                        coach_id=player.coach_id,
                        full_name=player.fio,
                        title_id=self.current_title_id,
                        pay_rejting=player.pay_rejting or "",
                        comment=player.comment or "",
                        patronymic_id=player.patronymic_id.id if player.patronymic_id else None,
                        sex=player.sex
                    )
                    
                    # Удаляем игрока из таблицы Player
                    player.delete_instance()
                
                QMessageBox.information(dialog, "Успех", f"Удалено {pending_count} участников")
                dialog.accept()
                
            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось удалить участников: {str(e)}")

    def refresh_pending_players_list(self, players_list):
        """Обновление списка неподтвержденных игроков"""
        players_list.clear()
        
        pending_players = Player.select().where(
            (Player.title_id == self.current_title_id) &
            (Player.application != "основная")
        )
        
        for player in pending_players:
            item_text = f"🏅 {player.fio} | {player.city} | {player.razryad}"
            if player.coach_id:
                coach = Coach.get_or_none(Coach.id == player.coach_id)
                if coach:
                    item_text += f" | Тренер: {coach.coach}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, player.id)
            players_list.addItem(item)

    def update_seeding_info(self):
        """Обновление информации о посеянных игроках"""
        group_list = ["Квалификация", "Квалификация. 1-й полуфинал", "Квалификация. 2-й полуфинал"]
        if not self.current_title_id:
            return
        
        total_players = Player.select().where(Player.title_id == self.current_title_id).count()
        
        # Получаем количество игроков уже распределенных по финалам
        systems = System.select().where(System.title_id == self.current_title_id)
        
        seeded_players = 0
        for system in systems:
            if system.stage not in group_list and "финал" in system.stage.lower():
                seeded_players += system.max_player
        
        remaining_players = total_players - seeded_players
        
        # Показываем информацию в левой панели
        if hasattr(self, 'seeding_info_label') and self.seeding_info_label is not None:
            self.seeding_info_label.setText(f"🎯 Посев игроков: {seeded_players} из {total_players} ({remaining_players} осталось)")
            if remaining_players == 0:
                self.seeding_info_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.seeding_info_label.setStyleSheet("color: brown; font-weight: bold;")
        return seeded_players
    
    def show_distribution_info(self):
        """Отображение подробной информации о распределении игроков"""
        distribution = self.get_players_distribution_info()
        
        info_text = "📊 РАСПРЕДЕЛЕНИЕ ИГРОКОВ:\n"
        info_text += "=" * 40 + "\n\n"
        
        if distribution['qualification']['total_groups'] > 0:
            info_text += f"🏆 Квалификация:\n"
            info_text += f"   • Групп: {distribution['qualification']['total_groups']}\n"
            info_text += f"   • Игроков в группе: {distribution['qualification']['players_per_group']}\n"
            info_text += f"   • Вышло в полуфинал из группы: {distribution['qualification']['exited_per_group']}\n"
            info_text += f"   • Всего вышло: {distribution['qualification']['exited_total']}\n"
            info_text += f"   • Осталось в квалификации: {distribution['qualification']['remaining_total']}\n\n"
        
        if distribution['semifinal_1']['total_groups'] > 0:
            info_text += f"🏆 1-й полуфинал:\n"
            info_text += f"   • Групп: {distribution['semifinal_1']['total_groups']}\n"
            info_text += f"   • Игроков в группе: {distribution['semifinal_1']['players_per_group']}\n"
            info_text += f"   • Вышло в финал из группы: {distribution['semifinal_1']['exited_per_group']}\n"
            info_text += f"   • Всего вышло: {distribution['semifinal_1']['exited_total']}\n"
            info_text += f"   • Осталось в полуфинале: {distribution['semifinal_1']['remaining_total']}\n\n"
        
        if distribution['semifinal_2']['total_groups'] > 0:
            info_text += f"🏆 2-й полуфинал:\n"
            info_text += f"   • Групп: {distribution['semifinal_2']['total_groups']}\n"
            info_text += f"   • Игроков в группе: {distribution['semifinal_2']['players_per_group']}\n"
            info_text += f"   • Вышло в финал из группы: {distribution['semifinal_2']['exited_per_group']}\n"
            info_text += f"   • Всего вышло: {distribution['semifinal_2']['exited_total']}\n"
            info_text += f"   • Осталось в полуфинале: {distribution['semifinal_2']['remaining_total']}\n\n"
        
        if distribution['finals']:
            info_text += f"🏆 Финалы:\n"
            for final in distribution['finals']:
                info_text += f"   • {final['stage_name']}: {final['players']} игроков\n"
        
        QMessageBox.information(self, "Информация о распределении", info_text)

    def fill_choice_table(self):
        """Заполнение таблицы Choice игроками соревнования"""
        if not self.current_title_id:
            return
      
        try:
            # Проверяем, есть ли уже записи в Choice для этого соревнования
            existing_choices = Choice.select().where(Choice.title_id == self.current_title_id).count()
            
            if existing_choices > 0:
                reply = QMessageBox.question(self, "Подтверждение", 
                                            f"Таблица Choice уже содержит {existing_choices} записей.\n"
                                            f"Перезаписать?",
                                            QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    return
                # Удаляем существующие записи
                Choice.delete().where(Choice.title_id == self.current_title_id).execute()
            else:
                
                # Получаем всех игроков соревнования
                players = Player.select().where(Player.title_id == self.current_title_id)
                
                # Получаем систему для определения групп
                systems = System.select().where(System.title_id == self.current_title_id).order_by(System.id)
                
                # Находим квалификацию
                qualification = None
                for system in systems:
                    if "Квалификация" in system.stage and "полуфинал" not in system.stage:
                        qualification = system
                        break
                
                if not qualification:
                    QMessageBox.warning(self, "Ошибка", "Не найдена квалификация для заполнения Choice")
                    return
                
                # Распределяем игроков по группам
                total_players = players.count()
                groups = qualification.total_group
                players_per_group = total_players // groups
                remainder = total_players % groups
                
                # Сортируем игроков по рейтингу для посева
                players_sorted = players.order_by(Player.rank.desc())
                
                group_counter = 1
                player_index = 0
                players_list = list(players_sorted)
                
                for i in range(groups):
                    # Определяем размер группы
                    current_group_size = players_per_group + (1 if i < remainder else 0)
                    
                    for j in range(current_group_size):
                        if player_index < len(players_list):
                            player = players_list[player_index]
                            
                            # Получаем тренера
                            coach_name = ""
                            if player.coach_id:
                                coach = Coach.get_or_none(Coach.id == player.coach_id)
                                if coach:
                                    coach_name = coach.coach
                            
                            # Получаем регион
                            region_name = player.region if player.region else ""
                            
                            # Создаем запись в Choice
                            Choice.create(
                                player_choice=player.id,
                                family=player.fio or player.player,
                                region=region_name,
                                coach=coach_name,
                                rank=player.rank or 0,
                                basic=None,
                                group=None,
                                posev_group=None,
                                mesto_group=0,
                                title_id=self.current_title_id,
                                sex=player.sex
                            )
                            player_index += 1
                    
                    group_counter += 1
                
                QMessageBox.information(self, "Успех", 
                                    f"Таблица Choice заполнена.\n"
                                    f"Всего игроков: {player_index}\n"
                                    f"Количество групп: {groups}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось заполнить Choice: {str(e)}")

    def calculate_stage_time(self, total_games, tables, match_time):
        """Расчет времени этапа в минутах"""
        if total_games == 0 or tables == 0:
            return 0
        import math
        return math.ceil(total_games / tables) * match_time

    def format_time(self, minutes):
        """Форматирование времени в часы и минуты"""
        if minutes < 60:
            return f"{minutes} мин"
        else:
            hours = minutes // 60
            mins = minutes % 60
            if mins == 0:
                return f"{hours} ч"
            else:
                return f"{hours} ч {mins} мин"

    def get_system_parameters(self):
        """Запрос параметров системы (количество столов, время на матч)"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Параметры системы")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Заголовок
        title_label = QLabel("Настройка параметров проведения соревнования")
        title_label.setStyleSheet("font-weight: bold; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Количество столов
        tables_layout = QHBoxLayout()
        tables_layout.addWidget(QLabel("Количество столов:"))
        tables_spin = QSpinBox()
        tables_spin.setMinimum(1)
        tables_spin.setMaximum(50)
        tables_spin.setValue(4)
        tables_spin.setMinimumWidth(100)
        tables_layout.addWidget(tables_spin)
        tables_layout.addStretch()
        layout.addLayout(tables_layout)
        
        # Время на матч
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Время на один матч (минут):"))
        time_spin = QSpinBox()
        time_spin.setMinimum(1)
        time_spin.setMaximum(180)
        time_spin.setValue(15)
        time_spin.setMinimumWidth(100)
        time_layout.addWidget(time_spin)
        time_layout.addWidget(QLabel("мин."))
        time_layout.addStretch()
        layout.addLayout(time_layout)
        
        # Дополнительная информация
        info_label = QLabel("Время будет рассчитано автоматически для каждого этапа")
        info_label.setStyleSheet("color: gray; font-size: 10px; margin-top: 10px;")
        layout.addWidget(info_label)
        
        layout.addSpacing(10)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet("background-color: #f44336; color: white; padding: 5px;")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            return tables_spin.value(), time_spin.value()
        else:
            return None, None

    def change_system_parameters(self):
        """Изменение параметров системы (столы, время)"""
        # Сохраняем текущие значения для восстановления при отмене
        old_tables = getattr(self, 'system_tables', 4)
        old_time = getattr(self, 'match_time', 15)
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Параметры системы")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Заголовок
        title_label = QLabel("Настройка параметров проведения соревнования")
        title_label.setStyleSheet("font-weight: bold; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Количество столов
        tables_layout = QHBoxLayout()
        tables_layout.addWidget(QLabel("Количество столов:"))
        tables_spin = QSpinBox()
        tables_spin.setMinimum(1)
        tables_spin.setMaximum(50)
        tables_spin.setValue(old_tables)
        tables_spin.setMinimumWidth(100)
        tables_layout.addWidget(tables_spin)
        tables_layout.addStretch()
        layout.addLayout(tables_layout)
        
        # Время на матч
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Время на один матч (минут):"))
        time_spin = QSpinBox()
        time_spin.setMinimum(1)
        time_spin.setMaximum(180)
        time_spin.setValue(old_time)
        time_spin.setMinimumWidth(100)
        time_layout.addWidget(time_spin)
        time_layout.addWidget(QLabel("мин."))
        time_layout.addStretch()
        layout.addLayout(time_layout)
        
        # Дополнительная информация
        info_label = QLabel("Время будет рассчитано автоматически для каждого этапа")
        info_label.setStyleSheet("color: gray; font-size: 10px; margin-top: 10px;")
        layout.addWidget(info_label)
        
        layout.addSpacing(10)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet("background-color: #f44336; color: white; padding: 5px;")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            self.system_tables = tables_spin.value()
            self.match_time = time_spin.value()
            # Обновляем информацию в окне
            self.update_stages_info()
            QMessageBox.information(self, "Успех", 
                                f"Параметры обновлены:\n"
                                f"🏓 Столов: {self.system_tables}\n"
                                f"⏱️ Время на матч: {self.match_time} мин.")
        
    def calculate_tables_per_tour(self, group_sizes):
        """Расчет количества столов, необходимых для одного тура"""
        total_tables = 0
        for size in group_sizes:
            if size >= 2:
                # В группе с n игроками в туре играет n // 2 пар
                total_tables += size // 2
        return total_tables

    def calculate_max_tours_in_stage(self, group_sizes):
        """Расчет максимального количества туров в этапе (по самой большой группе)"""
        if not group_sizes:
            return 0
        max_players = max(group_sizes)
        return self.calculate_tours_in_group(max_players)

    def calculate_tours_in_group(self, players_count):
        """Расчет количества туров в группе в зависимости от количества игроков"""
        if players_count <= 1:
            return 0
        elif players_count == 2:
            return 1
        elif players_count == 3:
            return 3  # 3 тура: 1-3, 1-2, 2-3
        elif players_count == 4:
            return 3  # 3 тура: (1-3,2-4), (1-4,2-3), (1-2,3-4)
        elif players_count == 5:
            return 5
        elif players_count == 6:
            return 5
        elif players_count == 7:
            return 7
        elif players_count == 8:
            return 7
        else:
            # Для большего количества игроков: количество туров = players_count - 1 (для нечетного)
            # или players_count - 1 (для четного)
            return players_count - 1 if players_count % 2 == 0 else players_count

    def get_drawing_type(self):
        """Запрос типа жеребьевки (ручная или автоматическая)"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Выбор типа жеребьевки")
        dialog.setModal(True)
        dialog.setFixedSize(400, 200)
        
        layout = QVBoxLayout(dialog)
        
        # Заголовок
        title_label = QLabel("Выберите способ проведения жеребьевки")
        title_label.setStyleSheet("font-weight: bold; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        layout.addSpacing(10)
        
        # Кнопки выбора
        auto_btn = QPushButton("🎲 Автоматическая жеребьевка")
        auto_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 12px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        manual_btn = QPushButton("✏️ Ручная жеребьевка")
        manual_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 12px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        auto_btn.clicked.connect(lambda: self.set_drawing_type_and_accept(dialog, "auto"))
        manual_btn.clicked.connect(lambda: self.set_drawing_type_and_accept(dialog, "manual"))
        
        layout.addWidget(auto_btn)
        layout.addWidget(manual_btn)
        
        # Сохраняем результат
        self.drawing_type = None
        
        if dialog.exec_() == QDialog.Accepted:
            return self.drawing_type
        return None

    def set_drawing_type_and_accept(self, dialog, drawing_type):
        """Установка типа жеребьевки и закрытие диалога"""
        self.drawing_type = drawing_type
        dialog.accept()

    def update_finals_menu(self, finals_menu):
        """Обновление меню финалов (динамически)"""
        # Очищаем меню
        finals_menu.clear()
        
        if not self.current_title_id:
            # Если нет выбранного соревнования, добавляем заглушку
            no_finals_action = QAction("Нет доступных финалов", self)
            no_finals_action.setEnabled(False)
            finals_menu.addAction(no_finals_action)
            return
        
        # Получаем все финалы для текущего соревнования
        finals = System.select().where(
            (System.title_id == self.current_title_id) &
            (System.stage.contains("финал")) &
            (~System.stage.contains("полуфинал"))
        ).order_by(System.id)
        
        if finals.count() == 0:
            no_finals_action = QAction("Нет доступных финалов", self)
            no_finals_action.setEnabled(False)
            finals_menu.addAction(no_finals_action)
        else:
            for final in finals:
                final_action = QAction(final.stage, self)
                final_action.triggered.connect(lambda checked, f=final: self.run_drawing_for_final(f))
                finals_menu.addAction(final_action)

    def run_drawing_for_stage(self, stage_name):
        """Запуск жеребьевки для указанного этапа"""
        if not self.current_title_id:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите соревнование")
            return
        
        # Находим этап в системе
        stage = System.get_or_none(
            (System.title_id == self.current_title_id) &
            (System.stage == stage_name)
        )
        
        if not stage:
            QMessageBox.warning(self, "Ошибка", f"Этап '{stage_name}' не найден в системе")
            return
        
        # Проверяем, есть ли уже жеребьевка для этого этапа
        if stage.choice_flag == 1:
            reply = QMessageBox.question(self, "Подтверждение", 
                                        f"Для этапа '{stage_name}' уже проведена жеребьевка.\n"
                                        f"Провести заново?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        # Запускаем жеребьевку
        self.drawing_for_stage(stage)

    def run_drawing_for_final(self, final):
        """Запуск жеребьевки для финала"""
        if not self.current_title_id:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите соревнование")
            return
        
        # Проверяем, есть ли уже жеребьевка для этого финала
        if final.choice_flag == 1:
            reply = QMessageBox.question(self, "Подтверждение", 
                                        f"Для этапа '{final.stage}' уже проведена жеребьевка.\n"
                                        f"Провести заново?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        # Запускаем жеребьевку для финала
        self.drawing_for_stage(final)

    def drawing_for_stage(self, stage):
        """Проведение жеребьевки для конкретного этапа"""
        # Выбор типа жеребьевки
        drawing_type = self.get_drawing_type()
        if drawing_type is None:
            return
        
        if drawing_type == "auto":
            self.auto_drawing_for_stage(stage)
        else:
            self.manual_drawing_for_stage(stage)

    def auto_drawing_for_stage(self, stage):
        """Автоматическая жеребьевка для указанного этапа"""
        try:
            # Заполняем таблицу Choice для этого этапа
            self.fill_choice_table_for_stage(stage)
            
            # Обновляем статус системы
            stage.choice_flag = 1
            stage.save()
            
            # Заполняем таблицу Result после жеребьевки
            self.fill_results_after_drawing()
            
            QMessageBox.information(self, "Автоматическая жеребьевка", 
                                f"✅ Жеребьевка для этапа '{stage.stage}' успешно проведена!\n\n"
                                f"📊 Параметры жеребьевки:\n"
                                f"   • Количество групп: {stage.total_group}\n"
                                f"   • Участников в группе: {stage.max_player}\n\n"
                                f"Таблицы Choice и Result обновлены.")
            
            # Обновляем отображение информации
            self.update_stages_info()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при автоматической жеребьевке: {str(e)}")

    def manual_drawing_for_stage(self, stage):
        """Ручная жеребьевка для указанного этапа"""
        from models import Player, Coach
        athletes = []

        # Создаем диалог для ручной жеребьевки
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Ручная жеребьевка - {stage.stage}")
        dialog.setModal(True)
        dialog.setMinimumWidth(800)
        dialog.setMinimumHeight(600)
        
        layout = QVBoxLayout(dialog)
        
        # Заголовок
        title_label = QLabel(f"Ручная жеребьевка - {stage.stage}")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Информация о группах
        info_label = QLabel(f"Количество групп: {stage.total_group} | "
                        f"Участников в группе: {stage.max_player}")
        info_label.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # =======================
        # Получаем список игроков
        players = Player.select().where(Player.title_id == self.current_title_id).order_by(Player.rank.desc())
        players_list = list(players)
        for pl in players_list:
            id = pl.id
            player = pl.fio
            rank = pl.rank
            region = pl.region
            coaches = Coach.get(Coach.id == pl.coach_id)
            coach = coaches.coach
            gamer = [id, player, rank, region, coach]
            athletes.append(gamer)
        
        num_groups = stage.total_group
        id_title = self.current_title_id
        #========================
        num_id_player = manual_choice.choice_group_manual(self, athletes, num_groups, id_title, parent=None)

        self.save_manual_drawing_for_stage(num_id_player, stage)

    def fill_choice_table_for_stage(self, stage):
        """Заполнение таблицы Choice для конкретного этапа"""
        try:
            # Удаляем существующие записи Choice для этого соревнования (если нужно заново)
            Choice.delete().where(Choice.title_id == self.current_title_id).execute()
            
            # Получаем всех игроков соревнования
            players = Player.select().where(Player.title_id == self.current_title_id)
            
            # Распределяем игроков змейкой
            total_players = players.count()
            groups = stage.total_group
            
            # Сортируем игроков по рейтингу
            players_sorted = players.order_by(Player.rank.desc())
            players_list = list(players_sorted)
            
            # Распределение змейкой
            assignments = []
            for i in range(total_players):
                group_num = i % groups
                if (i // groups) % 2 == 1:
                    group_num = groups - 1 - group_num
                assignments.append(group_num + 1)
            
            # Создаем записи в Choice
            for i, player in enumerate(players_list):
                group_num = assignments[i]
                
                # Получаем тренера
                coach_name = ""
                if player.coach_id:
                    coach = Coach.get_or_none(Coach.id == player.coach_id)
                    if coach:
                        coach_name = coach.coach
                
                Choice.create(
                    player_choice=player.id,
                    family=player.fio or player.player,
                    region=player.region or "",
                    coach=coach_name,
                    rank=player.rank or 0,
                    basic="",
                    group=f"Группа {group_num}",
                    posev_group=i + 1,
                    mesto_group=0,
                    title_id=self.current_title_id,
                    sex=player.sex
                )
            
        except Exception as e:
            raise Exception(f"Ошибка заполнения Choice: {str(e)}")

    def auto_assign_players_for_stage(self, table, players_list, stage):
        """Автоматическое распределение игроков для указанного этапа"""
        total_players = len(players_list)
        groups = stage.total_group
        
        # Распределение змейкой
        assignments = []
        for i in range(total_players):
            group_num = i % groups
            if (i // groups) % 2 == 1:
                group_num = groups - 1 - group_num
            assignments.append(group_num + 1)
        
        # Обновляем comboBox
        for row, group_num in enumerate(assignments):
            combo = table.cellWidget(row, 1)
            combo.setCurrentIndex(group_num)

    def save_manual_drawing_for_stage(self, num_id_player, stage):
        """Сохранение ручной жеребьевки для указанного этапа"""
        systems = System.select().where((System.title_id == self.current_title_id) and (System.stage == stage.stage)).get()
        try:
                   
            for pl in num_id_player:
                id = pl['id_player']
                group = f"{pl['group']} группа"
                posev = pl['seed_num']
                Choice.update(group=group, posev_group=posev).where(Choice.player_choice_id == id).execute()

            # Обновляем статус системы
            systems.choice_flag = 1
            systems.save()

            # Заполняем таблицу Result после жеребьевки
            self.fill_results_after_drawing()
            
            QMessageBox.information(self, "Успех", 
                                f"Жеребьевка для этапа '{stage.stage}' сохранена!\n"
                                f"Таблицы Choice и Result обновлены.")
            self.update_stages_info()
            # self.dialog.accept()
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {str(e)}")
# ========= Создание PDF файлов ===========

# ========== AI вариант PDF ============        
    def export_participants_to_pdf(self):
        """Экспорт списка участников в PDF с выбором сортировки"""
        from reportlab.platypus import Table
        from reportlab.platypus import Paragraph

        if not self.current_title_id:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите соревнование")
            return
        
        # Выбор типа сортировки
        sorting_type = self.get_sorting_type()
        if sorting_type is None:
            return  # Пользователь отменил
        
        try:
            # Получаем данные о соревновании
            title = Title.get(Title.id == self.current_title_id)
            
            # Создаем папку table_pdf, если её нет
            pdf_dir = "table_pdf"
            if not os.path.exists(pdf_dir):
                os.makedirs(pdf_dir)
            
            # Используем короткое имя из Title
            short_name = title.short_name_comp if title.short_name_comp else title.name
            if not short_name:
                short_name = "competition"
            import re
            clean_name = re.sub(r'[\\/*?:"<>|]', "", str(short_name))
            clean_name = clean_name[:50] if len(clean_name) > 50 else clean_name
            
            # Сортируем список участников в зависимости от выбора
            if sorting_type == "alpha":
                # Сортировка по алфавиту
                player_list = Player.select().where(Player.title_id == self.current_title_id).order_by(Player.player.asc())
                file_suffix = "alf"
            else:
                # Сортировка по рейтингу
                player_list = Player.select().where(Player.title_id == self.current_title_id).order_by(Player.rank.desc())
                file_suffix = "rating"
            
            # Путь к файлу
            file_path = os.path.join(pdf_dir, f"{clean_name}_player_list_{file_suffix}.pdf")
            
            if player_list.count() == 0:
                QMessageBox.warning(self, "Ошибка", "Нет участников для экспорта")
                return
            
            # Получаем параметры
            gamer = title.gamer if title.gamer else "Участники"
            otc = title.otchestvo if title.otchestvo else 0
            
            # Подготовка данных для таблицы
            elements = []
            n = 0
            
            for player in player_list:
                n += 1
                # Формируем ФИО с отчеством или без
                if otc == 1:
                    patronymic_text = ""
                    if player.patronymic_id:
                        try:
                            patronymic = Patronymic.get(Patronymic.id == player.patronymic_id)
                            patronymic_text = patronymic.patronymic
                        except:
                            pass
                    full_name = f"{player.player} {patronymic_text}".strip()
                else:
                    full_name = player.player
                
                # Форматируем дату
                birth_date = player.bday.strftime("%d.%m.%Y") if player.bday else "---"
                
                # Получаем тренера
                coach_text = ""
                if player.coach_id:
                    try:
                        coach = Coach.get(Coach.id == player.coach_id)
                        coach_text = coach.coach
                    except:
                        pass
# ==================================================                
                # Подготовка стилей перенос длинной строки
                styles = getSampleStyleSheet()
                custom_style = styles['Normal'].fontName = 'DejaVuSerif'
                custom_style = styles['Normal'].fontSize = 6
                custom_style = styles["Normal"].clone("CustomStyle")
                custom_style.wordWrap = 'LTR' # Перенос слов (LTR - Left-To-Right)
                custom_style.leading = 6 # Межстрочный интервал
                
                data_row = [
                    str(n),
                    Paragraph(full_name, custom_style),
                    birth_date,
                    str(player.rank) if player.rank else "0",
                    player.city or "",
                    Paragraph(player.region or "", custom_style),
                    player.razryad or "",
                    Paragraph(coach_text, custom_style),
                ]
                elements.append(data_row)
            
            # Добавляем заголовок таблицы
            headers = ["№", "ФИО", "Дата рожд.", "R", "Город", "Субъект РФ", "Разряд", "Тренер(ы)"]
            elements.insert(0, headers)
            
            # Создаем таблицу
            table = Table(elements, repeatRows=1)
            
            # Настраиваем ширину колонок
            col_widths = [0.8*cm, 5.0*cm, 1.6*cm, 0.8*cm, 2.5*cm, 3.2*cm, 1.1*cm, 4.0*cm]
            table._argW = col_widths
            
            # Стиль таблицы
            table_style = TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSerif'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BACKGROUND', (0, 0), (8, 0), colors.yellow),
                ('TEXTCOLOR', (0, 0), (8, 0), colors.darkblue),
                ('LINEABOVE', (0, 0), (-1, -1), 0.5, colors.blue),
                ('INNERGRID', (0, 0), (-1, -1), 0.2, colors.grey),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ])
            
            table.setStyle(table_style)
# ==========================================            
            # Создаем PDF документ
            doc = SimpleDocTemplate(file_path, pagesize=A4,
                                    topMargin=15*mm, bottomMargin=10*mm,
                                    leftMargin=5*mm, rightMargin=5*mm)
           
            # =========стиль заголовка ===========
            story = []
            h3 = PS("normal", fontSize=12, fontName="DejaVuSerif-Italic", leftIndent=180,
            firstLineIndent = 10, textColor="green")  # стиль параграфа
            h3.spaceAfter = 10  # промежуток после заголовка
            story.append(Paragraph(f'Список участников. {gamer}', h3))
            story.append(table)
            
            # Добавляем информацию о сортировке в заголовок
            sort_text = "по алфавиту" if sorting_type == "alpha" else "по рейтингу"
                        
            # Строим документ с использованием функции заголовка
            doc.build(story, onFirstPage=self.func_zagolovok, onLaterPages=self.func_zagolovok)
            
            QMessageBox.information(self, "Успех", 
                                f"Список участников успешно сохранен в PDF:\n{file_path}\n"
                                f"Сортировка: {sort_text}")
            
            # Предлагаем открыть файл
            reply = QMessageBox.question(self, "Открыть файл", 
                                        "Открыть созданный PDF файл?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                if sys.platform == 'win32':
                    os.startfile(file_path)
                else:
                    os.system(f'open "{file_path}"')
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать PDF: {str(e)}")
# ===============================================
    def _export_participants_to_pdf(self):
        """Экспорт списка участников в PDF с использованием reportlab"""
        from reportlab.platypus import Table
        from reportlab.platypus import Paragraph

        if not self.current_title_id:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите соревнование")
            return
        
        try:
            # Получаем данные о соревновании
            title = Title.get(Title.id == self.current_title_id)
            
            # Создаем папку table_pdf, если её нет
            pdf_dir = "table_pdf"
            if not os.path.exists(pdf_dir):
                os.makedirs(pdf_dir)
            
            # Используем короткое имя из Title
            short_name = title.short_name_comp if title.short_name_comp else title.name
            if not short_name:
                short_name = "competition"
            import re
            clean_name = re.sub(r'[\\/*?:"<>|]', "", str(short_name))
            clean_name = clean_name[:50] if len(clean_name) > 50 else clean_name
            
            # Путь к файлу
            file_path = os.path.join(pdf_dir, f"{clean_name}_player_list.pdf")
            
            # Получаем параметры
            gamer = title.gamer if title.gamer else "Участники"
            otc = title.otchestvo if title.otchestvo else 0
            
            # Получаем список участников
            player_list = Player.select().where(Player.title_id == self.current_title_id).order_by(Player.player)
            
            if player_list.count() == 0:
                QMessageBox.warning(self, "Ошибка", "Нет участников для экспорта")
                return
            
            # Подготовка данных для таблицы
            elements = []
            n = 0
            
            for player in player_list:
                n += 1
                # Формируем ФИО с отчеством или без
                if otc == 1:
                    patronymic_text = ""
                    if player.patronymic_id:
                        try:
                            patronymic = Patronymic.get(Patronymic.id == player.patronymic_id)
                            patronymic_text = patronymic.patronymic
                        except:
                            pass
                    full_name = f"{player.player} {patronymic_text}".strip()
                else:
                    full_name = player.player
                
                # Форматируем дату
                birth_date = player.bday.strftime("%d.%m.%Y") if player.bday else "---"
                
                # Получаем тренера
                coach_text = ""
                if player.coach_id:
                    try:
                        coach = Coach.get(Coach.id == player.coach_id)
                        coach_text = coach.coach
                    except:
                        pass
                
                # Создаем ячейки с переносом текста
                from reportlab.platypus import Paragraph
                # from reportlab.lib.styles import ParagraphStyle
                
                 # Подготовка стилей перенос длинной строки
                styles = getSampleStyleSheet()
                custom_style = styles['Normal'].fontName = 'DejaVuSerif'
                custom_style = styles['Normal'].fontSize = 6
                custom_style = styles["Normal"].clone("CustomStyle")
                custom_style.wordWrap = 'LTR' # Перенос слов (LTR - Left-To-Right)
                custom_style.leading = 6 # Межстрочный интервал
                
                data_row = [
                    str(n),
                    Paragraph(full_name, custom_style),
                    birth_date,
                    str(player.rank) if player.rank else "0",
                    player.city or "",
                    Paragraph(player.region or "", custom_style),
                    player.razryad or "",
                    Paragraph(coach_text, custom_style),
                    # str(player.mesto) if player.mesto else ""
                ]
                elements.append(data_row)
            
            # Добавляем заголовок таблицы
            headers = ["№", "ФИО", "Дата рожд.", "R", "Город", "Субъект РФ", "Разряд", "Тренер(ы)"]
            elements.insert(0, headers)
            
            # Создаем таблицу
            table = Table(elements, repeatRows=1)
            
            # Настраиваем ширину колонок
            col_widths = [0.8*cm, 5.0*cm, 1.6*cm, 0.8*cm, 2.5*cm, 3.2*cm, 1.1*cm, 4.0*cm]
            table._argW = col_widths
            
            # Стиль таблицы
            table_style = TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSerif'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BACKGROUND', (0, 0), (8, 0), colors.yellow),
                ('TEXTCOLOR', (0, 0), (8, 0), colors.darkblue),
                ('LINEABOVE', (0, 0), (-1, -1), 0.5, colors.blue),
                ('INNERGRID', (0, 0), (-1, -1), 0.2, colors.grey),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ])
            
            table.setStyle(table_style)
            
            # Создаем PDF документ
            doc = SimpleDocTemplate(file_path, pagesize=A4,
                                    topMargin=15*mm, bottomMargin=10*mm,
                                    leftMargin=5*mm, rightMargin=5*mm)
           
            # =========стиль заголовка ===========
            story = []
            h3 = PS("normal", fontSize=12, fontName="DejaVuSerif-Italic", leftIndent=180,
            firstLineIndent = 10, textColor="green")  # стиль параграфа
            h3.spaceAfter = 10  # промежуток после заголовка
            story.append(Paragraph(f'Список участников. {gamer}', h3))
            story.append(table)
                        
            # Строим документ с использованием функции заголовка
            doc.build(story, onFirstPage=self.func_zagolovok, onLaterPages=self.func_zagolovok)
            
            QMessageBox.information(self, "Успех", 
                                f"Список участников успешно сохранен в PDF:\n{file_path}")
            
            # Предлагаем открыть файл
            reply = QMessageBox.question(self, "Открыть файл", 
                                        "Открыть созданный PDF файл?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                if sys.platform == 'win32':
                    os.startfile(file_path)
                else:
                    os.system(f'open "{file_path}"')
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать PDF: {str(e)}")

    def get_sorting_type(self):
        """Запрос типа сортировки для списка участников"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Сортировка списка участников")
        dialog.setModal(True)
        dialog.setFixedSize(400, 200)
        
        layout = QVBoxLayout(dialog)
        
        # Заголовок
        title_label = QLabel("Выберите способ сортировки списка участников")
        title_label.setStyleSheet("font-weight: bold; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        layout.addSpacing(10)
        
        # Кнопки выбора
        alpha_btn = QPushButton("🔤 По алфавиту (А-Я)")
        alpha_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 12px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        rating_btn = QPushButton("📊 По рейтингу (по убыванию)")
        rating_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 12px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        self.sorting_type = None
        
        def set_alpha():
            self.sorting_type = "alpha"
            dialog.accept()
        
        def set_rating():
            self.sorting_type = "rating"
            dialog.accept()
        
        alpha_btn.clicked.connect(set_alpha)
        rating_btn.clicked.connect(set_rating)
        
        layout.addWidget(alpha_btn)
        layout.addWidget(rating_btn)
        
        if dialog.exec_() == QDialog.Accepted:
            return self.sorting_type
        return None
# =============================================
    def func_zagolovok(self, canvas, doc):
        """создание заголовка страниц для PDF"""
        pagesizeW = doc.width
        pagesizeH = doc.height
        
        # Определяем ориентацию страницы
        if pagesizeH > pagesizeW:
            pv = A4
        else:
            pv = landscape(A4)
        (width, height) = pv
        
        # Получаем данные о соревновании
        if not hasattr(self, 'current_title_id') or not self.current_title_id:
            return
        
        try:
            title = Title.get(Title.id == self.current_title_id)
            
            nz = title.name if title.name else ""
            ind = title.perenos if hasattr(title, 'perenos') else 0
            ms = title.mesto if title.mesto else ""
            sr = f"среди {title.sredi} {title.vozrast}" if title.sredi else ""
            
            # Формируем дату
            data_comp = ""
            if title.data_start:
                data_comp = title.data_start.strftime("%d.%m.%Y")
                if title.data_end and title.data_end != title.data_start:
                    data_comp += f" - {title.data_end.strftime('%d.%m.%Y')}"
            
            # Определяем текущую вкладку
            current_button = "0"
            if hasattr(self, 'tab_widget'):
                tb = self.tab_widget.currentIndex()
            
            canvas.saveState()
            
            # Устанавливаем шрифт (если DejaVu недоступен, используем Helvetica)
            try:
                canvas.setFont("DejaVuSerif-Italic", 11)
            except:
                canvas.setFont("Helvetica", 11)
            
            canvas.setFillColor(black)

            # Центральный текст титула
            if ind > 0 and pv == A4:
                nz_list = nz.split()
                if len(nz_list) > ind:
                    word = nz_list[ind]
                    s1 = nz.find(word) + len(word)
                    strline1 = nz[:s1]
                    strline2 = nz[s1 + 1:]
                    canvas.drawCentredString(width / 2.0, height - 1.1 * cm, strline1)
                    canvas.drawCentredString(width / 2.0, height - 1.5 * cm, strline2)
                    try:
                        canvas.setFont("DejaVuSerif-Italic", 11)
                    except:
                        canvas.setFont("Helvetica", 11)
                    canvas.drawCentredString(width / 2.0, height - 1.9 * cm, sr)
                    try:
                        canvas.setFont("DejaVuSerif-Italic", 10)
                    except:
                        canvas.setFont("Helvetica", 10)
                else:
                    canvas.drawCentredString(width / 2.0, height - 1.1 * cm, nz)
                    canvas.drawCentredString(width / 2.0, height - 1.5 * cm, sr)
                    try:
                        canvas.setFont("DejaVuSerif-Italic", 11)
                    except:
                        canvas.setFont("Helvetica", 11)
            else:
                canvas.drawCentredString(width / 2.0, height - 1.1 * cm, nz)
                canvas.drawCentredString(width / 2.0, height - 1.5 * cm, sr)
                try:
                    canvas.setFont("DejaVuSerif-Italic", 11)
                except:
                    canvas.setFont("Helvetica", 11)
            
            

            # Текст титула по основным
            canvas.drawRightString(width - 1 * cm, height - 1.9 * cm, f"г. {ms}")
            canvas.drawString(0.8 * cm, height - 1.9 * cm, data_comp)
            
            # Текст судейской коллегии
            try:
                canvas.setFont("DejaVuSerif-Italic", 10)
            except:
                canvas.setFont("Helvetica", 10)
            
            canvas.setFillColor(blue)
            
            if pv == landscape(A4):
                main_referee_collegia = (f"Гл. судья: судья {title.kat_ref} ______________ {title.referee}   "
                                        f"Гл. секретарь: судья {title.kat_sec} ______________ {title.secretary}")
                if current_button == "3":
                    canvas.drawCentredString(width / 2.0, height - 15 * cm, main_referee_collegia)
                else:
                    canvas.drawCentredString(width / 2.0, height - 20 * cm, main_referee_collegia)
            else:
                main_referee = f"Гл. судья: судья {title.kat_ref} ______________ {title.referee}"
                if current_button == "1":
                    canvas.drawString(2 * cm, 20 * cm, main_referee)
                elif current_button == "2":
                    # Сдвигает подпись судьи относительно количества регионов
                    regions_list = []
                    players = Player.select().where(Player.title_id == self.current_title_id)
                    for k in players:
                        region = k.region
                        if region:
                            regions_list.append(region)
                    regions_set = set(regions_list)
                    count = len(regions_set)
                    canvas.drawString(2 * cm, ((29 - count) * cm), main_referee)
                else:
                    main_secretary = f"Гл. секретарь: судья {title.kat_sec} ______________ {title.secretary}"
                    canvas.drawString(2 * cm, 1.8 * cm, main_referee)
                    canvas.drawString(2 * cm, 0.8 * cm, main_secretary)
            
            canvas.restoreState()
            
        except Exception as e:
            print(f"Ошибка в func_zagolovok: {e}")
            canvas.restoreState()
# =========================================
    def export_schedule_to_pdf(self):
        """Экспорт расписания соревнований в PDF"""
        from reportlab.platypus import Table
        from reportlab.platypus import Paragraph

        if not self.current_title_id:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите соревнование")
            return
        
        try:
            title = Title.get(Title.id == self.current_title_id)
            
            # Получаем этапы системы
            stages = []
            for stage in System.select().where(System.title_id == self.current_title_id).order_by(System.id):
                stages.append({
                    'id': stage.id,
                    'stage': stage.stage,
                    'total_group': stage.total_group,
                    'max_player': stage.max_player,
                    'type_table': stage.type_table
                })
            
            if len(stages) == 0:
                QMessageBox.warning(self, "Ошибка", "Система проведения не настроена")
                return
            
            # Получаем данные Choice
            choices_data = []
            for choice in Choice.select().where(Choice.title_id == self.current_title_id).order_by(Choice.group):
                try:
                    player = Player.get(Player.id == choice.player_choice.id)
                    choices_data.append({
                        'id': choice.id,
                        'player_id': player.id,
                        'fio': player.fio,
                        'rank': player.rank,
                        'group': choice.group
                    })
                except:
                    pass
            
            # Создаем папку table_pdf, если её нет
            pdf_dir = "table_pdf"
            if not os.path.exists(pdf_dir):
                os.makedirs(pdf_dir)
            
            # Используем короткое имя из Title
            short_name = title.short_name_comp if title.short_name_comp else title.name
            if not short_name:
                short_name = "competition"
            import re
            clean_name = re.sub(r'[\\/*?:"<>|]', "", str(short_name))
            clean_name = clean_name[:50] if len(clean_name) > 50 else clean_name
            
            default_path = os.path.join(pdf_dir, f"schedule_{clean_name}_{QDate.currentDate().toString('yyyy_MM_dd')}.pdf")
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить расписание",
                default_path,
                "PDF files (*.pdf)"
            )
            
            if not file_path:
                return
            
            doc = SimpleDocTemplate(file_path, pagesize=landscape(A4),
                                    topMargin=20*mm, bottomMargin=20*mm,
                                    leftMargin=15*mm, rightMargin=15*mm)
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                alignment=1,
                spaceAfter=20
            )
            
            elements = []
            
            # Заголовок
            elements.append(Paragraph(f"Расписание соревнований", title_style))
            elements.append(Paragraph(f"{title.name}", styles['Heading2']))
            elements.append(Spacer(1, 10*mm))
            
            # Данные по этапам
            for idx, stage in enumerate(stages, 1):
                elements.append(Paragraph(f"Этап {idx}: {stage['stage']}", styles['Heading3']))
                elements.append(Spacer(1, 5*mm))
                
                if len(choices_data) > 0:
                    # Группируем по группам
                    groups = {}
                    for choice in choices_data:
                        group_name = choice['group']
                        if group_name not in groups:
                            groups[group_name] = []
                        groups[group_name].append(choice)
                    
                    for group_name, group_choices in groups.items():
                        elements.append(Paragraph(f"{group_name}", styles['Heading4']))
                        
                        # Таблица участников группы
                        data = [['№', 'ФИО', 'Рейтинг']]
                        for i, choice in enumerate(group_choices, 1):
                            data.append([str(i), choice['fio'], str(choice['rank'])])
                        
                        table = Table(data)
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ]))
                        elements.append(table)
                        elements.append(Spacer(1, 5*mm))
                else:
                    elements.append(Paragraph("Жеребьевка не проведена", styles['Normal']))
                
                elements.append(Spacer(1, 10*mm))
            
            doc.build(elements)
            
            QMessageBox.information(self, "Успех", f"Расписание сохранено в PDF:\n{file_path}")
            
            reply = QMessageBox.question(self, "Открыть файл", 
                                        "Открыть созданный PDF файл?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                if sys.platform == 'win32':
                    os.startfile(file_path)
                else:
                    os.system(f'open "{file_path}"')
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать PDF: {str(e)}")

    def register_fonts(self):
        """Регистрация русских шрифтов для PDF"""
        try:
            # Путь к шрифту DejaVu (если есть)
            font_path = "C:/Windows/Fonts/arial.ttf"
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Arial', font_path))
        except:
            pass
# ======================================================       
    def tours_list(self, players_count):
        """туры таблиц по кругу в зависимости от кол-во участников"""
        # cp = players_count - 3 (индекс в списке туров)
        cp = max(0, players_count - 3)
        
        tr = [[['1-3'], ['1-2'], ['2-3']],
            [['1-3', '2-4'], ['1-2', '3-4'], ['2-3', '1-4']],
            [['2-4', '1-5'], ['1-4', '3-5'], ['1-3', '2-5'], ['2-3', '4-5'], ['1-2', '3-4']],
            [['2-4', '1-5', '3-6'], ['1-4', '2-6', '3-5'], ['1-3', '2-5', '4-6'], ['2-3', '1-6', '4-5'],
                ['1-2', '3-4', '5-6']],
            [['2-6', '3-5', '1-7'], ['2-5', '1-6', '4-7'], ['1-5', '4-6', '3-7'], ['4-5', '2-7', '3-6'],
                ['1-3', '2-4', '5-7'], ['1-4', '2-3', '6-7'], ['1-2', '3-4', '5-6']],
            [['2-6', '3-5', '1-7', '4-8'], ['2-5', '1-6', '3-8', '4-7'], ['1-5', '2-8', '4-6', '3-7'],
                ['1-8', '4-5', '2-7', '3-6'], ['1-3', '2-4', '5-7', '6-8'], ['1-4', '2-3', '6-7', '5-8'],
                ['1-2', '3-4', '5-6', '7-8']],
            [['1-9', '2-8', '3-7', '4-6'], ['5-9', '1-8', '2-7', '3-6'], ['4-9', '5-8', '1-7', '2-6'],
                ['3-9', '4-8', '5-7', '1-6'], ['2-4', '1-5', '3-8', '7-9'], ['4-1', '5-3', '9-2', '8-6'],
                ['1-3', '2-5', '4-7', '6-9'], ['3-2', '5-4', '8-9', '7-6'], ['1-2', '3-4', '5-6', '7-8']],
            [['1-9', '2-8', '3-7', '4-6', '5-10'], ['5-9', '1-8', '2-7', '3-6', '4-10'], ['4-9', '5-8', '1-7', '2-6', '3-10'],
                ['3-9', '4-8', '5-7', '1-6', '2-10'], ['2-4', '1-5', '3-8', '7-9', '6-10'], ['4-1', '5-3', '9-2', '8-6', '7-10'],
                ['1-3', '2-5', '4-7', '6-9', '8-10'], ['3-2', '5-4', '8-9', '7-6', '1-10'], ['1-2', '3-4', '5-6', '7-8', '9-10']],
            [['1-11', '2-10', '3-9', '4-8', '5-7'], ['6-11', '1-10', '2-9', '3-8', '4-7'], ['5-11', '6-10', '1-9', '2-8', '3-7'],
                ['4-11', '5-10', '6-9', '1-8', '2-7'], ['3-11', '4-10', '5-9', '6-8', '1-7'], ['2-11', '3-10', '4-9', '5-8', '6-7'],
                ['2-4', '1-5', '3-6', '7-10', '9-11'], ['1-4', '2-6', '3-5', '8-10', '7-11'], ['1-3', '2-5', '4-6', '7-9', '8-11'],
                ['2-3', '1-6', '4-5', '8-9', '10-11'], ['1-2', '3-4', '5-6', '7-8', '9-10']],
            [['1-11', '2-10', '3-9', '4-8', '5-7', '6-12'], ['6-11', '1-10', '2-9', '3-8', '4-7', '5-12'],
                ['5-11', '6-10', '1-9', '2-8', '3-7', '4-12'], ['4-11', '5-10', '6-9', '1-8', '2-7', '3-12'],
                ['3-11', '4-10', '5-9', '6-8', '1-7', '2-12'], ['2-11', '3-10', '4-9', '5-8', '6-7', '1-12'],
                ['2-4', '1-5', '3-6', '7-10', '9-11', '8-12'], ['1-4', '2-6', '3-5', '8-10', '7-11', '9-12'],
                ['1-3', '2-5', '4-6', '7-9', '8-11', '10-12'], ['2-3', '1-6', '4-5', '8-9', '10-11', '7-12'],
                ['1-2', '3-4', '5-6', '7-8', '9-10', '11-12']],
            [['1-13', '2-12', '3-11', '4-10', '5-9', '6-8'], ['7-13', '1-12', '2-11', '3-10', '4-9', '5-8'],
                ['6-13', '7-12', '1-11', '2-10', '3-9', '4-8'], ['5-13', '6-12', '7-11', '1-10', '2-9', '3-8'],
                ['4-13', '5-12', '6-11', '7-10', '1-9', '2-8'], ['3-13', '4-12', '5-11', '6-10', '7-9', '1-8'],
                ['1-7', '2-6', '3-5', '4-11', '9-13', '10-12'], ['1-6', '2-5', '4-7', '3-12', '8-11', '10-13'],
                ['1-4', '2-7', '3-6', '5-10', '8-13', '9-12'], ['1-5', '3-7', '4-6', '2-13', '8-12', '9-11'],
                ['1-3', '2-4', '5-7', '6-9', '8-10', '11-13'], ['2-3', '4-5', '6-7', '8-9', '10-11', '12-13'],
                ['1-2', '3-4', '5-6', '7-8', '9-10', '11-12']],
            [['1-13', '2-12', '3-11', '4-10', '5-9', '6-8', '7-14'], ['7-13', '1-12', '2-11', '3-10', '4-9', '5-8', '6-14'],
                ['6-13', '7-12', '1-11', '2-10', '3-9', '4-8', '5-14'], ['5-13', '6-12', '7-11', '1-10', '2-9', '3-8', '4-14'],
                ['4-13', '5-12', '6-11', '7-10', '1-9', '2-8', '3-14'], ['3-13', '4-12', '5-11', '6-10', '7-9', '1-8', '2-14'],
                ['1-7', '2-6', '3-5', '4-11', '9-13', '10-12', '8-14'], ['1-6', '2-5', '4-7', '3-12', '8-11', '10-13', '9-14'],
                ['1-4', '2-7', '3-6', '5-10', '8-13', '9-12', '11-14'], ['1-5', '3-7', '4-6', '2-13', '8-12', '9-11', '10-14'],
                ['1-3', '2-4', '5-7', '6-9', '8-10', '11-13', '12-14'], ['2-3', '4-5', '6-7', '8-9', '10-11', '12-13', '1-14'],
                ['1-2', '3-4', '5-6', '7-8', '9-10', '11-12', '13-14']],
            [['1-15', '2-14', '3-13', '4-12', '5-11', '6-10', '7-9'], ['8-15', '1-14', '2-13', '3-12', '4-11', '5-10', '6-9'],
                ['8-15', '1-14', '2-13', '3-12', '4-11', '5-10', '6-9'], ['7-15', '8-14', '1-13', '2-12', '3-11', '4-10', '5-9'],
                ['6-15', '7-14', '8-13', '1-12', '2-11', '3-10', '4-9'], ['5-15', '6-14', '7-13', '8-12', '1-11', '2-10', '3-9'],
                ['4-15', '5-14', '6-13', '7-12', '8-11', '1-10', '2-9'], ['3-15', '4-14', '5-13', '6-12', '7-11', '8-10', '1-9'],
                ['2-15', '3-14', '4-13', '5-12', '6-11', '7-10', '8-9'], ['1-7', '2-6', '3-5', '4-8', '9-13', '12-14', '11-15'],
                ['1-6', '2-5', '3-8', '4-7', '9-14', '10-13', '12-15'], ['1-5', '2-8', '3-7', '4-6', '9-15', '10-14', '11-13'],
                ['1-4', '2-7', '3-6', '5-8', '9-12', '10-15', '11-14'], ['1-3', '2-4', '5-7', '6-8', '9-11', '10-12', '13-15'],
                ['1-8', '2-3', '4-5', '6-7', '10-11', '12-13', '14-15'], ['1-2', '3-4', '5-6', '7-8', '9-10', '11-12', '13-14']],
            [['1-15', '2-14', '3-13', '4-12', '5-11', '6-10', '7-9', '8-16'],
                ['8-15', '1-14', '2-13', '3-12', '4-11', '5-10', '6-9', '7-16'],
                ['7-15', '8-14', '1-13', '2-12', '3-11', '4-10', '5-9', '6-16'],
                ['6-15', '7-14', '8-13', '1-12', '2-11', '3-10', '4-9', '5-16'],
                ['5-15', '6-14', '7-13', '8-12', '1-11', '2-10', '3-9', '4-16'],
                ['4-15', '5-14', '6-13', '7-12', '8-11', '1-10', '2-9', '3-16'],
                ['3-15', '4-14', '5-13', '6-12', '7-11', '8-10', '1-9', '2-16'],
                ['2-15', '3-14', '4-13', '5-12', '6-11', '7-10', '8-9', '1-16'],
                ['1-7', '2-6', '3-5', '4-8', '9-13', '12-14', '11-15', '10-16'],
                ['1-6', '2-5', '3-8', '4-7', '9-14', '10-13', '12-15', '11-16'],
                ['1-5', '2-8', '3-7', '4-6', '9-15', '10-14', '11-13', '12-16'],
                ['1-4', '2-7', '3-6', '5-8', '9-12', '10-15', '11-14', '13-16'],
                ['1-3', '2-4', '5-7', '6-8', '9-11', '10-12', '13-15', '14-16'],
                ['1-8', '2-3', '4-5', '6-7', '10-11', '12-13', '14-15', '9-16'],
                ['1-2', '3-4', '5-6', '7-8', '9-10', '11-12', '13-14', '15-16']],
            [['2-17', '3-16', '4-15', '5-14', '6-13', '7-12', '8-11','9-10'],
                ['1-17', '2-15', '3-14', '4-13', '5-12', '6-11', '7-10','8-9'],
                ['1-16', '15-17', '2-13', '3-12', '4-11', '5-10', '6-9','7-8'],
                ['1-15', '14-16', '13-17', '2-11', '3-10', '4-9', '5-8','6-7'],
                ['1-14', '13-15', '12-16', '11-17', '2-9', '3-8', '4-7','5-6'],
                ['1-13', '12-14', '11-15', '10-16', '9-17', '2-7', '3-6','4-5'],
                ['1-12', '11-13', '10-14', '9-15', '8-16', '7-17', '2-5','3-4'],
                ['1-11', '10-12', '9-13', '8-14', '7-15', '6-16', '5-17', '2-3'],
                ['1-10', '9-11', '8-12', '7-13', '6-14', '5-15', '4-16', '3-17'],
                ['1-9', '8-10', '7-11', '6-12', '5-13', '4-14', '3-15', '2-16'],
                ['1-8', '7-9', '6-10', '5-11', '4-12', '3-13', '2-14', '16-17'],
                ['1-7', '6-8', '5-9', '4-10', '3-11', '2-12', '14-17','15-16'],
                ['1-6', '5-7', '4-8', '3-9', '2-10', '12-17', '13-16','14-15'],
                ['1-5', '4-6', '3-7', '2-8', '10-17', '11-16', '12-15','13-14'],
                ['1-4', '3-5', '2-6', '8-17', '9-16', '10-15', '11-14','12-13'],
                ['1-3', '2-4', '6-17', '7-16', '8-15', '9-14', '10-13','11-12'],
                ['1-2', '4-17', '5-16', '6-15', '7-14', '8-13', '9-12','10-11']]
        ]
        
        if cp < len(tr):
            return tr[cp]
        else:
            # Для большего количества участников возвращаем последний вариант
            return tr[-1]
    
    def _write_drawing_results_to_result(self, group_players, stage_name, group_number, system_id):
        """Запись результатов жеребьевки в таблицу Result"""
        try:
            players_count = len(group_players)
            
            # Получаем туры для данного количества участников
            tours = self.tours_list(players_count)
            
            if not tours:
                print(f"Нет расписания туров для {players_count} участников")
                return
            
            for tour_idx, tour_matches in enumerate(tours, 1):
                # tour_matches - список пар для одного тура, например ['1-3', '2-4']
                for match in tour_matches:
                    # Разбираем пару, например '1-3'
                    players_pair = match.split('-')
                    if len(players_pair) == 2:
                        try:
                            player1_idx = int(players_pair[0]) - 1  # переводим в индекс массива (0-based)
                            player2_idx = int(players_pair[1]) - 1
                            
                            # Получаем игроков по индексам
                            if player1_idx < len(group_players) and player2_idx < len(group_players):
                                player1 = group_players[player1_idx]
                                player2 = group_players[player2_idx]
                                
                                # Формируем ФИО с городом
                                player1_fio_city = f"{player1.fio} ({player1.city})" if player1.city else player1.fio
                                player2_fio_city = f"{player2.fio} ({player2.city})" if player2.city else player2.fio
                                
                                # Создаем запись в таблице Result
                                Result.create(
                                    system_stage=stage_name,
                                    number_group=str(group_number),
                                    tours=str(tour_idx),
                                    player1=player1_fio_city,
                                    player2=player2_fio_city,
                                    winner=None,
                                    points_win=None,
                                    score_in_game=None,
                                    score_win=None,
                                    loser=None,
                                    points_loser=None,
                                    score_loser=None,
                                    title_id=self.current_title_id,
                                    round="",
                                    system_id=system_id,
                                    sex=self.current_sex if self.current_sex else "man",
                                    schedule_date=None,
                                    schedule_time=None,
                                    schedule_table="",
                                    stage_net=""
                                )
                        except (ValueError, IndexError) as e:
                            print(f"Ошибка при обработке пары {match}: {e}")
                            continue
            
            print(f"Создано результатов для группы {group_number}: {len(tours)} туров")
            
        except Exception as e:
            print(f"Ошибка записи результатов: {e}")
# ============
    def fill_results_after_drawing(self):
        """Заполнение таблицы Result после жеребьевки квалификации"""
        if not self.current_title_id:
            return
        
        try:
            # Получаем все записи Choice для этого соревнования
            choices = Choice.select().where(Choice.title_id == self.current_title_id).order_by(Choice.group)
            
            if choices.count() == 0:
                QMessageBox.warning(self, "Ошибка", "Нет данных жеребьевки для заполнения результатов")
                return
            
            # Группируем по группам
            groups = {}
            for choice in choices:
                group_name = choice.group
                if group_name not in groups:
                    groups[group_name] = []
                groups[group_name].append(choice)
            
            # Получаем систему для определения типа таблицы
            system = System.get_or_none(System.title_id == self.current_title_id)
            system_stage = system.stage if system else "Квалификация"
            
            # Очищаем существующие результаты для этого этапа
            Result.delete().where(
                (Result.title_id == self.current_title_id) &
                (Result.system_stage == system_stage)
            ).execute()
            # Очищаем существующие результаты для этого этапа
            Game_list.delete().where(
                (Game_list.title_id == self.current_title_id) &
                (Game_list.system_id == system.id)
            ).execute()
        
            total_matches = 0
            
            # Для каждой группы создаем туры
            for group_name, group_choices in groups.items():
                # Извлекаем номер группы
                group_num = group_name

                players_count = len(group_choices)
                
                # Сортируем игроков для получения номеров
                group_choices.sort(key=lambda x: x.posev_group)
                
                # Создаем словарь для отображения номера на данные игрока
                player_data = {}
                for idx, choice in enumerate(group_choices, 1):
                    player = Player.get(Player.id == choice.player_choice.id)
                    player_data[str(idx)] = {
                        'fio': player.fio_city,
                        'player_obj': player
                    }
                
                # Получаем туры для этого количества игроков
                tours = self.tours_list(players_count)
                
                if tours and len(tours) > 0:
                    round = 0
                    for tour in tours: # цикл заполнения db таблиц -Result-
                        round += 1
                        for match in tour:
                            znak = match.find("-")
                            p1_num = str(match[:znak])  # игрок под номером в группе
                            p2_num = str(match[znak + 1:])  # игрок под номером в группе
                            p1 = player_data[p1_num]
                            p2 = player_data[p2_num]
                                    
                            # Создаем запись в Result
                            Result.create(
                                system_stage=system_stage,
                                number_group=group_num,
                                tours=match,
                                player1=f"{p1['fio']}",
                                player2=f"{p2['fio']}",
                                winner=None,
                                points_win=0,
                                score_in_game=None,
                                score_win=None,
                                loser=None,
                                points_loser=0,
                                score_loser=None,
                                title_id=self.current_title_id,
                                round=round,
                                system_id=system.id if system else 1,
                                sex=self.current_sex if self.current_sex else "man",
                                schedule_date=None,
                                schedule_time=None,
                                schedule_table="",
                                stage_net=""
                            )
                            total_matches += 1
                # ===============================
                # Потом заполняем Game_list (информация о игроках в группах)
                for idx, player in enumerate(group_choices, 1):
                    Game_list.create(
                        number_group=player.group,
                        rank_num_player=player.posev_group,  # номер посева в группе
                        player_group=player.player_choice_id,
                        system_id=system.id if system else 1,
                        title_id=self.current_title_id,
                        sex=self.current_sex if self.current_sex else "man",
                        player_double_id=None,
                        team_id=None
                    )
            # =================================
            
            QMessageBox.information(self, "Успех", 
                                f"Таблица Result и Game_list заполнены!\n"
                                f"Всего матчей создано: {total_matches}")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Не удалось заполнить результаты: {str(e)}")

    def save_current_competition(self):
        """Сохранение текущего соревнования"""
        if not self.current_title_id:
            return
        
        try:
            title = Title.get_by_id(self.current_title_id)
            
            reply = QMessageBox.question(self, "Сохранение соревнования", 
                                        f"Сохранить резервную копию соревнования '{title.name}'?",
                                        QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # Создаем папку backup_db, если её нет
                backup_dir = "backup_db"
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                
                # Формируем имя файла
                short_name = title.short_name_comp if title.short_name_comp else title.name
                import re
                clean_name = re.sub(r'[\\/*?:"<>|]', "", str(short_name))
                clean_name = clean_name[:50] if len(clean_name) > 50 else clean_name
                
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                backup_file = os.path.join(backup_dir, f"{clean_name}_{timestamp}.sql")
                
                # Экспортируем базу данных
                self.export_database_internal(backup_file, None)
                
                QMessageBox.information(self, "Успех", f"Соревнование сохранено в:\n{backup_file}")
                
        except Exception as e:
            print(f"Ошибка сохранения соревнования: {e}")

    def export_database_internal(self, file_path, progress=None):
        """Встроенный экспорт базы данных (без mysqldump)"""
        try:
            from models import (
                Title, Coach, Region, City, Patronymic, Player, Players_full,
                R_list_m, R_list_d, R1_list_m, R1_list_d, Referee, Team,
                Players_double, Choice, Result, System, Choice_Team, Game_list,
                Choice_double_player, Delete_player, db
            )
            from datetime import datetime, date
            
            models = [
                Title, Coach, Region, City, Patronymic, Player, Players_full,
                R_list_m, R_list_d, R1_list_m, R1_list_d, Referee, Team,
                Players_double, Choice, Result, System, Choice_Team, Game_list,
                Choice_double_player, Delete_player
            ]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"-- Backup created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Database: {db.database}\n\n")
                
                for i, model in enumerate(models):
                    if progress and progress.wasCanceled():
                        break
                    
                    if progress:
                        progress.setValue(i)
                        progress.setLabelText(f"Экспорт таблицы: {model._meta.table_name}")
                    
                    table_name = model._meta.table_name
                    f.write(f"-- Table structure for table {table_name}\n")
                    f.write(f"DROP TABLE IF EXISTS `{table_name}`;\n")
                    
                    # Получаем колонки таблицы
                    columns = []
                    for field_name, field in model._meta.fields.items():
                        # Получаем имя колонки (db_column или column или name)
                        if hasattr(field, 'db_column') and field.db_column:
                            col_name = field.db_column
                        elif hasattr(field, 'column'):
                            col_name = field.column
                        else:
                            col_name = field_name
                        
                        # Получаем тип поля
                        if hasattr(field, 'field_type'):
                            col_type = field.field_type
                        else:
                            col_type = str(type(field).__name__).upper()
                        
                        col_def = f"`{col_name}` {col_type}"
                        
                        # Primary Key
                        if field.primary_key:
                            col_def += " PRIMARY KEY AUTO_INCREMENT"
                        
                        # NOT NULL
                        if not field.null and not field.primary_key:
                            col_def += " NOT NULL"
                        
                        # DEFAULT
                        if field.default is not None and not callable(field.default):
                            if isinstance(field.default, str):
                                col_def += f" DEFAULT '{field.default}'"
                            else:
                                col_def += f" DEFAULT {field.default}"
                        
                        columns.append(col_def)
                    
                    create_sql = f"CREATE TABLE `{table_name}` (\n  " + ",\n  ".join(columns) + "\n);"
                    f.write(f"{create_sql}\n\n")
                    
                    # Получаем данные
                    try:
                        query = model.select()
                        rows = list(query)
                        
                        if rows:
                            for row in rows:
                                values = []
                                for field_name, field in model._meta.fields.items():
                                    val = getattr(row, field_name)
                                    if val is None:
                                        values.append('NULL')
                                    elif isinstance(val, str):
                                        val = val.replace("'", "''")
                                        values.append(f"'{val}'")
                                    elif isinstance(val, (datetime, date)):
                                        values.append(f"'{val}'")
                                    elif isinstance(val, bool):
                                        values.append('1' if val else '0')
                                    else:
                                        values.append(str(val))
                                
                                # Получаем имена колонок
                                col_names = []
                                for field_name, field in model._meta.fields.items():
                                    if hasattr(field, 'db_column') and field.db_column:
                                        col_names.append(f"`{field.db_column}`")
                                    elif hasattr(field, 'column'):
                                        col_names.append(f"`{field.column}`")
                                    else:
                                        col_names.append(f"`{field_name}`")
                                
                                f.write(f"INSERT INTO `{table_name}` ({','.join(col_names)}) VALUES ({','.join(values)});\n")
                            f.write("\n")
                    except Exception as e:
                        print(f"Ошибка экспорта данных из {table_name}: {e}")
                        f.write(f"-- Ошибка экспорта данных: {e}\n\n")
            
            if progress:
                progress.setValue(len(models))
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e
# ===============================        
    def search_in_choice_table(self):
        """Поиск информации в таблице Choice"""
        if not self.current_title_id:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите соревнование")
            return
        
        # Проверяем существование таблицы Choice
        try:
            # Проверяем, есть ли записи в Choice для текущего соревнования
            choices_count = Choice.select().where(Choice.title_id == self.current_title_id).count()
            
            if choices_count == 0:
                QMessageBox.information(self, "Информация", 
                                    "Таблица Choice пуста.\n"
                                    "Сначала проведите жеребьевку квалификации.")
                return
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка доступа к таблице Choice: {str(e)}")
            return
        
        # Создаем диалог поиска
        dialog = QDialog(self)
        dialog.setWindowTitle("Поиск в таблице Choice")
        dialog.setModal(True)
        dialog.setMinimumWidth(650)
        dialog.setMinimumHeight(550)
        
        layout = QVBoxLayout(dialog)
        
        # Заголовок
        title_label = QLabel("Поиск участников в жеребьевке (таблица Choice)")
        title_label.setStyleSheet("font-weight: bold; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Поле для ввода поискового запроса
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("Введите ФИО, регион, тренера или группу...")
        search_edit.setMinimumWidth(300)
        search_layout.addWidget(search_edit)
        layout.addLayout(search_layout)
        
        # Выбор типа поиска
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Тип поиска:"))
        search_type_combo = QComboBox()
        search_type_combo.addItems(["Везде", "По ФИО", "По региону", "По тренеру", "По группе", "По рейтингу"])
        type_layout.addWidget(search_type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        search_btn = QPushButton("🔍 Найти")
        search_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
        clear_btn = QPushButton("🗑️ Очистить")
        clear_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 5px;")
        close_btn = QPushButton("Закрыть")
        close_btn.setStyleSheet("background-color: #f44336; color: white; padding: 5px;")
        buttons_layout.addWidget(search_btn)
        buttons_layout.addWidget(clear_btn)
        buttons_layout.addWidget(close_btn)
        layout.addLayout(buttons_layout)
        
        # Результаты поиска
        result_label = QLabel("Результаты поиска:")
        result_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(result_label)
        
        result_list = QListWidget()
        result_list.setStyleSheet("""
            QListWidget {
                min-height: 350px;
                border: 1px solid #ccc;
                border-radius: 3px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)
        layout.addWidget(result_list)
        
        def perform_search():
            search_text = search_edit.text().strip().lower()
            search_type = search_type_combo.currentText()
            
            if not search_text:
                QMessageBox.warning(dialog, "Ошибка", "Введите текст для поиска")
                return
            
            result_list.clear()
            
            try:
                # Получаем все записи Choice для текущего соревнования
                choices = Choice.select().where(Choice.title_id == self.current_title_id)
                
                results = []
                for choice in choices:
                    # Получаем данные игрока
                    player = Player.get_or_none(Player.id == choice.player_choice.id)
                    if not player:
                        continue
                    
                    match = False
                    highlight_text = ""
                    
                    # Приводим все к нижнему регистру для сравнения
                    family_lower = choice.family.lower() if choice.family else ""
                    region_lower = choice.region.lower() if choice.region else ""
                    coach_lower = choice.coach.lower() if choice.coach else ""
                    group_lower = choice.group.lower() if choice.group else ""
                    rank_str = str(choice.rank)
                    
                    if search_type == "Везде":
                        if (search_text in family_lower or
                            search_text in region_lower or
                            search_text in coach_lower or
                            search_text in group_lower or
                            search_text == rank_str):
                            match = True
                            if search_text in family_lower:
                                highlight_text = f"ФИО: {choice.family}"
                            elif search_text in region_lower:
                                highlight_text = f"Регион: {choice.region}"
                            elif search_text in coach_lower:
                                highlight_text = f"Тренер: {choice.coach}"
                            elif search_text in group_lower:
                                highlight_text = f"Группа: {choice.group}"
                            elif search_text == rank_str:
                                highlight_text = f"Рейтинг: {choice.rank}"
                    
                    elif search_type == "По ФИО":
                        if search_text in family_lower:
                            match = True
                            highlight_text = f"ФИО: {choice.family}"
                    
                    elif search_type == "По региону":
                        if search_text in region_lower:
                            match = True
                            highlight_text = f"Регион: {choice.region}"
                    
                    elif search_type == "По тренеру":
                        if search_text in coach_lower:
                            match = True
                            highlight_text = f"Тренер: {choice.coach}"
                    
                    elif search_type == "По группе":
                        if search_text in group_lower:
                            match = True
                            highlight_text = f"Группа: {choice.group}"
                    
                    elif search_type == "По рейтингу":
                        if search_text == rank_str:
                            match = True
                            highlight_text = f"Рейтинг: {choice.rank}"
                    
                    if match:
                        results.append({
                            'id': choice.id,
                            'family': choice.family,
                            'region': choice.region,
                            'coach': choice.coach,
                            'rank': choice.rank,
                            'group': choice.group,
                            'posev_group': choice.posev_group,
                            'mesto_group': choice.mesto_group,
                            'highlight': highlight_text
                        })
                
                if results:
                    for r in results:
                        item_text = f"""🏅 {r['family']}
    📍 Регион: {r['region']}
    👨‍🏫 Тренер: {r['coach']}
    📊 Рейтинг: {r['rank']}
    🏆 Группа: {r['group']} (посев: {r['posev_group']}, место: {r['mesto_group'] or 'не определено'})
    🔍 Найдено по: {r['highlight']}"""
                        item = QListWidgetItem(item_text)
                        item.setData(Qt.UserRole, r['id'])
                        result_list.addItem(item)
                    
                    result_label.setText(f"Результаты поиска: найдено {len(results)} участников")
                else:
                    result_list.addItem("Ничего не найдено")
                    result_label.setText("Результаты поиска: ничего не найдено")
                    
            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Ошибка поиска: {str(e)}")
        
        def clear_search():
            search_edit.clear()
            search_type_combo.setCurrentIndex(0)
            result_list.clear()
            result_label.setText("Результаты поиска:")
        
        search_btn.clicked.connect(perform_search)
        clear_btn.clicked.connect(clear_search)
        close_btn.clicked.connect(dialog.reject)
        search_edit.returnPressed.connect(perform_search)
        
        dialog.exec_()
# ================================
    def show_choice_statistics(self):
        """Показать статистику по таблице Choice"""
        if not self.current_title_id:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите соревнование")
            return
        
        try:
            total_players = Choice.select().where(Choice.title_id == self.current_title_id).count()
            
            # Группировка по группам
            from collections import Counter
            groups_counter = Counter()
            regions_counter = Counter()
            
            choices = Choice.select().where(Choice.title_id == self.current_title_id)
            
            for choice in choices:
                groups_counter[choice.group] += 1
                if choice.region:
                    regions_counter[choice.region] += 1
            
            stats_text = f"📊 СТАТИСТИКА ЖЕРЕБЬЕВКИ\n"
            stats_text += "=" * 40 + "\n\n"
            stats_text += f"👥 Всего участников: {total_players}\n\n"
            
            stats_text += "🏆 РАСПРЕДЕЛЕНИЕ ПО ГРУППАМ:\n"
            for group, count in sorted(groups_counter.items()):
                stats_text += f"   • {group}: {count} чел.\n"
            
            if regions_counter:
                stats_text += "\n📍 РАСПРЕДЕЛЕНИЕ ПО РЕГИОНАМ:\n"
                for region, count in regions_counter.most_common(10):
                    stats_text += f"   • {region}: {count} чел.\n"
            
            QMessageBox.information(self, "Статистика", stats_text)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")

    def clear_choice_table(self):
        """Очистка таблицы Choice для текущего соревнования"""
        if not self.current_title_id:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите соревнование")
            return
        
        reply = QMessageBox.question(self, "Подтверждение", 
                                    "Очистить таблицу Choice для текущего соревнования?\n"
                                    "Все данные жеребьевки будут удалены!",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                deleted = Choice.delete().where(Choice.title_id == self.current_title_id).execute()
                QMessageBox.information(self, "Успех", f"Удалено {deleted} записей из Choice")
                self.update_stages_info()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")

    def export_choice_report(self):
        """Экспорт отчета по жеребьевке в PDF"""
        QMessageBox.information(self, "Экспорт", "Функция экспорта отчета в разработке")
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

    registerFontFamily('DejaVuSerif', normal='DejaVuSerif',
                   bold='DejaVuSerif-Bold', italic='DejaVuSerif-Italic')
    outpath = os.path.join(os.getcwd(), 'font')
    pdfmetrics.registerFont(TTFont('DejaVuSans', os.path.join(outpath, 'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', os.path.join(outpath, 'DejaVuSans-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('DejaVuSerif', os.path.join(outpath, 'DejaVuSerif.ttf')))
    pdfmetrics.registerFont(TTFont('DejaVuSerif-Bold', os.path.join(outpath, 'DejaVuSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('DejaVuSerif-Italic', os.path.join(outpath, 'DejaVuSerif-Italic.ttf')))

    main()