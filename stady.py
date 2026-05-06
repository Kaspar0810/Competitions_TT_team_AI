import math

def get_match_title_from_excel(match_number, highest_place=33, total_players=32):
    """
    Определяет название стадии матча по его номеру в турнирной сетке
    на основе структуры из Excel-файла.
    
    Аргументы:
    match_number (int): Номер встречи
    highest_place (int): Наивысшее место в данной сетке
    total_players (int): Количество участников (8, 16 или 32)
    
    Возвращает:
    str: Название стадии матча
    """
    
    # Проверка корректности параметров
    valid_sizes = [8, 16, 32]
    if total_players not in valid_sizes:
        return f"Ошибка: поддерживаются только сетки на {valid_sizes} участников"
    
    # Расчет базовых параметров
    if total_players == 32:
        max_match = 80
        # Структура для 32 участников (как в Excel)
        main_rounds = {
            'first_round': (1, 16, f"1/16 финала"),
            'second_round': (17, 24, f"1/8 финала"),
            'quarter': (25, 28, f"1/4 финала"),
            'semi': (29, 32, f"1/2 финала")
        }
        
        # Стыковые матчи - распределение мест
        consolation = [
            # Места 33-36 (финал основной сетки)
            {'matches': [37, 38], 'offset': 0, 'type': 'final_group'},
            # Места 37-40
            {'matches': [33, 34, 35, 36], 'offset': 4, 'type': 'full_group'},
            # Места 41-44
            {'matches': [39, 40, 41, 42], 'offset': 8, 'type': 'full_group'},
            # Места 45-48
            {'matches': [43, 44, 45, 46], 'offset': 12, 'type': 'full_group'},
            # Места 49-52
            {'matches': [47, 48, 49, 50], 'offset': 16, 'type': 'full_group'},
            # Места 53-56
            {'matches': [51, 52, 53, 54], 'offset': 20, 'type': 'full_group'},
            # Места 57-60
            {'matches': [55, 56, 57, 58], 'offset': 24, 'type': 'full_group'},
            # Места 61-64
            {'matches': [59, 60, 61, 62], 'offset': 28, 'type': 'full_group'},
        ]
    elif total_players == 16:
        max_match = 40
        # Структура для 16 участников
        main_rounds = {
            'first_round': (1, 8, f"1/8 финала"),
            'quarter': (9, 12, f"1/4 финала"),
            'semi': (13, 14, f"1/2 финала"),
            'final': (15, 15, f"финал")
        }
        
        consolation = [
            # Места 17-18 (финал основной сетки)
            {'matches': [19, 20], 'offset': 0, 'type': 'final_group'},
            # Места 19-22
            {'matches': [16, 17, 18, 21], 'offset': 2, 'type': 'mixed_group'},
            # Места 23-26
            {'matches': [22, 23, 24, 25], 'offset': 6, 'type': 'full_group'},
            # Места 27-30
            {'matches': [26, 27, 28, 29], 'offset': 10, 'type': 'full_group'},
            # Места 31-32
            {'matches': [30, 31, 32, 33], 'offset': 14, 'type': 'full_group'},
        ]
    else:  # total_players == 8
        max_match = 20
        # Структура для 8 участников
        main_rounds = {
            'first_round': (1, 4, f"1/4 финала"),
            'semi': (5, 6, f"1/2 финала"),
            'final': (7, 7, f"финал")
        }
        
        consolation = [
            # Места 9-10 (финал основной сетки)
            {'matches': [9, 10], 'offset': 0, 'type': 'final_group'},
            # Места 11-14
            {'matches': [8, 11, 12, 13], 'offset': 2, 'type': 'mixed_group'},
            # Места 15-16
            {'matches': [14, 15, 16, 17], 'offset': 6, 'type': 'full_group'},
        ]
    
    # Проверка на допустимый номер матча
    if match_number < 1 or match_number > max_match:
        return f"Матч {match_number} (вне диапазона для {total_players} участников)"
    
    # Проверка основной сетки
    for round_name, round_data in main_rounds.items():
        start, end, title = round_data
        if start <= match_number <= end:
            return title
    
    # Проверка стыковых матчей
    for group in consolation:
        if match_number in group['matches']:
            idx = group['matches'].index(match_number)
            offset = group['offset']
            
            if group['type'] == 'final_group':
                # Для финальной группы (2 матча)
                if idx == 0:  # Финал за highest_place - highest_place+1
                    return f"Финал за {highest_place + offset}-{highest_place + offset + 1} место"
                else:  # Матч за highest_place+2 - highest_place+3
                    return f"Матч за {highest_place + offset + 2}-{highest_place + offset + 3} место"
            
            elif group['type'] == 'full_group':
                # Полная группа из 4 матчей
                if idx == 0 or idx == 1:  # Полуфиналы
                    start_place = highest_place + offset
                    end_place = highest_place + offset + 3
                    return f"За {start_place}-{end_place} место (1/2 финала)"
                elif idx == 2:  # Финал группы
                    return f"Финал за {highest_place + offset}-{highest_place + offset + 1} место"
                else:  # Матч за 3-4 место в группе
                    return f"Матч за {highest_place + offset + 2}-{highest_place + offset + 3} место"
            
            elif group['type'] == 'mixed_group':
                # Смешанная группа (адаптация для 16 и 8 участников)
                if idx == 0 or idx == 1:  # Полуфиналы
                    start_place = highest_place + offset
                    end_place = highest_place + offset + 3
                    return f"За {start_place}-{end_place} место (1/2 финала)"
                elif idx == 2:  # Финал
                    return f"Финал за {highest_place + offset}-{highest_place + offset + 1} место"
                else:  # Матч за 3-4 место
                    return f"Матч за {highest_place + offset + 2}-{highest_place + offset + 3} место"
    
    return f"Матч {match_number} (стадия не определена)"


def print_tournament_structure_excel(highest_place=33, total_players=32):
    """
    Выводит полную структуру турнирной сетки в формате Excel
    """
    last_place = highest_place + total_players - 1
    print(f"ТУРНИРНАЯ СЕТКА ({total_players} участников, места {highest_place}-{last_place})")
    print("=" * 80)
    
    if total_players == 32:
        # Основная сетка
        print("\n📋 ОСНОВНАЯ СЕТКА:")
        print(f"  Матчи 1-16:  1/16 финала")
        print(f"  Матчи 17-24: 1/8 финала")
        print(f"  Матчи 25-28: 1/4 финала")
        print(f"  Матчи 29-32: 1/2 финала")
        
        # Финалы основной сетки
        print(f"\n🏆 ФИНАЛЫ ОСНОВНОЙ СЕТКИ:")
        print(f"  Матч 37: Финал за {highest_place}-{highest_place+1} место")
        print(f"  Матч 38: Матч за {highest_place+2}-{highest_place+3} место")
        
        # Стыковые матчи по группам
        print(f"\n🔄 СТЫКОВЫЕ МАТЧИ:")
        
        groups = [
            (4, 33, 36, f"{highest_place+4}-{highest_place+7}"),
            (8, 39, 42, f"{highest_place+8}-{highest_place+11}"),
            (12, 43, 46, f"{highest_place+12}-{highest_place+15}"),
            (16, 47, 50, f"{highest_place+16}-{highest_place+19}"),
            (20, 51, 54, f"{highest_place+20}-{highest_place+23}"),
            (24, 55, 58, f"{highest_place+24}-{highest_place+27}"),
            (28, 59, 62, f"{highest_place+28}-{highest_place+31}"),
        ]
        
        for offset, start, end, places in groups:
            print(f"\n  Группа за места {places}:")
            print(f"    Матчи {start}-{start+1}: 1/2 финала за {places}")
            print(f"    Матч {start+2}: Финал за {highest_place+offset}-{highest_place+offset+1} место")
            print(f"    Матч {start+3}: Матч за {highest_place+offset+2}-{highest_place+offset+3} место")
    
    elif total_players == 16:
        print("\n📋 ОСНОВНАЯ СЕТКА:")
        print(f"  Матчи 1-8:   1/8 финала")
        print(f"  Матчи 9-12:  1/4 финала")
        print(f"  Матчи 13-14: 1/2 финала")
        print(f"  Матч 15:     финал")
        
        print(f"\n🏆 ФИНАЛЫ ОСНОВНОЙ СЕТКИ:")
        print(f"  Матч 19: Финал за {highest_place}-{highest_place+1} место")
        print(f"  Матч 20: Матч за {highest_place+2}-{highest_place+3} место")
        
        print(f"\n🔄 СТЫКОВЫЕ МАТЧИ:")
        print(f"  Матчи 16-17: 1/2 финала за {highest_place+2}-{highest_place+5} место")
        print(f"  Матч 18:     Финал за {highest_place+2}-{highest_place+3} место")
        print(f"  Матч 21:     Матч за {highest_place+4}-{highest_place+5} место")
        print(f"  Матчи 22-23: 1/2 финала за {highest_place+6}-{highest_place+9} место")
        print(f"  Матч 24:     Финал за {highest_place+6}-{highest_place+7} место")
        print(f"  Матч 25:     Матч за {highest_place+8}-{highest_place+9} место")
        print(f"  Матчи 26-27: 1/2 финала за {highest_place+10}-{highest_place+13} место")
        print(f"  Матч 28:     Финал за {highest_place+10}-{highest_place+11} место")
        print(f"  Матч 29:     Матч за {highest_place+12}-{highest_place+13} место")
        print(f"  Матчи 30-31: 1/2 финала за {highest_place+14}-{highest_place+15} место")
        print(f"  Матч 32:     Финал за {highest_place+14} место")
        print(f"  Матч 33:     Матч за {highest_place+15} место")
    
    else:  # total_players == 8
        print("\n📋 ОСНОВНАЯ СЕТКА:")
        print(f"  Матчи 1-4: 1/4 финала")
        print(f"  Матчи 5-6: 1/2 финала")
        print(f"  Матч 7:    финал")
        
        print(f"\n🏆 ФИНАЛЫ ОСНОВНОЙ СЕТКИ:")
        print(f"  Матч 9:  Финал за {highest_place}-{highest_place+1} место")
        print(f"  Матч 10: Матч за {highest_place+2}-{highest_place+3} место")
        
        print(f"\n🔄 СТЫКОВЫЕ МАТЧИ:")
        print(f"  Матч 8:     1/2 финала за {highest_place+2}-{highest_place+5} место")
        print(f"  Матчи 11-12: 1/2 финала за {highest_place+2}-{highest_place+5} место")
        print(f"  Матч 13:     Финал за {highest_place+2}-{highest_place+3} место")
        print(f"  Матч 14:     Матч за {highest_place+4}-{highest_place+5} место")
        print(f"  Матчи 15-16: 1/2 финала за {highest_place+6}-{highest_place+7} место")
        print(f"  Матч 17:     Финал за {highest_place+6} место")
        print(f"  Матч 18:     Матч за {highest_place+7} место")


def demonstrate_excel_structure():
    """
    Демонстрирует работу функции для разных форматов
    """
    test_cases = [
        (33, 32, "Мужчины, 33-64 места (как в Excel)"),
        (1, 32, "Чемпионат, 1-32 места"),
        (65, 32, "Утешительный турнир, 65-96 места"),
        (1, 16, "Турнир 16 участников, 1-16 места"),
        (17, 16, "Турнир 16 участников, 17-32 места"),
        (1, 8, "Турнир 8 участников, 1-8 места"),
        (9, 8, "Турнир 8 участников, 9-16 места"),
    ]
    
    for highest, players, description in test_cases:
        print("\n" + "=" * 80)
        print(f"📊 ТЕСТ: {description}")
        print("=" * 80)
        
        # Показываем ключевые матчи
        print(f"\n🔍 Ключевые матчи:")
        
        # Первый матч
        print(f"  Матч 1: {get_match_title_from_excel(1, highest, players)}")
        
        # Матчи основной сетки
        if players == 32:
            print(f"  Матч 16: {get_match_title_from_excel(16, highest, players)}")
            print(f"  Матч 32: {get_match_title_from_excel(32, highest, players)}")
            print(f"  Матч 37: {get_match_title_from_excel(37, highest, players)}")
            print(f"  Матч 38: {get_match_title_from_excel(38, highest, players)}")
            print(f"  Матч 33: {get_match_title_from_excel(33, highest, players)}")
            print(f"  Матч 35: {get_match_title_from_excel(35, highest, players)}")
            print(f"  Матч 36: {get_match_title_from_excel(36, highest, players)}")
            print(f"  Матч 62: {get_match_title_from_excel(62, highest, players)}")
        elif players == 16:
            print(f"  Матч 8: {get_match_title_from_excel(8, highest, players)}")
            print(f"  Матч 15: {get_match_title_from_excel(15, highest, players)}")
            print(f"  Матч 19: {get_match_title_from_excel(19, highest, players)}")
            print(f"  Матч 20: {get_match_title_from_excel(20, highest, players)}")
            print(f"  Матч 16: {get_match_title_from_excel(16, highest, players)}")
            print(f"  Матч 18: {get_match_title_from_excel(18, highest, players)}")
            print(f"  Матч 33: {get_match_title_from_excel(33, highest, players)}")
        else:  # players == 8
            print(f"  Матч 4: {get_match_title_from_excel(4, highest, players)}")
            print(f"  Матч 7: {get_match_title_from_excel(7, highest, players)}")
            print(f"  Матч 9: {get_match_title_from_excel(9, highest, players)}")
            print(f"  Матч 10: {get_match_title_from_excel(10, highest, players)}")
            print(f"  Матч 8: {get_match_title_from_excel(8, highest, players)}")
            print(f"  Матч 13: {get_match_title_from_excel(13, highest, players)}")
            print(f"  Матч 18: {get_match_title_from_excel(18, highest, players)}")


# Пример использования
if __name__ == "__main__":
    print("=" * 80)
    print("🏓 ТУРНИРНАЯ СЕТКА ПО НАСТОЛЬНОМУ ТЕННИСУ")
    print("=" * 80)
    print("Основано на структуре из Excel-файла")
    print("Поддерживаются форматы: 32, 16 и 8 участников")
    
    # Демонстрация всех форматов
    demonstrate_excel_structure()
    
    # Подробный вывод для конкретного примера из Excel
    print("\n" + "=" * 80)
    print("📋 ДЕТАЛЬНЫЙ ПРИМЕР: Мужчины, 33-64 места (как в Excel)")
    print("=" * 80)
    print_tournament_structure_excel(33, 32)
    
    # Проверка конкретных матчей из Excel
    print("\n" + "=" * 80)
    print("✅ ПРОВЕРКА КОНКРЕТНЫХ МАТЧЕЙ ИЗ EXCEL:")
    print("=" * 80)
    
    excel_matches = [
        (1, "1/16 финала"),
        (17, "1/8 финала"),
        (25, "1/4 финала"),
        (29, "1/2 финала"),
        (37, "Финал за 33-34 место"),
        (38, "Матч за 35-36 место"),
        (33, "За 37-40 место (1/2 финала)"),
        (35, "Финал за 37-38 место"),
        (36, "Матч за 39-40 место"),
        (62, "Матч за 61-62 место"),
    ]
    
    for match_num, expected in excel_matches:
        result = get_match_title_from_excel(match_num, 33, 32)
        print(f"  Матч {match_num}: {result}")
        if expected in result:
            print(f"    ✓ Совпадает с ожиданием: {expected}")