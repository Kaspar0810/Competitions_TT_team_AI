import os
import sys
import datetime
import subprocess
import platform
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox

class BackupThread(QThread):
    """Поток для создания бэкапа MySQL"""
    
    progress_updated = pyqtSignal(int, str)
    backup_finished = pyqtSignal(bool, str, str)  # успех, сообщение, путь к файлу
    
    def __init__(self, host, port, username, password, database, backup_path, compress=False):
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.backup_path = backup_path
        self.compress = compress
        self.is_running = True
        
def backup_mysql_database(host, port, username, password, database, backup_path, compress=False):
    """
    Улучшенная версия функции бэкапа
    
    Args:
        host: Хост MySQL
        port: Порт MySQL
        username: Имя пользователя
        password: Пароль
        database: Имя базы данных
        backup_path: Путь для сохранения бэкапа
        compress: Сжимать ли бэкап (True/False)
    
    Returns:
        str: Путь к созданному файлу бэкапа
    """
    
    # Проверяем и создаем директорию если нужно
    if not os.path.exists(backup_path):
        try:
            os.makedirs(backup_path)
            print(f"Создана директория: {backup_path}")
        except Exception as e:
            print(f"Ошибка создания директории: {e}")
            return None
    
    # Формируем имя файла
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = os.path.join(backup_path, f"{database}_{timestamp}.sql")
    
    # Формируем команду
    if platform.system() == 'Windows':
        redirect = '2>nul'
    else:
        redirect = '2>/dev/null'
    
    dump_command = (
        f'mysqldump --no-tablespaces '
        f'--host={host} --port={port} '
        f'--user={username} --password={password} '
        f'--single-transaction --routines --triggers '
        f'--default-character-set=utf8mb4 '
        f'{database} > "{backup_file}" {redirect}'
    )
    
    print(f"Выполняется бэкап: {backup_file}")
    
    try:
        # Выполняем команду
        result = subprocess.run(dump_command, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Ошибка выполнения mysqldump: {result.stderr}")
            return None
        
        # Проверяем созданный файл
        if os.path.exists(backup_file) and os.path.getsize(backup_file) > 0:
            size = os.path.getsize(backup_file)
            print(f"Бэкап создан: {backup_file} (Размер: {format_size(size)})")
            
            # Сжатие если нужно
            if compress:
                import zipfile
                zip_file = backup_file + '.zip'
                with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(backup_file, os.path.basename(backup_file))
                os.remove(backup_file)
                print(f"Бэкап сжат: {zip_file}")
                return zip_file
            
            return backup_file
        else:
            print("Ошибка: файл бэкапа не создан или пуст")
            return None
            
    except FileNotFoundError:
        print("Ошибка: mysqldump не найден. Установите MySQL client.")
        return None
    except Exception as e:
        print(f"Ошибка: {e}")
        return None


def format_size(size):
    """Форматирование размера файла"""
    for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} ТБ"

def run_backup_db(self=True):
    """запуск backup db"""
    # Настройки подключения
    backup_file = backup_mysql_database(
        host='localhost',
        port=3306,
        username='root',
        password='db_pass',
        database='mysql_db',
        backup_path='./backup_db'
        # compress=False  # Создать сжатый бэкап
    )
    
    if backup_file:
        QMessageBox.information(
            self,
            "Успех",
            f"✅ Бэкап базы данных успешно создан!\n\n"
            f"📁 Файл: {os.path.basename(backup_file)}\n"
            f"📂 Путь: {os.path.dirname(backup_file)}"
        )
        self.status_label.setText("✓ Бэкап создан успешно")
    else:
        print("Не удалось создать бэкап")

