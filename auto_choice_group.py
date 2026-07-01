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
        self.conflicts_found = []  # Список конфликтов для ручного редактирования
        self.unplaced_athletes = []  # Спортсмены, которых не удалось разместить
        
    def calculate_max_rows(self):
        """Расчет максимального количества строк в группе"""
        total_athletes = len(self.athletes)
        self.max_rows_per_group = (total_athletes + self.num_groups - 1) // self.num_groups
        if self.max_rows_per_group < 1:
            self.max_rows_per_group = 1
            
    def get_current_round(self):
        """Определение текущего раунда на основе количества размещенных спортсменов"""
        placed_count = self.current_athlete_index
        
        placed_count = self.current_athlete_index
        
        if placed_count == 0:
            return 1
        round_num = placed_count // self.num_groups + 1
        return round_num

    def get_group_players_count(self, group_idx):
        """Получить количество игроков в группе"""
        if group_idx < len(self.groups):
            return len([a for a in self.groups[group_idx] if a is not None])
        return 0
    
    def get_next_row_in_group(self, group_idx):
        """Получить следующую свободную строку в группе"""
        group = self.groups[group_idx]
        for row in range(self.max_rows_per_group):
            if row >= len(group) or group[row] is None:
                return row
        return None
    
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
    
    def get_group_order(self):
        """Получить порядок обхода групп в зависимости от текущего круга"""
        current_round = self.get_current_round()
        
        if current_round == 1:
            # 1-й круг: от первой к последней
            return range(self.num_groups)
        elif current_round % 2 == 0:
            # Четный круг: от последней к первой
            return range(self.num_groups - 1, -1, -1)
        else:
            # Нечетный круг: от первой к последней
            return range(self.num_groups)
    
    def find_best_group_for_athlete(self, athlete):
        """
        Найти лучшую группу для спортсмена с учетом правил:
        1. Сначала проверяем наличие свободных мест в текущем посеве
        2. Затем проверяем конфликт регионов
        3. Затем проверяем конфликт тренеров
        4. Если конфликт не решается - добавляем в список для ручного редактирования
        """
        current_round = self.get_current_round()
        group_order = self.get_group_order()
        
        # Определяем, какая строка (посев) сейчас заполняется
        current_row = self.current_athlete_index // self.num_groups
        if current_row >= self.max_rows_per_group:
            current_row = self.max_rows_per_group - 1
        
        # Шаг 1: Ищем группы, где есть свободное место в текущем посеве
        for g_idx in group_order:
            # Проверяем, есть ли свободное место в группе
            if len(self.groups[g_idx]) <= current_row or self.groups[g_idx][current_row] is None:
                # Проверяем конфликты
                region_conflict, coach_conflict = self.check_conflicts(athlete, g_idx)
                
                # Если нет конфликтов - размещаем
                if not region_conflict and not coach_conflict:
                    return g_idx, current_row, "no_conflict"
        
        # Шаг 2: Если не нашли без конфликтов, ищем с разрешением конфликта региона
        for g_idx in group_order:
            if len(self.groups[g_idx]) <= current_row or self.groups[g_idx][current_row] is None:
                region_conflict, coach_conflict = self.check_conflicts(athlete, g_idx)
                
                # Разрешаем конфликт региона, но не тренера
                if region_conflict and not coach_conflict:
                    return g_idx, current_row, "region_conflict"
        
        # Шаг 3: Если не нашли с разрешением региона, ищем с разрешением обоих конфликтов
        for g_idx in group_order:
            if len(self.groups[g_idx]) <= current_row or self.groups[g_idx][current_row] is None:
                region_conflict, coach_conflict = self.check_conflicts(athlete, g_idx)
                
                # Разрешаем оба конфликта (только в крайнем случае)
                if region_conflict and coach_conflict:
                    return g_idx, current_row, "both_conflict"
        
        # Шаг 4: Если в текущем посеве нет свободных мест
        # Ищем свободное место в следующем посеве (но это нарушит правило)
        next_row = current_row + 1
        if next_row < self.max_rows_per_group:
            for g_idx in group_order:
                if len(self.groups[g_idx]) <= next_row or self.groups[g_idx][next_row] is None:
                    return g_idx, next_row, "next_row"
        
        # Шаг 5: Если не нашли места - добавляем в список неразмещенных
        return None, None, "unplaced"
    
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
        self.conflicts_found = []
        self.unplaced_athletes = []
        
        # 1-й круг: заполняем первые места (от 1 к N)
        for i in range(min(self.num_groups, len(self.sorted_athletes))):
            self.groups[i] = [self.sorted_athletes[i]]
            self.current_athlete_index += 1
        
        # Продолжаем заполнение оставшихся спортсменов
        while self.current_athlete_index < len(self.sorted_athletes):
            athlete = self.sorted_athletes[self.current_athlete_index]
            
            # Находим группу для спортсмена
            group_idx, row, conflict_type = self.find_best_group_for_athlete(athlete)
            
            if group_idx is not None and row is not None:
                # Размещаем спортсмена
                self.place_athlete(athlete, group_idx, row)
                
                # Если был конфликт - запоминаем
                if conflict_type == "region_conflict":
                    self.conflicts_found.append({
                        'athlete': athlete,
                        'group': group_idx + 1,
                        'row': row + 1,
                        'conflict_type': 'Регион'
                    })
                elif conflict_type == "both_conflict":
                    self.conflicts_found.append({
                        'athlete': athlete,
                        'group': group_idx + 1,
                        'row': row + 1,
                        'conflict_type': 'Регион и тренер'
                    })
                elif conflict_type == "next_row":
                    self.conflicts_found.append({
                        'athlete': athlete,
                        'group': group_idx + 1,
                        'row': row + 1,
                        'conflict_type': 'Следующий посев (нарушение порядка)'
                    })
            else:
                # Не удалось разместить спортсмена
                self.unplaced_athletes.append(athlete)
                self.current_athlete_index += 1
        
        # Проверяем, есть ли неразмещенные спортсмены
        if self.unplaced_athletes:
            # Пытаемся разместить их в любые свободные места
            for athlete in self.unplaced_athletes:
                placed = False
                for g_idx in range(self.num_groups):
                    if len(self.groups[g_idx]) < self.max_rows_per_group:
                        row = self.get_next_row_in_group(g_idx)
                        if row is not None:
                            self.place_athlete(athlete, g_idx, row)
                            placed = True
                            break
                
                if not placed:
                    # Если все равно не разместили - добавляем в список ошибок
                    self.conflicts_found.append({
                        'athlete': athlete,
                        'group': 'Не размещен',
                        'row': '-',
                        'conflict_type': 'Нет свободных мест'
                    })
        
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
        
        # Если есть конфликты - выводим предупреждение
        if self.conflicts_found:
            conflict_text = "В процессе жеребьевки возникли следующие конфликты:\n\n"
            for i, conflict in enumerate(self.conflicts_found, 1):
                conflict_text += f"{i}. {conflict['athlete'][1]} "
                conflict_text += f"(рейтинг: {conflict['athlete'][2]}) - "
                conflict_text += f"конфликт: {conflict['conflict_type']}\n"
                if conflict['group'] != 'Не размещен':
                    conflict_text += f"   Размещен в группу {conflict['group']}, "
                    conflict_text += f"позиция {conflict['row']}\n"
                else:
                    conflict_text += f"   НЕ РАЗМЕЩЕН!\n"
            
            conflict_text += "\nРекомендуется открыть ручную жеребьевку для исправления конфликтов."
            
            QMessageBox.warning(self.parent if self.parent else None, 
                               "Конфликты в жеребьевке", conflict_text)
        
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


def save_choice_results(self, results):
    """Сохранение результатов жеребьевки в базу данных"""
    try:
        # Получаем систему
        system = System.select().where((System.stage == "Квалификация") & (System.title_id == self.current_title_id)).get()
        id_system = system.id
        
        # # Очищаем старые данные Choice
        # Choice.delete().where(Choice.title_id == self.current_title_id).execute()
        
        # Сохраняем новые результаты
        for result in results:
            Choice.update(
                title_id=self.current_title_id,
                group=f"{result['group']} группа",
                posev_group=result['seed_num']
            ).where(Choice.player_choice_id == result['id_player']).execute()
        
        # Обновляем флаг выбора в System
        System.update(choice_flag=True).where(System.id == id_system).execute()
        
        return True
    except Exception as e:
        print(f"Ошибка при сохранении результатов: {e}")
        return False


def choice_group_auto(self, athletes, num_groups, stage, parent=None):
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
            system = System.select().where((System.title_id == self.current_title_id) & (System.stage == "Одна таблица")).get()
        else:
            system = System.select().where((System.title_id == self.current_title_id) & (System.stage == "Квалификация")).get()
        
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
            clear_db_before_choice(self.current_title_id)
        
        # Запускаем автоматическую жеребьевку
        auto_draw = ChoiceGroupAuto(athletes, num_groups, self.current_title_id, parent)
        results = auto_draw.run()
        
        if results:
            # Сохраняем результаты
            if save_choice_results(self, results):
                # Выводим информацию о распределении
                groups_info = {}
                for r in results:
                    g = r['group']
                    if g not in groups_info:
                        groups_info[g] = 0
                    groups_info[g] += 1
                
                info_text = f"Автоматическая жеребьевка завершена!\n"
                info_text += f"Распределено {len(results)} спортсменов по {num_groups} группам.\n\n"
                info_text += "Распределение по группам:\n"
                for g in sorted(groups_info.keys()):
                    info_text += f"Группа {g}: {groups_info[g]} спортсменов\n"
                
                if auto_draw.conflicts_found:
                    info_text += f"\n⚠️ Внимание! Возникли конфликты при жеребьевке.\n"
                    info_text += f"Подробности в отдельном сообщении."
                
                QMessageBox.information(parent, "Успех", info_text)
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