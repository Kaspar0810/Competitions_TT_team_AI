def create_semi_final_2():
    print("\n" + "="*50)
    print("СОЗДАНИЕ 2-го ПОЛУФИНАЛА")
    print("="*50)
    
    # Создаем 16 групп для второго полуфинала
    sf2_groups = []
    for i in range(1, 17):
        sf2_groups.append({
            'sf_group_num': i,
            'players': [],
            'from_groups': []
        })
    
    # 1-й ЭТАП: Добавляем игроков с 1-2 мест из групп 1-16
    print("\n--- 1-й ЭТАП: Игроки с 1-2 мест из групп 1-16 ---")
    for group_num in range(1, 17):
        players = get_players_by_group_and_place(group_num, [1, 2])
        if players:
            # Находим соответствующую группу полуфинала (такой же номер)
            for g in sf2_groups:
                if g['sf_group_num'] == group_num:
                    g['players'].extend(players)
                    g['from_groups'].append(group_num)
                    print(f"Группа {group_num}: добавлено {len(players)} игроков с 1-2 мест")
                    for p in players:
                        print(f"  - {p.family} ({p.region}) - {p.mesto_group} место")
                    break
    
    # Выводим текущее состояние групп после 1-го этапа
    print("\n--- СОСТОЯНИЕ ГРУПП ПОСЛЕ 1-го ЭТАПА ---")
    for g in sf2_groups:
        print(f"Группа {g['sf_group_num']}: {len(g['players'])} игроков")
        for p in g['players']:
            print(f"  - {p.family} ({p.region})")
    
    # 2-й, 3-й, 4-й ЭТАПЫ: Добавление игроков из групп 17-32
    print("\n--- 2-й, 3-й, 4-й ЭТАПЫ: Добавление игроков из групп 17-32 ---")
    
    # Собираем игроков с 3-4 мест из групп 17-32
    groups_17_32_players = []
    for group_num in range(17, 33):
        players = get_players_by_group_and_place(group_num, [3, 4])
        if players:
            groups_17_32_players.append({
                'group_num': group_num,
                'players': players
            })
    
    print(f"\nИгроки из групп 17-32 для добавления:")
    for g in groups_17_32_players:
        print(f"  Группа {g['group_num']}: {len(g['players'])} игроков")
        for p in g['players']:
            print(f"    - {p.family} ({p.region}) - {p.mesto_group} место")
    
    # Создаем список для отслеживания еще не обработанных групп
    # Начинаем с группы 17
    pending_groups = groups_17_32_players.copy()
    processed_groups = set()
    
    # Продолжаем, пока есть необработанные группы
    while pending_groups:
        # Берем первую необработанную группу
        source_group = pending_groups.pop(0)
        source_group_num = source_group['group_num']
        
        # Определяем целевую группу полуфинала (17→16, 18→15, 19→14 и т.д.)
        target_group_num = 33 - source_group_num
        
        print(f"\n--- Обработка группы {source_group_num} (целевая группа {target_group_num}) ---")
        print(f"  Игроки для добавления: {[p.family for p in source_group['players']]}")
        
        # Находим целевую группу полуфинала
        target_group = None
        for g in sf2_groups:
            if g['sf_group_num'] == target_group_num:
                target_group = g
                break
        
        if target_group:
            # Проверяем текущее количество игроков в целевой группе
            current_count = len(target_group['players'])
            new_count = current_count + len(source_group['players'])
            
            print(f"  Текущее количество в группе {target_group_num}: {current_count}")
            print(f"  После добавления будет: {new_count}")
            
            if new_count >= 3:
                # Если после добавления будет 3 или более игроков, добавляем
                print(f"  ✓ Добавляем игроков в группу {target_group_num}")
                target_group['players'].extend(source_group['players'])
                target_group['from_groups'].append(source_group_num)
                processed_groups.add(source_group_num)
            else:
                # Если менее 3, ищем группу выше для перемещения
                print(f"  ✗ После добавления будет {new_count} игроков (<3)")
                print(f"  Смещаем игроков группы {source_group_num} в группу {target_group_num - 1}")
                
                # Смещаем на одну группу выше
                new_target_group_num = target_group_num - 1
                
                # Находим новую целевую группу
                new_target_group = None
                for g in sf2_groups:
                    if g['sf_group_num'] == new_target_group_num:
                        new_target_group = g
                        break
                
                if new_target_group:
                    new_current_count = len(new_target_group['players'])
                    new_new_count = new_current_count + len(source_group['players'])
                    
                    print(f"  Проверяем группу {new_target_group_num}: текущее {new_current_count}, после добавления {new_new_count}")
                    
                    if new_new_count >= 3:
                        print(f"  ✓ Добавляем игроков в группу {new_target_group_num}")
                        new_target_group['players'].extend(source_group['players'])
                        new_target_group['from_groups'].append(source_group_num)
                        processed_groups.add(source_group_num)
                        
                        # Важно: после успешного добавления, следующую группу (source_group_num + 1)
                        # будем обрабатывать с ее целевой группой, но нужно проверить,
                        # не была ли уже обработана группа new_target_group_num? 
                        # По условию, следующая группа (18) должна идти в 16-ю, которая еще не была в жеребьевке
                        # То есть нужно начать сначала с целевой группы для следующей группы
                        print(f"  Следующая группа будет обрабатываться со своей целевой группы")
                    else:
                        print(f"  ✗ В группе {new_target_group_num} после добавления будет {new_new_count} (<3)")
                        print(f"  Продолжаем смещение выше...")
                        
                        # Если и здесь менее 3, продолжаем смещать вверх, пока не найдем подходящую группу
                        found_suitable = False
                        for shift in range(2, target_group_num):
                            check_group_num = target_group_num - shift
                            if check_group_num < 1:
                                break
                            
                            check_group = None
                            for g in sf2_groups:
                                if g['sf_group_num'] == check_group_num:
                                    check_group = g
                                    break
                            
                            if check_group:
                                check_current_count = len(check_group['players'])
                                check_new_count = check_current_count + len(source_group['players'])
                                
                                print(f"  Проверяем группу {check_group_num}: текущее {check_current_count}, после добавления {check_new_count}")
                                
                                if check_new_count >= 3:
                                    print(f"  ✓ Добавляем игроков в группу {check_group_num}")
                                    check_group['players'].extend(source_group['players'])
                                    check_group['from_groups'].append(source_group_num)
                                    processed_groups.add(source_group_num)
                                    found_suitable = True
                                    break
                        
                        if not found_suitable:
                            # Если не нашли подходящую группу, добавляем в самую верхнюю возможную
                            print(f"  Не найдено подходящей группы, добавляем в группу 1")
                            group_1 = None
                            for g in sf2_groups:
                                if g['sf_group_num'] == 1:
                                    group_1 = g
                                    break
                            if group_1:
                                group_1['players'].extend(source_group['players'])
                                group_1['from_groups'].append(source_group_num)
                                processed_groups.add(source_group_num)
                
                # После обработки текущей группы со смещением, 
                # следующая группа (source_group_num + 1) будет обрабатываться
                # со своей целевой группой (33 - (source_group_num + 1))
                # Это автоматически выполнится на следующей итерации цикла
    
    # Проверяем итоговое состояние групп
    print("\n" + "="*50)
    print("ИТОГОВОЕ СОСТОЯНИЕ ГРУПП 2-го ПОЛУФИНАЛА")
    print("="*50)
    
    for g in sf2_groups:
        print(f"\nГруппа {g['sf_group_num']}: {len(g['players'])} игроков")
        print(f"  Из групп: {g['from_groups']}")
        for p in g['players']:
            print(f"    - {p.family} ({p.region}) - место в группе: {p.mesto_group}")
    
    # Проверяем, что во всех группах 3 или 4 игрока
    print("\n--- ПРОВЕРКА ---")
    all_valid = True
    for g in sf2_groups:
        count = len(g['players'])
        if count < 3 or count > 4:
            print(f"⚠️ Группа {g['sf_group_num']}: {count} игроков (должно быть 3 или 4)")
            all_valid = False
        else:
            print(f"✓ Группа {g['sf_group_num']}: {count} игроков")
    
    if all_valid:
        print("\n✓ Все группы сформированы корректно (3-4 игрока)")
    else:
        print("\n⚠️ Есть группы с некорректным количеством игроков")
    
    return sf2_groups