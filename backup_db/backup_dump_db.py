import os
import sys
import datetime
import subprocess
import platform
from PyQt5.QtCore import QThread, pyqtSignal

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
        
    def stop(self):
        """Остановка процесса"""
        self.is_running = False
    
    def run(self):
        """Выполнение бэкапа"""
        try:
            self.progress_updated.emit(0, "Проверка директории для бэкапа...")
            
            # Проверяем и создаем директорию если нужно
            if not os.path.exists(self.backup_path):
                try:
                    os.makedirs(self.backup_path)
                    self.progress_updated.emit(10, f"Создана директория: {self.backup_path}")
                except Exception as e:
                    self.backup_finished.emit(False, f"Не удалось создать директорию: {e}", "")
                    return
            
            # Формируем имя файла
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_file = os.path.join(self.backup_path, f"{self.database}_{timestamp}.sql")
            
            self.progress_updated.emit(20, f"Файл бэкапа: {os.path.basename(backup_file)}")
            
            # Формируем команду mysqldump
            dump_command = self.build_mysqldump_command(backup_file)
            
            self.progress_updated.emit(40, "Выполнение mysqldump...")
            
            # Выполняем команду
            success, error_msg = self.execute_backup(dump_command)
            
            if not success:
                self.backup_finished.emit(False, f"Ошибка при создании бэкапа: {error_msg}", "")
                return
            
            # Проверяем размер файла
            if os.path.exists(backup_file):
                file_size = os.path.getsize(backup_file)
                if file_size == 0:
                    self.backup_finished.emit(False, "Создан пустой файл бэкапа", "")
                    return
                
                self.progress_updated.emit(70, f"Бэкап создан. Размер: {self.format_size(file_size)}")
            else:
                self.backup_finished.emit(False, "Файл бэкапа не создан", "")
                return
            
            # Сжатие если нужно
            if self.compress:
                self.progress_updated.emit(80, "Сжатие бэкапа...")
                compressed_file = self.compress_backup(backup_file)
                if compressed_file:
                    backup_file = compressed_file
                    self.progress_updated.emit(90, f"Сжатие завершено. Размер: {self.format_size(os.path.getsize(backup_file))}")
                else:
                    self.backup_finished.emit(False, "Ошибка при сжатии бэкапа", "")
                    return
            
            self.progress_updated.emit(100, "Бэкап успешно создан!")
            self.backup_finished.emit(True, f"Бэкап создан: {os.path.basename(backup_file)}", backup_file)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.backup_finished.emit(False, f"Ошибка: {str(e)}", "")
    
    def build_mysqldump_command(self, backup_file):
        """Формирование команды mysqldump"""
        # Базовые параметры
        cmd = [
            'mysqldump',
            f'--host={self.host}',
            f'--port={self.port}',
            f'--user={self.username}',
            f'--password={self.password}',
            '--no-tablespaces',
            '--single-transaction',  # Для целостности данных
            '--routines',           # Включаем хранимые процедуры
            '--triggers',           # Включаем триггеры
            '--default-character-set=utf8mb4',
            self.database
        ]
        
        # В Windows используем другой синтаксис для перенаправления
        if platform.system() == 'Windows':
            cmd_str = ' '.join(cmd) + f' > "{backup_file}" 2>nul'
        else:
            cmd_str = ' '.join(cmd) + f' > "{backup_file}" 2>/dev/null'
        
        return cmd_str
    
    def execute_backup(self, command):
        """Выполнение команды бэкапа"""
        try:
            # Запускаем процесс
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            # Ждем завершения с возможностью остановки
            while process.poll() is None:
                if not self.is_running:
                    process.terminate()
                    return False, "Бэкап отменен пользователем"
            
            # Проверяем результат
            if process.returncode != 0:
                stderr = process.stderr.read()
                return False, f"mysqldump завершился с ошибкой: {stderr}"
            
            return True, "Успешно"
            
        except FileNotFoundError:
            return False, "mysqldump не найден. Убедитесь, что MySQL установлен."
        except Exception as e:
            return False, str(e)
    
    def compress_backup(self, backup_file):
        """Сжатие бэкапа в ZIP"""
        try:
            import zipfile
            
            zip_file = backup_file + '.zip'
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(backup_file, os.path.basename(backup_file))
            
            # Удаляем исходный файл
            os.remove(backup_file)
            
            return zip_file
            
        except Exception as e:
            print(f"Ошибка сжатия: {e}")
            return None
    
    def format_size(self, size):
        """Форматирование размера файла"""
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} ТБ"


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


# Пример использования:
if __name__ == "__main__":
    # Настройки подключения
    backup_file = backup_mysql_database(
        host='localhost',
        port=3306,
        username='root',
        password='db_pass',
        database='mysql_db',
        backup_path='./backup_db',
        compress=True  # Создать сжатый бэкап
    )
    
    if backup_file:
        print(f"Бэкап сохранен: {backup_file}")
    else:
        print("Не удалось создать бэкап")