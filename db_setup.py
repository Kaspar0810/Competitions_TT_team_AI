# db_setup.py или в начале main_AI.py
import sys
import os
import subprocess
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QLineEdit, QFormLayout, QHBoxLayout
from PyQt5.QtCore import Qt
from models import db, Title  # импортируйте вашу БД и модели

def check_database_connection():
    """Проверяет подключение к БД и наличие таблиц."""
    try:
        db.connect()
        # Проверяем, существует ли хотя бы одна таблица
        db.execute_sql('SELECT 1')
        # Проверяем, есть ли таблицы (например, Title)
        if Title.table_exists():
            return True
        else:
            # Таблицы не созданы, но подключение есть
            return True
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        return False
    finally:
        if not db.is_closed():
            db.close()

def run_mysql_installer():
    """Запускает диалог выбора установщика MySQL и запускает его."""
    installer_path, _ = QFileDialog.getOpenFileName(
        None,
        "Выберите установщик MySQL",
        os.path.expanduser("~"),
        "Executable files (*.exe *.msi);;All files (*.*)"
    )
    if installer_path:
        try:
            # Запускаем установщик
            subprocess.Popen([installer_path])
            QMessageBox.information(None, "Установка MySQL", 
                                    "Установщик MySQL запущен.\n"
                                    "После завершения установки перезапустите приложение.")
            return True
        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось запустить установщик: {e}")
            return False
    return False

def get_mysql_credentials():
    """Диалог для ввода логина и пароля MySQL."""
    dialog = QDialog()
    dialog.setWindowTitle("Настройка подключения к MySQL")
    layout = QVBoxLayout(dialog)
    layout.addWidget(QLabel("Введите данные для подключения к MySQL:"))
    
    form = QFormLayout()
    login_edit = QLineEdit()
    login_edit.setText("root")
    password_edit = QLineEdit()
    password_edit.setEchoMode(QLineEdit.Password)
    form.addRow("Логин:", login_edit)
    form.addRow("Пароль:", password_edit)
    layout.addLayout(form)
    
    btn_layout = QHBoxLayout()
    ok_btn = QPushButton("Подключиться")
    cancel_btn = QPushButton("Отмена")
    btn_layout.addWidget(ok_btn)
    btn_layout.addWidget(cancel_btn)
    layout.addLayout(btn_layout)
    
    result = None
    def on_ok():
        nonlocal result
        result = (login_edit.text(), password_edit.text())
        dialog.accept()
    ok_btn.clicked.connect(on_ok)
    cancel_btn.clicked.connect(dialog.reject)
    
    if dialog.exec_() == QDialog.Accepted:
        return result
    return None

def setup_database():
    """Основная функция настройки БД при запуске."""
    if check_database_connection():
        return True
    
    # Нет подключения
    reply = QMessageBox.question(
        None,
        "База данных не найдена",
        "Не удалось подключиться к MySQL.\n\n"
        "Установить MySQL сейчас?",
        QMessageBox.Yes | QMessageBox.No
    )
    if reply == QMessageBox.Yes:
        # Предлагаем выбрать установщик
        if run_mysql_installer():
            # После установки просим перезапустить приложение
            QMessageBox.information(None, "Перезапуск", 
                                    "После установки MySQL нажмите ОК для продолжения.\n"
                                    "Если установка не завершена, приложение будет закрыто.")
            # Пробуем снова подключиться
            if check_database_connection():
                return True
            else:
                # Запрашиваем логин/пароль
                creds = get_mysql_credentials()
                if creds:
                    # Обновляем параметры подключения в models.py
                    from models import update_db_credentials
                    update_db_credentials(creds[0], creds[1])
                    if check_database_connection():
                        return True
        else:
            QMessageBox.critical(None, "Ошибка", "Установка MySQL не выполнена.")
    else:
        QMessageBox.critical(None, "Ошибка", "Приложение не может работать без MySQL.\n"
                             "Установите MySQL и настройте подключение, затем перезапустите программу.")
    return False