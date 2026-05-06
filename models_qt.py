# models_qt.py
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QDate
from PyQt5.QtWidgets import QMessageBox
from models import *
from datetime import datetime, date

class PlayersTableModel(QAbstractTableModel):
    """Модель для отображения игроков"""
    
    def __init__(self, title_id=None, sex=None, parent=None):
        super().__init__(parent)
        self._data = []
        self.title_id = title_id
        self.sex = sex
        self._headers = ['ID', 'ФИО', 'Отчество', 'Дата рождения', 'Рейтинг', 
                        'Город', 'Регион', 'Разряд', 'Тренер']
        self.load_data()
    
    def load_data(self):
        try:
            query = Player.select().order_by(Player.rank)
            if self.title_id:
                query = query.where(Player.title_id == self.title_id)
            if self.sex:
                query = query.where(Player.sex == self.sex)
            self._data = list(query)
            self.layoutChanged.emit()
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            self._data = []
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    
    def _format_date(self, date_value):
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
    
    def _get_patronymic_text(self, patronymic_id):
        if not patronymic_id:
            return ""
        try:
            patronymic = Patronymic.get_or_none(Patronymic.id == patronymic_id)
            return patronymic.patronymic if patronymic else ""
        except:
            return ""
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        col = index.column()
        row = index.row()
        
        # Для отображения номера строки (заменяем ID)
        if role == Qt.DisplayRole:
            if col == 0:
                return str(row + 1)  # Нумерация строк с 1
            elif col == 1:
                return self._data[row].player or ""
            elif col == 2:
                return self._get_patronymic_text(self._data[row].patronymic_id)
            elif col == 3:
                return self._format_date(self._data[row].bday)
            elif col == 4:
                return str(self._data[row].rank) if self._data[row].rank else "0"
            elif col == 5:
                return self._data[row].city or ""
            elif col == 6:
                return self._data[row].region or ""
            elif col == 7:
                return self._data[row].razryad or ""
            elif col == 8:
                if self._data[row].coach_id:
                    return self._data[row].coach_id.coach or ""
                return ""
        
        # Для выравнивания по центру номеров строк
        if role == Qt.TextAlignmentRole and col == 0:
            return Qt.AlignCenter
        
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            headers = ['№', 'ФИО', 'Отчество', 'Дата рождения', 'Рейтинг', 
                      'Город', 'Регион', 'Разряд', 'Тренер']
            if section < len(headers):
                return headers[section]
        return None
    
    def get_player(self, row):
        if 0 <= row < len(self._data):
            return self._data[row]
        return None
    
    def add_player(self, data):
        try:
            if 'bday' in data and hasattr(data['bday'], 'toPyDate'):
                data['bday'] = data['bday'].toPyDate()
            player = Player.create(**data)
            self.load_data()
            return player.id
        except Exception as e:
            print(f"Ошибка добавления: {e}")
            return None
    
    def delete_player(self, player_id):
        try:
            Player.delete().where(Player.id == player_id).execute()
            self.load_data()
            return True
        except Exception as e:
            print(f"Ошибка удаления: {e}")
            return False

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
    """Модель для отображения результатов"""
    
    def __init__(self, title_id=None, parent=None):
        super().__init__(parent)
        self._data = []
        self.title_id = title_id
        self._headers = ['ID', 'Этап', 'Группа', 'Игрок 1', 'Игрок 2', 
                        'Победитель', 'Счёт', 'Раунд']
        self.load_data()
    
    def load_data(self):
        try:
            query = Result.select().order_by(Result.id)
            if self.title_id:
                query = query.where(Result.title_id == self.title_id)
            self._data = list(query)
            self.layoutChanged.emit()
        except Exception as e:
            print(f"Ошибка загрузки результатов: {e}")
            self._data = []
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        
        try:
            result = self._data[index.row()]
            col = index.column()
            
            if col == 0:
                return str(result.id)
            elif col == 1:
                return result.system_stage or ""
            elif col == 2:
                return result.number_group or ""
            elif col == 3:
                return result.player1 or ""
            elif col == 4:
                return result.player2 or ""
            elif col == 5:
                return result.winner or ""
            elif col == 6:
                return result.score_in_game or ""
            elif col == 7:
                return result.round or ""
            
            return ""
        except Exception as e:
            print(f"Ошибка получения данных результата: {e}")
            return ""
    
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