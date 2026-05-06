
import random

# Исходные данные
sportsmen = [
    ["Иванов", "Москва", 450],
    ["Петров", "Москва", 435],
    ["Сидоров", "Москва", 429],
    ["Лазарев", "Москва", 480],
    ["Зырянов", "Москва", 520],
    ["Котов", "Свердловская обл.", 272],
    ["Ветров", "Свердловская обл.", 654],
    ["Лаптев", "Свердловская обл.", 320],
    ["Малышев", "Свердловская обл.", 400],
    ["Реутов", "Свердловская обл.", 250],
    ["Пушкин", "Вологодская обл.", 140],
    ["Клюкин", "Вологодская обл.", 300],
    ["Лермонтов", "Вологодская обл.", 290],
    ["Лапшин", "Вологодская обл.", 570],
    ["Стеклов", "Вологодская обл.", 420],
    ["Кротов", "Нижегородская обл.", 240],
    ["Киселев", "Нижегородская обл.", 235],
    ["Гусев", "Нижегородская обл.", 360],
    ["Бондаренко", "Нижегородская обл.", 125],
    ["Романов", "Нижегородская обл.", 255],
    ["Гладышев", "Тюменская обл.", 710],
    ["Павлов", "Тюменская обл.", 390],
    ["Шибаев", "Самарская обл.", 310],
    ["Лукин", "Самарская обл.", 410],
    ["Стоянов", "Оренбургская обл.", 320],
    ["Орлов", "Ивановская обл.", 515],
    ["Ветров", "Ивановская обл.", 110],
    ["Волков", "Иркутская обл.", 310],
    ["Медведев", "Иркутская обл.", 160],
    ["Зайцев", "Иркутская обл.", 260],
    ["Лосев", "Саратовская обл.", 180],
    ["Тихонов", "Кемеровская обл.", 460]
    ]

# Сортируем спортсменов по рейтингу (по убыванию)
sorted_sportsmen = sorted(sportsmen, key=lambda x: x[2], reverse=True)

# Определение четверти для номера
def get_quarter(position):
    if 1 <= position <= 8:
        return 1
    elif 9 <= position <= 16:
        return 2
    elif 17 <= position <= 24:
        return 3
    elif 25 <= position <= 32:
        return 4
    else:
        return None

# Определение половины для номера
def get_half(position):
    if 1 <= position <= 16:
        return 1
    else:
        return 2

# Посевы (номера в таблице)
seeds = {
    1: [1, 32],
    2: [16, 17],
    3: [8, 9, 24, 25],
    4: [4, 5, 12, 13, 20, 21, 28, 29],
    5: [2, 3, 6, 7, 10, 11, 14, 15, 18, 19, 22, 23, 26, 27, 30, 31]
    }

# Таблица для размещения спортсменов
table = {i: None for i in range(1, 33)}

# Счетчики для отслеживания распределения по четвертям
region_quarters = {} # регион -> {четверть: количество}

def initialize_region_quarters():
    """Инициализация структуры для отслеживания распределения регионов по четвертям"""
    for sportsman in sorted_sportsmen:
        region = sportsman[1]
        if region not in region_quarters:
            region_quarters[region] = {1: 0, 2: 0, 3: 0, 4: 0}

def get_allowed_positions(sportsman, available_positions):
    """Получить разрешенные позиции для спортсмена с учетом региональных ограничений"""
    region = sportsman[1]
    allowed_positions = []

    dict_region = region_quarters[region]
    count = sum(dict_region.values()) # кол-во игроков данного регионов посеянных

    if count <= 2:
        for pos in available_positions:
            quarter = get_half(pos)
            if region_quarters[region][quarter] >= 4:
                allowed_positions.append(pos)
            else:
            # Проверяем, можно ли разместить здесь спортсмена
            # (в четверти меньше 4 спортсменов из этого региона)
                if region_quarters[region][quarter] < 4:
                    allowed_positions.append(pos)
    else:
        for pos in available_positions:
            quarter = get_quarter(pos)
            if region_quarters[region][quarter] >= 4:
                allowed_positions.append(pos)
            else:
            # Проверяем, можно ли разместить здесь спортсмена
            # (в четверти меньше 4 спортсменов из этого региона)
                if region_quarters[region][quarter] < 4:
                    allowed_positions.append(pos)
# Если в этой четверти уже есть 4 или более спортсменов из региона,
# то ограничение не действует
    
    
        # if region_quarters[region][quarter] >= 4:
        #     allowed_positions.append(pos)
        # else:
        # # Проверяем, можно ли разместить здесь спортсмена
        # # (в четверти меньше 4 спортсменов из этого региона)
        #     if region_quarters[region][quarter] < 4:
        #         allowed_positions.append(pos)

    return allowed_positions

# Инициализируем структуру для отслеживания регионов
initialize_region_quarters()

# Посев 1: позиции 1 и 32
table[1] = sorted_sportsmen[0] # Самый сильный спортсмен
region_quarters[sorted_sportsmen[0][1]][1] += 1

table[32] = sorted_sportsmen[1] # Второй по силе спортсмен
region_quarters[sorted_sportsmen[1][1]][4] += 1

# Обработанные спортсмены
used_sportsmen = [0, 1]
available_sportsmen_indices = [i for i in range(len(sorted_sportsmen)) if i not in used_sportsmen]

# for seed_number in available_sportsmen_indices:
    # Функция для жеребьевки посева
def draw_seed(seed_number, sportsmen_indices):
    """Жеребьевка для посева"""
    positions = seeds[seed_number].copy()
    random.shuffle(positions) # Перемешиваем позиции

    # Для каждого спортсмена в посеве
    for i, sportsman_idx in enumerate(sportsmen_indices):
        sportsman = sorted_sportsmen[sportsman_idx]

        # Получаем доступные позиции
        available_positions = positions.copy()

        # Получаем разрешенные позиции с учетом региональных ограничений
        allowed_positions = get_allowed_positions(sportsman, available_positions)

        # Если есть разрешенные позиции, выбираем первую
        if allowed_positions:
            position = allowed_positions[0]
            positions.remove(position)
        else:
        # Если нет разрешенных позиций, берем любую доступную
            position = available_positions[0]
            positions.remove(position)

        # Размещаем спортсмена в таблице
        table[position] = sportsman

        # Обновляем счетчик для региона в соответствующей четверти
        quarter = get_quarter(position)
        region_quarters[sportsman[1]][quarter] += 1

        # Помечаем спортсмена как использованного
        used_sportsmen.append(sportsman_idx)

# Посев 2: спортсмены 3 и 4 (индексы 2 и 3)
draw_seed(2, [2, 3])

# Посев 3: спортсмены 5, 6, 7, 8 (индексы 4, 5, 6, 7)
draw_seed(3, [4, 5, 6, 7])

# Посев 4: спортсмены 9, 10, 11, 12, 13, 14, 15, 16 (индексы 8-15)
draw_seed(4, list(range(8, 16)))

    # Посев 5: оставшиеся спортсмены (индексы 16-31)
remaining_indices = [i for i in range(len(sorted_sportsmen)) if i not in used_sportsmen]
draw_seed(5, remaining_indices)

    # Вывод результатов
print("Результаты жеребьевки:")
print("-" * 80)
print(f"{'Позиция':<8} {'Фамилия':<15} {'Регион':<25} {'Рейтинг':<8} {'Четверть':<10}")
print("-" * 80)

for position in range(1, 33):
    sportsman = table[position]
    quarter = get_quarter(position)
print(f"{position:<8} {sportsman[0]:<15} {sportsman[1]:<25} {sportsman[2]:<8} {quarter:<10}")

print("\nРаспределение по четвертям:")
for region in region_quarters:
    print(f"{region}:")
for quarter in [1, 2, 3, 4]:
    count = region_quarters[region][quarter]
    print(f" Четверть {quarter}: {count} спортсменов")

    # Проверка корректности распределения
print("\nПроверка распределения:")
for region in region_quarters:
    for quarter in [1, 2, 3, 4]:
        if region_quarters[region][quarter] > 4:
            print(f"Внимание: в регионе {region} в четверти {quarter} больше 4 спортсменов ({region_quarters[region][quarter]})")
        elif region_quarters[region][quarter] <= 4:
            print(f"OK: в регионе {region} в четверти {quarter} {region_quarters[region][quarter]} спортсменов")
print(table)

# Этот код выполняет следующее:

# 1. Сортировка спортсменов: все спортсмены сортируются по рейтингу в порядке убывания.
# 2. Определение посевов: номера в таблице распределены по посевам согласно условию.
# 3. Жеребьевка:
# · Посев 1: самый сильный спортсмен идет на позицию 1, второй по силе - на позицию 32.
# · Посев 2: спортсмены 3 и 4 случайным образом распределяются на позиции 16 и 17 с учетом региональных ограничений.
# · Посев 3: спортсмены 5-8 распределяются на позиции 8, 9, 24, 25.
# · Посев 4: спортсмены 9-16 распределяются на позиции 4, 5, 12, 13, 20, 21, 28, 29.
# · Посев 5: оставшиеся спортсмены занимают все остальные позиции.
# 4. Региональные ограничения:
# · Счетчик отслеживает количество спортсменов из каждого региона в каждой четверти.
# · Если в четверти уже есть 4 спортсмена из одного региона, ограничение не действует.
# · В противном случае спортсмены из одного региона распределяются по разным четвертям.
# 5. Вывод результатов: таблица с распределением спортсменов по позициям и статистика по регионам.
