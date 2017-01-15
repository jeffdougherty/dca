from helperfunctions import connect_to_db

def cleanup_game_db():
    cursor, conn = connect_to_db(returnConnection=True)
    cursor.execute("""DELETE FROM 'Game'""")
    cursor.execute("""DELETE FROM 'Game Log'""")
    cursor.execute("""DELETE FROM 'Game Ship Formation Ship'""")
    cursor.execute("""DELETE FROM 'Game Ship Gun Mount'""")
    cursor.execute("""DELETE FROM 'Game Ship Torp Mount'""")
    cursor.execute("""DELETE FROM 'Game Ship Other Mounts'""")
    cursor.execute("""DELETE FROM 'Game Ship FC Director'""")
    cursor.execute("""DELETE FROM 'Game Ship Sensor'""")
    cursor.execute("""DELETE FROM 'Game Ship Fire/Flood'""")
    conn.commit()

cleanup_game_db()