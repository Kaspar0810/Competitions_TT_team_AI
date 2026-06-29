import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from models import *
from models import db

class ChoiceGroupAuto:
    """
    Автоматическая жеребьевка групп
    """
    def __init__(self, athletes, num_groups, id_title, parent=None):
        self.athletes = athletes
        self.num_groups = num_groups
        self.id_title = id_title
        self.parent = parent
        self.sorted_athletes = []
        self.groups = []
        self.current_athlete_index = 0
        self.max_rows_per_group = 0
        self.current_round = 1
        
    def calculate_max_rows(self):
        """Расчет максимального количества строк в группе"""
        total_athletes = len(self.athletes)
        self.max_rows_per_group = (total_athletes + self.num_groups - 1) // self.num_groups
        if self.max_rows_per_group < 1:
            self.max_rows_per_group = 1
            
    def get_current_round(self):
        """Определение текущего раунда на основе количества размещенных спортсменов"""
        placed_count = self.current_athlete_index
        
        if placed_count == 0:
            return 1
        
        if placed_count <= self.num_groups:
            return 1
        else:
            round_num = (placed_count - 1) // self.num_groups + 1
            return round_num
    
    def get_group_players_count(self, group_idx):
        """Получить количество игроков в группе"""
        if group_idx < len(self.groups):
            return len([a for a in self.groups[group_idx] if a is not None])
        return 0
    
    def find_next_group_for_seed(self, current_group_for_seed):
        """Найти следующую группу для посева (с наименьшим количеством игроков)"""
        groups_info = []
        for g in range(self.num_groups):
            count = self.get_group_players_count(g)
            groups_info.append((g, count))
        
        if not groups_info:
            return 0
            
        min_count = min(count for _, count in groups_info)
        min_groups = [g for g, count in groups_info if count == min_count]
        
        current_round = self.get_current_round()
        if current_round % 2 == 1:
            for g in min_groups:
                if g >= current_group_for_seed:
                    return g
            return min_groups[0]
        else:
            for g in reversed(min_groups):
                if g <= current_group_for_seed:
                    return g
            return min_groups[-1]
    
    def check_conflicts(self, athlete, group_idx):
        """Проверка конфликтов"""
        if group_idx >= len(self.groups):
            return False, False
            
        _, _, _, region, coach = athlete
        
        group_regions = [a[3] for a in self.groups[group_idx] if a]
        group_coaches = [a[4] for a in self.groups[group_idx] if a]
        
        region_conflict = region in group_regions
        coach_conflict = coach in group_coaches and region_conflict
        
        return region_conflict, coach_conflict
    
    def find_available_cell(self, athlete, start_group=0):
        """Найти доступную ячейку для спортсмена"""
        # Проходим по всем группам, начиная с start_group
        for g_idx in range(start_group, self.num_groups):
            group = self.groups[g_idx]
            
            # Проверяем, есть ли свободное место в группе
            if len(group) < self.max_rows_per_group:
                # Проверяем конфликты
                region_conflict, coach_conflict = self.check_conflicts(athlete, g_idx)
                
                # Если конфликт тренера - пропускаем группу
                if coach_conflict:
                    continue
                
                # Если конфликт региона - спрашиваем (в автоматическом режиме пропускаем)
                if region_conflict:
                    # В автоматическом режиме ищем другую группу
                    continue
                
                # Возвращаем первую свободную позицию
                for row in range(self.max_rows_per_group):
                    if row >= len(group) or group[row] is None:
                        return g_idx, row
        
        # Если не нашли подходящую группу, ищем с учетом конфликта региона (разрешаем)
        for g_idx in range(start_group, self.num_groups):
            group = self.groups[g_idx]
            
            if len(group) < self.max_rows_per_group:
                region_conflict, coach_conflict = self.check_conflicts(athlete, g_idx)
                
                if coach_conflict:
                    continue
                
                for row in range(self.max_rows_per_group):
                    if row >= len(group) or group[row] is None:
                        return g_idx, row
        
        # Если совсем нет места - возвращаем None
        return None, None
    
    def place_athlete(self, athlete, group_idx, row):
        """Разместить спортсмена в группе"""
        while len(self.groups[group_idx]) <= row:
            self.groups[group_idx].append(None)
        self.groups[group_idx][row] = athlete
        self.current_athlete_index += 1
    
    def run(self):
        """Запуск автоматической жеребьевки"""
        # Сортируем спортсменов по рейтингу (убывание)
        self.sorted_athletes = sorted(self.athletes, key=lambda x: x[2], reverse=True)
        
        # Инициализируем группы
        self.groups = [[] for _ in range(self.num_groups)]
        self.current_athlete_index = 0
        self.calculate_max_rows()
        
        # Заполняем первые номера групп
        for i in range(min(self.num_groups, len(self.sorted_athletes))):
            self.groups[i] = [self.sorted_athletes[i]]
            self.current_athlete_index += 1
        
        # Определяем начальную группу для продолжения (последняя группа)
        current_group_for_seed = self.num_groups - 1
        
        # Продолжаем заполнение оставшихся спортсменов
        while self.current_athlete_index < len(self.sorted_athletes):
            athlete = self.sorted_athletes[self.current_athlete_index]
            
            # Ищем доступную ячейку
            group_idx, row = self.find_available_cell(athlete, 0)
            
            if group_idx is not None:
                self.place_athlete(athlete, group_idx, row)
                
                # Если разместили в текущей группе, переходим к следующей
                if group_idx == current_group_for_seed:
                    current_group_for_seed = self.find_next_group_for_seed(current_group_for_seed)
            else:
                # Если не нашли подходящую ячейку, размещаем в первую свободную
                placed = False
                for g_idx in range(self.num_groups):
                    if len(self.groups[g_idx]) < self.max_rows_per_group:
                        region_conflict, coach_conflict = self.check_conflicts(athlete, g_idx)
                        if not coach_conflict:  # Только если нет конфликта тренера
                            for row in range(self.max_rows_per_group):
                                if row >= len(self.groups[g_idx]) or self.groups[g_idx][row] is None:
                                    self.place_athlete(athlete, g_idx, row)
                                    placed = True
                                    break
                            if placed:
                                break
                
                if not placed:
                    # Если все равно не разместили - размещаем в первую свободную ячейку
                    for g_idx in range(self.num_groups):
                        if len(self.groups[g_idx]) < self.max_rows_per_group:
                            for row in range(self.max_rows_per_group):
                                if row >= len(self.groups[g_idx]) or self.groups[g_idx][row] is None:
                                    self.place_athlete(athlete, g_idx, row)
                                    placed = True
                                    break
                            if placed:
                                break
        
        # Формируем результаты
        results = []
        for group_idx, group in enumerate(self.groups):
            gr = group_idx + 1
            for seed_num, athlete in enumerate(group, 1):
                if athlete:
                    results.append({
                        'seed_num': seed_num,
                        'id_player': athlete[0],
                        'name': athlete[1],
                        'region': athlete[3],
                        'group': gr
                    })
        
        return results


def clear_db_before_choice(title_id):
    """очищает базу данных -Game_list- и -Result- перед повторной жеребьевкой групп"""
    try:
        system = System.select().where((System.stage == "Квалификация") & (System.title_id == title_id)).get()
        id_system = system.id

        # Удаляем Game_list
        gamelist = Game_list.select().where((Game_list.title_id == title_id) & (Game_list.system_id == id_system))
        for i in gamelist:
            i.delete_instance()
        
        # Удаляем Result
        results = Result.select().where((Result.title_id == title_id) & (Result.system_id == id_system))
        for i in results:
            i.delete_instance()
        
        # Обновляем Choice
        choice = Choice.select().where(Choice.title_id == title_id)
        for i in choice:
            Choice.update(group=None, posev_group=None).where(Choice.id == i.id).execute()
            
        # Обновляем флаг выбора в System
        System.update(choice_flag=False).where(System.id == id_system).execute()
        
    except Exception as e:
        print(f"Ошибка при очистке БД: {e}")


def save_choice_results(results, title_id):
    """Сохранение результатов жеребьевки в базу данных"""
    try:
        # Получаем систему
        system = System.select().where((System.stage == "Квалификация") & (System.title_id == title_id)).get()
        id_system = system.id
        
        # Очищаем старые данные Choice
        Choice.delete().where(Choice.title_id == title_id).execute()
        
        # Сохраняем новые результаты
        for result in results:
            Choice.create(
                title_id=title_id,
                system_id=id_system,
                player_choice_id=result['id_player'],
                group=f"Группа {result['group']}",
                posev_group=result['seed_num']
            )
        
        # Обновляем флаг выбора в System
        System.update(choice_flag=True).where(System.id == id_system).execute()
        
        return True
    except Exception as e:
        print(f"Ошибка при сохранении результатов: {e}")
        return False


def choice_group_auto(athletes, num_groups, id_title, parent=None):
    """
    Функция для автоматической жеребьевки
    
    Args:
        athletes: список списков [id игрока, фамилия_имя, рейтинг, регион, тренер]
        num_groups: количество групп (от 2 до 32)
        id_title: ID турнира
        parent: родительское окно
    
    Returns:
        list: список результатов или None если ошибка
    """
    if num_groups < 2 or num_groups > 48:
        raise ValueError("Количество групп должно быть от 2 до 48")
    
    try:
        # Проверяем наличие системы
        if num_groups == 1:
            system = System.select().where((System.title_id == id_title) & (System.stage == "Одна таблица")).get()
        else:
            system = System.select().where((System.title_id == id_title) & (System.stage == "Квалификация")).get()
        
        check_flag = system.choice_flag
        
        # Если есть существующая жеребьевка
        if check_flag:
            reply = QMessageBox.question(parent, 'Подтверждение',
                'В базе данных уже есть результаты жеребьевки.\n'
                'Перезаписать существующие результаты?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.No:
                return None
            
            # Очищаем старые данные
            clear_db_before_choice(id_title)
        
        # Запускаем автоматическую жеребьевку
        auto_draw = ChoiceGroupAuto(athletes, num_groups, id_title, parent)
        results = auto_draw.run()
        
        if results:
            # Сохраняем результаты
            if save_choice_results(results, id_title):
                QMessageBox.information(parent, "Успех", 
                    f"Автоматическая жеребьевка завершена!\n"
                    f"Распределено {len(results)} спортсменов по {num_groups} группам.")
                return results
            else:
                QMessageBox.warning(parent, "Ошибка", "Не удалось сохранить результаты в базу данных.")
                return None
        else:
            QMessageBox.warning(parent, "Ошибка", "Не удалось выполнить жеребьевку.")
            return None
            
    except Exception as e:
        QMessageBox.warning(parent, "Ошибка", f"Ошибка при автоматической жеребьевке:\n{str(e)}")
        return None


def choice_group_manual(self, athletes, num_groups, id_title, parent=None):
    """
    Функция для вызова ручной жеребьевки
    
    Args:
        athletes: список списков [id игрока, фамилия_имя, рейтинг, регион, тренер]
        num_groups: количество групп (от 2 до 32)
        parent: родительское окно
    
    Returns:
        list: список результатов или None если отмена
    """
    if num_groups < 2 or num_groups > 48:
        raise ValueError("Количество групп должно быть от 2 до 48")

    existing_data = None
    try:
        if num_groups == 1:
            system = System.select().where((System.title_id == id_title) & (System.stage == "Одна таблица")).get()
        else:
            system = System.select().where((System.title_id == id_title) & (System.stage == "Квалификация")).get()
        
        check_flag = system.choice_flag
        if check_flag:
            existing_data = load_existing_draw_from_db(id_title)
    except Exception as e:
        print(f"Ошибка при проверке системы: {e}")
        existing_data = None
    
    if existing_data:
        action_dialog = ChoiceActionDialog(parent)
        result = action_dialog.exec_()
        
        if result == 1:  # Сбросить
            clear_db_before_choice(id_title)
            try:
                existing_data = None
                QMessageBox.information(parent, "Информация", 
                    "Начинаем новую жеребьевку. Предыдущие данные удалены.")
            except Exception as e:
                QMessageBox.warning(parent, "Ошибка", f"Ошибка при очистке БД: {str(e)}")
                return None
        elif result == 2:  # Загрузить
            pass
        else:  # Отмена
            return None
    
    dialog = ChoiceGroupManual(athletes, num_groups, id_title, parent, existing_data)
    result_code = dialog.exec_()
    
    if result_code == QDialog.Accepted:
        return dialog.get_results()
    else:
        return None