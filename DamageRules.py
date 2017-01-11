from random import randrange
from helperfunctions import connect_to_db, close_connection, to_precision
import tkMessageBox

AVIATION_SHIPS = ['CVL', 'CV', 'CVE', 'AV', 'AVP', 'AVT', 'AVM', 'CA'] #!!!!! Removed 'CA' before release!  Debug only!
MERCHANT_AUXILIARY = ['AM', 'LSI', 'LCF', 'LCG', 'LCI(L)', 'LCS(L)', 'LCT(R)', 'LSD', 'AC', 'LCP', 'AO', 'AF', 'AK', 'APD']

def shell_bomb_hit(target, dp, hit_type, armor_pen, d6=None, d20_list=None):

    cursor, conn = connect_to_db(returnConnection=True)
    print target
    if armor_pen == False:
        dp = int(dp * 0.5)
    remaining_points = target['Damage Pts'] - dp
    #First thing, check to see if the ship's sunk
    if remaining_points <= 0:
        log_string = target['Ship Name'] + 'runs out of DP ' + sink_ship(target)
        return log_string
    #else
    log_string = target['Ship Name'] + " hit for " + str(dp) + " DP by shell/bomb. "
    ship_info = get_ship_id_info(target)
    cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Damage Pts] = ? WHERE [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",(remaining_points,ship_info[0],ship_info[1], ship_info[2], ship_info[3],))
    conn.commit()
    close_connection(cursor)

    #Check for speed reduction
    log_string += check_speed_reduction(target, remaining_points)
    #Check for massive damage
    massive_damage_result = check_massive_damage(target, dp, remaining_points, hit_type)
    if 'sinks' in massive_damage_result:
        return massive_damage_result #Massive damage sank the ship, terminate function
    else:
        log_string += massive_damage_result
    #Now we start checking for crits

    #!!!Auto crits first
    if hit_type == 'Bomb' and target['Ship Type'] in AVIATION_SHIPS and armor_pen:
        if tkMessageBox.askyesno(title='Bomb', message='Is the bomb 100 lb/50 kg or more?'):
            apply_crit('Flight Deck')
    elif hit_type == 'Shell' and target['Ship Type'] in AVIATION_SHIPS and armor_pen:
        if tkMessageBox.askyesno(message='Was the ship hit by >= 120mm fire at Long or Extreme range?'):
            die = rolld10()
            if tkMessageBox.askyesno(message='Was the ship at Extreme range when it was hit?'):
                deck_hit = (die <= 7)
            else:
                deck_hit = (die <= 6)
            if deck_hit:
                apply_crit('Flight Deck')

    #Regular crit rolling
    damage_ratio = float(dp / remaining_points)
    if dp / target['Damage Pts Start'] <= 0.01:
        damage_ratio_dict = {}
    elif damage_ratio < 0.10:
        damage_ratio_dict = {6: 1}
    elif damage_ratio < 0.20:
        damage_ratio_dict = {5: 1, 6: 2}
    elif damage_ratio < 0.30:
        damage_ratio_dict = {4: 1, 5: 2, 6: 3}
    elif damage_ratio < 0.40:
        damage_ratio_dict = {3: 1, 4: 2, 5: 3, 6: 4}
    elif damage_ratio < 0.50:
        damage_ratio_dict = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5}
    elif damage_ratio < 0.60:
        damage_ratio_dict = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6}
    elif damage_ratio < 0.70:
        damage_ratio_dict = {1: 2, 2: 3, 3: 4, 5: 6, 6: 7}
    elif damage_ratio < 0.80:
        damage_ratio_dict = {1: 3, 2: 4, 3: 5, 4: 6, 5: 7, 6: 8}
    elif damage_ratio < 0.90:
        damage_ratio_dict = {1: 4, 2: 5, 3: 6, 4: 7, 5: 8, 6: 9}
    elif damage_ratio < 1.00:
        damage_ratio_dict = {1: 5, 2: 6, 3: 7, 4: 8, 5: 9, 6: 10}
    elif damage_ratio < 1.20:
        damage_ratio_dict = {1: 6, 2: 7, 3: 8, 4: 9, 5: 10, 6: 11}
    elif damage_ratio < 3.00:
        damage_ratio_dict = {1: 6, 2: 7, 3: 8, 4: 9, 5: 10, 6: 11}
        addl_crits = int((damage_ratio - 1.00) / 0.2)
        for this_key in damage_ratio_dict.keys():
            damage_ratio_dict[this_key] = damage_ratio_dict[this_key] + addl_crits
    else:
        # !!! Massive damage kicks in
        log_string += 'Reduced to 10% DP by massive damage.  '
        new_dp = 0.1 * target['Damage Pts Start']
        cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Damage Pts]=?;""",(new_dp,))
        return log_string

    if d6 == None: #No value supplied for debug mode
        d6 = rolld6()

    if d6 in damage_ratio_dict.keys():
        num_crits = damage_ratio_dict[d6]
    else:
        num_crits = 0

    for i in range(num_crits):
        if d20_list != None:
            crit_tuple = roll_for_crits(target, armor_pen, d20_list)
            this_crit = crit_tuple[0]
            d20_list = crit_tuple[1]
        else:
            this_crit = roll_for_crits(target, armor_pen, d20_list)
        if this_crit == 'Unsupported Ship':
            return 'Unsupported Ship'
        if this_crit != None:
            apply_crit(this_crit)


def sink_ship(target):
    cursor, conn = connect_to_db(returnConnection=True)
    ship_id_info = get_ship_id_info(target)
    cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Critical Hits] = 'SUNK', [Damage Pts]=0 WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""", ship_id_info)
    conn.commit()
    close_connection(cursor)
    return target['Ship Name'] + "and sinks!"


def check_speed_reduction(target, remaining_points):
    cursor, conn = connect_to_db(returnConnection=True)
    addl_log_string = ""
    target_speed_start = float(to_precision(float(target['Speed']), 3))
    if remaining_points <= 0.25 * target['Damage Pts Start']:
        #new_speed = float(to_precision(target['Speed'] * 0.25, 3))
        new_speed = target_speed_start * 0.25
    elif remaining_points <= 0.5 * target['Damage Pts Start']:
        #new_speed = float(to_precision(target['Speed'] * 0.5, 3))
        new_speed = target_speed_start * 0.5
    elif remaining_points <= 0.75 * target['Damage Pts Start']:
        #new_speed = float(to_precision(target['Speed'] * 0.75, 3))
        new_speed = target_speed_start * 0.75
    else:
        new_speed = None

    if new_speed != None:
        cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Speed Damaged]=?;""", (new_speed,))
        addl_log_string = "Speed reduced to " + str(new_speed) + "knots. "
        # !!! Will need something here to take in the effect of engineering criticals
        conn.commit()
        close_connection(cursor)
    return addl_log_string

def check_massive_damage(target, dp, remaining_points, hit_type):
    log_string = ""
    crossed_25_this_hit = False
    #Check to see if massive damage sinks the ship
    if dp >= (0.75 * target['Damage Pts Start']):
        roll = rolld10()
        if (roll <= 4 and hit_type == 'Bomb') or (roll <= 8 and hit_type == 'Torpedo/Mine'):
            return ' takes massive damage from a single hit ' + sink_ship(target)
        else:
            print "Massive damage checked, ship not sunk"

    if (remaining_points <= 0.25 * target['Damage Pts Start']) and target['25% Threshold Crossed'] == 0:
        #Just crossed the 25% threshold
        ship_id_info = get_ship_id_info(target)
        cursor, conn = connect_to_db(returnConnection=True)
        cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [25% Threshold Crossed] = 1 WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""", ship_id_info)
        cursor.execute("""UPDATE 'Game Ship Gun Mount' SET [Crit Mount] = 1 WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""", ship_id_info)
        conn.commit()
        close_connection(cursor)
        log_string = ' reaches 25% of original DP, all main/secondary guns out, flight deck damaged. '
        crossed_25_this_hit = True
    if (remaining_points <= 0.10 * target['Damage Pts Start'] and target['10% Threshold Crossed'] == 0):
        # Just crossed the 10% threshold
        ship_id_info = get_ship_id_info(target)
        cursor, conn = connect_to_db(returnConnection=True)
        cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [10% Threshold Crossed] = 1 WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""", ship_id_info)
        cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Area AA Damaged Rating] = 0 WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""", ship_id_info)
        cursor.execute("""UPDATE 'Game Ship Foramtion Ship' SET [Light AA Damaged Rating] = 0 WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""", ship_id_info)
        cursor.execute("""UPDATE 'Game Ship Torp Mount' SET [Crit Mount] = 1 WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""", ship_id_info)
        cursor.execute("""UPDATE 'Game Ship Other Mount' SET [Crit Mount] = 1 WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""", ship_id_info)
        conn.commit()
        close_connection()
        if crossed_25_this_hit:
            log_string += ' Also reaches 10% of original DP, all weapons out.  '
        else:
            log_string += ' reaches 10% of original DP, all weapons out. '
    return log_string

def roll_for_crits(target, armor_pen, d20_list):
    d20_list = d20_list #Defensive programming to make sure we have a local copy to mutate
    this_ship_type = target['Ship Type']
    this_size_class = target['Size Class']
    if this_ship_type in MERCHANT_AUXILIARY:
        crit_dict = {1: 'Cargo', 2: 'Cargo', 3: 'Cargo', 4: 'Cargo', 5: 'Cargo', 6: 'Cargo', 7: 'Cargo', 8: 'Weapon', 9: 'Weapon', 10: 'Engineering', 11: 'Engineering', 12: 'Flooding', 13: 'Flooding', 14: 'Flooding', 15: 'Fire', 16: 'Fire', 17: 'Fire', 18: 'Sensor/Comms', 19: 'Bridge', 20: 'Rudder'}
    elif this_ship_type in AVIATION_SHIPS:
        crit_dict = {1: 'Flight Deck*', 2: 'Flight Deck*', 3: 'Flight Deck*', 4: 'Other Wpn', 5: 'Other Wpn', 6: 'Ammo/Fuel*', 7:'Ammo/Fuel*', 8:'Light AA', 9: 'Light AA', 10: 'Engineering*', 11: 'Engineering*', 12: 'Flooding', 13: 'Flooding', 14: 'Flooding', 15: 'Fire', 16: 'Fire', 17: 'Fire', 18: 'Sensor/Comms', 19: 'Bridge*', 20: 'Rudder*'}
        #RAW indicate you need to penetrate armor to do a sensor/comms hit on an aviation ship, but I think that's a misprint
    elif this_size_class == 'A' or this_size_class == 'B':
        #Major surface combatant
        crit_dict = {1: 'Main Battery*', 2: 'Main Battery*', 3: 'Main Battery*', 4: 'Sec Battery', 5: 'Sec Battery', 6: 'Other Wpn*', 7: 'Other Wpn*', 8: 'Light AA', 9: 'Light AA', 10: 'Engineering*', 11: 'Engineering*', 12: 'Flooding*', 13: 'Flooding*', 14: 'Flooding*', 15: 'Fire*', 16: 'Fire*', 17: 'Fire*', 18: 'Sensor/Comms', 19: 'Bridge*', 20: 'Rudder*'}
    elif this_size_class == 'C' or this_size_class == 'D':
        #Minor surface combatant
        crit_dict = {1: 'Main Battery*', 2: 'Main Battery*', 3: 'Main Battery*', 4: 'Other Wpn', 5: 'Other Wpn', 6: 'Other Wpn', 7: 'Other Wpn', 8: 'Light AA', 9: 'Light AA', 10: 'Engineering*', 11: 'Engineering*', 12: 'Flooding*', 13: 'Flooding*', 14: 'Flooding*', 15: 'Fire*', 16: 'Fire*', 17: 'Fire', 18: 'Sensor/Comms', 19: 'Bridge', 20: 'Rudder*'}
    else:
        return 'Unsupported Ship'
    if d20_list != None:
        d20 = d20_list.pop(0)
    else:
        d20 = rolld20()
    this_critical_hit = crit_dict[d20]
    if '*' in this_critical_hit:
        if armor_pen == False:
            this_critical_hit = None
        else:
            this_critical_hit = this_critical_hit[:-1] #Takes off the '*'
    if d20_list != None:
        return (this_critical_hit, d20_list)
    else:
        return this_critical_hit

def apply_crit(this_crit):
    pass

def get_ship_id_info(target):
    game_id = target['Game ID']
    side_index = target['Scenario Side']
    formation_id = target['Formation ID']
    formation_ship_key = target['Formation Ship Key']
    return (game_id, side_index, formation_id, formation_ship_key,)

def rolld6():
    return randrange(1, 6)

def rolld10():
    return randrange(1, 10)

def rolld20():
    return randrange(1, 20)