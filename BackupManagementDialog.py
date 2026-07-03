import os
import datetime
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QLabel, QFileDialog, QMessageBox, QSpinBox,
                             QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal


class BackupManagementDialog(QDialog):
    """Диалог для управления бэкапами"""
    
    # Сигнал, который можно использовать для обновления главного окна (опционально)
    backups_deleted = pyqtSignal()
    
    def __init__(self, parent=None, backup_dir="backup_db"):
        super().__init__(parent)
        self.backup_dir = backup_dir
        self.setWindowTitle("Управление бэкапами")
        self.setMinimumSize(700, 500)
        self.init_ui()
        self.refresh_backup_list()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Верхняя панель
        top_layout = QHBoxLayout()
        
        self.dir_label = QLabel(f"Папка: {self.backup_dir}")
        top_layout.addWidget(self.dir_label)
        
        self.change_dir_btn = QPushButton("Выбрать папку")
        self.change_dir_btn.clicked.connect(self.change_directory)
        top_layout.addWidget(self.change_dir_btn)
        
        top_layout.addStretch()
        
        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.clicked.connect(self.refresh_backup_list)
        top_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(top_layout)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Имя файла", "Размер", "Дата изменения", "Дней", "Путь"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        layout.addWidget(self.table)
        
        # Панель действий
        actions_layout = QHBoxLayout()
        
        # Группа выделения
        select_group = QHBoxLayout()
        self.select_all_btn = QPushButton("Выбрать все")
        self.select_all_btn.clicked.connect(self.select_all)
        select_group.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("Снять выделение")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        select_group.addWidget(self.deselect_all_btn)
        actions_layout.addLayout(select_group)
        
        actions_layout.addStretch()
        
        # Удаление
        self.delete_selected_btn = QPushButton("Удалить выбранные")
        self.delete_selected_btn.clicked.connect(self.delete_selected)
        self.delete_selected_btn.setStyleSheet("background-color: #f44336; color: white;")
        actions_layout.addWidget(self.delete_selected_btn)
        
        # Удаление старых
        self.old_layout = QHBoxLayout()
        self.old_layout.addWidget(QLabel("Старше:"))
        self.days_spin = QSpinBox()
        self.days_spin.setRange(1, 365)
        self.days_spin.setValue(3)
        self.old_layout.addWidget(self.days_spin)
        self.old_layout.addWidget(QLabel("дней"))
        
        self.delete_old_btn = QPushButton("Удалить старые")
        self.delete_old_btn.clicked.connect(self.delete_old_backups)
        self.delete_old_btn.setStyleSheet("background-color: #ff9800; color: white;")
        self.old_layout.addWidget(self.delete_old_btn)
        actions_layout.addLayout(self.old_layout)
        
        actions_layout.addStretch()
        
        self.open_folder_btn = QPushButton("Открыть папку")
        self.open_folder_btn.clicked.connect(self.open_backup_folder)
        actions_layout.addWidget(self.open_folder_btn)
        
        # Кнопка закрытия
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.accept)
        actions_layout.addWidget(self.close_btn)
        
        layout.addLayout(actions_layout)
        
        # Статус
        self.status_label = QLabel("Готов")
        layout.addWidget(self.status_label)
    
    def change_directory(self):
        """Выбор другой папки"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку с бэкапами",
            self.backup_dir
        )
        if dir_path:
            self.backup_dir = dir_path
            self.dir_label.setText(f"Папка: {self.backup_dir}")
            self.refresh_backup_list()
    
    def refresh_backup_list(self):
        """Обновление списка бэкапов"""
        if not os.path.exists(self.backup_dir):
            self.status_label.setText(f"Папка {self.backup_dir} не существует")
            self.table.setRowCount(0)
            return
        
        files = []
        for filename in os.listdir(self.backup_dir):
            filepath = os.path.join(self.backup_dir, filename)
            if os.path.isfile(filepath):
                if filename.lower().endswith(('.sql', '.zip', '.gz', '.7z')):
                    stat = os.stat(filepath)
                    mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                    size = stat.st_size
                    days_old = (datetime.datetime.now() - mtime).days
                    files.append((filename, size, mtime, days_old, filepath))
        
        files.sort(key=lambda x: x[2], reverse=True)  # сортируем по дате (новые сверху)
        
        self.table.setRowCount(len(files))
        for row, (filename, size, mtime, days_old, filepath) in enumerate(files):
            # Имя
            item = QTableWidgetItem(filename)
            item.setData(Qt.UserRole, filepath)
            self.table.setItem(row, 0, item)
            # Размер
            self.table.setItem(row, 1, QTableWidgetItem(self.format_size(size)))
            # Дата
            self.table.setItem(row, 2, QTableWidgetItem(mtime.strftime("%Y-%m-%d %H:%M:%S")))
            # Дней
            days_item = QTableWidgetItem(str(days_old))
            if days_old >= self.days_spin.value():
                days_item.setBackground(Qt.red)
                days_item.setForeground(Qt.white)
            self.table.setItem(row, 3, days_item)
            # Полный путь (скрытый столбец)
            self.table.setItem(row, 4, QTableWidgetItem(filepath))
        
        self.table.resizeColumnToContents(4)  # скрываем путь, но можно показать
        self.table.setColumnHidden(4, True)   # скрываем столбец с путём
        
        self.status_label.setText(f"Найдено {len(files)} файлов")
    
    def format_size(self, size):
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} ТБ"
    
    def select_all(self):
        self.table.selectAll()
    
    def deselect_all(self):
        self.table.clearSelection()
    
    def get_selected_files(self):
        """Получить список путей выбранных файлов"""
        selected = []
        for item in self.table.selectedItems():
            if item.column() == 0:  # только первая колонка
                filepath = item.data(Qt.UserRole)
                if filepath:
                    selected.append(filepath)
        return selected
    
    def delete_selected(self):
        selected = self.get_selected_files()
        if not selected:
            QMessageBox.information(self, "Информация", "Не выбрано ни одного файла")
            return
        
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить {len(selected)} выбранных файлов?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        
        deleted = 0
        errors = []
        for filepath in selected:
            try:
                os.remove(filepath)
                deleted += 1
            except Exception as e:
                errors.append(f"{os.path.basename(filepath)}: {str(e)}")
        
        if errors:
            QMessageBox.warning(
                self,
                "Ошибки при удалении",
                f"Удалено {deleted} файлов\n\nОшибки:\n" + "\n".join(errors)
            )
        else:
            QMessageBox.information(self, "Успех", f"Удалено {deleted} файлов")
        
        self.refresh_backup_list()
        self.backups_deleted.emit()  # сигнал, если нужно обновить что-то в главном окне
    
    def delete_old_backups(self):
        days = self.days_spin.value()
        old_files = []
        for row in range(self.table.rowCount()):
            days_item = self.table.item(row, 3)
            if days_item:
                days_old = int(days_item.text())
                if days_old >= days:
                    filepath = self.table.item(row, 0).data(Qt.UserRole)
                    if filepath:
                        old_files.append(filepath)
        
        if not old_files:
            QMessageBox.information(self, "Информация", f"Нет файлов старше {days} дней")
            return
        
        files_list = "\n".join([os.path.basename(f) for f in old_files[:10]])
        if len(old_files) > 10:
            files_list += f"\n... и еще {len(old_files) - 10} файлов"
        
        reply = QMessageBox.question(
            self,
            f"Удалить бэкапы старше {days} дней",
            f"Найдено {len(old_files)} файлов старше {days} дней.\n\n"
            f"Файлы:\n{files_list}\n\n"
            f"Удалить их?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        
        deleted = 0
        for filepath in old_files:
            try:
                os.remove(filepath)
                deleted += 1
            except:
                pass
        
        QMessageBox.information(self, "Готово", f"Удалено {deleted} файлов")
        self.refresh_backup_list()
        self.backups_deleted.emit()
    
    def open_backup_folder(self):
        if not os.path.exists(self.backup_dir):
            QMessageBox.warning(self, "Ошибка", f"Папка {self.backup_dir} не существует")
            return
        
        import subprocess
        import platform
        if platform.system() == 'Windows':
            os.startfile(self.backup_dir)
        else:
            subprocess.Popen(['xdg-open', self.backup_dir])