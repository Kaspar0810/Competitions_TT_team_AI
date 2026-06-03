# import_initial_data.py
import csv
import os
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFileDialog, QCheckBox, QGroupBox,
                            QProgressBar, QMessageBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from models import Region, Patronymic, Players_full, Coach, db

class ImportThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, import_data, file_paths):
        super().__init__()
        self.import_data = import_data
        self.file_paths = file_paths
        
    def run(self):
        try:
            total_steps = sum(1 for k, v in self.import_data.items() if v)
            current_step = 0
            
            # Импорт регионов
            if self.import_data.get('regions'):
                self.progress.emit(0, "Импорт регионов...")
                self.import_regions()
                current_step += 1
                self.progress.emit(int(current_step / total_steps * 100), "Регионы импортированы")
            
            # Импорт отчеств
            if self.import_data.get('patronymics'):
                self.progress.emit(0, "Импорт отчеств...")
                self.import_patronymics()
                current_step += 1
                self.progress.emit(int(current_step / total_steps * 100), "Отчества импортированы")
            
            # Импорт тренеров
            if self.import_data.get('coaches'):
                self.progress.emit(0, "Импорт тренеров...")
                self.import_coaches()
                current_step += 1
                self.progress.emit(int(current_step / total_steps * 100), "Тренеры импортированы")
            
            # Импорт полных данных игроков
            if self.import_data.get('players_full'):
                self.progress.emit(0, "Импорт полных данных игроков...")
                self.import_players_full()
                current_step += 1
                self.progress.emit(int(current_step / total_steps * 100), "Данные игроков импортированы")
            
            self.finished.emit(True, "Импорт завершен успешно!")
            
        except Exception as e:
            self.finished.emit(False, f"Ошибка импорта: {str(e)}")
    
    def import_regions(self):
        """Импорт регионов из CSV"""
        file_path = self.file_paths.get('regions')
        if not file_path or not os.path.exists(file_path):
            return
        
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                region_name = row.get('region') or row.get('Регион') or row.get('название')
                if region_name:
                    Region.get_or_create(region=region_name.strip())
    
    def import_patronymics(self):
        """Импорт отчеств из CSV"""
        file_path = self.file_paths.get('patronymics')
        if not file_path or not os.path.exists(file_path):
            return
        
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                patronymic = row.get('patronymic') or row.get('Отчество') or row.get('название')
                sex = row.get('sex') or row.get('Пол') or row.get('пол')
                if patronymic:
                    Patronymic.get_or_create(
                        patronymic=patronymic.strip(),
                        defaults={'sex': sex[0].lower() if sex else 'm'}
                    )
    
    def import_coaches(self):
        """Импорт тренеров из CSV"""
        file_path = self.file_paths.get('coaches')
        if not file_path or not os.path.exists(file_path):
            return
        
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                coach_name = row.get('coach') or row.get('Тренер') or row.get('ФИО')
                if coach_name:
                    Coach.get_or_create(coach=coach_name.strip())
    
    def import_players_full(self):
        """Импорт полных данных игроков из CSV"""
        file_path = self.file_paths.get('players_full')
        if not file_path or not os.path.exists(file_path):
            return
        
        from datetime import datetime
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                player_name = row.get('player') or row.get('ФИО') or row.get('Игрок')
                if not player_name:
                    continue
                
                # Обработка даты рождения
                bday_str = row.get('bday') or row.get('Дата рождения')
                bday = None
                if bday_str:
                    try:
                        for fmt in ["%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d", "%d/%m/%Y"]:
                            try:
                                bday = datetime.strptime(bday_str.strip(), fmt).date()
                                break
                            except:
                                continue
                    except:
                        pass
                
                # Получаем регион
                region_name = row.get('region') or row.get('Регион')
                region = None
                if region_name:
                    region_obj = Region.get_or_none(Region.region == region_name.strip())
                    if region_obj:
                        region = region_obj.region
                
                # Получаем отчество
                patronymic_name = row.get('patronymic') or row.get('Отчество')
                patronymic_id = None
                if patronymic_name:
                    patronymic_obj = Patronymic.get_or_none(Patronymic.patronymic == patronymic_name.strip())
                    if patronymic_obj:
                        patronymic_id = patronymic_obj.id
                
                # Получаем тренера
                coach_name = row.get('coach_id') or row.get('Тренер')
                coach_id = None
                if coach_name:
                    coach_obj = Coach.get_or_none(Coach.coach == coach_name.strip())
                    if coach_obj:
                        coach_id = coach_obj.id
                
                # Пол
                sex = row.get('sex') or row.get('Пол')
                if sex:
                    sex = 'man' if sex.lower().startswith('м') else 'woman'
                
                # Создаем или обновляем запись
                Players_full.get_or_create(
                    player=player_name.strip(),
                    defaults={
                        'bday': bday,
                        'city': row.get('city') or row.get('Город'),
                        'region': region,
                        'razryad': row.get('razryad') or row.get('Разряд'),
                        'coach_id': coach_id,
                        'patronymic_id': patronymic_id,
                        'sex': sex
                    }
                )


class InitialDataImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Импорт начальных данных")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.file_paths = {}
        self.import_data = {
            'regions': False,
            'patronymics': False,
            'coaches': False,
            'players_full': False
        }
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Заголовок
        title_label = QLabel("Импорт начальных данных")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        info_label = QLabel("База данных успешно создана.\n"
                           "Выберите CSV файлы для импорта справочных данных:")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Группа для выбора файлов
        files_group = QGroupBox("Выбор файлов для импорта")
        files_layout = QVBoxLayout(files_group)
        
        # Регионы
        regions_widget = self.create_file_selector("Регионы", "regions")
        files_layout.addWidget(regions_widget)
        
        # Отчества
        patronymics_widget = self.create_file_selector("Отчества", "patronymics")
        files_layout.addWidget(patronymics_widget)
        
        # Тренеры
        coaches_widget = self.create_file_selector("Тренеры", "coaches")
        files_layout.addWidget(coaches_widget)
        
        # Полные данные игроков
        players_widget = self.create_file_selector("Полные данные игроков", "players_full")
        files_layout.addWidget(players_widget)
        
        layout.addWidget(files_group)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("🚀 Начать импорт")
        self.import_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        self.import_btn.clicked.connect(self.start_import)
        
        skip_btn = QPushButton("⏭️ Пропустить")
        skip_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        skip_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.import_btn)
        btn_layout.addWidget(skip_btn)
        layout.addLayout(btn_layout)
        
        # Прогресс
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: green;")
        layout.addWidget(self.status_label)
    
    def create_file_selector(self, title, key):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        checkbox = QCheckBox(title)
        checkbox.stateChanged.connect(lambda state, k=key: self.on_checkbox_changed(k, state))
        layout.addWidget(checkbox)
        
        file_label = QLabel("Файл не выбран")
        file_label.setStyleSheet("color: gray;")
        layout.addWidget(file_label, 1)
        
        select_btn = QPushButton("Выбрать")
        select_btn.clicked.connect(lambda: self.select_file(key, file_label))
        layout.addWidget(select_btn)
        
        self.file_paths[key] = None
        widget.checkbox = checkbox
        widget.file_label = file_label
        
        return widget
    
    def on_checkbox_changed(self, key, state):
        self.import_data[key] = (state == Qt.Checked)
    
    def select_file(self, key, label):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Выберите CSV файл",
            "",
            "CSV files (*.csv);;All files (*.*)"
        )
        if file_path:
            self.file_paths[key] = file_path
            label.setText(os.path.basename(file_path))
            label.setStyleSheet("color: green;")
    
    def start_import(self):
        # Проверяем, выбраны ли файлы для импорта
        has_selected = False
        for key, selected in self.import_data.items():
            if selected and not self.file_paths.get(key):
                QMessageBox.warning(self, "Ошибка", 
                                   f"Для импорта '{key}' необходимо выбрать файл")
                return
            if selected and self.file_paths.get(key):
                has_selected = True
        
        if not has_selected:
            QMessageBox.warning(self, "Ошибка", "Не выбрано ни одного файла для импорта")
            return
        
        # Запускаем импорт
        self.import_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.import_thread = ImportThread(self.import_data, self.file_paths)
        self.import_thread.progress.connect(self.update_progress)
        self.import_thread.finished.connect(self.import_finished)
        self.import_thread.start()
    
    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def import_finished(self, success, message):
        self.progress_bar.setValue(100)
        if success:
            QMessageBox.information(self, "Успех", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", message)
            self.import_btn.setEnabled(True)