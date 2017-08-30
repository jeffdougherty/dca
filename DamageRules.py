from random import randrange, choice
from helperfunctions import connect_to_db, close_connection, to_precision
import tkMessageBox

AVIATION_SHIPS = ['CVL', 'CV', 'CVE', 'AV', 'AVP', 'AVT', 'AVM']
MERCHANT_AUXILIARY = ['AM', 'LSI', 'LCF', 'LCG', 'LCI(L)', 'LCS(L)', 'LCT(R)', 'LSD', 'AC', 'LCP', 'AO', 'AF', 'AK', 'APD']
# !!!IMPORTANT: This is the only thing 'telling' the program which types are aviation ships and merchant/auxillaries.
# If a new type of aviation ship/merchant is added to Annex A, it must be added to the appropriate list
# Otherwise, it will be treated as a surface combatant.

def shell_bomb_hit(target, dp, hit_type, armor_pen, d6=None, d100_list=None):

    cursor, conn = connect_to_db(returnConnection=True)
    print target

    (log_string, remaining_points) = damage_ship(target, dp, armor_pen, hit_type)
    if d6 != None or d100_list != None:
        debug_mode = True
    else:
        debug_mode = False
    ship_id_info = get_ship_id_info(target)
    cursor.execute("""SELECT * FROM 'Game Ship Formation Ship' WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""",ship_id_info)
    this_ship_record = cursor.fetchone()
    ship_column_names = [description[0] for description in cursor.description]
    #Check for speed reduction
    log_string += check_speed_reduction(target, remaining_points, this_ship_record[ship_column_names.index('Flooding Severity')])
    #Check for massive damage
    massive_damage_result = check_massive_damage(target, dp, remaining_points, hit_type)
    if 'sinks' in massive_damage_result:
        return massive_damage_result #Massive damage sank the ship, terminate function
    else:
        log_string += massive_damage_result
    #Now we start checking for crits
    ship_id_info = get_ship_id_info(target)
    #!!!Auto crits first
    if hit_type == 'Bomb' and target['Ship Type'] in AVIATION_SHIPS and armor_pen:
        if tkMessageBox.askyesno(title='Bomb', message='Is the bomb 100 lb/50 kg or more?'):
            apply_crit(target, 'Flight Deck', armor_pen, debug_mode)
    elif hit_type == 'Shell' and target['Ship Type'] in AVIATION_SHIPS and armor_pen:
        if tkMessageBox.askyesno(message='Was the ship hit by >= 120mm fire at Long or Extreme range?'):
            die = rolld10()
            if tkMessageBox.askyesno(message='Was the ship at Extreme range when it was hit?'):
                deck_hit = (die <= 7)
            else:
                deck_hit = (die <= 6)
            if deck_hit:
                log_string += apply_crit(target, 'Flight Deck', armor_pen, debug_mode)

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
        cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Damage Pts]=? WHERE [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;;""",(new_dp,ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3],))
        return log_string

    if debug_mode:
        log_string += "Damage ratio is " + str(damage_ratio) + " Using supplied d6 value of " + str(d6) + " for number of crits."
    else:
        d6 = rolld6()

    if d6 in damage_ratio_dict.keys():
        num_crits = damage_ratio_dict[d6]
    else:
        num_crits = 0

    if debug_mode:
        log_string += " Number of crits rolled is " + str(num_crits) + "."

    for i in range(num_crits):
        if d100_list != None:
            this_d100 = d100_list.pop(0)
            log_string += "Using supplied d100 value of " + str(this_d100) + " for critical hit."
            this_crit = roll_for_crits(target, armor_pen, this_d100)
        else:
            this_crit = roll_for_crits(target, armor_pen, rolld100())
        if this_crit == 'Unsupported Ship':
            return 'Unsupported Ship'

        log_string += apply_crit(target, ship_column_names, this_crit, armor_pen, debug_mode)

    return log_string

def damage_ship(target, dp, armor_pen, hit_type):
    cursor, conn = connect_to_db(returnConnection=True)
    if armor_pen == False:
        dp = int(dp * 0.5)
    remaining_points = target['Damage Pts'] - dp
    # First thing, check to see if the ship's sunk
    if remaining_points <= 0:
        log_string = target['Ship Name'] + 'runs out of DP ' + sink_ship(target)
        return log_string
    # else
    log_string = target['Ship Name'] + " hit for " + str(dp) + " DP by " + str(hit_type)
    ship_info = get_ship_id_info(target)
    cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Damage Pts] = ? WHERE [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",(remaining_points, ship_info[0], ship_info[1], ship_info[2], ship_info[3],))
    conn.commit()
    close_connection(cursor)
    return (log_string, remaining_points)

def sink_ship(target):
    cursor, conn = connect_to_db(returnConnection=True)
    ship_id_info = get_ship_id_info(target)
    cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Critical Hits] = 'SUNK', [Damage Pts]=0 WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""", ship_id_info)
    conn.commit()
    close_connection(cursor)
    return target['Ship Name'] + " sinks!"

def check_speed_reduction(target, remaining_points, current_flooding_severity):
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
        ship_id_info = get_ship_id_info(target)
        new_speed = target_speed_thresholds[current_speed_index]
        if new_speed > 15 and current_flooding_severity >= 2: #Speed limited by flooding
            new_speed = 15
        cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Speed Damaged]=? WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation Ship Key]=?;""", (new_speed, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3], ))
        addl_log_string = "Max speed is now " + str(new_speed) + "knots. "
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

def roll_for_crits(target, armor_pen, d100, debug_mode=False):
    this_ship_type = target['Ship Type']
    this_size_class = target['Size Class']

    if this_ship_type in MERCHANT_AUXILIARY:
        if d100 <= 9:
            this_crit = 'Weapon - Mount Lost'
        elif d100 == 10:
            this_crit = 'Weapon - Magazine explodes'
        elif d100 <= 45:
            this_crit = 'Cargo'
        elif d100 <= 50:
            this_crit = "Lt AA"
        elif d100 <= 59:
            this_crit = 'Engineering'
        elif d100 == 60:
            this_crit = 'Engineering - Boiler Explosion'
        elif d100 <= 75:
            this_crit = 'Flooding'
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
            this_crit = 'Weapon - Magazine explodes*'
        elif d100 <= 28:
            this_crit = 'Aviation Ammo - explodes*'
        elif d100 == 29:
            this_crit = 'Aviation Ammo - explodes, Ship Sunk*'
        elif d100 <= 35:
            this_crit = 'Aviation Fuel*'
        elif d100 <= 45:
            this_crit = 'Lt AA'
        elif d100 <= 59:
            this_crit = 'Engineering*'
        elif d100 == 60:
            this_crit = 'Engineering - Boiler Explosion*'
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
            this_crit = 'Engineering - Boiler Explosion*'
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
            this_crit = 'Engineering - Boiler Explosion*'
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

def apply_crit(target, ship_column_names, this_crit, armor_pen, debug_mode=False):
    #This is going to be the mother of all 'if...elif' statements
    #For each crit we need to: make any database changes needed, and return an appropriate entry for the log string
    #Need the full database entry for the ship
    ship_id_info = get_ship_id_info(target)
    cursor, conn = connect_to_db(returnConnection=True)
    #Getting a new copy of the ship record in case it's changed due to the last crit
    this_ship_record = cursor.execute("""SELECT * FROM 'Game Ship Formation Ship' WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation Ship Key]=?;""", ship_id_info)
    current_crits = this_ship_record[ship_column_names.index('Critical Hits')]
    #Deal with the crits in the order they happen in the tables.  Got to handle it somehow.

    if 'Ship Sunk' in this_crit:
        if this_ship_record[ship_column_names.index('Ship Type')] in AVIATION_SHIPS:
            return 'Aviation bomb magazine explodes, ' + sink_ship(target)
        else:
            return 'Main battery magazine explodes, ' + sink_ship(target)

    if 'director' in this_crit:
        if 'Main battery' in this_crit:
            batt_type = 'Main battery '
            cursor.execute("""SELECT * IN 'Game Ship FC Director WHERE [Gun Battery Class] = 'M' AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", ship_id_info)
        else:
            batt_type = 'Secondary battery '
            cursor.execute("""SELECT * IN 'Game Ship FC Director WHERE [Gun Battery Class] = 'A' AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", ship_id_info)
        directors = cursor.fetchall()
        director_column_names = [description[0] for description in cursor.description]
        eligible_directors = [this_director[director_column_names.index('Director Number')] for this_director in directors]
        this_director = choice(eligible_directors)
        cursor.execute("""UPDATE 'Game Ship FC Director' SET [Director Crit] = 1 WHERE [Director Number] = ? AND SELECT * IN 'Game Ship FC Director WHERE [Gun Battery Class] = 'M' AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", (this_director, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3],))
        conn.commit()
        cursor.execute("""UPDATE 'Game Ship Gun Mount' SET [Crit FC] = 1 WHERE [Primary Director = ? AND [Alternative Director] IS NULL AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", (this_director, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3],))
        conn.commit()
        #For those annoying mounts with 2 directors...
        #May code that later, will be ugly and require multiple SQL lookups
        new_crit_string = batt_type + "director # " + str(this_director) + "hit, linked guns lose FC."

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
            # !!! Need to figure out how to deal with mine mounts- how are they affected if there's no magazine explosion?
            # !!! How about light AA guns- do they have to go in here?
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
            # !!! Need to figure out how to deal with mine mounts- how are they affected if there's no magazine explosion?
            # !!! How about light AA guns- do they have to go in here?
            mounts = gun_mounts + other_mounts + torp_mounts + asw_mounts

        mount_hit = choice(mounts)

        #OK, so now we know what mount was hit
        #Now we have to find that mount again in the database and update its entry

        if batt_type == 'Main battery ' or batt_type == 'Secondary battery ':
            #We know what table it's going back in
            this_mount_class = mount_hit[gun_battery_column_headings.index('Mount Class')]
            this_mount_key = mount_hit[gun_battery_column_headings.index('Mount Number')]
            cursor.execute("""UPDATE 'Game Ship Gun Mount' SET [Crit Mount] = 1 WHERE [Mount Class] = ? AND [Mount Number] = ? AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",(this_mount_class, this_mount_key, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3],))
        else:
            if mount_hit in gun_mounts:
                #Do the same things we just did
                batt_type = 'Gun battery '
                this_mount_class = mount_hit[gun_battery_column_headings.index('Mount Class')]
                this_mount_key = mount_hit[gun_battery_column_headings.index('Mount Number')]
                cursor.execute("""UPDATE 'Game Ship Gun Mount' SET [Crit Mount] = 1 WHERE [Mount Class] = ? AND [Mount Number] = ? AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",(this_mount_class, this_mount_key, ship_id_info[0], ship_id_info[1], ship_id_info[2],ship_id_info[3],))
            elif mount_hit in other_mounts:
                batt_type = 'Other mount '
                #Don't know if mounts are only numbered by same type.  Better not take chances.
                this_mount_type = mount_hit[other_mount_column_headings.index('Mount Type')]
                this_mount_key = mount_hit[other_mount_column_headings.index('Mount Number')]
                cursor.execute("""UPDATE 'Game Ship Other Mounts' SET [Crit Mount] = 1 WHERE [Mount Type] = ? AND [Mount Number] = ? AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",(this_mount_type, this_mount_key, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3],))
            elif mount_hit in torp_mounts:
                batt_type = 'Torp mount '
                this_mount_key = mount_hit[torp_mount_column_headings.index('Torp Mount Key')]
                cursor.execute("""UPDATE 'Game Ship Torp Mount' SET [Crit Mount] = 1 WHERE [Torp Mount Key] = ? AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",(this_mount_key, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3],))
            elif mount_hit in asw_mounts:
                batt_type = 'ASW mount '
                this_mount_key = mount_hit[asw_mount_column_headings.index('Mount Number')]
                this_mount_type = mount_hit[asw_mount_column_headings.index('Mount Type')]
                cursor.execute("""UPDATE 'Game Ship ASW Mount' SET [Crit Mount] = 1 WHERE [Mount Number] = ? AND [Mount Type] = ? AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",(this_mount_key, this_mount_type, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3],))
            else:
                raise Exception('Weapon mount hit, but a nonexistent mount was specified!')

        if batt_type != 'ASW mount' and batt_type != 'Other mount':
            new_crit_string = batt_type + str(this_mount_key) + " disabled. "
        else:
            new_crit_string = this_mount_type + " " + str(this_mount_key) + " disabled. "

        if 'explodes' in this_crit:
            explosion_happens = True
            # We have to calculate explosion damage.  If it auto-sank the ship it would have been dealt with above.
            if batt_type == 'Gun battery ':
                cursor.execute("""SELECT * IN 'Game Ship Gun Mount' WHERE [Mount Class] = ? AND [Mount Number] = ? AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",(this_mount_class, this_mount_key, ship_id_info[0], ship_id_info[1], ship_id_info[2],ship_id_info[3],))
                this_mount_data = cursor.fetchall()
                this_gun_key = this_mount_data[gun_battery_column_headings.index('Gun Key')]
                cursor.execute("""SELECT * IN 'Gun Ammo' WHERE [Key Gun]=? AND [Key Shell]='HE';""",(this_gun_key,))
                ammo_record = cursor.fetchall()
                ammo_columns = [description[0] for description in cursor.description]
                this_damage = ammo_record[ammo_columns.index('SR Dam')]

            elif batt_type == 'Torp mount ':
                cursor.execute("""SELECT * IN 'Game Ship Torp Mount' WHERE [Mount Number] = ? AND [Mount Type] = ? AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",(this_mount_key, this_mount_type, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3],))
                this_mount_data = cursor.fetchall()
                this_torp_key = this_mount_data[torp_mount_column_headings.index('Torpedo')]
                this_mount_tubes = this_mount_data[torp_mount_column_headings.index('Tubes')]
                cursor.execute("""SELECT * IN 'Torpedo' WHERE [Torp Key]=?;""",(this_torp_key,))
                torp_record = cursor.fetchall()
                torp_columns = [description[0] for description in cursor.description]
                this_torp_damage = torp_record[torp_columns.index('Damage Points')]
                this_damage = (this_mount_tubes * this_torp_damage) / 2
                if this_damage < this_torp_damage:
                    this_damage = this_torp_damage

            elif batt_type == 'ASW Mount':
                cursor.execute("""SELECT * IN 'Game Ship ASW Mount' WHERE [Mount Number] = ? AND [Mount Type] = ? AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""",(this_mount_key, this_mount_type, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3],))
                this_mount_data = cursor.fetchall()
                this_mount_key = this_mount_data[asw_mount_column_headings.index('DC Key')]
                this_mount_rounds = this_mount_data[asw_mount_column_headings.index('Ready Rounds')]
                if str.isdigit(str(this_mount_rounds)) == False:
                    # Hack: if there's a NULL, default to 1.0 Ready rounds
                    this_mount_rounds = 1.0
                asw_weap_type = 'DC'
                if this_mount_key == 0:
                    #It was an ATW instead, oops
                    this_mount_key = this_mount_data[asw_mount_column_headings.index('ATW Key')]
                    asw_weap_type = 'ATW'
                #Need to do the next lookup in parallel since the column names are different between the tables
                if asw_weap_type == 'DC':
                    cursor.execute("""SELECT * IN 'Depth Charges - Surface' WHERE [Ship DC Key] = ?""", (this_mount_key,))
                    asw_weap_column_headings = [description[0] for description in cursor.description]
                    this_weapon_data = cursor.fetchall()
                    this_weapon_damage = this_weapon_data[asw_weap_column_headings.index('Lethal Dam Pts')]
                else:
                    cursor.execute("""SELECT * IN 'ATW Launcher' WHERE [ATW Key]=?;""", (this_mount_key,))
                    asw_weap_column_headings = [description[0] for description in cursor.description]
                    this_weapon_data = cursor.fetchall()
                    this_weapon_damage = this_weapon_data[asw_weap_column_headings.index('Damage Points')]
                this_damage = (this_mount_rounds * this_weapon_damage) / 2
                if this_damage < this_weapon_damage:
                    this_damage = this_weapon_damage

            else:
                #Mine mounts not included since that part of the database is not currently filled out.
                explosion_happens = False

            if explosion_happens:
                new_crit_string += damage_ship(target, this_damage, True, 'magazine explosion')[0] #Not interested in the remaining points, at least not now
            else:
                new_crit_string += 'Magazine explodes, but no magazine is present.  Whew! '

    elif 'Lt AA' in this_crit:
        current_rating = this_ship_record['Light AA Damaged Rating']
        if current_rating > 0:
            new_rating = current_rating - 0.5
            if new_rating < 0:
                new_rating = 0
            new_crit_string = 'Light AA hit, rating reduced to ' + str(new_rating) + ' '
            cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Light AA Damaged Rating] = ? WHERE [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", (new_rating, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3]))
            conn.commit()
        else:
            new_crit_string = "Light AA hit, but rating already reduced to 0. "

    elif 'Engineering' in this_crit:
        current_engineering_crits = this_ship_record[ship_column_names.index('Crit Engineering')]
        current_engineering_crits += 1
        cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Crit Engineering] = ? WHERE [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", (current_engineering_crits, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3],))
        conn.commit()
        new_crit_string = 'Engineering hit, ' + check_speed_reduction(target, this_ship_record[ship_column_names.index('Speed Damaged'), this_ship_record[ship_column_names.index('Flooding Severity')]])

        if 'Boiler Explosion' in this_crit:
            boiler_damage = this_ship_record[ship_column_names.index('Damage Pts Start')] * 0.10
            new_crit_string += 'Boiler explodes, ' + damage_ship(target, boiler_damage, True, 'Boiler Explosion ')
            new_crit_string += start_fire(target, this_ship_record, ship_column_names, armor_pen=armor_pen, this_strength_mod='0', debug_mode=debug_mode)
        else:
            new_crit_string += start_fire(target, this_ship_record, ship_column_names, armor_pen=armor_pen, this_strength_mod='/2', debug_mode=debug_mode)
        #Fire critical- d6 / 2, d6 if a boiler explosion


    elif 'Sensor' in this_crit:
        cursor.execute("""SELECT * IN 'Game Ship Sensor WHERE [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", ship_id_info)
        eligible_sensors = cursor.fetchall()
        sensor_column_names = [description[0] for description in cursor.description]
        #Going to try a different approach here- select a table entry rather than a number
        this_sensor = choice(eligible_sensors)
        sensor_number = this_sensor[sensor_column_names.index('Sensor Number')]
        cursor.execute("""UPDATE 'Game Ship Sensor' SET [Crit Sensor] = 1 WHERE [Sensor Number] = ? AND [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", (sensor_number, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3]))
        conn.commit()
        sensor_name = this_sensor[sensor_column_names.index('Sensor Name')]
        new_crit_string = sensor_name + " hit, sensor out of action."

    elif 'Comms' in this_crit:
        comms_type = rolld6()
        if comms_type == 1 or comms_type == 2:
            if this_ship_record[ship_column_names.index('Crit Radio Short Range')] == 1:
                new_crit_string = ""
            else:
                new_crit_string = 'Long-range radio communications knocked out, no OTH communications.'
                cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Crit Radio Short Range] = 1 WHERE [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", ship_id_info)
                conn.commit()
        elif comms_type == 3 or comms_type == 4:
            if this_ship_record[ship_column_names.index('Crit Radio Long Range')] == 1:
                new_crit_string = ""
            else:
                new_crit_string = "Short-range radio communications knocked out, no communications with ships in same formation."
                cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Crit Radio Long Range] = 1 WHERE [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", ship_id_info)
                conn.commit()
        elif comms_type == 5 or comms_type == 6:
            if this_ship_record[ship_column_names.index('Crit Radio Aircraft')] == 1:
                new_crit_string = ""
            else:
                new_crit_string = 'Aircraft radio communications knocked out, ship cannot communicate with aircraft.'
                cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Crit Radio Aircraft] = 1 WHERE [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", ship_id_info)
                conn.commit()

    elif 'Bridge' in this_crit:
        # !!! Assuming that the stuff with fire doesn't happen, since it's not in the expanded crit tables.  Need to query
        direction_start = this_crit.index('-') + 2 #1 for the space, 1 for the first letter
        this_direction = this_crit[direction_start:]
        cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Crit Bridge] = 1, [Crit Bridge Direction] = ? WHERE [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", (this_direction, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3]))
        if this_direction == 'straight':
            new_crit_string = "Bridge hit, ship maintains current movement"
        else:
            new_crit_string = "Bridge hit, ship circles to the " + this_direction

    elif 'Rudder' in this_crit:
        direction_start = this_crit.index('-') + 2  # 1 for the space, 1 for the first letter
        this_direction = this_crit[direction_start:]
        cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Crit Rudder] = 1, [Crit Rudder Direction] = ? WHERE [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", (this_direction, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3]))
        if this_direction == 'straight':
            new_crit_string = "Rudder hit, ship maintains current movement"
        else:
            new_crit_string = "Rudder hit, ship circles to the " + this_direction

    elif 'Elevator' in this_crit:
        #!!! What does an elevator critical hit do, anyway?
        if debug_mode:
            new_crit_string = "Elevator crit rolled, not yet represented."

    elif 'Flight Deck' in this_crit:
        #Have already filtered to make sure the hit has penetrated the armor.
        location = rolld6()
        if location == 1 or location == 2:
            hit_location = "Forward"
        elif location == 3 or location == 4:
            hit_location = "Midships"
        else:
            hit_location = "Aft"
        new_crit_string = hit_location + " flight deck hit. "
        if tkMessageBox.askyesno(message=new_crit_string+' Were there aircraft stored in that location?'):
            ac_hit = rolld6()
            new_crit_string += str(ac_hit) + " aircraft hit. "
            for ac in xrange(ac_hit):
                new_crit_string += start_fire(this_ship_record, ship_column_names, armor_pen=True, this_strength_mod='-2', debug_mode=debug_mode)
        hangar_pen = rolld10()
        if hangar_pen >= 6:
            ac_hit = rolld6()
            new_crit_string += str(ac_hit) + " aircraft hit. "
            for ac in xrange(ac_hit):
                new_crit_string += start_fire(this_ship_record, ship_column_names, armor_pen=True, this_strength_mod='-2', debug_mode=debug_mode)
        else:
            new_crit_string += " Hangar not penetrated. "

    elif 'Aviation Ammo' in this_crit:
        #!!! Not sure yet what an aviation ammo hit does if the magazine doesn't explode.
        new_crit_string = "Aviation Ammo hit rolled, no magazine explosion."

    elif 'Aviation Fuel' in this_crit:
        if debug_mode:
            new_crit_string = "Aviation Fuel hit, starting fire.  "  + start_fire(target, this_ship_record, ship_column_names, armor_pen=True, this_strength_mod='+2', this_reduction_mod='+2', debug_mode=debug_mode)
        else:
            new_crit_string = start_fire(target, this_ship_record, ship_column_names, armor_pen=True, this_strength_mod='+2', this_reduction_mod='+2', debug_mode=debug_mode)

    elif 'Fire' in this_crit:
        #Start a fire
        if debug_mode:
            new_crit_string = "Fire crit rolled, starting fire. " + start_fire(target, this_ship_record, ship_column_names, armor_pen=armor_pen, this_strength_mod='0', debug_mode=debug_mode)
        else:
            new_crit_string = start_fire(target, this_ship_record, ship_column_names, armor_pen=armor_pen, this_strength_mod='0', debug_mode=debug_mode)

    elif 'Flood' in this_crit:
        if debug_mode:
            new_crit_string = "Flooding crit rolled, starting flood" + start_flooding(target, this_ship_record, ship_column_names, armor_pen=armor_pen, debug_mode=debug_mode)
        pass

    elif 'Cargo' in this_crit:
        #May add a function to search Remarks field for ammo, fuel, or troops
        #new_crit_string = "Cargo hit, effect not currently modeled"
        new_crit_string = "Cargo hit.  "
        this_ship_remarks = this_ship_record[ship_column_names.index('Remarks')].lower() #convert to lower-case string to avoid case problems
        if 'ammo' in this_ship_remarks or 'ammunition' in this_ship_remarks:
            ammo_effects_roll = rolld10()
            if debug_mode:
                new_crit_string += 'Ammo effects roll is ' + str(ammo_effects_roll)
            if ammo_effects_roll >= 8:
                new_crit_string += 'Ammo explodes, ship sunk! ' + sink_ship(target)
            elif ammo_effects_roll >= 3:
                new_crit_string += 'Starting fire, risk of explosion on Intermediate Turns.  ' + start_fire(target, this_ship_record, ship_column_names, armor_pen, this_strength_mod='+1', this_reduction_mod='+1', debug_mode=debug_mode)
                cursor.execute("""UPDATE 'Game Ship Fire Flood' INSERT VALUES (?,?,?,?,'Non-cumulative explosion check',25,0,1);""",(ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3], ))
                conn.commit()
            else:
                new_crit_string += 'Some ammo lost, no other effect.'
            pass
        elif 'petroleum' in this_ship_remarks or 'fuel' or 'pol' in this_ship_remarks:
            #Default is crude oil
            if 'avgas' in this_ship_remarks or 'aviation' in this_ship_remarks:
                cargo_fire_mod = '+' + str(rolld6() + rolld6())
            elif 'refined' or 'gasoline' or 'lubricants' in this_ship_remarks:
                cargo_fire_mod = '+' + str(rolld6())
            else:
                cargo_fire_mod = '+2'
            new_crit_string += 'Petroleum cargo hit, starting fire. ' + start_fire(target, this_ship_record, ship_column_names, armor_pen, this_strength_mod=cargo_fire_mod, this_reduction_mod=cargo_fire_mod, debug_mode=debug_mode)
        else:
            new_crit_string += 'No other effect.'


    else:
        new_crit_string = "Error, could not find matching handler for this critical hit in the if...elif statement"
        raise Exception("Could not find a matching handler in the big if...elif statement")

    #After all the possible crits
    crit_string_to_write = current_crits + new_crit_string #new_crit_string is filled in by the appropriate if...elif block
    cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Critical Hits] = ?;""",(crit_string_to_write,))
    conn.commit()
    close_connection(cursor)
    return new_crit_string

def start_fire(target, this_ship_record, ship_column_names, armor_pen, this_strength_mod, this_reduction_mod='0', debug_mode=False):
    this_annex_a_entry, annex_a_column_names = get_annex_a_entry(this_ship_record, ship_column_names)
    this_in_service_date = int(this_annex_a_entry[annex_a_column_names.index('In Service')])
    ship_id_info = get_ship_id_info(this_ship_record)

    if this_in_service_date <= 1907:
        this_severity = rolld6() + rolld6() + 2
    elif this_in_service_date <= 1924:
        this_severity = rolld6() + 2
    else:
        this_severity = rolld6()

    if debug_mode:
        this_severity_original = this_severity

    if armor_pen == False:
        this_severity = int(this_severity * 0.5) #Should convert to an integer and round down.

    if "-" in this_strength_mod or "+" in this_strength_mod:
        this_severity += convert_mod_to_number(this_strength_mod)
    elif "*" in this_strength_mod:
        this_severity *= convert_mod_to_number(this_strength_mod)
    elif "/" in this_strength_mod:
        this_severity = this_severity / this_strength_mod

    if this_severity >= 1:
        cursor, conn = connect_to_db(returnConnection=True)
        #First, update the overall fire severity

        current_fire = int(this_ship_record[ship_column_names.index('Crit Fire')])
        current_fire += this_severity
        this_reduction_mod = convert_mod_to_number(this_reduction_mod)
        cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Crit Fire] = ? WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""",(this_severity, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3], ))
        if this_reduction_mod != 0:
            cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Fire Reduction Mod] = ? WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""",(this_reduction_mod, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3], ))

        #Make an entry for damage that will hit on the third tac turn after this one

        cursor.execute("""UPDATE 'Game Ship Fire/Flood' INSERT VALUES (?,?,?,?,'Fire',?,?,3);""",(ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3], this_severity, this_reduction_mod,))
        conn.commit()

        return_string = "Fire increases in severity by " + str(this_severity) + "%, total now " + str(current_fire)
        return_string += check_severity_levels(target, this_ship_record, ship_column_names, this_fire=current_fire, this_flooding=None, debug_mode=debug_mode)
        return return_string
    elif debug_mode:
        return "Fire severity of " + str(this_severity_original) + " rolled, reduced by modifiers to less than 1, no fire."
    else:
        return ""

def start_flooding(target, this_ship_record, ship_column_names, armor_pen, debug_mode = False):
    this_annex_a_entry, annex_a_column_names = get_annex_a_entry(this_ship_record, ship_column_names)
    this_in_service_date = int(this_annex_a_entry[annex_a_column_names.index('In Service')])
    ship_id_info = get_ship_id_info(this_ship_record)

    if this_in_service_date <= 1907:
        this_severity = rolld6() + rolld6() + 2
    elif this_in_service_date <= 1924:
        this_severity = rolld6() + 2
    else:
        this_severity = rolld6()

    if debug_mode:
        this_severity_original = this_severity

    if armor_pen == False:
        this_severity = int(this_severity * 0.5)  # Should convert to an integer and round down.

    #Don't think there are modifiers to flooding the same way there are to fire, but could still roll 1 and have it be halved to 0.

    if this_severity >= 1:
        cursor, conn = connect_to_db(returnConnection=True)
        #First, update the overall flooding severity
        current_flooding = int(this_ship_record[ship_column_names.index('Crit Flooding')])
        current_flooding += this_severity
        cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Crit Flooding]=? WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""",(current_flooding, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3], ))

        #Make an entry for the damage that's going to hit

        cursor.execute("""UPDATE 'Game Ship Fire/Flood' INSERT VALUES (?,?,?,?,'Flooding',?,0,3);""",(ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3], this_severity, ))
        conn.commit()

        return_string = "Flooding increases by " + str(this_severity) + "%, total now " + str(current_flooding)
        return_string += check_severity_levels(target, this_ship_record, ship_column_names, this_fire=None, this_flooding=current_flooding, debug_mode=debug_mode)
        return return_string
    elif debug_mode:
        return "Flooding severity of " + str(this_severity) + "% rolled, reduced by modifiers to less than 1, no flooding."
    else:
        return ""

def check_severity_levels(target, this_ship_record, ship_column_names, this_fire=None, this_flooding=None, debug_mode=False):

    severity_dict = {0: 'None', 1: 'Minor', 2: 'Major', 3: 'Severe', 4: 'Overwhelmed'}
    annex_a_entry, annex_a_column_names = get_annex_a_entry(this_ship_record, ship_column_names)
    ship_id_info = get_ship_id_info(this_ship_record)
    this_in_service_date = annex_a_entry[annex_a_column_names.index('In Service')] #Retrieving instead of passing because we need to go into Annex A anyway, so avoid the overhead of passing params
    this_size_class = annex_a_entry[annex_a_column_names.index('Size Class')]
    current_fire_severity = this_ship_record[ship_column_names.index('Fire Severity')]
    current_flooding_severity = this_ship_record[ship_column_names.index('Flooding Severity')]
    current_combined_severity = this_ship_record[ship_column_names.index('Combined Severity')]
    return_string = ""
    if this_fire == None:
        this_fire = this_ship_record[ship_column_names.index('Crit Fire')]
    if this_flooding == None:
        this_flooding = this_ship_record[ship_column_names.index('Crit Flooding')]
    this_combined = this_fire + this_flooding
    this_fire_severity = ""
    this_flooding_severity = ""
    this_combined_severity = ""
    severity_level_vars = [this_fire_severity, this_flooding_severity, this_combined_severity]

    #Now find the threshold values and adjust for in-service date

    if this_size_class == 'A' or this_size_class == 'B':
        major_threshold = 11
        severe_threshold = 16
        overwhelmed_threshold = 18
    elif this_size_class == 'C' or this_size_class == 'D':
        major_threshold = 9
        severe_threshold = 13
        overwhelmed_threshold = 15
    else:
        major_threshold = 7
        severe_threshold = 11
        overwhelmed_threshold = 13

    if this_in_service_date <= 1907:
        this_svc_mod = '-2'
    elif this_in_service_date <= 1924:
        this_svc_mod = '-1'
    elif this_in_service_date <= 1941:
        this_svc_mod = 0
    elif this_in_service_date <= 1959:
        this_svc_mod = '+1'
    else:
        this_svc_mod = '+2'

    if this_svc_mod != 0:
        this_svc_mod = convert_mod_to_number(this_svc_mod)
        for threshold in [major_threshold, severe_threshold, overwhelmed_threshold]:
            threshold += this_svc_mod

    #Now we check to see where the values stand relative to the thresholds

    for i, severity in enumerate([this_fire, this_flooding, this_combined]):
        if severity >= overwhelmed_threshold:
            severity_level_vars[i] = 4
        elif severity >= severe_threshold:
            severity_level_vars[i] = 3
        elif severity >= major_threshold:
            severity_level_vars[i] = 2
        else:
            severity_level_vars[i] = 1

    if this_combined_severity != current_combined_severity:
        #All we have to do is pass on the new value
        cursor, conn = connect_to_db(returnConnection=True)
        cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Combined Severity]=? WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""",(this_combined_severity, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3], ))
        conn.commit()
        close_connection(cursor)

    if this_fire_severity != current_fire_severity:
        return_string += 'Fire severity is now ' + severity_dict[this_fire_severity]
        cursor, conn = connect_to_db(returnConnection=True)
        cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Fire Severity]=? WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""",(this_fire_severity, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3],))

        #Minor has none to apply, since we're not covering submarines yet
        if this_fire_severity == 2:
            this_ship_remarks = this_ship_record[ship_column_names.index('Remarks')]
            new_ship_remarks = this_ship_remarks + 'Ship illuminated by fire.'
            cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Remarks]=? WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""",(new_ship_remarks, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3], ))
        elif this_fire_severity == 4:
            explosion_check = rolld100()
            if explosion_check <= 25:
                return_string += "Conflagration causes explosion, " + sink_ship(target)
        conn.commit()
        close_connection(cursor)

    if this_flooding_severity != current_flooding_severity:
        return_string += "Flooding severity is now " + severity_dict[this_flooding_severity]
        cursor, conn = connect_to_db(returnConnection=True)
        cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Flooding Severity]=? WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""",(this_flooding_severity, ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3], ))
        if this_flooding_severity > current_flooding_severity: #Applying new consequences
            if this_flooding_severity >= 2 and this_ship_record[ship_column_names.index('Speed Damaged')] > 15:
                return_string += 'Speed reduced to max of 15 knots. '
                cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Speed Damaged]=15 WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""",(ship_id_info[0], ship_id_info[1], ship_id_info[2], ship_id_info[3], ))
            if this_flooding_severity == 4:
                capsize_check = rolld100()
                if capsize_check <= 25:
                    return_string += "Ship capsizes, " + sink_ship(target)
        elif this_flooding_severity < 2: #Severity is going down and is now less than Major, may have a change of speed
            return_string += check_speed_reduction(target, this_ship_record[ship_column_names.index('Damage Pts')], this_flooding_severity)
        conn.commit()
        close_connection(cursor)

    return return_string

def convert_mod_to_number(this_mod):
    #Takes a modifier in the form of "+2", "-2", "/2", etc and returns the number in question
    subtract = False
    divide = False
    if '-' in this_mod:
        subtract = True
    elif '/' in this_mod:
        divide = True
    while str.isdigit(this_mod) == False:
        this_mod = this_mod[1:]
    this_mod = int(this_mod)
    if subtract:
        this_mod = this_mod * -1
    return this_mod

def get_ship_id_info(target):
    game_id = target['Game ID']
    side_index = target['Scenario Side']
    formation_id = target['Formation ID']
    formation_ship_key = target['Formation Ship Key']
    return (game_id, side_index, formation_id, formation_ship_key,)

def get_annex_a_entry(target, ship_column_names):
    cursor = connect_to_db()
    this_annex_a_key = target[ship_column_names.index('Annex A Key')]
    cursor.execute("""SELECT * FROM 'Ship' WHERE [Ship Key]=?;""", (this_annex_a_key,))
    this_annex_a_entry = cursor.fetchone()
    annex_a_column_names = [description[0] for description in cursor.description]
    close_connection(cursor)
    return this_annex_a_entry, annex_a_column_names

def rolld6():
    return randrange(1, 6)

def rolld10():
    return randrange(1, 10)

def rolld20():
    return randrange(1, 20)

def rolld100():
    return randrange(1, 100)