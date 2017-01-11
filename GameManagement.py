from tkintertable import *
from helperfunctions import connect_to_db, determine_index, generate_data_set, close_connection
from helperclasses import ToplevelUpdate, TableCanvasWithHide
from PrintScenarioDocs import DocsPrinter
from InGameWindow import GameWindow
from ttk import Combobox
from time import strftime

#IMPORTANT GENERAL NOTE: Game ID is UNIQUE within the whole database, not just within a given scenario number.  It can be used to find a unique game without needing any other information.

class NewGamePicker(Frame):
    #Base class now contains elements I may want to reuse with the Load Game UI
    #NewGamePicker contains the elements necessary to actually choose a scenario
    #May or may not end up being redundant, but I want flexibility.

    def __init__(self, parent, from_main_menu=False, scenario_key=None, scenario_name=None):
        self.parent = parent
        self.from_main_menu = from_main_menu
        if self.from_main_menu:
            self.width = 720
            self.height = 96
            self.center_window()
        Frame.__init__(self, parent, background='white')
        self.pack(fill=BOTH, expand=1)
        windowLabel = Label(self.parent, text='New Game Setup')
        windowLabel.pack(side='top')
        master_frame = Frame(self.parent)
        master_frame.pack(side='top')
        name_field_frame = Frame(master_frame, width=self.winfo_width() / 5)
        name_field_frame.pack(side='left')
        name_field_label = Label(name_field_frame, text='Game Name')
        name_field_label.pack(side='top')
        self.name_field = Entry(name_field_frame)
        self.name_field.pack(side='top')

        scenario_frame = Frame(master_frame, width=self.winfo_width() / 5)
        scenario_frame.pack(side='left')
        scenario_picker_label = Label(scenario_frame, text = 'Scenario')
        scenario_picker_label.pack(side='top')
        scenario_selected = StringVar()
        self.scenario_picker = Combobox(scenario_frame, textvariable=scenario_selected)
        if scenario_name != None:
            scenario_selected.set(scenario_name)
        self.scenario_key = scenario_key
        self.scenario_picker.configure(state='disabled')

        self.scenario_picker.pack(side='top')
        date_field_frame = Frame(master_frame, width=self.winfo_width() / 5)
        date_field_frame.pack(side='left')
        date_field_label = Label(date_field_frame, text='Game Date')
        date_field_label.pack(side='top')
        self.date_field = Entry(date_field_frame)
        self.date_field.pack(side='top')
        self.date_field.insert(0, strftime("%m/%d/%Y")) #New game, so by default we insert today's date.
        turn_field_frame = Frame(master_frame, width=self.winfo_width() / 5)
        turn_field_frame.pack(side='left')
        turn_field_label = Label(turn_field_frame, text='Turn')
        turn_field_label.pack(side='top')
        self.turn_field = Entry(turn_field_frame, width=5)
        self.turn_field.pack(side='top')
        button_frame = Frame(master_frame, width=self.winfo_width() / 5)
        button_frame.pack(side='left')
        self.ok_button = Button(button_frame, text="OK", command=lambda: self.load_this_game())
        self.ok_button.pack(side='top')
        cancel_button = Button(button_frame, text="Cancel", command=lambda: self.close_picker())
        cancel_button.pack(side='top')

        self.scenarios_available = self.get_scenarios()
        self.scenario_picker.configure(values=self.scenarios_available.keys(), state='readonly')
        self.scenario_picker.bind("<<ComboboxSelected>>", lambda a: self.on_select())
        if scenario_key != None:
            scenario_string = StringVar()
            scenario_string.set(str(scenario_name))
            self.scenario_picker.configure(textvariable=scenario_string)
        self.turn_field.insert(0, '1')
        self.turn_field.configure(state='disabled')

    def get_scenarios(self):
        scenarios_avail = {}
        cursor = connect_to_db()
        cursor.execute("""SELECT * FROM 'Scenario'""")
        db_dump = cursor.fetchall()
        column_labels = [description[0] for description in cursor.description]
        key_index = column_labels.index('Scenario Key')
        name_index = column_labels.index('Scenario Title')
        for this_scenario in db_dump:
            this_key = this_scenario[key_index]
            this_name = this_scenario[name_index]
            scenarios_avail[this_name] = this_key
        return scenarios_avail

    def center_window(self):
        w, h = self.width, self.height
        self.sw = self.parent.winfo_screenwidth()
        self.sh = self.parent.winfo_screenheight()
        x = (self.sw - self.width) / 2
        y = (self.sh - self.height) / 2
        self.parent.geometry('%dx%d+%d+%d' % (w, h, x, y))

    def close_picker(self):
        self.destroy()
        self.parent.destroy()

    def on_select(self):
        this_name = self.scenario_picker.get()
        self.scenario_key = self.scenarios_available[this_name]

    def load_this_game(self):
        cursor, conn = connect_to_db(returnConnection=True)
        game_indexes = []
        cursor.execute("""SELECT * FROM 'Game'""")
        column_titles = [description[0] for description in cursor.description]
        game_index_loc = column_titles.index('Game ID')
        for entry in cursor.fetchall():
            game_indexes.append(entry[game_index_loc])
        if len(game_indexes) == 0:
            next_game_index = 1
        else:
            next_game_index = determine_index(game_indexes)
        self.this_game_index = next_game_index
        cursor.execute("""SELECT * FROM 'Scenario' WHERE [Scenario Key] = ?;""",(self.scenario_key,))
        game_name = self.name_field.get()
        game_date = self.date_field.get()
        game_turn = 1
        cursor.execute("""INSERT INTO 'Game' VALUES(?,?,?,?,?);""", (next_game_index, self.scenario_key, game_name, game_date, game_turn,))
        cursor.execute("""INSERT INTO 'Game Log' VALUES (?,?,?,?);""", (next_game_index, 1, 1, "Game Log Opened"))
        conn.commit()
        # Create the ship entries, that's going to be its own thing...
        self.load_ships()
        self.game_window = Toplevel(self.parent, width = 720, height = 480)
        self.destroy()
        this_game_window = GameWindow(self.game_window, self.this_game_index)


    def load_ships(self):
        cursor, conn = connect_to_db(returnConnection=True)
        cursor.execute("""SELECT * FROM 'Game Ship Formation Ship'""")
        columns_needed = [description[0] for description in cursor.description]
        cursor.execute("""SELECT * FROM 'Scenario Ship Formation Ship' WHERE [Scenario Key]=?""", (self.scenario_key,))
        scenario_columns = [description[0] for description in cursor.description]
        scenario_data = cursor.fetchall()
        for i in range(len(scenario_data)):
            ship = scenario_data[i]
            this_data = {}
            data_to_submit = []
            annex_a_key = ship[scenario_columns.index('Annex A Key')]
            cursor.execute("""SELECT * FROM 'Ship' WHERE [Ship Key]=?""", (annex_a_key,))
            annex_a_columns = [description[0] for description in cursor.description]
            annex_a_data = cursor.fetchall()
            annex_a_data = annex_a_data[0]
            for this_column in columns_needed:
                if this_column in scenario_columns:
                    this_column_index = scenario_columns.index(this_column)
                    this_data[this_column] = scenario_data[i][this_column_index]
                elif this_column == 'Damage Pts':
                    this_column_index = annex_a_columns.index(this_column)
                    this_data[this_column] = annex_a_data[this_column_index]
                    this_data['Damage Pts Start'] = annex_a_data[this_column_index]
                elif this_column in annex_a_columns:
                    this_column_index = annex_a_columns.index(this_column)
                    this_data[this_column] = annex_a_data[this_column_index]
                elif this_column == 'Game ID':
                    this_data[this_column] = self.this_game_index
                elif this_column == 'UWP Port Max' or this_column == 'UWP Stbd Max' or this_column == 'UWP Port Dmg' or this_column == 'UWP Stbd Dmg':
                    this_data[this_column] = annex_a_data[annex_a_columns.index('Armor UW')]
                elif this_column == 'Light AA Damaged Rating':
                    this_data[this_column] = annex_a_data[annex_a_columns.index('Light AA Rating')]
                elif this_column == 'Area AA Damaged Rarting':
                    this_data[this_column] = annex_a_data[annex_a_columns.index('Area AA Rating')]
                elif this_column == 'Speed Damaged':
                    this_data[this_column] = annex_a_data[annex_a_columns.index('Speed')]
                elif this_column == 'Speed Damaged Submerged':
                    this_data[this_column] = annex_a_data[annex_a_columns.index('Speed Submerged')]
                elif this_column == 'Critical Hits':
                    this_data[this_column] = ""
                elif this_column == 'Damage Pts Start':
                    pass #Already set while we were on 'Damage Pts, but don't want it set to 0
                else:
                    this_data[this_column] = 0
            # Dictionary is done, now we need to get it into a list in the proper order
            for j in range(len(columns_needed)):
                this_column = columns_needed[j]
                data_to_submit.append(this_data[this_column])
            data_to_submit = tuple(data_to_submit)
            cursor.execute("""INSERT INTO 'Game Ship Formation Ship' VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", data_to_submit)
            conn.commit()
            # Now we need to check for mounts and sensors associated with that ship.
            cursor = conn.cursor()
            cursor.execute("""SELECT * FROM 'Ship Gun Mount' WHERE [Ship Key]=?""", (annex_a_key,))
            gun_mount_data = cursor.fetchall()
            if len(gun_mount_data) > 0:  # We have to process at least one mount
                gun_mount_columns = [description[0] for description in cursor.description]
                cursor.execute("""SELECT * FROM 'Game Ship Gun Mount'""")
                gun_mount_columns_needed = [description[0] for description in cursor.description]
                for mount in gun_mount_data:
                    mount_data = {}
                    mount_data_to_submit = []
                    for this_column in gun_mount_columns_needed:
                        if this_column in gun_mount_columns:
                            mount_data[this_column] = mount[gun_mount_columns.index(this_column)]
                        elif this_column in scenario_columns:
                            mount_data[this_column] = scenario_data[i][scenario_columns.index(this_column)]
                        elif this_column == 'AA Factor':
                            mount_data[this_column] = 0.0  # Need to replace with the real formula
                        elif this_column == 'Game ID':
                            mount_data[this_column] = self.this_game_index
                        else:
                            mount_data[this_column] = 0
                    for k in range(len(gun_mount_columns_needed)):
                        this_column = gun_mount_columns_needed[k]
                        mount_data_to_submit.append(mount_data[this_column])
                    mount_data_to_submit = tuple(mount_data_to_submit)
                    cursor.execute("""INSERT INTO 'Game Ship Gun Mount' VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                                   mount_data_to_submit)
                    conn.commit()
            # Gun mounts done, now we need to check for other mounts.  Code very similar.
            cursor.execute("""SELECT * FROM 'Ship Other Mounts' WHERE [Ship Key]=?""", (annex_a_key,))
            other_mount_data = cursor.fetchall()
            if len(other_mount_data) > 0:
                other_mount_columns = [description[0] for description in cursor.description]
                cursor.execute("""SELECT * FROM 'Game Ship Other Mounts'""")
                other_mount_columns_needed = [description[0] for description in cursor.description]
                for mount in other_mount_data:
                    mount_data = {}
                    mount_data_to_submit = []
                    for this_column in other_mount_columns_needed:
                        if this_column in other_mount_columns:
                            mount_data[this_column] = other_mount_columns.index(this_column)
                        elif this_column in scenario_columns:
                            mount_data[this_column] = scenario_data[i][scenario_columns.index(this_column)]
                        elif this_column == 'Game ID':
                            mount_data[this_column] = self.this_game_index
                        else:
                            mount_data[this_column] = 0
                    for k in range(len(other_mount_columns_needed)):
                        this_column = other_mount_columns_needed[k]
                        mount_data_to_submit.append(mount_data[this_column])
                    mount_data_to_submit = tuple(mount_data_to_submit)
                    cursor.execute("""INSERT INTO 'Game Ship Other Mounts' VALUES(?,?,?,?,?,?,?,?,?)""", mount_data_to_submit)
                    conn.commit()
            # And torpedo mounts
            cursor.execute("""SELECT * FROM 'Ship Torp Mount' WHERE [Ship Key]=?""", (annex_a_key,))
            torp_mount_data = cursor.fetchall()
            if len(torp_mount_data) > 0:
                torp_mount_columns = [description[0] for description in cursor.description]
                cursor.execute("""SELECT * FROM 'Game Ship Torp Mount'""")
                torp_mount_columns_needed = [description[0] for description in cursor.description]
                for this_mount in torp_mount_data:
                    torp_mount_data = {}
                    torp_mount_data_to_submit = []
                    for this_column in torp_mount_columns_needed:
                        if this_column in torp_mount_columns:
                            torp_mount_data[this_column] = this_mount[torp_mount_columns.index(this_column)]
                        elif this_column in scenario_columns:
                            torp_mount_data[this_column] = scenario_data[i][scenario_columns.index(this_column)]
                        elif this_column == 'Game ID':
                            torp_mount_data[this_column] = self.this_game_index
                        else:
                            torp_mount_data[this_column] = 0 #Catcher, should just be for Crit Mount
                    for k in range(len(torp_mount_columns_needed)):
                        this_column = torp_mount_columns_needed[k]
                        torp_mount_data_to_submit.append(torp_mount_data[this_column])
                    torp_mount_data_to_submit = tuple(torp_mount_data_to_submit)
                    cursor.execute("""INSERT INTO 'Game Ship Torp Mount' VALUES(?,?,?,?,?,?,?,?)""", torp_mount_data_to_submit)
                    conn.commit()
            # Now we do the same thing with fire directors
            cursor.execute("""SELECT * FROM 'Ship FC Director' WHERE [Ship Key]=?""", (annex_a_key,))
            fc_director_data = cursor.fetchall()
            if len(fc_director_data) > 0:
                fc_director_columns = [description[0] for description in cursor.description]
                cursor.execute("""SELECT * FROM 'Game Ship FC Director'""")
                fc_director_columns_needed = [description[0] for description in cursor.description]
                for director in fc_director_data:
                    director_data = {}
                    director_data_to_submit = []
                    for this_column in fc_director_columns_needed:
                        if this_column in fc_director_columns:
                            director_data[this_column] = director[fc_director_columns.index(this_column)]
                        elif this_column in scenario_columns:
                            director_data[this_column] = scenario_data[i][scenario_columns.index(this_column)]
                        elif this_column == 'Game ID':
                            director_data[this_column] = self.this_game_index
                        else:
                            director_data[this_column] = 0
                    for k in range(len(fc_director_columns_needed)):
                        this_column = fc_director_columns_needed[k]
                        director_data_to_submit.append(director_data[this_column])
                    director_data_to_submit = tuple(director_data_to_submit)
                    cursor.execute("""INSERT INTO 'Game Ship FC Director' VALUES(?,?,?,?,?,?,?,?,?,?)""", director_data_to_submit)
                    conn.commit()
            # Now we need to do sensors, which requires doing multiple lookups in the database
            sensor_index = 1
            cursor.execute("""SELECT * FROM 'Game Ship Sensor'""")
            sensor_columns_needed = [description[0] for description in cursor.description]
            cursor.execute("""SELECT * FROM 'Ship Radar' WHERE [Ship Key]=?""", (annex_a_key,))
            radar_data = cursor.fetchall()
            if len(radar_data) > 0:
                radar_columns = [description[0] for description in cursor.description]
                for this_radar in radar_data:  # Might be more than one radar of each type present...
                    num_radars = this_radar[radar_columns.index('Number')]
                    cursor.execute("""SELECT * FROM 'Radar - Ship' WHERE [Radar Key]=?""", (this_radar[radar_columns.index('Radar Key')],))
                    returned_data = cursor.fetchone()  # Will only get one, since we're using a unique radar key
                    radar_entry_columns = [description[0] for description in cursor.description]
                    name_index = radar_entry_columns.index('Name')
                    radar_name = returned_data[name_index]
                    for i in range(num_radars):
                        radar_data = {}
                        radar_data_to_submit = []
                        for this_column in sensor_columns_needed:
                            if this_column in radar_columns:
                                this_column_index = radar_columns.index(this_column)
                                radar_data[this_column] = this_radar[this_column_index]
                            elif this_column in scenario_columns:
                                radar_data[this_column] = scenario_data[i][scenario_columns.index(this_column)]
                            elif this_column == 'Sensor Type':
                                radar_data[this_column] = 'Radar'
                            elif this_column == 'Sensor Name':
                                radar_data[this_column] = radar_name
                            elif this_column == 'Sensor Key':
                                key_index = radar_columns.index('Radar Key')
                                radar_data[this_column] = this_radar[key_index]
                            elif this_column == 'Sensor Number':
                                radar_data[this_column] = sensor_index
                                sensor_index += 1
                            elif this_column == 'Game ID':
                                radar_data[this_column] = self.this_game_index
                            else:
                                radar_data[this_column] = 0
                        for k in range(len(sensor_columns_needed)):
                            this_column = sensor_columns_needed[k]
                            radar_data_to_submit.append(radar_data[this_column])
                        radar_data_to_submit = tuple(radar_data_to_submit)
                        cursor.execute("""INSERT INTO 'Game Ship Sensor' VALUES(?,?,?,?,?,?,?,?,?,?)""", radar_data_to_submit)
                        conn.commit()
            cursor.execute("""SELECT * FROM 'Ship Sonar' WHERE [Ship Key]=?""", (annex_a_key,))
            sonar_data = cursor.fetchall()
            if len(sonar_data) > 0:
                sonar_columns = [description[0] for description in cursor.description]
                sonar_key_index = sonar_columns.index('Sonar Key')
                # Here we apparently don't have to consider multiple copies of the same type of sonar
                for this_sonar in sonar_data:
                    cursor.execute("""SELECT * FROM 'Sonar' WHERE [Sonar Key]=?""",(this_sonar[sonar_key_index],))
                    sonar_entry_columns = [description[0] for description in cursor.description]
                    name_index = sonar_entry_columns.index('Designation')
                    returned_data = cursor.fetchone()
                    sonar_name = returned_data[name_index]
                    sonar_data = {}
                    sonar_data_to_submit = []
                    for this_column in sensor_columns_needed:
                        if this_column in sonar_columns:
                            sonar_data[this_column] = this_sonar[sonar_columns.index(this_column)]
                        elif this_column in scenario_columns:
                            sonar_data[this_column] = scenario_data[i][scenario_columns.index(this_column)]
                        elif this_column == 'Sensor Type':
                            sonar_data[this_column] = 'Sonar'
                        elif this_column == 'Sensor Name':
                            sonar_data[this_column] = sonar_name
                        elif this_column == 'Sensor Key':
                            sonar_data[this_column] = this_sonar[sonar_key_index]
                        elif this_column == 'Sensor Number':
                            sonar_data[this_column] = sensor_index
                            sensor_index += 1
                        elif this_column == 'Game ID':
                            sonar_data[this_column] = self.this_game_index
                        else:
                            sonar_data[this_column] = 0
                    for k in range(len(sensor_columns_needed)):
                        this_column = sensor_columns_needed[k]
                        sonar_data_to_submit.append(sonar_data[this_column])
                    sonar_data_to_submit = tuple(sonar_data_to_submit)
                    cursor.execute("""INSERT INTO 'Game Ship Sensor' VALUES(?,?,?,?,?,?,?,?,?,?)""", sonar_data_to_submit)
                    conn.commit()
            cursor.execute("""SELECT * FROM 'Ship Other Sensor' WHERE [Ship Key]=?""", (annex_a_key,))
            other_data = cursor.fetchall()
            # Now we check for other sensors
            if len(other_data) > 0:
                other_columns = [description[0] for description in cursor.description]
                name_index = other_columns.index('Other Sensor Type')
                # Don't need names for this one
                for this_sensor in other_data:
                    sensor_data = {}
                    sensor_data_to_submit = []
                    for this_column in sensor_columns_needed:
                        if this_column in other_columns:
                            sensor_data[this_column] = this_sensor[other_columns.index(this_column)]
                        elif this_column in scenario_columns:
                            sensor_data[this_column] = scenario_data[i][scenario_columns.index(this_column)]
                        elif this_column == 'Sensor Type':
                            sensor_data[this_column] = 'Other Sensor'
                        elif this_column == 'Sensor Name':
                            sensor_data[this_column] = this_sensor[name_index]
                        elif this_column == 'Sensor Number':
                            sensor_data[this_column] = sensor_index
                            sensor_index += 1
                        elif this_column == 'Game ID':
                            sensor_data[this_column] = self.this_game_index
                        else:
                            sensor_data[this_column] = 0
                    for k in range(len(sensor_columns_needed)):
                        this_column = sensor_columns_needed[k]
                        sensor_data_to_submit.append(sensor_data[this_column])
                    sensor_data_to_submit = tuple(sensor_data_to_submit)
                    cursor.execute("""INSERT INTO 'Game Ship Sensor' VALUES(?,?,?,?,?,?,?,?,?,?)""", sensor_data_to_submit)
                    conn.commit()

class LoadGamePicker(Frame):
    #Load or delete an existing game file.  Turns out we may not be reusing as much code from NewGamePicker as I thought...

    def __init__(self, parent, from_main_menu):
        self.parent = parent
        self.from_main_menu = from_main_menu
        if self.from_main_menu:
            self.width = 1024
            self.height = 768
            self.center_window()
        Frame.__init__(self, parent, background='white')
        self.pack(fill=BOTH, expand=1)
        windowLabel = Label(self, text='Load Existing Game')
        windowLabel.pack(side='top')
        master_frame = Frame(self)
        master_frame.pack(side='top')
        #Make the data table with the list of current games
        cursor = connect_to_db()
        game_data = cursor.execute("""SELECT * FROM 'Game'""")
        game_data = game_data.fetchall()
        self.column_name_list = [description[0] for description in cursor.description]
        (the_data, num_records) = generate_data_set(game_data, self.column_name_list, {'Game Name':'text', 'Game Date':'text', 'default':'number'})
        #Doing the table directly from tkintertable rather than using DataTable class since we don't have a ScenarioKey to go off
        self.thisModel = TableModel(newdict=the_data)
        self.thisTable = TableCanvasWithHide(parent=master_frame, model=self.thisModel, width=self.width * 0.88, editable=False)
        self.thisTable.height = self.thisTable.rowheight * num_records
        self.thisTable.createTableFrame()
        self.thisTable.autoResizeColumns()
        close_connection(cursor)

        #self.thisTable.hide_column('Game ID')
        self.thisModel.moveColumn(self.thisModel.getColumnIndex('Game ID'), self.thisModel.getColumnCount())
        self.thisTable.hide_column('Game ID')
        self.thisModel.deleteColumn(self.thisModel.getColumnIndex('Scenario Key'))
        self.thisTable.redrawVisible()

        #Now we make the buttons
        button_frame = Frame(self)
        button_frame.pack(side='top')
        load_button = Button(button_frame, text="Load Game", command=lambda: self.load_this_game())
        load_button.pack(side='left')
        delete_button = Button(button_frame, text="Delete Game", command=lambda: self.delete_this_game())
        delete_button.pack(side='left')
        print_docs_button = Button(button_frame, text="Print Docs", command=lambda: self.prepare_scenario_documents())
        print_docs_button.pack(side='left')
        quit_button = Button(button_frame, text="Quit", command=self.quit)
        quit_button.pack(side='right')
        close_button = Button(button_frame, text="Close", command=lambda: self.close_picker())
        close_button.pack(side='right')



    def load_this_game(self):
        try:
            this_data = self.thisTable.get_currentRecord()
        except:
            tkMessageBox.showerror(title="Error!", message="Please select a valid record")
            return
        self.this_game_index = this_data['Game ID']
        self.game_window = Toplevel(self.parent, width=720, height=480)
        this_game_window = GameWindow(self.game_window, self.this_game_index)

    def center_window(self):
        w, h = self.width, self.height
        self.sw = self.parent.winfo_screenwidth()
        self.sh = self.parent.winfo_screenheight()
        x = (self.sw - self.width) / 2
        y = (self.sh - self.height) / 2
        self.parent.geometry('%dx%d+%d+%d' % (w, h, x, y))

    def force_refresh(self):
        print "force_refresh invoked!"
        # Need to retrieve new data from db.
        cursor = connect_to_db()
        num_records = len(self.thisModel.data)
        print "Current number of records: " + str(num_records)
        avail_games = cursor.execute("SELECT * FROM Game")
        avail_games = avail_games.fetchall()
        print "New number of records: " + str(len(avail_games))
        self.column_name_list = [description[0] for description in cursor.description]
        (new_data, num_records) = generate_data_set(avail_games, self.column_name_list,
                                                    {'Game Name': 'text', 'Game Date': 'text', 'default': 'number'})
        self.thisModel = TableModel(newdict=new_data)
        self.thisTable.setModel(self.thisModel)
        self.thisTable.height = 20 * self.thisTable.rowheight * num_records
        self.thisTable.redrawTable()
        self.thisModel.moveColumn(self.thisModel.getColumnIndex('Game ID'), self.thisModel.getColumnCount())
        self.thisTable.hide_column('Game ID')
        self.thisModel.deleteColumn(self.thisModel.getColumnIndex('Scenario Key'))
        self.thisTable.redrawVisible()
        close_connection(cursor)

    def close_picker(self):
        self.destroy()
        self.parent.destroy()

    def update_screen(self):
        self.parent.update()

    def prepare_scenario_documents(self):
        this_data = self.thisTable.get_currentRecord()
        print this_data
        self.printLayer = ToplevelUpdate(self, orig_screen=self, width=self.width * 0.6, height=self.width * 0.2)
        self.printLayer.center_window()
        self.update_screen()
        prepare_documents = DocsPrinter(parent=self.printLayer, data=this_data)

    def delete_this_game(self):
        confirm_delete = tkMessageBox.askyesno(title='Confirm Delete', message="This will permanently delete the record of this game, losing everything that has happened since the scenario began.  Are you sure you wish to do this?", default='no')
        if confirm_delete:
            this_data = self.thisTable.get_currentRecord()
            cursor, connection = connect_to_db(returnConnection=True)
            #delete the game record
            game_key = this_data['Game ID']
            cursor.execute("""DELETE FROM 'Game' WHERE [Game ID]=?;""", (game_key,))
            # connection.commit()
            #now delete the related records from all the other game-specific tables
            cursor.execute("""DELETE FROM 'Game Log' WHERE [Game ID]=?;""", (game_key,))
            cursor.execute("""DELETE FROM 'Game Ship Critical Hit' WHERE [Game ID]=?;""", (game_key,))
            cursor.execute("""DELETE FROM 'Game Ship Damage' WHERE [Game ID]=?;""", (game_key,))
            cursor.execute("""DELETE FROM 'Game Ship FC Director' WHERE [Game ID]=?;""", (game_key,))
            cursor.execute("""DELETE FROM 'Game Ship Formation Ship' WHERE [Game ID]=?;""", (game_key,))
            cursor.execute("""DELETE FROM 'Game Ship Gun Mount' WHERE [Game ID]=?;""", (game_key,))
            cursor.execute("""DELETE FROM 'Game Ship Torp Mount' WHERE [Game ID]=?;""", (game_key,))
            cursor.execute("""DELETE FROM 'Game Ship Other Mounts' WHERE [Game ID]=?;""", (game_key,))
            cursor.execute("""DELETE FROM 'Game Ship Sensor' WHERE [Game ID]=?;""", (game_key,))
            connection.commit()
            close_connection(cursor)
            self.thisTable.setSelectedRow(0)
            self.force_refresh()