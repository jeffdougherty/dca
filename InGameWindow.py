from tkintertable import *
from helperfunctions import connect_to_db, close_connection, create_names_dict, parse_comma_separated_numbers
from helperclasses import DataTable
from ttk import Combobox, Checkbutton
from DamageRules import shell_bomb_hit

class GameWindow(Frame):

    def __init__(self, parent, game_id):
        self.parent = parent

        #Set up the window
        self.width = 1280
        self.height = 800
        self.center_window()
        self.damage_type_string = StringVar()
        self.damage_type_string.set('Bomb')
        self.torpedo_aspect_string = StringVar()
        self.torpedo_aspect_string.set('Other')
        self.armor_pen_string = StringVar()
        self.armor_pen_string.set('Yes')
        self.torpedo_depth_string = StringVar()
        self.torpedo_depth_string.set('Shallow')
        self.debug_frame_armed = IntVar()
        self.debug_frame_armed.set(0)
        self.verbose_mode = BooleanVar()
        self.verbose_mode.set(True)
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
        game_ship_table_column_names_list = ['Ship Name', 'Scenario Side', 'Ship Type', 'Size Class', 'Annex A Key', 'UWP Port Dmg', 'UWP Stbd Dmg', 'Critical Hits', 'Damage Pts Start', 'Side Name', 'Speed', 'Speed Damaged', 'Damage Pts','25% Threshold Crossed', '10% Threshold Crossed', 'Crit Engineering', 'Crit Flood Magazines', 'Extra DC', 'Game ID', 'Formation ID', 'Formation Ship Key']
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
        self.shipsTable.hide_column('Formation ID')
        self.shipsTable.hide_column('Formation Ship Key')
        self.shipsTable.hide_column('Speed')
        self.shipsTable.hide_column('25% Threshold Crossed')
        self.shipsTable.hide_column('10% Threshold Crossed')
        self.shipsTable.hide_column('Crit Engineering')
        self.shipsTable.hide_column('Crit Flood Magazines')
        self.shipsTable.hide_column('Extra DC')
        self.shipsTable.hide_column('Game ID')

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
        dc_label_frame = Frame(parent)
        dc_label_frame.pack(side='top')
        dc_label = Label(dc_label_frame, text='Damage Control')
        dc_label.pack(side='top')
        dc_buttons_frame = Frame(parent)
        dc_buttons_frame.pack(side='top')
        flood_button = Button(dc_buttons_frame, text='Flood Magazines', command=lambda: self.flood_this_magazine())
        flood_button.pack(side='left')
        extra_dc_button = Button(dc_buttons_frame, text='Toggle Extra DC', command=lambda: self.toggle_extra_dc())
        extra_dc_button.pack(side='right')
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
        verbose_mode_frame = Frame(parent)
        verbose_mode_frame.pack(side='top')
        verbose_mode_button = Checkbutton(verbose_mode_frame, text="VERBOSE", command = lambda: None, variable=self.verbose_mode)
        verbose_mode_button.pack(side='top')
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
        d100_label = Label(dice_entry_frame, text="D100 Rolls")
        d100_label.pack(side='left')
        self.d100_entry = Entry(dice_entry_frame, width=20)
        self.d100_entry.pack(side='left')
        self.d100_entry.config(state='disabled')

    def toggle_debug_frame(self):
        new_val = self.debug_frame_armed.get()
        if new_val == 1:
            self.d6_entry.config(state='normal')
            self.d100_entry.config(state='normal')
        else:
            self.d6_entry.delete(0, END)
            self.d6_entry.config(state='disabled')
            self.d100_entry.delete(0, END)
            self.d100_entry.config(state='disabled')

    def toggle_verbose(self):
        print("Verbose mode is now " + str(self.verbose_mode.get()))
        pass

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
        self.apply_fire_flooding_tac_turn()

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
        self.log_sequence += 1

    def generate_crits_statement(self, this_record):
        #this_record is a ship record from the database.  Renders into readable string form
        #Need to be able to read from multiple databases.  Need to write those as we go along
        pass

    def apply_this_hit(self, target = None, dp = None, hit_type = None): #Will usually be None, but occasionally we'll need to send in hits from fire/flooding
        #Note that when these values are set to None they're automatically initialized from where those values will *usually* be.
        if target == None:
            target = self.shipsTable.get_currentRecord()
        if dp == None:
            dp = self.hit_dp_amount.get()
        if hit_type == None:
            hit_type = self.damage_type_picker.get()
        debug = self.debug_frame_armed.get()
        if debug == 1:
            d6 = int(self.d6_entry.get())
            d100_list = parse_comma_separated_numbers(self.d100_entry.get())
        else:
            d6 = None
            d100_list = None
        if hit_type == 'Shell' or hit_type == 'Bomb':
            if self.armor_pen_picker.get() == 'Yes':
                armor_pen = True
            #default is no armor pen
            else:
                armor_pen = False
            self.write_game_log(target['Ship Name'] + " takes " + dp + " DP from " + hit_type + " hit. ")
            critical_hit_result = shell_bomb_hit(target, int(dp), hit_type, armor_pen, d6, d100_list, self.debug_frame_armed.get(), self.verbose_mode.get())
            if critical_hit_result == 'Unsupported Ship':
                tkMessageBox.showinfo('Unsupported Ship', 'Critical Hits for this ship are not yet supported by Damage Control Assistant')
            else:
                self.write_game_log(critical_hit_result)
        if hit_type == 'Torpedo':
            #!!! Finish me!
            depth = self.depth_picker.get()
            aspect = self.aspect_picker.get()
            #torpedo_hit(target, dp, depth, aspect)
        if hit_type == 'Fire' or hit_type == 'Flood':
            #!!! Finish me!
            armor_pen = True

    def flood_this_magazine(self):
        target = self.shipsTable.get_currentRecord()
        if target['Crit Flood Magazines'] == 0:
            cursor, conn = connect_to_db(returnConnection=True)
            cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Crit Flood Magazines]=1 WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""",(self.game_id, target['Scenario Side'], target['Formation ID'], target['Formation Ship Key'], ))
            self.shipsTable.update()
            conn.commit()
            close_connection(cursor)

    def toggle_extra_dc(self):
        target = self.shipsTable.get_currentRecord()
        cursor, conn = connect_to_db(returnConnection=True)
        if target['Extra DC'] == 0:
            new_val = 1
        else:
            new_val = 0
        cursor.execute("""UPDATE 'Game Ship Formation Ship' SET [Extra DC]=? WHERE [Game ID]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?;""",(new_val, self.game_id, target['Scenario Side'], target['Formation ID'], target['Formation Ship Key'], ))
        conn.commit()
        close_connection(cursor)

    def apply_fire_flooding_tac_turn(self):
        cursor, conn = connect_to_db(returnConnection=True)
        cursor.execute("""SELECT * FROM 'Game Ship Fire/Flood' WHERE [Game ID] = ? AND [Turns Remaining] > 0;""")
        fire_flood_data = cursor.fetchall
        fire_flood_columns = [description[0] for description in cursor.description]
        for i in xrange(len(fire_flood_data)):
            this_turns_remaining = fire_flood_data[i][fire_flood_columns.index('Turns Remaining')]
            this_turns_remaining -= 1
            if this_turns_remaining == 0:
                this_value = fire_flood_data[i][fire_flood_columns.index('Value')]
                this_type = fire_flood_data[i][fire_flood_columns.index('Type')]
                cursor.execute("""SELECT * FROM 'Game Ship Formation Ship' WHERE [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", (fire_flood_data[i][fire_flood_columns.index('Game ID')], fire_flood_data[i][fire_flood_columns.index('Scenario Side')], fire_flood_data[i][fire_flood_columns.index('Formation ID')], fire_flood_data[i][fire_flood_columns.index('Formation Ship Key')],))
                target_data = cursor.fetchone()
                self.apply_this_hit(target_data, dp = this_value, hit_type = this_type)


            cursor.execute("""UPDATE 'Game Ship Fire/Flood' SET [Turns Remaining] = ? WHERE [Game ID] = ? AND [Scenario Side] = ? AND [Formation ID] = ? AND [Formation Ship Key] = ?;""", (this_turns_remaining, fire_flood_data[i][fire_flood_columns.index('Game ID')], fire_flood_data[i][fire_flood_columns.index('Scenario Side')], fire_flood_data[i][fire_flood_columns.index('Formation ID')], fire_flood_data[i][fire_flood_columns.index('Formation Ship Key')],))
            conn.commit()
