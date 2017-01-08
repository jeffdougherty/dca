from tkintertable import *
from helperfunctions import connect_to_db, close_connection, create_names_dict
from helperclasses import DataTable
from ttk import Combobox, Checkbutton
from DamageRules import shell_bomb_hit

class GameWindow(Frame):

    def __init__(self, parent, game_id):
        self.parent = parent

        #Set up the window
        self.width = 900
        self.height = 480
        self.center_window()
        self.damage_type_string = StringVar()
        self.damage_type_string.set('Shell/Bomb')
        self.torpedo_aspect_string = StringVar()
        self.torpedo_aspect_string.set('Other')
        self.armor_pen_string = StringVar()
        self.armor_pen_string.set('Yes')
        self.torpedo_depth_string = StringVar()
        self.torpedo_depth_string.set('Shallow')
        self.debug_frame_armed = IntVar()
        self.debug_frame_armed.set(0)
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
        self.draw_console(self.console_frame)

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
        turn_label = Label(turn_frame, text='Game Turn')
        turn_label.pack(side='top')
        prev_turn_button = Button(turn_frame, text='<<<', command=lambda: self.prev_turn())
        prev_turn_button.pack(side='left')
        self.turn_readout = Entry(turn_frame, width=2)
        self.turn_readout.insert(0, self.game_turn)
        self.turn_readout.config(state='readonly')
        self.turn_readout.pack(side='left')
        next_turn_button = Button(turn_frame, text='>>>', command=lambda: self.next_turn())
        next_turn_button.pack(side='left')
        spacer_frame = Frame(parent)
        spacer_frame.pack(side='top')
        spacer_label = Label(spacer_frame, text='')
        spacer_label.pack(side='left')
        self.draw_hit_controls(parent)


    def draw_tables(self, parent):
        game_ship_table_column_names_list = ['Ship Name', 'Scenario Side', 'Ship Type', 'Size Class', 'Annex A Key', 'UWP Port Dmg', 'UWP Stbd Dmg', 'Critical Hits', 'Damage Pts Start', 'Side Name', 'Speed', 'Speed Damaged', 'Damage Pts']
        ship_table_column_types_dict = {'Ship Name': 'text', 'Scenario Side': 'text', 'Critical Hits': 'text', 'Side Name': 'text', 'default': 'number'}
        self.shipsTable = DataTable(parent, scenario_key=self.scenario_key, column_types_dict=ship_table_column_types_dict, table_name='Game Ship Formation Ship', column_names_list = game_ship_table_column_names_list, sig_figs=3, column_title_alias_dict={'Speed Damaged': 'Max Speed', 'Damage Pts': 'Damage Pts Left'})

        #Need to move columns, for that we need to address shipsTable's tableModel directly
        ships_table_model = self.shipsTable.get_model()
        ships_table_canvas = self.shipsTable.get_table()
        #ships_table_model.moveColumn(1, 3)
        ships_table_model.moveColumn(ships_table_model.getColumnIndex('Critical Hits'), ships_table_model.getColumnCount() - 1) #Puts "Critical Hits" in last place

        this_side_names_dict = create_names_dict(self.scenario_key)

        #Now we need to go through the data
        for this_record in ships_table_model.data.values():
            this_record['Side Name'] = this_side_names_dict[int(this_record['Scenario Side'])]
            this_record['Critical Hits'] = ''
            #fill in calculated columns
        ships_table_canvas.redrawTable()
        ships_table_model.setSortOrder(columnName='Scenario Side')
        self.shipsTable.hide_column('Starting Damage Pts')
        self.shipsTable.hide_column('Annex A Key')
        self.shipsTable.hide_column('Scenario Side')
        self.shipsTable.hide_column('Speed')

        ships_table_canvas.redrawVisible()
        #Need to store the columns and their indexes for later reference.
        self.ships_table_index_dict = {}
        for i in range(ships_table_model.getColumnCount()):
            self.ships_table_index_dict[ships_table_model.getColumnName(i)] = i

    def draw_nav_controls(self, parent):
        quit_button = Button(parent, text="Quit", command=self.quit)
        #quit_button.pack(side='right') #Do we want a quit button on every sub-window?!?
        close_button = Button(parent, text="Close", command=lambda: self.close_window())
        close_button.pack(side='left')

    def draw_console(self, parent):
        self.log_console = Text(master=parent, relief=RIDGE, bd=4)
        self.log_console.pack(side='top')
        #Initial load of game log events
        cursor = connect_to_db()
        cursor.execute("""SELECT * FROM 'Game Log' WHERE [Game ID]=?;""",(self.game_id,))
        for record in cursor.fetchall():
            this_record = str(record[1]) + " Turn: " + str(record[2]) + " " + record[3] + "\n"
            self.log_console.insert(END, this_record)
        self.log_console.config(state=DISABLED)
        close_connection(cursor)

    def draw_hit_controls(self, parent):
        hit_label_frame = Frame(parent)
        hit_label_frame.pack(side='top')
        panel_label = Label(hit_label_frame, text='Hit Controls')
        panel_label.pack(side='top')
        hit_type_frame = Frame(parent)
        hit_type_frame.pack(side='top')
        hit_type_label = Label(hit_type_frame, text="Type")
        hit_type_label.pack(side='left')
        self.damage_type_picker = Combobox(hit_type_frame, values=['Bomb','Shell', 'Torpedo/Mine'],
                                      textvariable=self.damage_type_string, state='readonly', width=9)
        self.damage_type_picker.pack(side='left')
        self.damage_type_picker.bind("<<ComboboxSelected>>", lambda a: self.set_hit_panels())
        hit_dp_frame = Frame(parent)
        hit_dp_frame.pack(side='top')
        self.hit_dp_amount = Entry(hit_type_frame, width=3)
        self.hit_dp_amount.pack(side='left')
        hit_dp_label = Label(hit_type_frame, text="DP")
        hit_dp_label.pack(side='left')
        self.bomb_shell_frame = Frame(parent)
        self.bomb_shell_frame.pack(side='top')
        armor_pen_label = Label(self.bomb_shell_frame, text="Armor Penetrated?")
        armor_pen_label.pack(side="left")
        self.armor_pen_picker = Combobox(self.bomb_shell_frame, values=['Yes', 'No'], state='readonly', textvariable = self.armor_pen_string, width=5)
        self.armor_pen_picker.pack(side='left')
        #Add something in for very small caliber hits
        self.torpedo_frame = Frame(parent)
        self.torpedo_frame.pack(side='top')
        depth_label = Label(self.torpedo_frame, text='Run Depth')
        depth_label.pack(side='left')
        self.depth_picker = Combobox(self.torpedo_frame, values=['Shallow', 'Deep'], state='disabled', textvariable=self.torpedo_depth_string, width=8)
        self.depth_picker.pack(side='left')
        aspect_label = Label(self.torpedo_frame, text="Hit Aspect")
        aspect_label.pack(side='left')
        self.aspect_picker = Combobox(self.torpedo_frame, values=['Bow', 'Stern', 'Other'], state='disabled', textvariable=self.torpedo_aspect_string, width=5)
        self.aspect_picker.pack(side='left')
        execute_button_frame = Frame(parent)
        execute_button_frame.pack(side='top')
        execute_button = Button(execute_button_frame, text='Apply', command=lambda: self.apply_this_hit())
        execute_button.pack(side='left')

        self.draw_debug_controls(parent) #!!! Can remove this when debug functionality no longer desired


    def set_hit_panels(self):
        new_val = self.damage_type_picker.get()
        assert new_val == 'Shell' or new_val == 'Torpedo/Mine' or new_val == 'Bomb'
        if new_val == 'Shell' or new_val == 'Bomb':
            bomb_shell_val = 'readonly'
            torpedo_val = 'disabled'
        elif new_val == 'Torpedo/Mine':
            bomb_shell_val = 'disabled'
            torpedo_val = 'readonly'
        for this_widget in self.bomb_shell_frame.winfo_children():
            if this_widget.widgetName == 'ttk::combobox':
                this_widget.config(state=bomb_shell_val)
        for this_widget in self.torpedo_frame.winfo_children():
            if this_widget.widgetName == 'ttk::combobox':
                this_widget.config(state=torpedo_val)

    def draw_debug_controls(self, parent):
        debug_arm_frame = Frame(parent)
        debug_arm_frame.pack(side='top')
        debug_arm_button = Checkbutton(debug_arm_frame, text="DEBUG", command = lambda: self.toggle_debug_frame(), variable=self.debug_frame_armed)
        debug_arm_button.pack(side='top')
        dice_entry_frame = Frame(parent)
        dice_entry_frame.pack(side='top')
        d6_label = Label(dice_entry_frame, text="D6")
        d6_label.pack(side='left')
        self.d6_entry = Entry(dice_entry_frame, width=2)
        self.d6_entry.pack(side='left')
        self.d6_entry.config(state='disabled')
        d20_label = Label(dice_entry_frame, text="D20")
        d20_label.pack(side='left')
        self.d20_entry = Entry(dice_entry_frame, width=2)
        self.d20_entry.pack(side='left')
        self.d20_entry.config(state='disabled')

    def toggle_debug_frame(self):
        new_val = self.debug_frame_armed.get()
        if new_val == 1:
            self.d6_entry.config(state='normal')
            self.d20_entry.config(state='normal')
        else:
            self.d6_entry.delete(0, END)
            self.d6_entry.config(state='disabled')
            self.d20_entry.delete(0, END)
            self.d20_entry.config(state='disabled')



    def close_window(self):
        self.destroy()
        self.parent.destroy()

    def prev_turn(self):
        self.write_game_log("Game turn moved back to " + str(self.game_turn - 1))
        self.game_turn -= 1
        self.update_turn_readout()


    def next_turn(self):
        self.write_game_log("Game turn advanced to " + str(self.game_turn + 1))
        self.game_turn += 1
        self.update_turn_readout()


    def update_turn_readout(self):
        self.turn_readout.config(state='normal')
        self.turn_readout.delete(0, END)
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
        close_connection(cursor)


    def write_game_log(self, message):
        #Do something here to make the message appear in the console, once that exists
        #Do something else here to write the message to the MySQL DB
        #First put it on the console
        self.log_console.config(state=NORMAL)
        this_message = str(self.log_sequence) + " Turn: " + str(self.game_turn) + " " + message + "\n"
        self.log_console.insert(END, this_message)
        self.log_console.config(state=DISABLED)
        self.log_console.see(END)
        self.log_console.update()
        cursor, conn = connect_to_db(returnConnection=True)
        cursor.execute("""INSERT INTO 'Game Log' VALUES (?,?,?,?);""", (self.game_id, self.log_sequence, self.game_turn, message,))
        conn.commit()
        close_connection(cursor)

    def generate_crits_statement(self, this_record):
        #this_record is a ship record from the database.  Renders into readable string form
        #Need to be able to read from multiple databases.  Need to write those as we go along
        pass

    def apply_this_hit(self):
        target = self.shipsTable.get_currentRecord()
        dp = self.hit_dp_amount.get()
        hit_type = self.damage_type_picker.get()
        debug = self.debug_frame_armed.get()
        if debug == 1:
            d6 = self.d6_entry.get()
            d20 = self.d20_entry.get()
        else:
            d6 = None
            d20 = None
        if hit_type == 'Shell' or hit_type == 'Bomb':
            if self.armor_pen_picker.get() == 'Yes':
                armor_pen = True
            #default is no armor pen
            else:
                armor_pen = False

            self.write_game_log(target[self.ships_table_index_dict['Ship Name']] + " takes " + str(dp) + " DP from shell/bomb hit.")
            critical_hit_result = shell_bomb_hit(target, self.ships_table_index_dict, dp, hit_type, armor_pen, d6, d20)
            if critical_hit_result == 'Unsupported Ship':
                tkMessageBox.showinfo('Unsupported Ship', 'Critical Hits for this ship are not yet supported by Damage Control Assistant')
            else:
                self.write_game_log(critical_hit_result)
        if hit_type == 'Torpedo':
            depth = self.depth_picker.get()
            aspect = self.aspect_picker.get()
            #torpedo_hit(target, dp, depth, aspect)