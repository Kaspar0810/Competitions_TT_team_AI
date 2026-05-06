import random
from typing import List, Tuple, Dict, Optional

# Данные спортсменов (16 группы)
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
    ["Снегов", "Ивановская обл.", 110, "14 группа", "1 место"],
    ["Волков", "Иркутская обл.", 310, "14 группа", "2 место"],
    ["Медведев", "Иркутская обл.", 160, "15 группа", "1 место"],
    ["Зайцев", "Иркутская обл.", 260, "15 группа", "2 место"],
    ["Лосев", "Саратовская обл.", 180, "16 группа", "1 место"],
    ["Тихонов", "Кемеровская обл.", 460, "16 группа", "2 место"]
]

# Данные спортсменов (32 групп)
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
    ["Снегов", "Ивановская обл.", 110, "14 группа", "1 место"],
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

def check_region_constraints(placement: Dict[int, List], sportsmen_data: List[List]) -> bool:
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

def draw_32_groups(sportsmen_data: List[List], max_attempts: int = 1000) -> Optional[Dict[int, List]]:
    """Жеребьевка для 32 групп"""
    # Сортируем по рейтингу (по убыванию)
    sorted_sportsmen = sorted(enumerate(sportsmen_data), key=lambda x: x[1][2], reverse=True)

    seeds = get_seed_groups()

    for attempt in range(max_attempts):
        # Создаем копию отсортированного списка для перемешивания
        shuffled = sorted_sportsmen.copy()

        # Перемешиваем 3-го и 4-го спортсменов (номера 16 и 17)
        if len(shuffled) > 3:
            # 1-й и 2-й остаются на своих местах
            # Меняем местами 3-го и 4-го с 50% вероятностью
            if random.random() > 0.5:
                shuffled[2], shuffled[3] = shuffled[3], shuffled[2]

        # Размещаем спортсменов согласно посевам
        placement = {i: None for i in range(1, 33)}

        # Распределяем по посевам
        seed_order = [1, 2, 3, 4, 5]
        # available_sportsmen = []
        for seed_num in seed_order:
            available_sportsmen = []
            # Берем спортсменов для текущего посева
            # число в подпосеве
            # m = 0
            count_sev = len(seeds[seed_num])
            for k in range(count_sev):
                txt = shuffled[k]
                available_sportsmen.append(txt)
            # =================
            # n = 0
            # for s in placement.keys():
            #     val = placement[s]
            #     if val is None:
            #         txt = shuffled[n]
            #         available_sportsmen.append(txt)
            #     n += 1
            #     if n == 32:
            #         break       # available_sportsmen = [s for s in shuffled if val is None]
            if not available_sportsmen:
                break

            # Получаем номера для текущего посева
            seed_positions = seeds[seed_num]

            # Для 5-го посева берем всех оставшихся
            if seed_num == 5:
                for i, (idx, _) in enumerate(available_sportsmen):
                    placement[seed_positions[i]] = idx
            else:
                # Размещаем спортсменов на позиции посева
                for pos in seed_positions:
                    if available_sportsmen:
                        sportsman_idx, _ = available_sportsmen.pop(0)
                        placement[pos] = sportsman_idx
                        shuffled.pop(0)
                check_region_constraints(placement, sportsmen_data)
        # Проверяем условия по регионам
        if check_region_constraints(placement, sportsmen_data):
            return placement

    print(f"Не удалось найти подходящее распределение за {max_attempts} попыток")
    return None

def draw_16_groups(sportsmen_data: List[List]) -> Dict[int, List]:
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

    # Посев для первых мест
    seed_order = [1, 2, 3, 4, 5]
    first_place_used = []

    for seed_num in seed_order:
        seed_positions = seeds[seed_num]
        available_positions = [pos for pos in seed_positions if placement[pos] is None]

        for pos in available_positions:
            if first_place_sorted:
                sportsman_idx, _ = first_place_sorted.pop(0)
                placement[pos] = sportsman_idx
                first_place_used.append(sportsman_idx)

    # Размещаем занявших 2-е место
    # Каждого второго места спортсмена размещаем в другую половину от его партнера по группе
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

def print_results(placement: Dict[int, List], sportsmen_data: List[List], title: str):
    """Выводит результаты жеребьевки"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"{'Номер':<8} {'Фамилия':<15} {'Регион':<20} {'Рейтинг':<10} {'Группа':<12} {'Место':<10}")
    print(f"{'-'*80}")

    for table_num in sorted(placement.keys()):
        sportsman_idx = placement[table_num]
        if sportsman_idx is not None:
            sportsman = sportsmen_data[sportsman_idx]
            print(f"{table_num:<8} {sportsman[0]:<15} {sportsman[1]:<20} {sportsman[2]:<10} {sportsman[3]:<12} {sportsman[4]:<10}")
        else:
            print(f"{table_num:<8} {'-':<15} {'-':<20} {'-':<10} {'-':<12} {'-':<10}")

    print(f"{'='*80}")

def main():
    """Основная функция"""
    print("Программа жеребьевки спортсменов")
    print("Выберите вариант:")
    print("1 - 32 группы")
    print("2 - 16 групп")

    choice = input("Ваш выбор (1 или 2): ").strip()

    if choice == "1":
        print("\nВыполняем жеребьевку для 32 групп...")
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
        placement = draw_16_groups(sportsmen_16)

        if placement:
            print_results(placement, sportsmen_16, "РЕЗУЛЬТАТЫ ЖЕРЕБЬЕВКИ (16 групп)")
        else:
            print("Не удалось выполнить жеребьевку")
    else:
        print("Неверный выбор!")

if __name__ == "__main__":
    main()
