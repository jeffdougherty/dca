from tkintertable import *
from helperfunctions import connect_to_db, determine_index, generate_data_set, close_connection, create_names_dict
from helperclasses import ToplevelUpdate, DataTable

class GameWindow(Frame):

    def __init__(self, parent, game_id):
        self.parent = parent

        #Set up the window
        self.width = 720
        self.height = 480
        self.center_window()
        Frame.__init__(self, parent, background='white')
        self.pack(fill=BOTH, expand=1)
        #Create the frames for holding the UI
        self.tables_frame = Frame(master=self)
        self.tables_frame.grid(row=1, column=1)
        controls_frame = Frame(master=self)
        controls_frame.grid(row=1, column=2)
        nav_controls_frame = Frame(master=self)
        nav_controls_frame.grid(row=2, column=1)
        self.console_frame = Frame(master=self)
        self.console_frame.grid(row=3, column=1)

        # Need the game turn before we proceed any further
        self.game_id = game_id
        cursor = connect_to_db()
        cmd_string = """SELECT * FROM Game WHERE [Game ID] = ?;"""
        cursor.execute(cmd_string, (self.game_id,))
        game_data = cursor.fetchone()
        col_headings = [description[0] for description in cursor.description]
        self.turn_index = col_headings.index('Game Turn')
        #print("Turn_index = " + str(self.turn_index))
        print("Game data: " + str(game_data))
        self.game_turn = game_data[self.turn_index]
        scenario_index = col_headings.index('Scenario Key')
        self.scenario_key = game_data[scenario_index]
        close_connection(cursor)
        self.load_game_log()
        self.draw_controls(controls_frame)
        self.draw_tables(self.tables_frame)
        self.draw_nav_controls(nav_controls_frame)
        #self.draw_console(console_frame)

    def center_window(self):
        w, h = self.width, self.height
        self.sw = self.parent.winfo_screenwidth()
        self.sh = self.parent.winfo_screenheight()
        x = (self.sw - self.width) / 2
        y = (self.sh - self.height) / 2
        self.parent.geometry('%dx%d+%d+%d' % (w, h, x, y))

    def draw_controls(self, parent):
        turn_frame = Frame(parent)
        turn_frame.pack(side='top')
        prev_turn_button = Button(turn_frame, text='<<<', command=lambda: self.prev_turn())
        prev_turn_button.pack(side='left')
        self.turn_readout = Entry(parent)
        self.turn_readout.insert(0, self.game_turn)
        self.turn_readout.config(state='readonly')
        self.turn_readout.pack(side='left')
        next_turn_button = Button(turn_frame, text='>>>', command=lambda: self.next_turn())
        next_turn_button.pack(side='left')

    def draw_tables(self, parent):
        game_ship_table_column_names_list = ['Ship Name', 'Scenario Side', 'Ship Type', 'Annex A Key', 'Damage Pts Taken', 'Damage Pts', 'UWP Port Dmg', 'UWP Stbd Dmg', 'Critical Hits']
        ship_table_column_names_list = game_ship_table_column_names_list[:]
        ship_table_column_types_dict = {'Ship Name': 'text', 'Scenario Side': 'text', 'Critical Hits': 'text', 'default': 'number'}
        self.shipsTable = DataTable(parent, scenario_key=self.scenario_key, column_types_dict=ship_table_column_types_dict, table_name='Game Ship Formation Ship', column_names_list = game_ship_table_column_names_list, sig_figs=3, column_title_alias_dict={'Speed Damaged': 'Max Speed'})
        #Now adjust the table
        self.shipsTable.hide_column('Annex A Key')
        #Need to move columns, for that we need to address shipsTable's tableModel directly
        ships_table_model = self.shipsTable.get_model()
        ships_table_canvas = self.shipsTable.get_table()
        ships_table_model.moveColumn(1, 3)
        crits_original_index = ships_table_model.getColumnIndex('Critical Hits')
        ships_table_model.moveColumn(ships_table_model.getColumnIndex('Critical Hits'), 8) #Puts "Critical Hits" in last place

        this_side_names_dict = create_names_dict(self.scenario_key)
        #Now we need to go through the data
        for this_record in ships_table_model.data.values():
            this_record['Scenario Side'] = this_side_names_dict[int(this_record['Scenario Side'])]
            this_record['Damage Pts'] = int(this_record['Damage Pts']) - int(this_record['Damage Pts Taken']) #'Damage Pts' is the total the ship has.  This tells you how many it has left.
            #fill in Critical Hits
        ships_table_model.setSortOrder(columnName='Scenario Side')
        self.shipsTable.hide_column('Damage Pts Taken')
        ships_table_canvas.redrawVisible()

    def draw_nav_controls(self, parent):
        quit_button = Button(parent, text="Quit", command=self.quit)
        #quit_button.pack(side='right') #Do we want a quit button on every sub-window?!?
        close_button = Button(parent, text="Close", command=lambda: self.close_window())
        close_button.pack(side='left')

    def close_window(self):
        self.destroy()
        self.parent.destroy()

    def prev_turn(self):
        self.game_turn -= 1
        self.update_turn_readout()
        self.write_game_log("Game turn moved back to " + str(self.game_turn))

    def next_turn(self):
        self.game_turn += 1
        self.update_turn_readout()
        self.write_game_log("Game turn advanced to " + str(self.game_turn))

    def update_turn_readout(self):
        self.turn_readout.config(state='normal')
        self.turn_readout.insert(0, self.game_turn)
        self.turn_readout.config(state='readonly')
        cursor, conn = connect_to_db(returnConnection=True)
        cursor.execute("""UPDATE Game SET [Game Turn] = ? WHERE [Game ID] = ?;""", (self.game_turn, self.game_id,))
        conn.commit()
        close_connection(cursor)

    def load_game_log(self):
        cursor = connect_to_db()
        cursor.execute("""SELECT * FROM 'Game Log' WHERE [Game ID] = ?;""", (self.game_id,))
        data_dump = cursor.fetchall()
        if len(data_dump) == 0: #No logs yet for this game
            self.log_sequence = 1
        else:
            last_record = data_dump[-1]
            col_headings = [description[0] for description in cursor.description]
            sequence_index = col_headings.index('Log Sequence')
            self.log_sequence = last_record[sequence_index]
        #May add something here to input existing entries into the console once that exists


    def write_game_log(self, message):
        #Do something here to make the message appear in the console, once that exists
        #Do something else here to write the message to the MySQL DB
        pass

    def generate_crits_statement(self, this_record):
        #this_record is a ship record from the database.  Renders into readable string form
        #Need to be able to read from multiple databases.  Need to write those as we go along
        pass