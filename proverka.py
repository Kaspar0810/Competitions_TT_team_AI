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

# Структуры для отслеживания распределения
region_half = {} # регион -> {половина: количество}
region_quarter = {} # регион -> {четверть: количество}

def initialize_region_tracking():
    """Инициализация структур для отслеживания распределения регионов"""
    for sportsman in sorted_sportsmen:
        region = sportsman[1]
        if region not in region_half:
            region_half[region] = {1: 0, 2: 0}
        if region not in region_quarter:
            region_quarter[region] = {1: 0, 2: 0, 3: 0, 4: 0}

# Инициализируем структуры для отслеживания
initialize_region_tracking()

# Посев 1: позиции 1 и 32
table[1] = sorted_sportsmen[0] # Самый сильный спортсмен
region_half[sorted_sportsmen[0][1]][1] += 1
region_quarter[sorted_sportsmen[0][1]][1] += 1

table[32] = sorted_sportsmen[1] # Второй по силе спортсмен
region_half[sorted_sportsmen[1][1]][2] += 1
region_quarter[sorted_sportsmen[1][1]][4] += 1

# Обработанные спортсмены
used_sportsmen_indices = [0, 1]

# Функция для определения, куда можно разместить спортсмена
def get_allowed_positions_for_sportsman(sportsman, available_positions, seed_num):
    """Определить разрешенные позиции для спортсмена"""
    region = sportsman[1]
    allowed_positions = []

    for pos in available_positions:
        half = get_half(pos)
        quarter = get_quarter(pos)

# Для 2-го посева: если спортсмен из того же региона,
# который уже есть в половине, то уйти в другую половину
        if seed_num == 2:
            if region_half[region][half] > 0:
                continue # Пропускаем эту позицию - регион уже есть в этой половине
            else:
                allowed_positions.append(pos)

                # Для 3-го посева:
        elif seed_num == 3:
        # Если это второй спортсмен из региона
            count_in_half = region_half[region][half]
            count_in_quarter = region_quarter[region][quarter]

            # 2-й спортсмен из региона должен уйти в другую половину
            if sum(region_half[region].values()) == 1:
                if half == 1 and region_half[region][1] > 0:
                    continue # Уже есть в первой половине, нужно во вторую
                elif half == 2 and region_half[region][2] > 0:
                    continue # Уже есть во второй половине, нужно в первую

            # 3-й и 4-й спортсмены из региона должны быть в разных четвертях
            elif sum(region_quarter[region].values()) >= 2 and sum(region_quarter[region].values()) < 4:
                if region_quarter[region][quarter] > 0:
                    continue # В этой четверти уже есть спортсмен из этого региона

            allowed_positions.append(pos)

        # Для 4-го и 5-го посевов: если уже 4 или более спортсменов в четверти,
        # ограничение не действует
        elif seed_num >= 4:
            if region_quarter[region][quarter] >= 4:
                allowed_positions.append(pos)
            else:
            # Проверяем, можно ли разместить (в четверти меньше 4)
                allowed_positions.append(pos)

        return allowed_positions

# Функция для жеребьевки посева
def draw_seed(seed_num, sportsmen_indices):
    """Жеребьевка для посева"""
    positions = seeds[seed_num].copy()
    random.shuffle(positions) # Перемешиваем позиции

    # Для каждого спортсмена в посеве
    for sportsman_idx in sportsmen_indices:
        sportsman = sorted_sportsmen[sportsman_idx]
        region = sportsman[1]

        # Получаем разрешенные позиции с учетом правил
        allowed_positions = get_allowed_positions_for_sportsman(sportsman, positions, seed_num)

        # Если есть разрешенные позиции, выбираем случайную
        if allowed_positions:
            position = random.choice(allowed_positions)
        else:
            # Если нет разрешенных позиций, берем любую доступную
            position = positions[0]

        # Удаляем выбранную позицию из доступных
        positions.remove(position)

        # Размещаем спортсмена в таблице
        table[position] = sportsman

        # Обновляем счетчики
        half = get_half(position)
        quarter = get_quarter(position)
        region_half[region][half] += 1
        region_quarter[region][quarter] += 1

        # Помечаем спортсмена как использованного
        used_sportsmen_indices.append(sportsman_idx)

        # Отладочный вывод
        print(f"Посев {seed_num}: {sportsman[0]} ({region}) -> позиция {position} (четверть {quarter}, половина {half})")

# Посев 2: спортсмены 3 и 4 (индексы 2 и 3)
print("\n=== Посев 2 ===")
draw_seed(2, [2, 3])

# Посев 3: спортсмены 5, 6, 7, 8 (индексы 4, 5, 6, 7)
print("\n=== Посев 3 ===")
draw_seed(3, [4, 5, 6, 7])

# Посев 4: спортсмены 9, 10, 11, 12, 13, 14, 15, 16 (индексы 8-15)
print("\n=== Посев 4 ===")
draw_seed(4, list(range(8, 16)))

# Посев 5: оставшиеся спортсмены (индексы 16-31)
print("\n=== Посев 5 ===")
remaining_indices = [i for i in range(len(sorted_sportsmen)) if i not in used_sportsmen_indices]
draw_seed(5, remaining_indices)

# Вывод результатов
print("\n" + "="*80)
print("ИТОГОВАЯ ТАБЛИЦА ЖЕРЕБЬЁВКИ:")
print("="*80)
print(f"{'Позиция':<8} {'Фамилия':<15} {'Регион':<25} {'Рейтинг':<8} {'Четверть':<10} {'Половина':<8}")
print("-"*80)

for position in range(1, 33):
    sportsman = table[position]
    quarter = get_quarter(position)
    half = get_half(position)
print(f"{position:<8} {sportsman[0]:<15} {sportsman[1]:<25} {sportsman[2]:<8} {quarter:<10} {half:<8}")

# Статистика по регионам
print("\n" + "="*80)
print("СТАТИСТИКА ПО РЕГИОНАМ:")
print("="*80)

for region in sorted(region_quarter.keys()):
    print(f"\n{region}:")
print(f" Всего спортсменов: {sum(region_quarter[region].values())}")

# По половинам
print(f" По половинам: Первая - {region_half[region][1]}, Вторая - {region_half[region][2]}")

# По четвертям
for q in [1, 2, 3, 4]:
     count = region_quarter[region][q]
if count > 0:
    print(f" Четверть {q}: {count} спортсменов")

# Проверка правильности распределения
print("\n" + "="*80)
print("ПРОВЕРКА РАСПРЕДЕЛЕНИЯ:")
print("="*80)

all_correct = True
for region in region_quarter:
    for q in [1, 2, 3, 4]:
        count = region_quarter[region][q]
        if count > 4:
            print(f"⚠ Внимание: в регионе '{region}' в четверти {q} больше 4 спортсменов ({count})")
            all_correct = False
        elif count <= 4:
            print(f"✓ Регион '{region}', четверть {q}: {count} спортсменов - OK")

        # Проверка для 2-го посева
        print("\nПроверка для 2-го посева (спортсмены из одного региона в разных половинах):")
        for region in region_half:
            if region_half[region][1] > 0 and region_half[region][2] > 0:
                # Проверяем спортсменов 3 и 4
                print(f" Регион '{region}': есть в обеих половинах - OK")

    if all_correct:
        print("\n✓ Все правила распределения соблюдены!")
    else:
        print("\n⚠ Нарушены некоторые правила распределения!")