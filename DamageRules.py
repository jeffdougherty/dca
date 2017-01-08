from random import randrange
from helperfunctions import connect_to_db, close_connection, to_precision

def shell_bomb_hit(target, column_index_dict, dp, armor_pen, d6, d20):

    aviation_ships = ['CVL', 'CV', 'CVE', 'AV', 'AVP', 'AVT', 'AVM']

    cursor, conn = connect_to_db(returnConnection=True)
    print target
    remaining_points = target[column_index_dict['Damage Pts']] - dp
    #First thing, check to see if the ship's sunk
    if remaining_points <= 0:
        return sink_ship(target, column_index_dict)
    #else
    log_string = target[column_index_dict['Ship Name']] + " hit for " + str(dp) + " DP by shell/bomb. "
    cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Damage Pts] = ?;""",(remaining_points,))
    #Check for speed reduction
    log_string += check_speed_reduction(target, column_index_dict, remaining_points)
    #Now we start checking for crits

    damage_ratio = float(dp / remaining_points)
    if damage_ratio <= 0.10:
        damage_ratio_dict = {6: 1}
    elif damage_ratio <= 0.20:
        damage_ratio_dict = {5: 1, 6: 2}
    elif damage_ratio <= 0.30:
        damage_ratio_dict = {4: 1, 5: 2, 6: 3}
    elif damage_ratio <= 0.40:
        damage_ratio_dict = {3: 1, 4: 2, 5: 3, 6: 4}
    elif damage_ratio <= 0.50:
        damage_ratio_dict = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5}
    elif damage_ratio <= 0.60:
        damage_ratio_dict = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6}
    elif damage_ratio <= 0.70:
        damage_ratio_dict = {1: 2, 2: 3, 3: 4, 5: 6, 6: 7}
    elif damage_ratio <= 0.80:
        damage_ratio_dict = {1: 3, 2: 4, 3: 5, 4: 6, 5: 7, 6: 8}
    elif damage_ratio <= 0.90:
        damage_ratio_dict = {1: 4, 2: 5, 3: 6, 4: 7, 5: 8, 6: 9}
    elif damage_ratio <= 1.00:
        damage_ratio_dict = {1: 5, 2: 6, 3: 7, 4: 8, 5: 9, 6: 10}
    elif damage_ratio <= 1.20:
        damage_ratio_dict = {1: 6, 2: 7, 3: 8, 4: 9, 5: 10, 6: 11}
    elif damage_ratio < 3.00:
        damage_ratio_dict = {1: 6, 2: 7, 3: 8, 4: 9, 5: 10, 6: 11}
        addl_crits = int((damage_ratio - 1.00) / 0.2)
        for this_key in damage_ratio_dict.keys():
            damage_ratio_dict[this_key] = damage_ratio_dict[this_key] + addl_crits
    else:
        pass
        # !!! Massive damage kicks in
    if d6 == None: #No value supplied for debug mode
        d6 = rolld6()

    num_crits = damage_ratio_dict[d6]




def sink_ship(target, column_index_dict):
    cursor, conn = connect_to_db(returnConnection=True)
    ship_id_info = get_ship_id_info(target, column_index_dict)
    cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Critical Hits] = 'SUNK', [Damage Pts]=0 WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""",(ship_id_info))
    conn.commit()
    close_connection(cursor)
    return target[column_index_dict['Ship Name']] + " runs out of DP and sinks!"

def check_speed_reduction(target, column_index_dict, remaining_points):
    cursor, conn = connect_to_db(returnConnection=True)

    if remaining_points <= 0.25 * target[column_index_dict['Damage Pts Start']]:
        new_speed = float(to_precision(target[column_index_dict['Speed']] * 0.25, 3))
    elif remaining_points <= 0.5 * target[column_index_dict['Damage Pts Start']]:
        new_speed = float(to_precision(target[column_index_dict['Speed']] * 0.5, 3))
    elif remaining_points <= 0.75 * target[column_index_dict['Damage Pts Start']]:
        new_speed = float(to_precision(target[column_index_dict['Speed']] * 0.75, 3))
    else:
        new_speed = None
        addl_log_string = ""

    if new_speed != None:
        cursor.execute("""UDPATE 'Game Ship Formation Ship' SET [Speed Damaged]=?;""", (new_speed,))
        addl_log_string = "Speed reduced to " + str(new_speed) + "knots. "
        # !!! Will need something here to take in the effect of engineering criticals
        conn.commit()
        close_connection(cursor)

    return addl_log_string

def get_ship_id_info(target, column_index_dict):
    game_id = target[column_index_dict['Game ID']]
    side_index = target[column_index_dict['Scenario Side']]
    formation_id = target[column_index_dict['Formation ID']]
    formation_ship_key = target[column_index_dict['Formation Ship Key']]
    return (game_id, side_index, formation_id, formation_ship_key,)

def rolld6():
    return randrange(1, 6)

def rolld20():
    return randrange(1, 20)