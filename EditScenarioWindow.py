from tkintertable import *
from helperfunctions import *
from helperclasses import ToplevelUpdate
from EditSideInfoWindow import SideInfoWindow
from ShowFormationScreens import ShipFormationScreen
from ttk import Combobox


#Will need to be rewritten if we ever add or subtract fields from the scenario listing, but so will the whole class.

class ScenarioInfoWindow(Frame):

    def __init__(self, parent, field_names_list, data=None, new_record_index=None):
        #Need a list of column names so we can label the different fields appropriately
        #Data is optional, because if we're creating a new entry we might not have it yet, but then we need the current highest index in the database.
        self.parent = parent
        self.field_values = []
        Frame.__init__(self, parent, background='white')
        self.app_window = self.parent
        self.title = "Scenario Info"
        self.pack(fill=BOTH, expand=1)
        self.update_geometry()
        self.field_names_list = field_names_list
        self.screen_frames = []
        self.text_fields_on_screen = []
        self.column_types_dict = {'Scenario Key': 'number', 'Side Key': 'number', 'default': 'text'}
        self.sides_window_column_names_dict = {} #Will be used when we draw the "Sides" table
        self.sides_window_column_names_list = []
        if data != None:
            self.is_new_record = False
            self.scenario_key = data['Scenario Key']
            for index in range(len(self.field_names_list)):
                this_column_name = self.field_names_list[index]
                self.field_values.insert(index, str(data[this_column_name]))
        else:
            self.is_new_record = True
            self.scenario_key = new_record_index
            self.field_values.append(self.scenario_key)
            for i in range(1, len(self.field_names_list)):
                self.field_values.append('')
        self.draw_entry_fields()
        self.draw_sides_objects()
        self.draw_ship_formations_objects()
        #self.draw_air_formations_objects()
        self.draw_buttons()

    def update_geometry(self):
        self.width = self.parent.winfo_width()
        self.height = self.parent.winfo_toplevel().winfo_height()
        self.parent.geometry = self.winfo_toplevel().winfo_geometry()

    def get_scenario_key(self):
        return int(self.scenario_key)

    def draw_entry_fields(self):
        #Using a combination of frames and pack()
        for i in xrange(9):
            # create frames to divide the screen into horizontal bands
            thisFrame = Frame(self, width=self.width, height=(self.height / 20))
            self.screen_frames.append(thisFrame)
            #thisFrame.grid(row=i, column=1)
            thisFrame.pack(fill=Y)
        for i in xrange(len(self.field_values)):
            #parent_frame = self.screen_frames[i // 3]
            if i <= 2:
                parent_frame = self.screen_frames[0]
            elif i <= 4:
                parent_frame = self.screen_frames[1]
            elif i <= 8:
                parent_frame = self.screen_frames[2]
            elif i <= 12:
                parent_frame = self.screen_frames[3]
            elif i <= 14:
                parent_frame = self.screen_frames[4]
            elif i == 15:
                parent_frame = self.screen_frames[8]
            else:
                break
            thisDataLabel = Label(parent_frame, text=self.field_names_list[i])
            thisDataLabel.pack(side='left')
            if i == 15:
                thisDataValue = Text(parent_frame, width=64, height = 24, highlightbackground='black', highlightthickness=1, wrap=WORD)
                thisDataValue.insert(INSERT, self.field_values[i])
            else:
                thisDataValue = Entry(parent_frame)
                thisDataValue.insert(0, self.field_values[i])
                if i == 0:
                    thisDataValue.config(state=DISABLED, width=2, justify=CENTER)
                elif i == 7 or i == 10:
                    thisDataValue.config(width=7)
                elif i == 6 or i == 8 or i == 9 or i == 11 or i == 12:
                    thisDataValue.config(width=5)
            self.text_fields_on_screen.insert(i, thisDataValue)
            thisDataValue.pack(side='left')

    def draw_sides_objects(self):
        # A number of Tkinter objects that create a table showing all the sides associated with this scenario
        # Frame to hold the table containing sides
        sidesLabel = Label(self.screen_frames[5], text="Scenario Sides")
        sidesLabel.pack(side='left')
        sidesFrame = Frame(self.screen_frames[5], background='black')
        sidesFrame.pack(side='left', expand=1)

        # Now get the data
        cursor = connect_to_db()

        if self.is_new_record:
            dummy_data, num_records, num_columns = generate_blank_data_set(cursor, 'Scenario Side', self.column_types_dict)
            for i in range(1, len(num_records) + 1):
                self.sides_window_column_names_dict[i] = dummy_data['columnorder'][i]
            self.thisTable(newdict=dummy_data, rows=1, columns=num_columns)
        else:
            the_sides = cursor.execute("""SELECT * FROM 'Scenario Side' WHERE [Scenario Key] = ?""",(self.scenario_key,))
            db_dump = the_sides.fetchall()
            column_names_list = [description[0] for description in cursor.description]
            self.sides_window_column_names_dict = generate_column_names_dict(cursor.description)
            the_data, num_records = generate_data_set(db_dump, column_names_list, self.column_types_dict)
            self.thisModel = TableModel(newdict=the_data)
            self.thisModel.addColumn(colname="# Formations", coltype='number')
            self.populate_sides_formations_column(force_refresh=True)
            num_columns = self.thisModel.getColumnCount()
        self.thisTable = TableCanvas(parent=sidesFrame, model=self.thisModel, width=num_columns * 115, editable=False)
        self.thisTable.height = 15 * num_records
        self.thisTable.createTableFrame()
        self.thisTable.autoResizeColumns()
        self.thisTable.redrawTable()
        close_connection(cursor)
        # Now we put in the buttons
        buttonFrame = Frame(self.screen_frames[5])
        buttonFrame.pack(side='right')
        plusButton = Button(buttonFrame, text="+", command=lambda: self.open_new_side_record())  # brings up a window that will let you add a new side
        plusButton.pack(side='top')
        minusButton = Button(buttonFrame, text='-', command=lambda: self.delete_side_record())  # delete the side currently selected.  Probably want to confirm as well, since it will also destroy any links to ship files etc.  Oy vey.
        # Related: right now deleting a scenario does not delete its related side, ship, etc. files.  Undecided yet on whether this is a good thing or not.
        # Maybe it makes sense to let people save existing forces (aka sides) and reuse them in multiple scenarios?
        # It would also be a lot less work writing the db management interfaces.  So yeah, let's go with that.
        minusButton.pack(side='top')
        editButton = Button(buttonFrame, text="Edit Side Info", command=lambda: self.open_edit_sides_window())
        editButton.pack(side='top')

    def populate_sides_formations_column(self, force_refresh = False):
        output_column = self.thisModel.getColumnIndex(columnName="# Formations")
        if self.is_new_record and not force_refresh:
            for i in xrange(self.thisModel.getRowCount()):
                self.thisModel.setValueAt(0, i, output_column)
        else:
            for i in xrange(self.thisModel.getRowCount()):
                this_side_key = self.thisModel.getCellRecord(i, 1) #2 is the side_key column
                print this_side_key
                cursor = connect_to_db()
                cmd_string = """SELECT * FROM [Scenario Ship Formation] WHERE [Scenario Key] = ? AND [Scenario Side] = ?""" #Side Key is named Scenario Side in this table
                cursor.execute(cmd_string, (self.scenario_key, this_side_key,))
                #db_dump = cursor.fetchall()
                num_formations = len(cursor.fetchall())
                cmd_string = """SELECT * FROM [Scenario Aircraft Formation] WHERE [Scenario Key] = ? AND [Scenario Side] = ?"""
                cursor.execute(cmd_string, (self.scenario_key, this_side_key,))
                num_formations += len(cursor.fetchall())
                close_connection(cursor)
                self.thisModel.setValueAt(int(num_formations), i, output_column)

    def draw_ship_formations_objects(self):
        formationsLabel = Label(self.screen_frames[6], text= "Ship Formations")
        formationsLabel.pack(side="left")
        shipFormationsFrame = Frame(self.screen_frames[6], background='black')
        shipFormationsFrame.pack(side='left', expand=1)
        column_names_list = ['Scenario Side', 'Formation ID', 'Formation Name']
        ship_formations_window_column_types_dict = {'Formation Name': 'text', 'default': 'number'}
        cursor = connect_to_db()
        the_formations = cursor.execute("""SELECT * FROM 'Scenario Ship Formation' WHERE [Scenario Key] = ?""",
                                        (self.scenario_key,))
        db_dump = the_formations.fetchall()
        if self.is_new_record or len(db_dump) == 0:
            ship_formations_window_column_names_dict = generate_column_names_dict(cursor.description, column_names_list)
            dummy_data, num_records, num_columns = generate_blank_data_set(cursor, 'Scenario Ship Formation', column_types_dict=ship_formations_window_column_types_dict, column_names_list=column_names_list)
            for i in range(1, num_columns + 1):
                ship_formations_window_column_names_dict.clear()
                ship_formations_window_column_names_dict[i] = dummy_data['columnorder'][i]
            self.ship_formations_model = TableModel(newdict=dummy_data, rows=1, columns=num_columns)
        else:
            ship_formations_window_column_names_dict = generate_column_names_dict(cursor.description, column_names_list)
            the_data, num_records = generate_restricted_data_set(db_dump, ship_formations_window_column_names_dict, ship_formations_window_column_types_dict)
            self.ship_formations_model = TableModel(newdict=the_data)
            self.ship_formations_model.addColumn("# Ships", "number")
            self.populate_num_ships_column()
            self.ship_formations_model.addColumn("Side Name", "text")
            self.ship_formations_model.moveColumn(self.ship_formations_model.getColumnIndex("Side Name"), self.ship_formations_model.getColumnIndex("Formation ID"))
            self.populate_side_name_column()
            num_columns = self.thisModel.getColumnCount()
        self.ship_formations_table = TableCanvas(parent=shipFormationsFrame, model=self.ship_formations_model, width=num_columns * 115, editable=False)
        self.ship_formations_table.height = 15 * num_records
        self.ship_formations_table.createTableFrame()
        self.ship_formations_table.autoResizeColumns()
        self.ship_formations_table.redrawTable()
        close_connection(cursor)
        buttonFrame = Frame(self.screen_frames[6])
        buttonFrame.pack(side='right')
        plusButton = Button(buttonFrame, text="+", command=lambda : self.pick_new_formation_side(is_ship_formation=True))# brings up a window that will let you add a new side
        plusButton.pack(side='top')
        minusButton = Button(buttonFrame, text='-', command=lambda : self.delete_ship_formation_record())
        minusButton.pack(side='top')
        formationsButton = Button(buttonFrame, text="Edit Formation", command=lambda: self.open_edit_ship_formation_window())
        formationsButton.pack(side='top')

    def populate_num_ships_column(self, force_refresh = False):
        output_column = self.ship_formations_model.getColumnIndex(columnName = "# Ships")
        if self.is_new_record and not force_refresh:
            for i in xrange(self.ship_formations_model.getRowCount()):
                self.ship_formations_model.setValueAt(0, i, output_column)
        else:
            for i in xrange(self.ship_formations_model.getRowCount()):
                this_side_key = self.ship_formations_model.getCellRecord(i, 0)
                this_formation_key = self.ship_formations_model.getCellRecord(i, 1)
                cursor = connect_to_db()
                cmd_string = """SELECT * FROM 'Scenario Ship Formation Ship' WHERE [Scenario Key] = ? AND [Scenario Side] = ? AND [Formation ID] = ?"""
                cursor.execute(cmd_string, (self.scenario_key, this_side_key, this_formation_key,))
                num_ships = len(cursor.fetchall())
                close_connection(cursor)
                self.ship_formations_model.setValueAt(int(num_ships), i, output_column)

    def draw_air_formations_objects(self):
        formationsLabel = Label(self.screen_frames[7], text="Air Formations")
        formationsLabel.pack(side="left")
        airFormationsFrame = Frame(self.screen_frames[7], background='black')
        airFormationsFrame.pack(side='left', expand=1)
        column_names_list = ['Scenario Side', 'Formation ID', 'Formation Name']
        air_formations_window_column_types_dict = {'Formation Name': 'text', 'default': 'number'}
        cursor = connect_to_db()
        the_formations = cursor.execute("""SELECT * FROM 'Scenario Aircraft Formation' WHERE [Scenario Key] = ?""",
                                        (self.scenario_key,))
        db_dump = the_formations.fetchall()
        if self.is_new_record or len(db_dump) == 0:
            air_formations_window_column_names_dict = generate_column_names_dict(cursor.description, column_names_list)
            dummy_data, num_records, num_columns = generate_blank_data_set(cursor, 'Scenario Aircraft Formation', column_types_dict=air_formations_window_column_types_dict, column_names_list=column_names_list)
            for i in range(1, num_columns + 1):
                air_formations_window_column_names_dict.clear()
                air_formations_window_column_names_dict[i] = dummy_data['columnorder'][i]
            self.air_formations_model = TableModel(newdict=dummy_data, rows=1, columns=num_columns)
        else:
            air_formations_window_column_names_dict = generate_column_names_dict(cursor.description, column_names_list)
            the_data, num_records = generate_restricted_data_set(db_dump, air_formations_window_column_names_dict,
                                                                 air_formations_window_column_types_dict)
            self.air_formations_model = TableModel(newdict=the_data)
            self.air_formations_model.addColumn("# Planes", "number")
            self.populate_num_planes_column()
            num_columns = self.air_formations_model.getColumnCount()
        self.air_formations_table = TableCanvas(parent=airFormationsFrame, model=self.air_formations_model, width=num_columns * 115, editable=False)
        self.air_formations_table.height = 15 * num_records
        self.air_formations_table.createTableFrame()
        self.air_formations_table.autoResizeColumns()
        self.air_formations_table.redrawTable()
        close_connection(cursor)
        buttonFrame = Frame(self.screen_frames[7])
        buttonFrame.pack(side='right')
        plusButton = Button(buttonFrame, text="+")  # brings up a window that will let you add a new side
        plusButton.pack(side='top')
        minusButton = Button(buttonFrame, text='-')
        minusButton.pack(side='top')
        formationsButton = Button(buttonFrame, text="Edit Formation", command=lambda: self.open_edit_air_formation_window())
        formationsButton.pack(side='top') ##To

    def populate_num_planes_column(self, force_refresh = False):
        output_column = self.air_formations_model.getColumnIndex(columnName = "# Planes")
        if self.is_new_record and not force_refresh:
            for i in xrange(self.air_formations_model.getRowCount()):
                self.air_formations_model.setValueAt(0, i, output_column)
        else:
            for i in xrange(self.air_formations_model.getRowCount()):
                this_side_key = self.air_formations_model.getCellRecord(i, 0)
                this_formation_key = self.air_formations_model.getCellRecord(i, 1)
                cursor = connect_to_db()
                cmd_string = """SELECT * FROM 'Scenario Aircraft Formation Planes' WHERE [Scenario Key] = ? AND [Scenario Side] = ? AND [Formation ID] = ?"""
                cursor.execute(cmd_string, (self.scenario_key, this_side_key, this_formation_key,))
                num_planes = len(cursor.fetchall())
                close_connection(cursor)
                self.air_formations_model.setValueAt(int(num_planes), i, output_column)

    def populate_side_name_column(self, force_refresh = False):
        output_column = self.ship_formations_model.getColumnIndex(columnName="Side Name")
        if self.is_new_record and not force_refresh:
            for i in xrange(self.ship_formations_model.getRowCount()):
                self.ship_formations_model.setValueAt("", i, output_column)
        else:
            for i in xrange(self.ship_formations_model.getRowCount()):
                this_side_key = self.ship_formations_model.getCellRecord(i, 0) #Get the side key for the formation we're talking about...
                for j in xrange(self.thisModel.getRowCount()):
                    if self.thisModel.getCellRecord(j, 1) == this_side_key: #Record in thisModel matches the side key we just retrieved...
                        this_side_name = self.thisModel.getCellRecord(j, 2)
                        self.ship_formations_model.setValueAt(this_side_name, i, output_column)
                        break

    def draw_buttons(self):
        buttonFrame = Frame(self.screen_frames[8])
        buttonFrame.pack(side='right')
        SaveAndCloseButton = Button(buttonFrame, text="Save and Close", command=lambda: self.save_and_close_window())
        SaveAndCloseButton.pack(side='bottom')

    def force_refresh(self):
        print "force_refresh invoked!"
        # Need to retrieve new data from db.
        cursor = connect_to_db()
        num_records = len(self.thisModel.data)
        print "Current number of records: " + str(num_records)
        the_sides = cursor.execute("""SELECT * FROM 'Scenario Side' WHERE [Scenario Key] = ?""", (self.scenario_key,))
        the_sides = the_sides.fetchall()
        print "New number of records: " + str(len(the_sides))
        self.column_name_list = [description[0] for description in cursor.description]
        (new_data, num_records) = generate_data_set(the_sides, self.column_name_list, self.column_types_dict)
        self.thisModel = TableModel(newdict=new_data)
        self.thisModel.addColumn(colname="# Formations", coltype='number')
        self.populate_sides_formations_column(force_refresh=True)
        self.thisTable.setModel(self.thisModel)
        self.thisTable.height = 10 * self.thisTable.rowheight * num_records
        self.thisTable.autoResizeColumns()
        self.thisTable.redrawTable()
        close_connection(cursor)

    def force_refresh_ship_formations(self):
        column_names_list = ['Scenario Side', 'Formation ID', 'Formation Name']
        ship_formations_window_column_types_dict = {'Formation Name': 'text', 'default': 'number'}
        cursor = connect_to_db()
        the_formations = cursor.execute("""SELECT * FROM 'Scenario Ship Formation' WHERE [Scenario Key] = ?""", (self.scenario_key,))
        the_formations = the_formations.fetchall()
        ship_formations_window_column_names_dict = generate_column_names_dict(cursor.description, column_names_list)
        (new_data, num_records) = generate_restricted_data_set(the_formations, column_names_dict=ship_formations_window_column_names_dict, column_types_dict=ship_formations_window_column_types_dict)
        self.ship_formations_model = TableModel(newdict=new_data)
        self.ship_formations_model.addColumn("# Ships", "number")
        self.populate_num_ships_column(force_refresh=True)
        self.ship_formations_table.setModel(self.ship_formations_model)
        self.ship_formations_table.height = 20 * self.ship_formations_table.rowheight * num_records
        self.ship_formations_table.autoResizeColumns()
        self.ship_formations_table.redrawTable()
        close_connection(cursor)

    def force_refresh_air_formations(self):
        column_names_list = ['Scenario Side', 'Formation ID', 'Formation Name']
        air_formations_window_column_types_dict = {'Formation Name': 'text', 'default': 'number'}
        cursor = connect_to_db()
        the_formations = cursor.execute("""SELECT * FROM 'Scenario Aircraft Formation' WHERE [Scenario Key] = ?""",
                                        (self.scenario_key,))
        the_formations = the_formations.fetchall()
        air_formations_window_column_names_dict = generate_column_names_dict(cursor.description, column_names_list)
        (new_data, num_records) = generate_restricted_data_set(the_formations,
                                                               column_names_dict=air_formations_window_column_names_dict,
                                                               column_types_dict=air_formations_window_column_types_dict)
        self.air_formations_model = TableModel(newdict=new_data)
        self.air_formations_model.addColumn("# Ships", "number")
        self.populate_num_planes_column(force_refresh=True)
        self.air_formations_table.setModel(self.air_formations_model)
        self.air_formations_table.height = 20 * self.air_formations_table.rowheight * num_records
        self.air_formations_table.autoResizeColumns()
        self.air_formations_table.redrawTable()
        close_connection(cursor)

    def open_edit_sides_window(self):
        try:
            this_data = self.thisTable.get_currentRecord()
        except:
            tkMessageBox.showerror(title="Error!", message="Please select a valid record")
            return
        windowLayer_width, windowLayer_height = self.width * 0.83, self.height * 0.83
        self.windowLayer = ToplevelUpdate(self.parent, orig_screen=self, width=windowLayer_width,
                                          height=windowLayer_height)
        self.update_screen()
        #Now need to make a new column list with column headings from the sides table

        editWindow = SideInfoWindow(parent=self.windowLayer, column_name_list=self.sides_window_column_names_dict,
                                        data=this_data)  # Turn things over to the edit window

    def open_new_side_record(self):
        windowLayer_width, windowLayer_height = self.width * 0.83, self.height * 0.83
        self.windowLayer = ToplevelUpdate(self.parent, orig_screen=self, width=windowLayer_width,
                                          height=windowLayer_height)
        self.update_screen()
        this_data = self.return_column_data(columnName='Side Key')
        this_index = determine_index(this_data)
        editWindow = SideInfoWindow(parent=self.windowLayer, column_name_list = self.sides_window_column_names_dict, new_record_index=this_index)

    def open_edit_ship_formation_window(self):
        windowLayer_width, windowLayer_height = self.width * 0.83, self.height * 0.83
        self.windowLayer = ToplevelUpdate(self.parent, orig_screen=self, width=windowLayer_width,
                                          height=windowLayer_height)
        self.update_screen()
        #Need to get the side key currently selected.
        try:
            this_data = self.ship_formations_table.get_currentRecord()
        except:
            tkMessageBox.showerror(title="Error!", message="Please select a valid record")
            return
        print this_data
        formationScreen = ShipFormationScreen(parent=self.windowLayer, scenario_key = self.scenario_key, data=this_data, is_new_record=False)

    def open_new_ship_formation_record(self, new_formation_side_key):
        new_formation_side_name = None
        indexes_in_use = []
        side_key_column = self.ship_formations_model.getColumnIndex('Scenario Side')
        side_name_column = self.ship_formations_model.getColumnIndex("Side Name")
        formation_key_column = self.ship_formations_model.getColumnIndex('Formation ID')
        for i in xrange(self.ship_formations_model.getRowCount()):
            if self.ship_formations_model.getCellRecord(i, side_key_column) == new_formation_side_key:
                indexes_in_use.append(self.ship_formations_model.getCellRecord(i, formation_key_column))
                if new_formation_side_key == None:
                    new_formation_side_name = self.ship_formations_model.getCellRecord(i, side_name_column)
        windowLayer_width, windowLayer_height = self.width * 0.83, self.height * 0.83
        self.windowLayer = ToplevelUpdate(self.parent, orig_screen=self, width=windowLayer_width, height=windowLayer_height)
        self.update_screen()
        #Now we have to find the appropriate index...
        this_index = determine_index(indexes_in_use)
        this_data = {'Scenario Side': new_formation_side_key, 'Scenario Side Name': new_formation_side_name, 'Formation ID': this_index, 'Formation Name': ""}
        formationScreen = ShipFormationScreen(parent=self.windowLayer, scenario_key=self.scenario_key, data=this_data, is_new_record=True)


    def delete_side_record(self):
        this_data = self.thisTable.get_currentRecord()
        msg_string = "This will permanently delete the side record for " + str(this_data['Side Name']) + ", possibly causing formations associated with it to be lost.  Are you sure you wish to do this?"
        confirm_delete = tkMessageBox.askyesno(title="Confirm delete", message=msg_string, default='no')
        if confirm_delete:
            cursor, connection = connect_to_db(return_connection=True)
            this_key = this_data['Side Key']
            cursor.execute("""DELETE FROM 'Scenario Side' WHERE [Side Key]=?;""",(this_key,))
            connection.commit()
            close_connection(cursor)
            self.force_refresh()

    def delete_ship_formation_record(self):
        this_data = self.ship_formations_table.get_currentRecord()
        msg_string = "this will permanently delete the formation record for " + str(this_data['Formation Name']) + ", causing data associated with it to be lost.  Are you sure you wish to do this?"
        confirm_delete = tkMessageBox.askyesno(title="Confirm delete", message=msg_string, default='no')
        if confirm_delete:
            cursor, connection = connect_to_db(return_connection=True)
            this_side_key = this_data['Scenario Side']
            this_formation_key = this_data['Formation ID']
            cursor.execute("""DELETE FROM 'Scenario Ship Formation' WHERE [Scenario Key] = ? AND [Scenario Side] = ? AND [Formation ID] = ?;""",(self.scenario_key, this_side_key, this_formation_key,))
            connection.commit()
            close_connection(cursor)
            self.force_refresh_ship_formations()

    def update_screen(self):
        self.parent.update()

    def return_column_data(self, modelName=None, columnIndex=None, columnName=None):
        """Return the data in a list for this col,
        filters is a tuple of the form (key,value,operator,bool)"""
        # The version supplied with Tkintertable is broken, so this is my fixed version without the fancy filtering
        if modelName == None:
            modelName = self.thisModel
        if columnIndex != None and columnIndex < len(self.columnNames):
            columnName = modelName.getColumnName(columnIndex)
        coldata = [modelName.data[str(n)][columnName] for n in range(1, modelName.getRowCount() + 1)]
        return coldata

    def pick_new_formation_side(self, is_ship_formation):
        pickSideLayer = ToplevelUpdate(self.parent, orig_screen=self, width=self.width * 0.2, height=self.height * 0.2)
        self.update_screen()
        # First need to find out what side the formation will be on...
        pickside_string = "Please choose side."
        side_name_list = self.return_column_data(columnName='Side Name')
        windowLabel = Label(pickSideLayer, text='Choose Side')
        windowLabel.pack(side='top')
        pickSideWindow = Combobox(pickSideLayer, textvariable=pickside_string, values=side_name_list,
                                  height=len(side_name_list))
        pickSideWindow.pack(side='top')
        buttonFrame = Frame(pickSideLayer)
        buttonFrame.pack(side='top')
        OKButton = Button(pickSideLayer, text='OK', command=lambda: self.confirm_new_formation_side(pickSideWindow, is_ship_formation))
        CancelButton = Button(pickSideLayer, text='Cancel', command=lambda: self.close_new_formation_side_picker(pickSideWindow))
        OKButton.pack(side='left')
        CancelButton.pack(side='left')
        self.update_screen()

    def confirm_new_formation_side(self, window_instance, is_ship_formation):
        new_formation_side = window_instance.get()
        key_column = self.thisModel.getColumnIndex('Side Key')
        name_column = self.thisModel.getColumnIndex('Side Name')
        for i in xrange(self.thisModel.getRowCount()):
            if self.thisModel.getCellRecord(i, name_column) == new_formation_side:
                new_formation_key = self.thisModel.getCellRecord(i, key_column)
                break
        if is_ship_formation:
            self.open_new_ship_formation_record(new_formation_side_key=new_formation_key, new_formation_side_name = new_formation_side)
        self.close_new_formation_side_picker(window_instance)

    def close_new_formation_side_picker(self, window_instance):
        window_instance.destroy()
        window_instance.master.destroy()
        #Don't force refresh yet...

    def close_window(self):
        self.destroy()
        self.parent.destroy()  # Have to take out that TopLayer canvas as well
        self.master.RefreshTable()

    def save_and_close_window(self):
        new_values = self.get_new_values()
        if self.is_new_record:
            for i in range(len(new_values)):
                if new_values[i] == '':  # Effectively a null result
                    new_values[i] = "NULL"
            new_values = tuple(new_values)
            cursor, connection = connect_to_db(returnConnection=True)
            cursor.execute("""INSERT INTO Scenario VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            new_values[0], new_values[1], new_values[2], new_values[3], new_values[4], new_values[5], new_values[6],
            new_values[7], new_values[8], new_values[9], new_values[10], new_values[11], new_values[12], new_values[13],
            new_values[14], new_values[15], new_values[16]))
            connection.commit()
            close_connection(cursor)
        else:
            changes_to_commit = {}
            # First we look for any discrepancies between the old data (if it exists) and the new
            for i in range(len(self.field_values)):
                if new_values[i] != self.field_values[i]:
                    changes_to_commit[self.field_names_list[i]] = new_values[i]
            if len(changes_to_commit) > 0:
                cursor, connection = connect_to_db(returnConnection=True)
                for key in changes_to_commit:
                    if key == 'Scenario Key':  # Final wall against the scenario key ever, ever being changed
                        break
                    else:
                        new_val = changes_to_commit[key]
                        cursor.execute("""UPDATE Scenario SET [{}]=? WHERE [Scenario Key]=?;""".format(key),(new_val, self.scenario_key))
                        connection.commit()
                close_connection(cursor)

        # Once save has been completed the function will end with:
        self.close_window()

    def get_new_values(self):
        # Returns a list consisting of all the field values currently on screen.
        self.update()
        self.update_idletasks()  # pure defensive programming
        new_values = []
        for i in range(len(self.field_values)):
            if i == 0:
                new_values.append(self.scenario_key)
            elif i == 15:
                new_values.append(self.text_fields_on_screen[i].get(1.0, END))
            else:
                new_values.insert(i, self.text_fields_on_screen[i].get())
        return new_values