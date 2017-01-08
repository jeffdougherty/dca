from helperfunctions import *
from helperclasses import DataTable, ToplevelUpdate
from tkintertable import *
from EditSideInfoWindow import SideInfoWindow
from FormationScreens import ShipFormationScreen, FormationSidePicker


class ScenarioInfoWindow(Frame):

    def __init__(self, parent, field_names_list, data=None, new_record_index=None):
        # Need a list of column names so we can label the different fields appropriately
        # Data is optional, because if we're creating a new entry we might not have it yet, but then we need the current highest index in the database.
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
        self.data_tables_on_screen = []

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
        self.side_names_dict = self.sidesTable.get_names_dict()
        self.draw_ship_formations_objects()
        self.draw_buttons()

    def update_geometry(self):
        self.width = self.parent.winfo_width()
        self.height = self.parent.winfo_toplevel().winfo_height()
        self.parent.geometry = self.winfo_toplevel().winfo_geometry()

    def draw_entry_fields(self):
        # Basic scenario data, not shown in a data table.
        # Using a combination of frames and pack()
        for i in xrange(9):
            thisFrame = Frame(self, width=self.width, height=(self.height / 20))
            self.screen_frames.append(thisFrame)
            # thisFrame.grid(row=i, column=1)
            thisFrame.pack(fill=Y)
        for i in xrange(len(self.field_values)):
            # parent_frame = self.screen_frames[i // 3]
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
                thisDataValue = Text(parent_frame, width=64, height=24, highlightbackground='black',
                                     highlightthickness=1, wrap=WORD)
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
        self.sidesFrame = Frame(self.screen_frames[5], background='black')
        self.sidesFrame.pack(side='left', expand=1)
        #Now we can make the data table itself
        self.draw_sides_table()
        self.data_tables_on_screen.append(self.sidesTable)
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

    def draw_sides_table(self):
        self.sidesTable = DataTable(self.sidesFrame, self.scenario_key,
                                    column_types_dict={'Scenario Key': 'number', 'Side Key': 'number',
                                                       'default': 'text'}, table_name='Scenario Side',
                                    names_column_title='Side Name', is_new_record=self.is_new_record)
        self.sidesTable.hide_column('Scenario Key')
        self.sidesTable.add_count_column(scenario_key=self.scenario_key, table='Scenario Ship Formation',
                                         count_column_title="# Formations", keys_to_iterate=['Scenario Side'])


    def draw_ship_formations_objects(self):
        #This is just a DataTable instance with a couple of controls.
        #Framing UI Widgets
        formationsLabel = Label(self.screen_frames[6], text="Ship Formations")
        formationsLabel.pack(side="left")
        self.shipFormationsFrame = Frame(self.screen_frames[6], background='black')
        self.shipFormationsFrame.pack(side='left', expand=1)
        #Basic information for setting up the table
        self.draw_ship_formations_table()
        self.data_tables_on_screen.append(self.shipFormationsTable)
        #Add buttons to add and delete formations
        buttonFrame = Frame(self.screen_frames[6])
        buttonFrame.pack(side='right')
        plusButton = Button(buttonFrame, text="+", command=lambda: self.pick_new_formation_side(self))  # brings up a window that will let you add a new side
        plusButton.pack(side='top')
        minusButton = Button(buttonFrame, text='-', command=lambda: self.delete_formation_record())
        minusButton.pack(side='top')
        formationsButton = Button(buttonFrame, text="Edit Formation", command=lambda: self.open_edit_ship_formation_window())
        formationsButton.pack(side='top')

    def draw_ship_formations_table(self):
        ship_formations_window_column_names_list = ['Scenario Side', 'Formation ID', 'Formation Name']
        ship_formations_window_column_types_dict = {'Formation Name': 'text', 'default': 'number'}
        # And finally we set up the table and register it.
        self.shipFormationsTable = DataTable(parent=self.shipFormationsFrame, scenario_key=self.scenario_key,
                                             column_types_dict=ship_formations_window_column_types_dict,
                                             table_name='Scenario Ship Formation', names_column_title='Formation Name',
                                             column_names_list=ship_formations_window_column_names_list)
        self.shipFormationsTable.hide_column('Scenario Side')
        self.shipFormationsTable.add_count_column(scenario_key=self.scenario_key, table='Scenario Ship Formation Ship',
                                                  count_column_title="# Ships",
                                                  keys_to_iterate=['Scenario Side', 'Formation ID'])
        self.add_side_names_column()
        self.shipFormationsTable.thisTable.width = self.shipFormationsFrame.winfo_width() * 0.88


    def draw_buttons(self):
        buttonFrame = Frame(self.screen_frames[8])
        buttonFrame.pack(side='right')
        SaveAndCloseButton = Button(buttonFrame, text="Save and Close", command=lambda: self.save_window_data(close_window_after=True))
        SaveAndCloseButton.pack(side='bottom')

    def add_side_names_column(self):
        try:
            side_name_index = self.shipFormationsTable.thisModel.getColumnIndex('Side Name')
        except:
            self.shipFormationsTable.thisTable.addColumn('Side Name')
            side_name_index = self.shipFormationsTable.thisModel.getColumnIndex('Side Name')
        side_key_index = self.shipFormationsTable.thisModel.getColumnIndex('Scenario Side')

        for i in range(self.shipFormationsTable.thisModel.getRowCount()):
            this_side_index = self.shipFormationsTable.thisModel.getCellRecord(i, side_key_index)
            self.shipFormationsTable.thisModel.setValueAt(self.side_names_dict[this_side_index], rowIndex=i, columnIndex=side_name_index)
        self.shipFormationsTable.thisModel.moveColumn(self.shipFormationsTable.thisModel.getColumnIndex("Side Name"), self.shipFormationsTable.thisModel.getColumnIndex("Formation ID"))

    #Sides window related functions
    def open_edit_sides_window(self):
        try:
            this_data = self.sidesTable.get_table().get_currentRecord()
        except:
            tkMessageBox.showerror(title="Error!", message="Please select a valid record")
            return
        windowLayer_width, windowLayer_height = self.width * 0.83, self.height * 0.83
        self.windowLayer = ToplevelUpdate(self.parent, orig_screen=self, width=windowLayer_width,
                                          height=windowLayer_height)
        self.update_screen()
        # Now need to make a new column list with column headings from the sides table
        sides_window_column_names_dict = self.sidesTable.get_column_names_dict()
        editWindow = SideInfoWindow(parent=self.windowLayer, column_name_list=sides_window_column_names_dict,
                                    data=this_data)  # Turn things over to the edit window

    def open_new_side_record(self):
        windowLayer_width, windowLayer_height = self.width * 0.83, self.height * 0.83
        self.windowLayer = ToplevelUpdate(self.parent, orig_screen=self, width=windowLayer_width,
                                          height=windowLayer_height)
        self.update_screen()
        sides_model = self.sidesTable.get_model()
        sides_window_column_names_dict = self.sidesTable.get_column_names_dict()
        this_data = self.return_column_data(modelName=sides_model, columnName='Side Key')
        this_index = determine_index(this_data)
        editWindow = SideInfoWindow(parent=self.windowLayer, column_name_list=sides_window_column_names_dict,
                                    new_record_index=this_index)

    def delete_side_record(self):
        this_data = self.sidesTable.get_currentRecord()
        msg_string = "This will permanently delete the side record for " + str(this_data[
                                                                                   'Side Name']) + ", possibly causing formations associated with it to be lost.  Are you sure you wish to do this?"
        confirm_delete = tkMessageBox.askyesno(title="Confirm delete", message=msg_string, default='no')
        if confirm_delete:
            cursor, connection = connect_to_db(returnConnection=True)
            this_key = this_data['Side Key']
            cursor.execute("""DELETE FROM 'Scenario Side' WHERE [Scenario Key]=? AND [Side Key]=?;""", (self.scenario_key, this_key,))
            connection.commit()
            close_connection(cursor)
            self.force_refresh()

    #Ship formation window related functions

    def open_edit_ship_formation_window(self):
        windowLayer_width, windowLayer_height = self.width * 0.83, self.height * 0.83
        self.windowLayer = ToplevelUpdate(self.parent, orig_screen=self, width=windowLayer_width,
                                          height=windowLayer_height)
        self.update_screen()
        # Need to get the side key currently selected.
        try:
            this_data = self.shipFormationsTable.thisTable.get_currentRecord()
        except:
            tkMessageBox.showerror(title="Error!", message="Please select a valid record")
            return
        print this_data
        formationScreen = ShipFormationScreen(parent=self.windowLayer, scenario_key=self.scenario_key, data=this_data, is_new_record=False)

    """
    def open_new_ship_formation_record(self):
        windowLayer_width, windowLayer_height = self.width * 0.83, self.height * 0.83
        self.windowLayer = ToplevelUpdate(self.parent, orig_screen=self, width=windowLayer_width,
                                          height=windowLayer_height)
        self.update_screen()
        formations_model = self.shipFormationsTable.get_model()
        #Finish this function
    """

    def open_new_ship_formation_record(self, new_formation_side_name, is_ship_formation):

        #Now we gather the data we need
        new_formation_side_key = None
        indexes_in_use = []
        formations_model = self.shipFormationsTable.get_model()
        side_key_column = formations_model.getColumnIndex('Scenario Side')
        side_name_column = formations_model.getColumnIndex("Side Name")
        formation_key_column = formations_model.getColumnIndex('Formation ID')
        for i in xrange(formations_model.getRowCount()):
            if formations_model.getCellRecord(i, side_name_column) == new_formation_side_name:
                indexes_in_use.append(formations_model.getCellRecord(i, formation_key_column))
                if new_formation_side_key == None:
                    new_formation_side_key = formations_model.getCellRecord(i, side_key_column)
        this_index = determine_index(indexes_in_use)
        this_data = {'Scenario Side': new_formation_side_key, 'Scenario Side Name': new_formation_side_name,
                     'Formation ID': this_index, 'Formation Name': ""}
        # First we set up the layer for the window itself
        windowLayer_width, windowLayer_height = self.width * 0.83, self.height * 0.83
        self.windowLayer = ToplevelUpdate(self.parent, orig_screen=self, width=windowLayer_width, height=windowLayer_height)
        self.update_screen()
        if is_ship_formation:
            formationScreen = ShipFormationScreen(parent=self.windowLayer, scenario_key=self.scenario_key, data=this_data, is_new_record=True)

    def pick_new_formation_side(self, is_ship_formation=True):
        pickSideLayer = ToplevelUpdate(self.parent, orig_screen=self, width=self.width * 0.2, height=self.height * 0.2)
        self.update_screen()
        # First need to find out what side the formation will be on...
        formation_model = self.shipFormationsTable.get_model()
        side_name_list = list(set(self.return_column_data(modelName=formation_model, columnName='Side Name')))
        pickSideWindow = FormationSidePicker(parent=pickSideLayer, scenario_window=self, side_name_list=side_name_list, is_ship_formation=is_ship_formation)
        self.update_screen()

    def delete_formation_record(self):
        this_data = self.shipFormationsTable.get_currentRecord()
        msg_string = "This will permanently delete the side record for " + str(this_data[
                                                                                   'Formation Name']) + ", possibly causing formations associated with it to be lost.  Are you sure you wish to do this?"
        confirm_delete = tkMessageBox.askyesno(title="Confirm delete", message=msg_string, default='no')
        if confirm_delete:
            cursor, connection = connect_to_db(returnConnection=True)
            side_key = this_data['Scenario Side']
            formation_key = this_data['Formation ID']
            cursor.execute("""DELETE FROM 'Scenario Ship Formation' WHERE [Scenario Key]=? AND [Scenario Side]=? AND [Formation ID]=?""", (self.scenario_key, side_key, formation_key,))
            connection.commit()
            close_connection(cursor)
            self.force_refresh()


    #Closing the window, saving data, and doing both at the same time

    def close_window(self):
        self.destroy()
        self.parent.destroy()  # Have to take out that TopLayer canvas as well
        self.master.force_refresh()

    def save_window_data(self, close_window_after=False):
        new_values = self.get_new_values()
        if self.is_new_record:
            for i in range(len(new_values)):
                if new_values[i] == '':  # Effectively a null result
                    new_values[i] = "NULL"
            new_values = tuple(new_values)
            cursor, connection = connect_to_db(returnConnection=True)
            cursor.execute("""INSERT INTO Scenario VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                new_values[0], new_values[1], new_values[2], new_values[3], new_values[4], new_values[5], new_values[6],
                new_values[7], new_values[8], new_values[9], new_values[10], new_values[11], new_values[12],
                new_values[13],
                new_values[14], new_values[15], new_values[16]))
            connection.commit()
            close_connection(cursor)
        else:
            changes_to_commit = {}
            # First we look for any discrepancies between the old data (if it exists) and the new
            for i in range(len(self.field_values)):
                if new_values[i] != self.field_values[i]:
                    changes_to_commit[self.field_names_list[i]] = new_values[i]
            if len(changes_to_commit) > 0: #If any values have changed, update those values only within the database.
                cursor, connection = connect_to_db(returnConnection=True)
                for key in changes_to_commit:
                    if key == 'Scenario Key':  # Final wall against the scenario key ever, ever being changed
                        pass
                    else:
                        new_val = changes_to_commit[key]
                        cursor.execute("""UPDATE Scenario SET [{}]=? WHERE [Scenario Key]=?;""".format(key),
                                       (new_val, self.scenario_key))
                        connection.commit()
                close_connection(cursor)
        # Once save has been completed the function will end with:
        if close_window_after:
            self.close_window()

    #General utility functions

    def update_screen(self):
        self.parent.update()

    def get_scenario_key(self):
        return int(self.scenario_key)

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

    def force_refresh(self):
        #Refresh all DataTables present on screen
        self.sidesTable.pack_forget()
        self.draw_sides_table()
        self.shipFormationsTable.pack_forget()
        self.draw_ship_formations_table()

    def return_column_data(self, modelName, columnIndex=None, columnName=None):
        """Return the data in a list for this col,
        filters is a tuple of the form (key,value,operator,bool)"""
        # The version supplied with Tkintertable is broken, so this is my fixed version without the fancy filtering
        if columnIndex != None and columnIndex < len(self.columnNames):
            columnName = modelName.getColumnName(columnIndex)
        coldata = [modelName.data[str(n)][columnName] for n in range(1, modelName.getRowCount() + 1)]
        return coldata

    """


        def open_new_formation_record(self):
            pickSideLayer = ToplevelUpdate(self.parent, orig_screen=self, width=self.width * 0.2, height=self.height * 0.2)
            self.update_screen()
    """