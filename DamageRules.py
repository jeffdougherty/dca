from random import randrange
from helperfunctions import connect_to_db

def shell_bomb_hit(target, column_index_dict, dp, armor_pen, d6=None, d20=None):
    print target
    remaining_points = target[column_index_dict['Damage Pts']] - dp
    #First thing, check to see if the ship's sunk
    if remaining_points <= 0:
        return sink_ship(target, column_index_dict)

def sink_ship(target, column_index_dict):
    ship_id_info = get_ship_id_info(target, column_index_dict)



def get_ship_id_info(target, column_index_dict):
    game_id = target[column_index_dict['Game ID']]
    side_index = target[column_index_dict['Scenario Side']]
    formation_id = target[column_index_dict['Formation ID']]
    formation_ship_key = target[column_index_dict['Formation Ship Key']]
    return (game_id, side_index, formation_id, formation_ship_key,)