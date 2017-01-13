from random import randrange, choice
from helperfunctions import connect_to_db, close_connection, to_precision
import tkMessageBox

AVIATION_SHIPS = ['CVL', 'CV', 'CVE', 'AV', 'AVP', 'AVT', 'AVM', 'CA'] #!!!!! Removed 'CA' before release!  Debug only!
MERCHANT_AUXILIARY = ['AM', 'LSI', 'LCF', 'LCG', 'LCI(L)', 'LCS(L)', 'LCT(R)', 'LSD', 'AC', 'LCP', 'AO', 'AF', 'AK', 'APD']

def shell_bomb_hit(target, dp, hit_type, armor_pen, d6=None, d100_list=None):

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
                log_string += apply_crit('Flight Deck')

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
        cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Damage Pts]=? WHERE [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;;""",(new_dp,ship_info[0], ship_info[1], ship_info[2], ship_info[3],))
        return log_string

    if d6 == None: #No value supplied for debug mode
        d6 = rolld6()

    if d6 in damage_ratio_dict.keys():
        num_crits = damage_ratio_dict[d6]
    else:
        num_crits = 0

    for i in range(num_crits):
        if d100_list != None:
            this_crit = roll_for_crits(target, armor_pen, d100_list.pop(0))
        else:
            this_crit = roll_for_crits(target, armor_pen, rolld100())
        if this_crit == 'Unsupported Ship':
            return 'Unsupported Ship'
        if this_crit != None:
            log_string += apply_crit(target, this_crit)


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
    target_speed_thresholds = [target_speed_start, to_precision(target_speed_start * 0.75, 3), to_precision(target_speed_start * 0.5, 3), to_precision(target_speed_start * 0.25, 3), 0]
    if remaining_points <= 0.25 * target['Damage Pts Start']:
        #new_speed = float(to_precision(target['Speed'] * 0.25, 3))
        #new_speed = target_speed_start * 0.25
        current_speed_index = 1
    elif remaining_points <= 0.5 * target['Damage Pts Start']:
        #new_speed = float(to_precision(target['Speed'] * 0.5, 3))
        #new_speed = target_speed_start * 0.5
        current_speed_index = 2
    elif remaining_points <= 0.75 * target['Damage Pts Start']:
        #new_speed = float(to_precision(target['Speed'] * 0.75, 3))
        #new_speed = target_speed_start * 0.75
        current_speed_index = 3
    else:
        current_speed_index = 0

    current_speed_index += target['Crit Engineering']
    if current_speed_index > 4:
        current_speed_index = 4 #Can't be reduced to less than 0 knots.

    if target_speed_thresholds[current_speed_index] != target['Speed Damaged']:
        new_speed = target_speed_thresholds[current_speed_index]
        cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Speed Damaged]=?;""", (new_speed,))
        addl_log_string = "Speed reduced to " + str(new_speed) + "knots. "
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

"""
This functions were written using the critical hit tables in the written CaS 4.1 rules.  roll_for_crits is complete, apply_crit is not.
Being superseded by a revised function using the expanded CaS crit tables

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
"""

def roll_for_crits(target, armor_pen, d100):
    this_ship_type = target['Ship Type']
    this_size_class = target['Size Class']

    if this_ship_type in MERCHANT_AUXILIARY:
        if d100 <= 9:
            this_crit = 'Weapon - Mount Lost'
        elif d100 == 10:
            this_crit = 'Weapon - Magazine Detonates'
        elif d100 <= 45:
            this_crit = 'Cargo'
        elif d100 <= 50:
            this_crit = "Lt AA"
        elif d100 <= 59:
            this_crit = 'Engineering'
        elif d100 == 60:
            this_crit = 'Boiler Explosion'
        elif d100 <= 75:
            this_crit = 'Floodinig'
        elif d100 <= 90:
            this_crit = 'Fire'
        elif d100 <= 92:
            this_crit = 'Sensor'
        elif d100 <= 94:
            this_crit = 'Comms'
        elif d100 == 95:
            this_crit = 'Bridge - straight'
        elif d100 == 96:
            this_crit = 'Bridge - starboard'
        elif d100 == 97:
            this_crit = 'Bridge - port'
        elif d100 == 98:
            this_crit = 'Rudder - port'
        elif d100 == 99:
            this_crit = 'Rudder - starboard'
        elif d100 == 100:
            this_crit = 'Rudder - straight'

    elif this_ship_type in AVIATION_SHIPS:
        if d100 <= 12:
            this_crit = 'Flight Deck*'
        elif d100 <= 15:
            this_crit = 'Elevator'
        elif d100 <= 24:
            this_crit = 'Weapon - Mount Lost*'
        elif d100 == 25:
            this_crit = 'Weapon - Magazine Detonates*'
        elif d100 <= 28:
            this_crit = 'Aviation Ammo - Explodes*'
        elif d100 == 29:
            this_crit = 'Aviation Ammo - Explodes, Ship Sunk*'
        elif d100 <= 35:
            this_crit = 'Aviation Fuel*'
        elif d100 <= 45:
            this_crit = 'Lt AA'
        elif d100 <= 59:
            this_crit = 'Engineering*'
        elif d100 == 60:
            this_crit = 'Boiler Explosion*'
        elif d100 <= 75:
            this_crit = 'Flooding*'
        elif d100 <= 90:
            this_crit = 'Fire*'
        elif d100 <= 93:
            this_crit = 'Sensor'
        elif d100 == 94:
            this_crit = 'Comms'
        elif d100 == 95:
            this_crit = 'Bridge - straight*'
        elif d100 == 96:
            this_crit = 'Bridge - starboard*'
        elif d100 == 97:
            this_crit = 'Bridge - port*'
        elif d100 == 98:
            this_crit = 'Rudder - port*'
        elif d100 == 99:
            this_crit = 'Rudder - starboard*'
        elif d100 == 100:
            this_crit = 'Rudder - straight*'

    elif this_size_class == 'A' or this_size_class == 'B':
        #Major surface combatant
        if d100 <= 2:
            this_crit = 'Main battery director*'
        elif d100 <= 14:
            this_crit = 'Weapon Main battery - Mount Lost*'
        elif d100 == 15:
            this_crit = 'Weapon Main battery - Magazine explodes, Ship Sunk*'
        elif d100 <= 17:
            this_crit = 'Secondary battery director'
        elif d100 <= 24:
            this_crit = 'Weapon Secondary battery - Mount Lost*'
        elif d100 == 25:
            this_crit = 'Weapon Secondary battery - Magazine explodes*'
        elif d100 <= 34:
            this_crit = 'Other Weapon - Mount Lost*'
        elif d100 == 35:
            this_crit = 'Other Weapon - Magazine explodes*'
        elif d100 <= 45:
            this_crit = 'Lt AA'
        elif d100 <= 59:
            this_crit = 'Engineering*'
        elif d100 == 60:
            this_crit = 'Boiler Explosion*'
        elif d100 <= 75:
            this_crit = 'Flooding*'
        elif d100 <= 90:
            this_crit = 'Fire*'
        elif d100 <= 93:
            this_crit = 'Sensor'
        elif d100 <= 94:
            this_crit = 'Comms'
        elif d100 == 95:
            this_crit = 'Bridge - straight*'
        elif d100 == 96:
            this_crit = 'Bridge - starboard*'
        elif d100 == 97:
            this_crit = 'Bridge - port*'
        elif d100 == 98:
            this_crit = 'Rudder - port*'
        elif d100 == 99:
            this_crit = 'Rudder - starboard*'
        elif d100 == 100:
            this_crit = 'Rudder - straight*'

    elif this_size_class == 'C' or this_size_class == 'D' or this_size_class == 'E':
        #Minor surface combatant
        if d100 <= 2:
            this_crit = 'Main battery director'
        elif d100 <= 14:
            this_crit = 'Weapon Main battery - Mount Lost*'
        elif d100 == 15:
            this_crit = 'Weapon Main battery - Magazine explodes, Ship Sunk*'
        elif d100 <= 34:
            this_crit = 'Other Weapon'
        elif d100 == 35:
            this_crit = 'Other Weapon - Magazine explodes'
        elif d100 <= 45:
            this_crit = 'Lt AA'
        elif d100 <= 59:
            this_crit = 'Engineering*'
        elif d100 == 60:
            this_crit = 'Boiler Explosion*'
        elif d100 <= 75:
            this_crit = 'Flooding*'
        elif d100 <= 90:
            this_crit = 'Fire*'
        elif d100 <= 93:
            this_crit = 'Sensor'
        elif d100 <= 94:
            this_crit = 'Comms'
        elif d100 == 95:
            this_crit = 'Bridge - straight'
        elif d100 == 96:
            this_crit = 'Bridge - starboard'
        elif d100 == 97:
            this_crit = 'Bridge - port'
        elif d100 == 98:
            this_crit = 'Rudder - port'
        elif d100 == 99:
            this_crit = 'Rudder - starboard'
        elif d100 == 100:
            this_crit = 'Rudder - straight'
    else:
        return 'Unsupported Ship'
    #Screen out crits not allowed due to lack of AP

    if '*' in this_crit:
        if armor_pen == False:
            this_crit = 'None - No AP'
        else:
            this_crit = this_crit[:-1]

    return this_crit





def apply_crit(target, this_crit):
    #This is going to be the mother of all 'if...elif' statements
    #For each crit we need to: make any database changes needed, and return an appropriate entry for the log string
    #Need the full database entry for the ship
    ship_id_info = get_ship_id_info(target)
    cursor, conn = connect_to_db(returnConnection=True)
    cursor.execute("""SELECT * FROM 'Game Ship Formation Ship' WHERE [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", ship_id_info)
    this_ship_record = cursor.fetchone()
    ship_column_names = [description[0] for description in cursor.description]

    #Deal with the crits in the order they happen in the tables.  Got to handle it somehow.

    if 'Ship Sunk' in this_crit:
        pass

    if 'director' in this_crit:
        if 'Main battery' in this_crit:
            batt_type = 'Main battery '
            cursor.execute("""SELECT * IN 'Game Ship FC Director WHERE [Gun Battery Class] = 'M' AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", ship_id_info)
        else:
            batt_type = 'Secondary battery '
            cursor.execute("""SELECT * IN 'Game Ship FC Director WHERE [Gun Battery Class] = 'A' AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", ship_id_info)
        directors = cursor.fetchall()
        eligible_directors = [this_director[ship_column_names.index('Director Number')] for this_director in directors]
        this_director = choice(eligible_directors)
        cursor.execute("""UPDATE 'Game Ship FC Director' SET [Director Crit] = 1 WHERE [Director Number] = ? AND SELECT * IN 'Game Ship FC Director WHERE [Gun Battery Class] = 'M' AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", (this_director, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3],))
        cursor.execute("""UPDATE 'Game Ship Gun Mount' SET [Crit FC] = 1 WHERE [Primary Director = ? AND [Alternative Director] IS NULL AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", (this_director, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3],))
        #For those annoying mounts with 2 directors...
        #May code that later, will be ugly and require multiple SQL lookups

        conn.commit()
        return batt_type + "director # " + str(this_director) + "hit, linked guns lose FC."

    elif 'Weapon' in this_crit:
        if 'Main battery' in this_crit:
            batt_type = 'Main battery '
            cursor.execute("""SELECT * IN 'Game Ship Gun Mount' WHERE [Mount Class] = 'M' AND [Crit Mount] = 0 AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",ship_id_info)
            gun_battery_column_headings = [description[0] for description in cursor.description]
            gun_mounts = cursor.fetchall()
            mounts = gun_mounts
        elif 'Secondary battery' in this_crit:
            batt_type = 'Secondary battery '
            cursor.execute("""SELECT * IN 'Game Ship Gun Mount WHERE [Mount Class] = 'A' AND [Crit Mount] = 0 AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",ship_id_info)
            gun_battery_column_headings = [description[0] for description in cursor.description]
            gun_mounts = cursor.fetchall()
            mounts = gun_mounts
        elif 'Other' in this_crit:
            batt_type = 'Other '
            gun_mounts = [] #Putting this in to make searching easier later.
            cursor.execute("""SELECT * IN 'Game Ship Other Mount' WHERE [Crit Mount] = 0 AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",ship_id_info)
            other_mount_column_headings = [description[0] for description in cursor.description]
            other_mounts = cursor.fetchall()
            cursor.execute("""SELECT * IN 'Game Ship Torp Mount' WHERE [Crit Mount] = 0 AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",ship_id_info)
            torp_mount_column_headings = [description[0] for description in cursor.description]
            torp_mounts = cursor.fetchall()
            cursor.execute("""SELECT * IN 'Game Ship ASW Mount' WHERE [Crit Mount] = 0 AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",ship_id_info)
            asw_mount_column_headings = [description[0] for description in cursor.description]
            asw_mounts = cursor.fetchall()
            mounts = other_mounts + torp_mounts + asw_mounts
        else:
            #General 'Weapon' - need to combine mounts of all types
            batt_type = ''
            cursor.execute("""SELECT * IN 'Game Ship Gun Mount' WHERE [Crit Mount] = 0 AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",ship_id_info)
            gun_battery_column_headings = [description[0] for description in cursor.description]
            gun_mounts = cursor.fetchall()
            cursor.execute("""SELECT * IN 'Game Ship Other Mount' WHERE [Crit Mount] = 0 AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",ship_id_info)
            other_mount_column_headings = [description[0] for description in cursor.description]
            other_mounts = cursor.fetchall()
            cursor.execute("""SELECT * IN 'Game Ship Torp Mount' WHERE [Crit Mount] = 0 AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",ship_id_info)
            torp_mount_column_headings = [description[0] for description in cursor.description]
            torp_mounts = cursor.fetchall()
            cursor.execute("""SELECT * IN 'Game Ship ASW Mount' WHERE [Crit Mount] = 0 AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",ship_id_info)
            asw_mount_column_headings = [description[0] for description in cursor.description]
            asw_mounts = cursor.fetchall()
            mounts = gun_mounts + other_mounts + torp_mounts + asw_mounts

        mount_hit = choice(mounts)

        #OK, so now we know what mount was hit
        #Now we have to find that mount again in the database and update its entry

        if batt_type == 'Main battery ' or batt_type == 'Secondary battery ':
            #We know what table it's going back in
            this_mount_class = mount_hit[gun_battery_column_headings.index('Mount Class')]
            this_mount_number = mount_hit[gun_battery_column_headings.index('Mount Number')]
            cursor.execute("""UPDATE 'Game Ship Gun Mount' SET [Crit Mount] = 1 WHERE [Mount Class] = ? AND [Mount Number] = ? AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",(this_mount_class, this_mount_number, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3],))
        else:
            if mount_hit in gun_mounts:
                #Do the same things we just did
                batt_type = 'Gun battery '
                this_mount_class = mount_hit[gun_battery_column_headings.index('Mount Class')]
                this_mount_number = mount_hit[gun_battery_column_headings.index('Mount Number')]
                cursor.execute("""UPDATE 'Game Ship Gun Mount' SET [Crit Mount] = 1 WHERE [Mount Class] = ? AND [Mount Number] = ? AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",(this_mount_class, this_mount_number, ship_id_info[0], ship_id_info[1], ship_id_info[2],ship_id_info[3],))
            elif mount_hit in other_mounts:
                batt_type = 'Other mount '
                #Don't know if mounts are only numbered by same type.  Better not take chances.
                this_mount_type = mount_hit[other_mount_column_headings.index('Mount Type')]
                this_mount_number = mount_hit[other_mount_column_headings.index('Mount Number')]
                cursor.execute("""UPDATE 'Game Ship Other Mounts' SET [Crit Mount] = 1 WHERE [Mount Type] = ? AND [Mount Number] = ? AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",(this_mount_type, this_mount_number, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3],))
            elif mount_hit in torp_mounts:
                batt_type = 'Torp mount'
                this_mount_key = mount_hit[torp_mount_column_headings.index('Torp Mount Key')]
                cursor.execute("""UPDATE 'Game Ship Torp Mount' SET [Crit Mount] = 1 WHERE [Torp Mount Key] = ? AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",(this_mount_key, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3],))
            elif mount_hit in asw_mounts:
                batt_type = 'ASW mount '
                this_mount_key = mount_hit[asw_mount_column_headings.index('Mount Number')]
                this_mount_type = mount_hit[asw_mount_column_headings.index('Mount Type')]
                cursor.execute("""UPDATE 'Game Ship ASW Mount' SET [Crit Mount] = 1 WHERE [Mount Number] = ? AND [Mount Type] = ? AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",(this_mount_key, this_mount_type, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3],))
            else:
                raise Exception('Weapon mount hit, but a nonexistent mount was specified!')

        if 'explodes' not in this_crit:
            #No explosion, so we can terminate the function and return our string
            pass
        else:
            #We have to calculate explosion damage.  If it auto-sank the ship it would have been dealt with above.
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

def rolld100():
    return randrange(1, 100)