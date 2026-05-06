import random
from typing import List, Tuple, Dict, Optional, Set
from collections import defaultdict

# Данные спортсменов (32 группы)
sportsmen_16 = [
    ["Иванов", "Москва", 450, "1 группа", "1 место"],
    ["Петров", "Москва", 435, "1 группа", "2 место"],
    ["Сидоров", "Москва", 429, "2 группа", "1 место"],
    ["Лазарев", "Москва", 480, "2 группа", "2 место"],
    ["Зырянов", "Москва", 520, "3 группа", "1 место"],
    ["Котов", "Свердловская обл.", 272, "3 группа", "2 место"],
    ["Ветров", "Свердловская обл.", 654, "4 группа", "1 место"],
    ["Лаптев", "Свердловская обл.", 320, "4 группа", "2 место"],
    ["Малышев", "Свердловская обл.", 400, "5 группа", "1 место"],
    ["Реутов", "Свердловская обл.", 250, "5 группа", "2 место"],
    ["Пушкин", "Вологодская обл.", 140, "6 группа", "1 место"],
    ["Клюкин", "Вологодская обл.", 300, "6 группа", "2 место"],
    ["Лермонтов", "Вологодская обл.", 290, "7 группа", "1 место"],
    ["Лапшин", "Вологодская обл.", 570, "7 группа", "2 место"],
    ["Стеклов", "Вологодская обл.", 420, "8 группа", "1 место"],
    ["Кротов", "Нижегородская обл.", 240, "8 группа", "2 место"],
    ["Киселев", "Нижегородская обл.", 235, "9 группа", "1 место"],
    ["Гусев", "Нижегородская обл.", 360, "9 группа", "2 место"],
    ["Бондаренко", "Нижегородская обл.", 125, "10 группа", "1 место"],
    ["Романов", "Нижегородская обл.", 255, "10 группа", "2 место"],
    ["Гладышев", "Тюменская обл.", 710, "11 группа", "1 место"],
    ["Павлов", "Тюменская обл.", 390, "11 группа", "2 место"],
    ["Шибаев", "Самарская обл.", 310, "12 группа", "1 место"],
    ["Лукин", "Самарская обл.", 410, "12 группа", "2 место"],
    ["Стоянов", "Оренбургская обл.", 320, "13 группа", "1 место"],
    ["Орлов", "Ивановская обл.", 515, "13 группа", "2 место"],
    ["Ветров", "Ивановская обл.", 110, "14 группа", "1 место"],
    ["Волков", "Иркутская обл.", 310, "14 группа", "2 место"],
    ["Медведев", "Иркутская обл.", 160, "15 группа", "1 место"],
    ["Зайцев", "Иркутская обл.", 260, "15 группа", "2 место"],
    ["Лосев", "Саратовская обл.", 180, "16 группа", "1 место"],
    ["Тихонов", "Кемеровская обл.", 460, "16 группа", "2 место"]
]

# Данные спортсменов (16 групп)
sportsmen_32 = [
    ["Иванов", "Москва", 450, "1 группа", "1 место"],
    ["Петров", "Москва", 435, "17 группа", "1 место"],
    ["Сидоров", "Москва", 429, "18 группа", "1 место"],
    ["Лазарев", "Москва", 480, "2 группа", "1 место"],
    ["Зырянов", "Москва", 520, "3 группа", "1 место"],
    ["Котов", "Свердловская обл.", 272, "19 группа", "1 место"],
    ["Ветров", "Свердловская обл.", 654, "4 группа", "1 место"],
    ["Лаптев", "Свердловская обл.", 320, "20 группа", "1 место"],
    ["Малышев", "Свердловская обл.", 400, "5 группа", "1 место"],
    ["Реутов", "Свердловская обл.", 250, "21 группа", "1 место"],
    ["Пушкин", "Вологодская обл.", 140, "6 группа", "1 место"],
    ["Клюкин", "Вологодская обл.", 300, "22 группа", "1 место"],
    ["Лермонтов", "Вологодская обл.", 290, "7 группа", "1 место"],
    ["Лапшин", "Вологодская обл.", 570, "23 группа", "1 место"],
    ["Стеклов", "Вологодская обл.", 420, "8 группа", "1 место"],
    ["Кротов", "Нижегородская обл.", 240, "24 группа", "1 место"],
    ["Киселев", "Нижегородская обл.", 235, "9 группа", "1 место"],
    ["Гусев", "Нижегородская обл.", 360, "25 группа", "1 место"],
    ["Бондаренко", "Нижегородская обл.", 125, "10 группа", "1 место"],
    ["Романов", "Нижегородская обл.", 255, "26 группа", "1 место"],
    ["Гладышев", "Тюменская обл.", 710, "11 группа", "1 место"],
    ["Павлов", "Тюменская обл.", 390, "27 группа", "1 место"],
    ["Шибаев", "Самарская обл.", 310, "12 группа", "1 место"],
    ["Лукин", "Самарская обл.", 410, "28 группа", "1 место"],
    ["Стоянов", "Оренбургская обл.", 320, "13 группа", "1 место"],
    ["Орлов", "Ивановская обл.", 515, "29 группа", "1 место"],
    ["Ветров", "Ивановская обл.", 110, "14 группа", "1 место"],
    ["Волков", "Иркутская обл.", 310, "30 группа", "1 место"],
    ["Медведев", "Иркутская обл.", 160, "15 группа", "1 место"],
    ["Зайцев", "Иркутская обл.", 260, "31 группа", "1 место"],
    ["Лосев", "Саратовская обл.", 180, "16 группа", "1 место"],
    ["Тихонов", "Кемеровская обл.", 460, "32 группа", "1 место"]
]

# Определяем посевы
def get_seed_groups() -> Dict[int, List[int]]:
    """Возвращает распределение номеров по посевам"""
    seeds = {
        1: [1, 32],
        2: [16, 17],
        3: [8, 9, 24, 25],
        4: [4, 5, 12, 13, 20, 21, 28, 29],
        5: list(range(1, 33))
    }

    # Убираем из 5-го посева номера, которые уже есть в предыдущих посевах
    used_numbers = set()
    for seed_num in range(1, 5):
        used_numbers.update(seeds[seed_num])
    
    seeds[5] = [num for num in seeds[5] if num not in used_numbers]
    return seeds

def get_half(number: int) -> int:
    """Определяет половину для номера таблицы"""
    return 1 if number <= 16 else 2

def get_quarter(number: int) -> int:
    """Определяет четверть для номера таблицы"""
    if number <= 8:
        return 1
    elif number <= 16:
        return 2
    elif number <= 24:
        return 3
    else:
        return 4

def check_region_constraints(placement: Dict[int, int], sportsmen_data: List[List]) -> bool:
    """Проверяет выполнение условий по регионам"""
    region_counts = {}
    region_positions = {}

    # Собираем информацию о регионах и позициях
    for table_num, sportsman_idx in placement.items():
        if sportsman_idx is None:
            continue
        region = sportsmen_data[sportsman_idx][1]

        if region not in region_counts:
            region_counts[region] = 0
            region_positions[region] = []

        region_counts[region] += 1
        region_positions[region].append(table_num)

    # Проверяем условия
    for region, count in region_counts.items():
        positions = region_positions[region]

        if count == 2:
            # Должны быть в разных половинах
            halves = [get_half(pos) for pos in positions]
            if len(set(halves)) != 2:
                return False

        elif count == 3 or count == 4:
            # Должны быть в разных четвертях
            quarters = [get_quarter(pos) for pos in positions]
            if len(set(quarters)) != count:
                return False

    # Для более 4 человек ограничений нет
    return True

def get_available_quarters_for_seed(seed_num: int, seeds: Dict[int, List[int]]) -> List[int]:
    """Возвращает доступные четверти для посева"""
    seed_positions = seeds[seed_num]
    quarters = [get_quarter(pos) for pos in seed_positions]
    return list(set(quarters))

def calculate_available_quarters_counts(sportsmen_indices: List[int],
                                        sportsmen_data: List[List],
                                        region_quarter_usage: Dict[str, Set[int]]) -> Dict[int, int]:
    """Рассчитывает количество доступных четвертей для каждого спортсмена"""
    counts = {}

    for idx in sportsmen_indices:
        region = sportsmen_data[idx][1]
        used_quarters = region_quarter_usage.get(region, set())

        # Если регион уже представлен в 4 или более четвертях, все четверти доступны
        if len(used_quarters) >= 4:
            counts[idx] = 4
        else:
            # Количество доступных четвертей = 4 - количество использованных четвертей региона
            counts[idx] = 4 - len(used_quarters)

    return counts

def draw_32_groups(sportsmen_data: List[List], max_attempts: int = 1000) -> Optional[Dict[int, int]]:
    """Жеребьевка для 32 групп с улучшенным алгоритмом"""
    # Сортируем по рейтингу (по убыванию)
    sorted_sportsmen = sorted(enumerate(sportsmen_data), key=lambda x: x[1][2], reverse=True)
    sorted_indices = [idx for idx, _ in sorted_sportsmen]

    seeds = get_seed_groups()

    for attempt in range(max_attempts):
        # Инициализируем размещение
        placement = {i: None for i in range(1, 33)}

        # Словарь для отслеживания использования четвертей регионами
        region_quarter_usage = defaultdict(set)

        # Для 1-го посева
        seed_num = 1
        seed_positions = seeds[seed_num]

        # Берем первых двух спортсменов из отсортированного списка
        if len(sorted_indices) >= 2:
            placement[seed_positions[0]] = sorted_indices[0]  # 1-й номер
            placement[seed_positions[1]] = sorted_indices[1]  # 32-й номер

            # Обновляем использование четвертей
            for pos in seed_positions:
                sportsman_idx = placement[pos]
                if sportsman_idx is not None:
                    region = sportsmen_data[sportsman_idx][1]
                    quarter = get_quarter(pos)
                    region_quarter_usage[region].add(quarter)

            # Удаляем использованных спортсменов
            used_indices = [idx for idx in placement.values() if idx is not None]
            available_indices = [idx for idx in sorted_indices if idx not in used_indices]

            # Для 2-го посева (номера 16 и 17)
            seed_num = 2
            seed_positions = seeds[seed_num]

            if len(available_indices) >= 2:
                # Случайно выбираем, кто будет на 16, а кто на 17
                if random.random() > 0.5:
                    placement[seed_positions[0]] = available_indices[0]  # 16
                    placement[seed_positions[1]] = available_indices[1]  # 17
                else:
                    placement[seed_positions[0]] = available_indices[1]  # 16
                    placement[seed_positions[1]] = available_indices[0]  # 17

            # Обновляем использование четвертей
            for pos in seed_positions:
                sportsman_idx = placement[pos]
                if sportsman_idx is not None:
                    region = sportsmen_data[sportsman_idx][1]
                    quarter = get_quarter(pos)
                    region_quarter_usage[region].add(quarter)

            # Обновляем доступные индексы
            used_indices = [idx for idx in placement.values() if idx is not None]
            available_indices = [idx for idx in sorted_indices if idx not in used_indices]

            # Для посевов 3, 4, 5 используем улучшенный алгоритм
            for seed_num in [3, 4, 5]:
                seed_positions = seeds[seed_num]
                count_sev = len(seed_positions)
                
                # Берем нужное количество спортсменов для этого посева
                if len(available_indices) < count_sev:
                    break
                
                upd_available_indices = available_indices[:count_sev]

                # Для каждой позиции в посеве
                for pos in seed_positions:
                    if placement[pos] is not None:
                        continue  # Позиция уже занята

                    quarter = get_quarter(pos)

                    # Получаем спортсменов, которые еще не размещены
                    unplaced_indices = [idx for idx in upd_available_indices if idx not in placement.values()]

                    if not unplaced_indices:
                        continue

                    # Рассчитываем доступные четверти для каждого спортсмена
                    quarter_counts = calculate_available_quarters_counts(unplaced_indices, sportsmen_data, region_quarter_usage)

                    # Фильтруем спортсменов, которые могут быть размещены в этой четверти
                    possible_sportsmen = []
                    for idx in unplaced_indices:
                        region = sportsmen_data[idx][1]
                        used_quarters = region_quarter_usage.get(region, set())

                        # Проверяем, может ли спортсмен быть размещен в этой четверти
                        can_place = True
                        if len(used_quarters) < 4 and quarter in used_quarters:
                            can_place = False

                        if can_place:
                            possible_sportsmen.append((idx, quarter_counts[idx]))

                    if not possible_sportsmen:
                        # Если нет подходящих спортсменов, выбираем любого
                        sportsman_idx = unplaced_indices[0]
                    else:
                        # Сортируем по наименьшему количеству доступных четвертей
                        possible_sportsmen.sort(key=lambda x: x[1])
                        sportsman_idx = possible_sportsmen[0][0]

                    # Размещаем спортсмена
                    placement[pos] = sportsman_idx

                    # Обновляем использование четвертей
                    region = sportsmen_data[sportsman_idx][1]
                    region_quarter_usage[region].add(quarter)

                    # Удаляем из доступных
                    if sportsman_idx in available_indices:
                        available_indices.remove(sportsman_idx)

            # Проверяем все условия
            if check_region_constraints(placement, sportsmen_data):
                # Дополнительная проверка: все спортсмены размещены
                if all(idx is not None for idx in placement.values()):
                    return placement

    print(f"Не удалось найти подходящее распределение за {max_attempts} попыток")
    return None

def draw_16_groups(sportsmen_data: List[List]) -> Dict[int, int]:
    """Жеребьевка для 16 групп"""
    # Разделяем на занявших 1-е и 2-е места
    first_place = []
    second_place = []

    for idx, sportsman in enumerate(sportsmen_data):
        if "1 место" in sportsman[4]:
            first_place.append((idx, sportsman))
        else:
            second_place.append((idx, sportsman))

    # Сортируем занявших 1-е место по рейтингу (по убыванию)
    first_place_sorted = sorted(first_place, key=lambda x: x[1][2], reverse=True)

    # Определяем пары (группы) - кто с кем был в группе
    group_pairs = {}
    for idx, sportsman in enumerate(sportsmen_data):
        group = sportsman[3]
        if group not in group_pairs:
            group_pairs[group] = []
        group_pairs[group].append(idx)

    # Размещаем занявших 1-е место
    placement = {i: None for i in range(1, 33)}
    seeds = get_seed_groups()

    # Для хранения использования четвертей регионами
    region_quarter_usage = defaultdict(set)

    # Посев для первых мест
    seed_order = [1, 2, 3, 4, 5]

    for seed_num in seed_order:
        seed_positions = seeds[seed_num]
        available_positions = [pos for pos in seed_positions if placement[pos] is None]

        # Получаем еще не размещенных спортсменов с 1-м местом
        unplaced_first = [idx for idx, _ in first_place_sorted if idx not in placement.values()]

        if not unplaced_first or not available_positions:
            continue

        # Для каждой позиции в посеве
        for pos in available_positions:
            if not unplaced_first:
                break

            quarter = get_quarter(pos)

            # Ищем спортсмена, которого можно разместить с учетом условий по регионам
            suitable_idx = None
            for idx in unplaced_first:
                region = sportsmen_data[idx][1]
                used_quarters = region_quarter_usage.get(region, set())

                # Проверяем условия по регионам
                can_place = True
                if len(used_quarters) < 4 and quarter in used_quarters:
                    # Если регион уже представлен в этой четверти и еще не заполнил все 4 четверти
                    can_place = False

                if can_place:
                    suitable_idx = idx
                    break

            # Если не нашли подходящего, берем первого
            if suitable_idx is None:
                suitable_idx = unplaced_first[0]

            # Размещаем спортсмена
            placement[pos] = suitable_idx

            # Обновляем использование четвертей
            region = sportsmen_data[suitable_idx][1]
            region_quarter_usage[region].add(quarter)

            # Удаляем из списка неразмещенных
            unplaced_first.remove(suitable_idx)

    # Размещаем занявших 2-е место
    for second_idx, second_sportsman in second_place:
        group = second_sportsman[3]

        # Находим партнера по группе
        partner_idx = None
        for idx in group_pairs[group]:
            if idx != second_idx:
                partner_idx = idx
                break

        if partner_idx is None:
            continue

        # Находим где размещен партнер
        partner_position = None
        for pos, idx in placement.items():
            if idx == partner_idx:
                partner_position = pos
                break

        if partner_position is None:
            continue

        # Определяем половину партнера
        partner_half = get_half(partner_position)

        # Ищем свободную позицию в другой половине
        target_half = 2 if partner_half == 1 else 1
        available_positions = []

        for pos in range(1, 33):
            if placement[pos] is None:
                if get_half(pos) == target_half:
                    available_positions.append(pos)

        if available_positions:
            # Берем первую доступную позицию
            chosen_pos = available_positions[0]
            placement[chosen_pos] = second_idx

    # Заполняем оставшиеся позиции оставшимися спортсменами
    remaining_sportsmen = [idx for idx, _ in enumerate(sportsmen_data) if idx not in placement.values()]
    for pos in range(1, 33):
        if placement[pos] is None and remaining_sportsmen:
            placement[pos] = remaining_sportsmen.pop(0)

    return placement

def print_results(placement: Dict[int, int], sportsmen_data: List[List], title: str):
    """Выводит результаты жеребьевки"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    print(f"{'Номер':<6} {'Фамилия':<12} {'Регион':<20} {'Рейтинг':<8} {'Группа':<10} {'Место':<10} {'Половина':<8} {'Четверть':<8}")
    print(f"{'-'*90}")

    for table_num in sorted(placement.keys()):
        sportsman_idx = placement[table_num]
        if sportsman_idx is not None:
            sportsman = sportsmen_data[sportsman_idx]
            half = get_half(table_num)
            quarter = get_quarter(table_num)
            print(f"{table_num:<6} {sportsman[0]:<12} {sportsman[1]:<20} {sportsman[2]:<8} {sportsman[3]:<10} {sportsman[4]:<10} {half:<8} {quarter:<8}")
        else:
            print(f"{table_num:<6} {'-':<12} {'-':<20} {'-':<8} {'-':<10} {'-':<10} {get_half(table_num):<8} {get_quarter(table_num):<8}")

    print(f"{'='*90}")

    # Выводим статистику по регионам
    print("\nСтатистика по регионам:")
    print(f"{'Регион':<20} {'Кол-во':<8} {'Размещение по четвертям':<30}")
    print(f"{'-'*60}")

    region_stats = defaultdict(lambda: {'count': 0, 'quarters': set()})
    for table_num, sportsman_idx in placement.items():
        if sportsman_idx is not None:
            sportsman = sportsmen_data[sportsman_idx]
            region = sportsman[1]
            region_stats[region]['count'] += 1
            region_stats[region]['quarters'].add(get_quarter(table_num))

    for region, stats in sorted(region_stats.items()):
        quarters = sorted(stats['quarters'])
        quarters_str = ', '.join(map(str, quarters))
        print(f"{region:<20} {stats['count']:<8} {quarters_str:<30}")

def main():
    """Основная функция"""
    print("Программа жеребьевки спортсменов")
    print("="*50)
    print("Выберите вариант:")
    print("1 - 32 группы (с условиями по регионам)")
    print("2 - 16 групп (с разделением по группам)")

    choice = input("Ваш выбор (1 или 2): ").strip()

    if choice == "1":
        print("\nВыполняем жеребьевку для 32 групп...")
        print("Условия:")
        print("- 2 спортсмена из одного региона → разные половины")
        print("- 3-4 спортсмена из одного региона → разные четверти")
        print("- Более 4 спортсменов → без ограничений")

        placement = draw_32_groups(sportsmen_32)

        if placement:
            print_results(placement, sportsmen_32, "РЕЗУЛЬТАТЫ ЖЕРЕБЬЕВКИ (32 группы)")

            # Проверяем условия по регионам
            if check_region_constraints(placement, sportsmen_32):
                print("\n✓ Условия по регионам выполнены!")
            else:
                print("\n✗ Условия по регионам НЕ выполнены!")
        else:
            print("Не удалось выполнить жеребьевку")

    elif choice == "2":
        print("\nВыполняем жеребьевку для 16 групп...")
        print("Условия:")
        print("- Спортсмены из одной группы → разные половины")
        print("- Для 1-х мест действуют условия по регионам")

        placement = draw_16_groups(sportsmen_16)

        if placement:
            print_results(placement, sportsmen_16, "РЕЗУЛЬТАТЫ ЖЕРЕБЬЕВКИ (16 групп)")

            # Проверяем условие по группам
            print("\nПроверка условия по группам:")
            group_pairs = {}
            for idx, sportsman in enumerate(sportsmen_16):
                group = sportsman[3]
                if group not in group_pairs:
                    group_pairs[group] = []
                group_pairs[group].append(idx)

            all_good = True
            for group, indices in group_pairs.items():
                if len(indices) == 2:
                    # Находим позиции этих спортсменов
                    positions = []
                    for table_num, sportsman_idx in placement.items():
                        if sportsman_idx in indices:
                            positions.append(table_num)

                    if len(positions) == 2:
                        halves = [get_half(pos) for pos in positions]
                        if len(set(halves)) != 2:
                            print(f"✗ Группа {group}: оба спортсмена в одной половине")
                            all_good = False
                        else:
                            print(f"✓ Группа {group}: спортсмены в разных половинах")

            if all_good:
                print("\n✓ Все условия по группам выполнены!")
            else:
                print("\n✗ Не все условия по группам выполнены!")
    else:
        print("Неверный выбор!")

if __name__ == "__main__":
    main()