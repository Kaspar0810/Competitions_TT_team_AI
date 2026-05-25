# models_qt.py
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QDate
from PyQt5.QtWidgets import QMessageBox
from models import *
from datetime import datetime, date
from PyQt5.QtGui import QFont, QColor

class PlayersTableModel(QAbstractTableModel):
    """Модель для отображения игроков с нумерацией строк"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self._headers = ['№', 'ФИО', 'Дата рождения', 'Рейтинг', 
                        'Город', 'Регион', 'Разряд', 'Тренер']
    
    def setData(self, data):
        """Установка данных для отображения"""
        self.beginResetModel()
        self._data = data
        self.endResetModel()
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    
    def _format_date(self, date_value):
        """Безопасное форматирование даты"""
        if not date_value:
            return ""
        if isinstance(date_value, str):
            for fmt in ["%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d"]:
                try:
                    date_obj = datetime.strptime(date_value, fmt).date()
                    return date_obj.strftime("%d.%m.%Y")
                except:
                    continue
            return date_value
        elif isinstance(date_value, date):
            return date_value.strftime("%d.%m.%Y")
        return str(date_value)
    
    # В классе PlayersTableModel добавьте метод data для цвета фона:

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        col = index.column()
        row = index.row()
        
        # Номер строки
        if role == Qt.DisplayRole and col == 0:
            return str(row + 1)
        
        if role == Qt.DisplayRole:
            if row >= len(self._data):
                return None
            
            player = self._data[row]
            
            if col == 1:  # ФИО
                return player.get('fio', '') or player.get('player', '')
            elif col == 2:  # Дата рождения
                return self._format_date(player.get('birth_date', ''))
            elif col == 3:  # Рейтинг
                return str(player.get('rank', 0))
            elif col == 4:  # Город
                return player.get('city', '')
            elif col == 5:  # Регион
                return player.get('region', '')
            elif col == 6:  # Разряд
                return player.get('razryad', '')
            elif col == 7:  # Тренер
                return player.get('coach', '')
        
        # Цвет фона для предварительных заявок
        if role == Qt.BackgroundRole:
            if row < len(self._data):
                application = self._data[row].get('application', '')
                if application == "предварительная":
                    return QColor(240, 240, 240)  # Светло-серый
                elif application == "основная":
                    return QColor(255, 255, 255)  # Белый
                
        # Цвет фона для удаленных игроков
        if role == Qt.BackgroundRole:
            if row < len(self._data):
                is_deleted = self._data[row].get('is_deleted', False)
                if is_deleted:
                    return QColor(255, 220, 220)  # Светло-красный для удаленных
                
        # Выравнивание номера строки по центру
        if role == Qt.TextAlignmentRole and col == 0:
            return Qt.AlignCenter
        
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section < len(self._headers):
                return self._headers[section]
        return None
    
    def get_id(self, row):
        """Получение ID участника по строке"""
        if 0 <= row < len(self._data):
            return self._data[row].get('id')
        return None
    
    def get_fio(self, row):
        """Получение ФИО участника по строке"""
        if 0 <= row < len(self._data):
            return self._data[row].get('fio', '') or self._data[row].get('player', '')
        return None
    
class TeamsTableModel(QAbstractTableModel):
    """Модель для отображения команд"""
    
    def __init__(self, title_id=None, parent=None):
        super().__init__(parent)
        self._data = []
        self.title_id = title_id
        self._headers = ['ID', 'Название', 'Регион', 'Тренер', 'Сумма рейтинга']
        self.load_data()
    
    def load_data(self):
        try:
            query = Team.select().order_by(Team.r_sum.desc())
            if self.title_id:
                query = query.where(Team.title_id == self.title_id)
            self._data = list(query)
            self.layoutChanged.emit()
        except Exception as e:
            print(f"Ошибка загрузки команд: {e}")
            self._data = []
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        
        try:
            team = self._data[index.row()]
            col = index.column()
            
            if col == 0:
                return str(team.id)
            elif col == 1:
                return team.team_name or ""
            elif col == 2:
                return team.region or ""
            elif col == 3:
                return team.coach_team or ""
            elif col == 4:
                return str(team.r_sum) if team.r_sum else "0"
            
            return ""
        except Exception as e:
            print(f"Ошибка получения данных команды: {e}")
            return ""
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section < len(self._headers):
                return self._headers[section]
        return None

class ResultsTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self._headers = ['ID', 'Этап', 'Группа', 'Тур', 'Игрок 1', 'Игрок 2', 'Победитель', 'Счет', 'Очки']
    
    def setData(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        
        if index.row() >= len(self._data):
            return None
        
        item = self._data[index.row()]
        col = index.column()
        
        if col == 0:  # ID
            return str(item.get('id', ''))
        elif col == 1:  # Этап
            return item.get('stage', '')
        elif col == 2:  # Группа
            return item.get('group', '')
        elif col == 3:  # Тур
            return item.get('tour', '')
        elif col == 4:  # Игрок 1
            return item.get('player1', '')
        elif col == 5:  # Игрок 2
            return item.get('player2', '')
        elif col == 6:  # Победитель
            return item.get('winner', '')
        elif col == 7:  # Счет
            return item.get('score', '')
        elif col == 8:  # Очки
            return item.get('points', '')
        
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section < len(self._headers):
                return self._headers[section]
        return None

class DoublePlayersTableModel(QAbstractTableModel):
    """Модель для отображения пар игроков"""
    
    def __init__(self, title_id=None, parent=None):
        super().__init__(parent)
        self._data = []
        self.title_id = title_id
        self._headers = ['ID', 'Игрок 1', 'Игрок 2', 'Регион', 'Сумма рейтинга', 'Посев', 'Место']
        self.load_data()
    
    def load_data(self):
        try:
            query = Players_double.select().order_by(Players_double.r_sum.desc())
            if self.title_id:
                query = query.where(Players_double.title_id == self.title_id)
            self._data = list(query)
            self.layoutChanged.emit()
        except Exception as e:
            print(f"Ошибка загрузки пар: {e}")
            self._data = []
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        
        try:
            double = self._data[index.row()]
            col = index.column()
            
            if col == 0:
                return str(double.id)
            elif col == 1:
                return double.player_1 or ""
            elif col == 2:
                return double.player_2 or ""
            elif col == 3:
                return double.region_main or ""
            elif col == 4:
                return str(double.r_sum) if double.r_sum else "0"
            elif col == 5:
                return str(double.posev) if double.posev else ""
            elif col == 6:
                return str(double.mesto) if double.mesto else ""
            
            return ""
        except Exception as e:
            print(f"Ошибка получения данных пары: {e}")
            return ""
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section < len(self._headers):
                return self._headers[section]
        return None


class TitlesTableModel(QAbstractTableModel):
    """Модель для отображения соревнований"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self._headers = ['ID', 'Название', 'Дата начала', 'Дата окончания', 
                        'Место', 'Среди', 'Возраст', 'Тип']
        self.load_data()
    
    def _format_date(self, date_value):
        """Безопасное форматирование даты"""
        if not date_value:
            return ""
        if isinstance(date_value, str):
            for fmt in ["%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d"]:
                try:
                    date_obj = datetime.strptime(date_value, fmt).date()
                    return date_obj.strftime("%d.%m.%Y")
                except:
                    continue
            return date_value
        elif isinstance(date_value, date):
            return date_value.strftime("%d.%m.%Y")
        return str(date_value)
    
    def load_data(self):
        try:
            self._data = list(Title.select().order_by(Title.data_start.desc()))
            self.layoutChanged.emit()
        except Exception as e:
            print(f"Ошибка загрузки соревнований: {e}")
            self._data = []
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        
        try:
            title = self._data[index.row()]
            col = index.column()
            
            if col == 0:
                return str(title.id)
            elif col == 1:
                return title.name or ""
            elif col == 2:
                return self._format_date(title.data_start)
            elif col == 3:
                return self._format_date(title.data_end)
            elif col == 4:
                return title.mesto or ""
            elif col == 5:
                return title.sredi or ""
            elif col == 6:
                return title.vozrast or ""
            elif col == 7:
                return title.vid_turnira or ""
            
            return ""
        except Exception as e:
            print(f"Ошибка получения данных соревнования: {e}")
            return ""
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section < len(self._headers):
                return self._headers[section]
        return None


class CoachesTableModel(QAbstractTableModel):
    """Модель для отображения тренеров"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self._headers = ['ID', 'Тренер']
        self.load_data()
    
    def load_data(self):
        try:
            self._data = list(Coach.select().order_by(Coach.coach))
            self.layoutChanged.emit()
        except Exception as e:
            print(f"Ошибка загрузки тренеров: {e}")
            self._data = []
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        
        try:
            coach = self._data[index.row()]
            col = index.column()
            
            if col == 0:
                return str(coach.id)
            elif col == 1:
                return coach.coach or ""
            
            return ""
        except Exception as e:
            print(f"Ошибка получения данных тренера: {e}")
            return ""
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section < len(self._headers):
                return self._headers[section]
        return None