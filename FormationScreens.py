from tkintertable import *
from helperfunctions import *
from helperclasses import DataTable, ToplevelUpdate
from ttk import Combobox

class ShipFormationScreen(Frame):

    def __init__(self, parent, scenario_key, data, is_new_record=False, column_names_dict=None):
        self.parent = parent

        Frame.__init__(self, parent, background='white')
        self.pack(fill=BOTH, expand=1)
        self.update_geometry()
        self.scenario_key = scenario_key
        self.side_key = data['Scenario Side']
        try:
            self.side_name = data['Side Name']
        except:
            self.side_name = data['Scenario Side']
        self.formation_key = data['Formation ID']
        self.formation_name = data['Formation Name']
        self.is_new_record = is_new_record
        self.field_names = ["Side Name", "Formation ID", "Formation Name"]
        self.field_values = [self.side_name, self.formation_key, self.formation_name]
        additional_fields_to_retrieve = ["Formation Starting Location", "Formation Course", "Formation Speed", "Formation Orders"]
        self.field_types_dict = {"Side Name": "text", "Formation Name": "text", "Formation Starting Location": "text", "Formation Orders": "text", "default": "number"}
        self.field_names += additional_fields_to_retrieve
        if is_new_record:
            for i in xrange(len(additional_fields_to_retrieve)):
                self.field_values.append("")
        else:
            cursor = connect_to_db()
            db_dump = cursor.execute("""SELECT * FROM 'Scenario Ship Formation' WHERE [Scenario Key]=? AND [Scenario Side]=? AND [Formation ID]=?""",(self.scenario_key, self.side_key, self.formation_key,))
            formation_record = db_dump.fetchall()
            assert len(formation_record) == 1, "More than one formation record retrieved during ShipFormationScreen init"
            formation_column_headings = [description[0] for description in cursor.description]
            for i in xrange(len(formation_column_headings)):
                if formation_column_headings[i] in additional_fields_to_retrieve:
                    self.field_values.insert(i, formation_record[0][i])
            close_connection(cursor)
        print self.field_values
        print len(self.field_values)
        self.screen_frames = []
        self.text_fields_on_screen = []
        self.data_tables_on_screen = []
        self.draw_entry_fields()
        self.draw_ships_table_objects()
        self.draw_buttons()

    def update_geometry(self):
        self.width = self.parent.winfo_width()
        self.height = self.parent.winfo_toplevel().winfo_height()
        self.parent.geometry = self.winfo_toplevel().winfo_geometry()

    def draw_entry_fields(self):
        for i in xrange(4): #Will need to expand the number of frames
            thisFrame = Frame(self, width=self.width, height=(self.height / 6))
            self.screen_frames.append(thisFrame)
            # thisFrame.grid(row=i, column=1)
            thisFrame.pack(fill=Y)
        for i in xrange(len(self.field_values)):
            if i <= 2:
                parent_frame = self.screen_frames[0]
            elif i <= 5:
                parent_frame = self.screen_frames[1]
            elif i == 6:
                parent_frame = self.screen_frames[3]
            this_label = Label(parent_frame, text=self.field_names[i])
            this_label.pack(side="left")
            if i <= 5:
                this_data_entry = Entry(parent_frame)
                this_data_entry.insert(0, self.field_values[i])
                if i == 0:
                    this_data_entry.config(state=DISABLED, width=8)
                elif i == 1:
                    this_data_entry.config(state=DISABLED, width=3, justify=CENTER)
                elif i <= 3:
                    this_data_entry.config(width=14)
                else:
                    this_data_entry.config(width=5)
            elif i == 6:
                parent_width = parent_frame.winfo_width()
                this_data_entry = Text(parent_frame, width=64, height=24, highlightbackground='black', highlightthickness=1, wrap=WORD)
                #this_data_value.config(width=parent_frame.winfo_width)
                this_data_entry.insert(INSERT, self.field_values[i])
            self.text_fields_on_screen.append(this_data_entry)
            this_data_entry.pack(side='left')

    def draw_ships_table_objects(self):
        shipsLabel = Label(self.screen_frames[2], text="Ships")
        shipsLabel.pack(side="left")
        self.shipsFrame = Frame(self.screen_frames[2], background='black')
        self.shipsFrame.pack(side='left', expand=1)
        self.draw_ships_table()
        buttonFrame = Frame(self.screen_frames[2])
        buttonFrame.pack(side='left')
        plusButton = Button(buttonFrame, text="+", command=lambda: self.create_new_ship_record())
        plusButton.pack(side='top')
        minusButton = Button(buttonFrame, text="-", command=lambda: self.delete_ship_record())
        minusButton.pack(side='top')
        editButton = Button(self.screen_frames[2], text='Edit Ship', command=lambda: self.edit_ship_record())
        editButton.pack(side='right')

    def draw_ships_table(self):
        ship_window_column_names_list = ['Formation Ship Key', 'Ship Name', 'Annex A Key', 'Remarks']
        ship_window_column_types_dict = {'default': 'text', 'Annex A Key': 'number'}
        ship_window_additional_keys = {'Scenario Side': self.side_key, 'Formation ID': self.field_values[1]}
        annex_a_column_names_list = ['Ship Type', 'Class', 'Class Variant', 'Damage Pts', 'Speed']
        ships_table_column_indexes = {}
        annex_a_column_types_dict = {'Damage Pts': 'number', 'Speed': 'number', 'default': 'text'}
        self.shipsTable = DataTable(parent=self.shipsFrame, scenario_key=self.scenario_key,
                                    column_types_dict=ship_window_column_types_dict,
                                    table_name='Scenario Ship Formation Ship',
                                    column_names_list=ship_window_column_names_list,
                                    additional_keys=ship_window_additional_keys)
        self.data_tables_on_screen.append(self.shipsTable)
        # Now add the data columns we want to fill in
        self.shipsTable.hide_column('Country')
        self.shipsTable.hide_column('Annex A Key')
        self.shipsTable.hide_column('Remarks')
        self.shipsTable.thisTable.width = 64

        for new_column in annex_a_column_names_list:
            if new_column in annex_a_column_types_dict.keys():
                this_col_type = annex_a_column_types_dict[new_column]
            else:
                this_col_type = annex_a_column_types_dict['default']
            self.shipsTable.thisModel.addColumn(colname=new_column, coltype=this_col_type)
            ships_table_column_indexes[new_column] = self.shipsTable.thisModel.getColumnIndex(new_column)
        # Now we know where to get the data from and where to write it to once we have it
        # Need to know where the Annex A key is
        annex_key_index = self.shipsTable.thisModel.getColumnIndex('Annex A Key')
        #Get the positions of columns in Annex A
        cursor = connect_to_db()
        cursor.execute("""SELECT * FROM 'Ship' WHERE [Ship Key]=1;""")
        annex_a_column_headings = [description[0] for description in cursor.description]
        # Now we can get the data and write it
        check_for_empty_table = [self.shipsTable.thisModel.getCellRecord(0, annex_key_index)]
        if not is_empty(check_for_empty_table):
            for i in xrange(self.shipsTable.thisModel.getRowCount()):

                this_ship_index = self.shipsTable.thisModel.getCellRecord(i, annex_key_index)
                query_parameters = tuple([this_ship_index])
                cursor.execute("SELECT * FROM 'Ship' WHERE [Ship Key]=?", query_parameters)
                this_record = cursor.fetchall()


                for this_column in annex_a_column_names_list:
                    source_index = annex_a_column_headings.index(this_column)
                    this_value = this_record[0][source_index]
                    dest_index = ships_table_column_indexes[this_column]
                    self.shipsTable.thisModel.setValueAt(this_value, i, dest_index)

    def draw_buttons(self):
        buttonFrame = Frame(self.screen_frames[3])
        buttonFrame.pack(side='left')
        SaveAndCloseButton = Button(buttonFrame, text="Save and Close", command=lambda: self.save_and_close_window())
        SaveAndCloseButton.pack(side='bottom')

    def create_new_ship_record(self):
        windowLayer_width, windowLayer_height = self.width * 0.83, self.height * 0.83
        self.windowLayer = ToplevelUpdate(self.parent, orig_screen=self, width=windowLayer_width,
                                          height=windowLayer_height)
        self.update_screen()
        formations_model = self.shipsTable.get_model()
        try:
            this_data = self.return_column_data(modelName=formations_model, columnName='Formation Ship Key')
            next_ship_index = determine_index(this_data)
        except:
            next_ship_index = 1
        ship_entry = ShipEntryForm(self.windowLayer, self.scenario_key, self.side_key, self.formation_key, next_ship_index)

    def delete_ship_record(self):
        try:
            this_record = self.shipsTable.thisTable.get_currentRecord()
        except:
            tkMessageBox.showerror(title="Error!", message="Please select a valid record")
            return
        ship_key_value = this_record['Formation Ship Key']
        msg_string = "This will permanently delete the ship record for " + str(this_record['Ship Name']) + ", Are you sure you wish to do this?"
        confirm_delete = tkMessageBox.askyesno(title="Confirm delete", message=msg_string, default='no')
        if confirm_delete:
            cursor, conn = connect_to_db(returnConnection=True)
            cursor.execute("""DELETE FROM 'Scenario Ship Formation Ship' WHERE [Scenario Key]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?""", (self.scenario_key, self.side_key, self.formation_key, ship_key_value))
            conn.commit()
            close_connection(cursor)
        self.update_screen()
        self.force_refresh()

    def edit_ship_record(self):
        try:
            this_ship_record = self.shipsTable.thisTable.get_currentRecord()
        except:
            tkMessageBox.showerror(title="Error!", message="Please select a valid record")
            return
        windowLayer_width, windowLayer_height = self.width * 0.83, self.height * 0.83
        self.windowLayer = ToplevelUpdate(self.parent, orig_screen=self, width=windowLayer_width,
                                          height=windowLayer_height)
        self.update_screen()
        ship_edit = ShipEditForm(self.windowLayer, self.scenario_key, self.side_key, self.formation_key, this_ship_record)

    def close_window(self):
        self.parent.force_refresh_data_tables()
        self.destroy()
        self.parent.destroy()  # Have to take out that TopLayer canvas as well


    def save_and_close_window(self):
        new_values = self.get_new_values()
        cursor = connect_to_db()
        if self.is_new_record:
            for i in range(len(new_values)):
                if new_values[i] == '':  # Effectively a null result
                    new_values[i] = "NULL"
            new_values = tuple(new_values)
            cursor.execute("""INSERT INTO 'Scenario Ship Formation' VALUES(?,?,?,?,?,?,?,?)""", (self.scenario_key, self.side_key, self.formation_key, new_values[2], new_values[3], new_values[4], new_values[5], new_values[6],))
            cursor.connection.commit()
            close_connection(cursor)
        else:
            changes_to_commit = {}
            # First we look for any discrepancies between the old data (if it exists) and the new
            for i in range(len(self.field_values)):
                if new_values[i] != self.field_values[i]:
                    changes_to_commit[self.field_names[i]] = new_values[i]
            if len(changes_to_commit) > 0:
                for key in changes_to_commit:
                    if key == 'Scenario Key' or key == 'Scenario Side' or key == 'Formation ID': #One last check against changing the indexes
                        pass
                    else:
                        print key
                        new_val = changes_to_commit[key]
                        cursor.execute("""UPDATE 'Scenario Ship Formation' SET [{}]=? WHERE [Scenario Key]=? AND [Scenario Side]=? AND [Formation ID]=?""".format(key), (new_val, self.scenario_key, self.side_key, self.formation_key,))
                        cursor.connection.commit()
        close_connection(cursor)
        self.close_window()

    def get_new_values(self):
        # Returns a list consisting of all the field values currently on screen.
        self.update()
        self.update_idletasks()  # pure defensive programming
        new_values = []
        for i in range(len(self.field_values)):
            if i == 6:
                new_values.append(self.text_fields_on_screen[i].get(1.0, END))
            else:
                #May be a text or number we need to insert
                if self.field_names[i] in self.field_types_dict.keys(): #Means it's a text field
                    new_values.insert(i, self.text_fields_on_screen[i].get())
                else: #Number field
                    new_values.insert(i, float(self.text_fields_on_screen[i].get()))
                #new_values.insert(i, self.text_fields_on_screen[i].get())
        return new_values

    def return_column_data(self, modelName, columnIndex=None, columnName=None):
        """Return the data in a list for this col,
        filters is a tuple of the form (key,value,operator,bool)"""
        # The version supplied with Tkintertable is broken, so this is my fixed version without the fancy filtering
        if columnIndex != None and columnIndex < len(self.columnNames):
            columnName = modelName.getColumnName(columnIndex)
        coldata = [modelName.data[str(n)][columnName] for n in range(1, modelName.getRowCount() + 1)]
        return coldata

    def force_refresh(self):
        #Refresh all DataTables present on screen
        self.shipsTable.pack_forget()
        self.draw_ships_table()

    def update_screen(self):
        self.parent.update()

class FormationSidePicker(Frame):
    "Used to define which side a new formation will be assigned to."
    def __init__(self, parent, scenario_window, side_name_list, is_ship_formation=True):
        self.parent = parent
        self.scenario_window = scenario_window
        self.is_ship_formation = is_ship_formation
        Frame.__init__(self, parent, background='white')
        self.pack(fill=BOTH, expand=1)
        windowLabel = Label(self.parent, text='Choose Side')
        windowLabel.pack(side='top')
        pickSideWindow = Combobox(self.parent, textvariable='Choose Side', values=side_name_list,
                                  height=len(side_name_list))
        pickSideWindow.pack(side='top')
        buttonFrame = Frame(self.parent)
        buttonFrame.pack(side='top')
        OKButton = Button(self.parent, text='OK',
                          command=lambda: self.confirm_new_formation_side(pickSideWindow))
        CancelButton = Button(self.parent, text='Cancel', command=lambda: self.close_side_picker())
        OKButton.pack(side='left')
        CancelButton.pack(side='left')
        self.parent.refresh_master_screen()

    def close_side_picker(self):
        self.destroy()
        self.parent.destroy()
        #self.parent.master.destroy() #The scenario info window.

    def confirm_new_formation_side(self, windowInstance):
        new_formation_side = windowInstance.get()
        """
        parent_object = self.parent
        master_object = self.parent.master
        scenario_window = self.parent.master.get_parent()
        scenario_window.open_new_ship_formation_record(self=scenario_window, new_formation_side_name=new_formation_side, is_ship_formation=self.is_ship_formation)
        """
        self.scenario_window.open_new_ship_formation_record(new_formation_side_name=new_formation_side, is_ship_formation=self.is_ship_formation)
        self.close_side_picker()

class ShipEntryForm(Frame):

    def __init__(self, parent, scenario_key, side_key, formation_key, new_ship_index):
        #Store all input parameters, will be needed multiple times throughout the class
        self.parent = parent
        self.scenario_key = scenario_key
        self.side_key = side_key
        self.formation_key = formation_key
        self.new_ship_key = 0
        self.new_ship_index = new_ship_index
        self.ship_name = ""
        #Draw the background frame
        Frame.__init__(self, parent, background='white')
        self.pack(fill=BOTH, expand=1)
        self.update_geometry()
        #Retrieve the data to make our lists.  Will need to be stored in the class since it also has to be changed from multiple places
        cursor = connect_to_db()
        self.base_cmd_string = """SELECT * FROM 'Ship'"""
        self.columns_to_retrieve = ['Country', 'Ship Type', 'Class', 'Class Variant']
        self.supplemental_cmd_string = ""
        self.supplemental_args = {}
        self.indexes_dict = {}
        lists_dict = {}
        self.combobox_dict = {}
        cursor.execute(self.base_cmd_string)
        self.ship_table_headings = [description[0] for description in cursor.description]
        db_dump = cursor.fetchall()
        for this_column in self.columns_to_retrieve:
            self.indexes_dict[this_column] = self.ship_table_headings.index(this_column)
            this_list = list(set([result[self.indexes_dict[this_column]] for result in db_dump]))
            this_list.sort()
            lists_dict[this_column] = this_list
        self.indexes_dict['Ship Key'] = self.ship_table_headings.index('Ship Key')
        self.window_frames = []
        for i in xrange(2):
            this_frame = Frame(self, width=self.width, height = self.height/2)
            self.window_frames.append(this_frame)
            this_frame.pack(side='top')
        self.draw_name_entry_field()
        self.draw_combo_boxes(lists_dict)
        self.draw_key_field()
        self.draw_notes_field()
        self.draw_buttons()
        close_connection(cursor)

    def update_geometry(self):
        self.width = self.parent.winfo_width()
        self.height = self.parent.winfo_toplevel().winfo_height()
        self.parent.geometry = self.winfo_toplevel().winfo_geometry()

    def draw_name_entry_field(self):
        name_entry_frame = Frame(self.window_frames[0], width = self.width / 5)
        name_entry_frame.pack(side='left')
        name_entry_label = Label(name_entry_frame, text = "Name")
        name_entry_label.pack(side='top')
        self.name_entry_form = Combobox(name_entry_frame, values="--", state='disabled')
        self.name_entry_form.bind("<<ComboboxSelected>>", lambda a: self.name_selected())
        self.name_entry_form.pack(side='top')
    """
        self.name_entry_form = Entry(name_entry_frame)
        self.name_entry_form.pack(side='top')
    """

    def draw_combo_boxes(self, initial_lists_dict):
        combobox_frames = {}
        for this_column in self.columns_to_retrieve:
            combobox_frames[this_column] = Frame(self.window_frames[0], width = self.width / 5)
            combobox_frames[this_column].pack(side='left')
            this_combobox_label = Label(combobox_frames[this_column], text = this_column)
            this_combobox_label.pack(side='top')
            self.combobox_dict[this_column] = Combobox(combobox_frames[this_column], values=initial_lists_dict[this_column])
            self.combobox_dict[this_column].pack(side='top')
            if this_column == 'Ship Type':
                #self.strings_dict[this_column].trace('w', lambda: self.on_select_ship_type)
                self.combobox_dict[this_column].bind("<<ComboboxSelected>>", lambda a: self.on_select('Ship Type'))
            elif this_column == 'Country':
                #self.strings_dict[this_column].trace('w', lambda a, b, c: self.on_select_country)
                self.combobox_dict[this_column].bind("<<ComboboxSelected>>", lambda a: self.on_select('Country'))
            elif this_column == 'Class':
                #self.strings_dict[this_column].trace('w', lambda a, b, c: self.on_select_class)
                self.combobox_dict[this_column].bind("<<ComboboxSelected>>", lambda a: self.on_select('Class'))
            elif this_column == 'Class Variant':
                #self.strings_dict[this_column].trace('w', lambda: self.on_select_class_variant)
                self.class_variant_string = StringVar()
                self.combobox_dict[this_column].bind("<<ComboboxSelected>>", lambda a: self.on_select('Class Variant'))
                #self.combobox_dict[this_column]['textvariable'] = self.class_variant_string
                self.combobox_dict[this_column].config(state='disabled', textvariable=self.class_variant_string)

    def draw_key_field(self):
        key_frame = Frame(self.window_frames[0], width = self.width / 5)
        key_frame.pack(side='left')
        key_label = Label(key_frame, text="Ship Key")
        key_label.pack(side='top')
        self.ship_key_field = Entry(key_frame, text= "", width = 3)
        self.ship_key_field.config(state='readonly')
        self.ship_key_field.pack(side='top')

    def draw_notes_field(self):
        notes_frame = Frame(self.window_frames[1], width = self.width/5, height=5)
        notes_frame.pack(side='left')
        notes_label = Label(notes_frame, text = "Notes")
        notes_label.pack(side='left')
        self.notes_field = Text(notes_frame, width = self.width / 5, height=5, highlightbackground='black', highlightthickness=1, wrap=WORD)
        self.notes_field.pack(side='left')

    def draw_buttons(self):
        button_frame = Frame(self.window_frames[1])
        button_frame.pack(side='right')
        self.cancel_button = Button(button_frame, text="Cancel", command=lambda: self.close_ship_entry_form())
        self.cancel_button.pack(side='bottom')
        self.ok_button = Button(button_frame, text='OK', command=lambda: self.ok_button_function())
        self.ok_button.pack(side='top')
        self.ok_button.config(state='disabled')

    def on_select(self, key):
        if self.supplemental_cmd_string == "":
            additional_string = """ WHERE [""" + key + """]=?"""
            self.supplemental_args[key] = self.combobox_dict[key].get()
            self.supplemental_cmd_string += additional_string
        elif not key in self.supplemental_cmd_string:
            additional_string = """ AND [""" + key + """]=?"""
            self.supplemental_args[key] = self.combobox_dict[key].get()
            self.supplemental_cmd_string += additional_string
        cursor = connect_to_db()
        command_string = self.base_cmd_string + self.supplemental_cmd_string
        arguments_present = [key for key in self.supplemental_args.keys()]
        query_arguments = self.arguments_in_order(command_string, arguments_present)
        #query_arguments = (arg for arg in self.supplemental_args)
        #query_arguments = tuple(self.supplemental_args)
        print command_string
        print query_arguments
        cursor.execute(command_string, query_arguments)
        db_dump = cursor.fetchall()
        self.update_boxes(db_dump, key)
        close_connection(cursor)

    def arguments_in_order(self, cmd_string, arguments_present):
        index_dict = {}
        vars_dict = {}
        for item in arguments_present:
            this_index = cmd_string.index(item)
            if this_index != 1:
                index_dict[this_index] = item
                vars_dict[item] = self.combobox_dict[item].get()
        order_list = self.process_dictionary(index_dict, vars_dict)

        parameters = tuple(order_list)
        return parameters

    def process_dictionary(self, index_dict, vars_dict):
        first_key = min(index_dict.keys())
        value = index_dict.pop(first_key)
        var_to_return = [vars_dict[value]]
        if len(index_dict) == 0:
            return var_to_return
        else:
            var_to_return.extend(self.process_dictionary(index_dict, vars_dict))
            return var_to_return

    def update_boxes(self, db_dump, box_key):
        for key in self.combobox_dict.keys():
            if key != box_key:
                new_list = list(set([result[self.indexes_dict[key]] for result in db_dump]))
                new_list.sort()
                #Deal with the problem of there being a blank at the top of every "Class Variant" list.  We want that to be the default value so people don't have to select it
                self.combobox_dict[key].config(values=new_list)
        #Check to see if we should be enabling 'Class Variant' or the OK Button
        if self.combobox_dict['Class'].get() != None and self.combobox_dict['Class'].get() != "":
            class_variant = self.combobox_dict['Class Variant'].get()
            print "Length of class_variant = " + str(len(class_variant))
            if class_variant != None and class_variant != "":
                self.lookup_ship_key(db_dump)
            elif len(self.combobox_dict['Class Variant']['values']) > 1:
                self.combobox_dict['Class Variant'].config(state='readonly')
            else:
                self.lookup_ship_key(db_dump)
        else:
            self.combobox_dict['Class Variant'].config(state='disabled')
            self.name_entry_form.config(state='disabled')
            self.ok_button.config(state='disabled')

    def lookup_ship_key(self, db_dump):
        self.new_ship_key = list(set([result[self.indexes_dict['Ship Key']] for result in db_dump]))
        print self.new_ship_key
        assert len(self.new_ship_key) == 1, "More than one ship class found!"
        self.new_ship_key = self.new_ship_key[0]
        self.ship_key_field.config(state='normal')
        self.ship_key_field.delete(0, 'end')
        self.ship_key_field.insert(0, str(self.new_ship_key))
        self.ship_key_field.config(state='readonly')
        self.ok_button.config(state='normal')
        ship_names_in_class = self.lookup_ship_names(self.new_ship_key)
        self.name_entry_form.config(values=ship_names_in_class, state='enabled')

    def lookup_ship_names(self, this_ship_key):
        ship_names_avail = []
        cursor = connect_to_db()
        cursor.execute("""SELECT * FROM 'Ship Names' WHERE [Ship Key]=?""",(this_ship_key,))
        column_labels = [description[0] for description in cursor.description]
        name_index = column_labels.index('Ship Name')
        ships_in_class = cursor.fetchall()
        for ship in ships_in_class:
            ship_names_avail.append(ship[name_index])
        close_connection(cursor)
        return ship_names_avail

    def name_selected(self):
        self.ok_button.config(state='normal')

    def save_new_ship_record(self):
        ship_name = self.name_entry_form.get()
        ship_remarks = self.notes_field.get("1.0", END)
        cursor, connection = connect_to_db(returnConnection=True)
        cursor.execute("""INSERT INTO 'Scenario Ship Formation Ship' VALUES(?,?,?,?,?,?,?)""", (self.scenario_key, self.side_key, self.formation_key, self.new_ship_index, self.new_ship_key, ship_name, ship_remarks,))
        connection.commit()
        close_connection(cursor)

    def ok_button_function(self):
        self.save_new_ship_record()
        self.parent.update()
        self.close_ship_entry_form()

    def close_ship_entry_form(self):
        self.parent.force_refresh_data_tables()
        self.destroy()
        self.parent.destroy()

class ShipEditForm(ShipEntryForm):

    #Consists largely of a ShipEntryForm modified to take some initial values.  Dropdown menus aren't as constrained so you can actually change things...

    def __init__(self, parent, scenario_key, side_key, formation_key, data):
        self.parent = parent
        self.ship_index = data['Formation Ship Key']
        self.starting_data = data
        print self.starting_data
        self.strings_dictionary = {}
        self.class_variants_list = []
        ShipEntryForm.__init__(self, parent, scenario_key, side_key, formation_key, self.ship_index)
        self.check_fields_and_buttons()

    def draw_name_entry_field(self):
        starting_class_names = []
        name_entry_frame = Frame(self.window_frames[0], width=self.width / 5)
        name_entry_frame.pack(side='left')
        name_entry_label = Label(name_entry_frame, text="Name")
        name_entry_label.pack(side='top')
        self.name_entry_string = StringVar()
        self.name_entry_string.set(self.starting_data['Ship Name'])
        starting_class_names = self.lookup_ship_names(self.starting_data['Annex A Key'])
        self.name_entry_form = Combobox(name_entry_frame, textvariable=self.name_entry_string, values=starting_class_names, state='enabled')
        self.name_entry_form.bind("<<ComboboxSelected>>", lambda a: self.name_selected())
        self.name_entry_form.pack(side='top')
        """
        self.name_entry_form = Entry(name_entry_frame)
        self.name_entry_form.insert(0, self.starting_data['Ship Name'])
        self.name_entry_form.pack(side='top')
        """

    def draw_combo_boxes(self, initial_lists_dict):
        combobox_frames = {}
        for this_column in self.columns_to_retrieve:
            combobox_frames[this_column] = Frame(self.window_frames[0], width=self.width / 5)
            combobox_frames[this_column].pack(side='left')
            this_combobox_label = Label(combobox_frames[this_column], text=this_column)
            this_combobox_label.pack(side='top')
            self.strings_dictionary[this_column] = StringVar() #Need to instantiate the variable since it has to be available to tkinter...
            self.strings_dictionary[this_column].set(self.starting_data[this_column])#...and THEN we can assign a value to it
            self.combobox_dict[this_column] = Combobox(combobox_frames[this_column], textvariable=self.strings_dictionary[this_column],
                                                       values=initial_lists_dict[this_column])
            self.combobox_dict[this_column].pack(side='top')
            if this_column == 'Ship Type':
                # self.strings_dict[this_column].trace('w', lambda: self.on_select_ship_type)
                self.combobox_dict[this_column].bind("<<ComboboxSelected>>", lambda a: self.on_select('Ship Type'))
            elif this_column == 'Country':
                # self.strings_dict[this_column].trace('w', lambda a, b, c: self.on_select_country)
                self.combobox_dict[this_column].bind("<<ComboboxSelected>>", lambda a: self.on_select('Country'))
            elif this_column == 'Class':
                # self.strings_dict[this_column].trace('w', lambda a, b, c: self.on_select_class)
                self.combobox_dict[this_column].bind("<<ComboboxSelected>>", lambda a: self.on_select('Class'))
            elif this_column == 'Class Variant':
                # self.strings_dict[this_column].trace('w', lambda: self.on_select_class_variant)
                self.combobox_dict[this_column]['state'] = 'disabled'

    def draw_key_field(self):
        key_frame = Frame(self.window_frames[0], width=self.width / 5)
        key_frame.pack(side='left')
        key_label = Label(key_frame, text="Ship Key")
        key_label.pack(side='top')
        self.ship_key_field = Entry(key_frame, text="", width=3)
        self.ship_key_field.insert(0, self.starting_data['Annex A Key'])
        self.ship_key_field.config(state='readonly')
        self.ship_key_field.pack(side='top')

    def draw_notes_field(self):
        notes_frame = Frame(self.window_frames[1], width=self.width / 5, height=5)
        notes_frame.pack(side='left')
        notes_label = Label(notes_frame, text="Notes")
        notes_label.pack(side='left')
        self.notes_field = Text(notes_frame, width=self.width / 5, height=5, highlightbackground='black',
                                highlightthickness=1, wrap=WORD)
        self.notes_field.insert(INSERT, self.starting_data['Remarks'])
        self.notes_field.pack(side='left')

    def check_fields_and_buttons(self):
        cursor = connect_to_db()
        print self.starting_data['Class']
        cursor.execute("""SELECT * FROM 'Ship' WHERE [Class]=?""", (self.starting_data['Class'],))
        db_dump = cursor.fetchall()
        if len(db_dump) > 1:
            self.class_variants_list = []
            for entry in db_dump:
                self.class_variants_list.append(entry['Class Variant'])
            self.class_variants_list.sort()
            self.combobox_dict['Class Variant'].config(state='enabled', values=self.class_variants_list)
        else:
            self.class_variants_list = []
            self.combobox_dict['Class Variant'].config(state='disabled', values=self.class_variants_list)
            self.lookup_ship_key(db_dump)

    def lookup_ship_key(self, db_dump):
        #Needs to be fixed to delete an existing ship key if one is there
        self.new_ship_key = list(set([result[self.indexes_dict['Ship Key']] for result in db_dump]))
        print self.new_ship_key
        assert len(self.new_ship_key) == 1, "More than one ship class found!"
        self.new_ship_key = self.new_ship_key[0]
        self.ship_key_field.config(state='normal')
        self.ship_key_field.delete(0, 'end')
        self.ship_key_field.insert(0, str(self.new_ship_key))
        self.ship_key_field.config(state='readonly')
        #self.ok_button.config(state='normal')
        ship_names_in_class = self.lookup_ship_names(self.new_ship_key)
        self.name_entry_form.config(values=ship_names_in_class, state='enabled')

    def save_new_ship_record(self):
        #Function name is baked into the button and I'm not rewriting it.
        self.save_ship_record_changes()

    def save_ship_record_changes(self):
        data_sent = False
        ship_name = self.name_entry_form.get()
        ship_remarks = self.notes_field.get("1.0", END)
        annex_a_key = self.ship_key_field.get()
        new_data = {'Ship Name': ship_name, 'Remarks': ship_remarks, 'Annex A Key': annex_a_key}
        cursor, conn = connect_to_db(returnConnection=True)
        for key in new_data.keys():
            if new_data[key] != self.starting_data[key]:
                cursor.execute("""UPDATE 'Scenario Ship Formation Ship' SET [{}]=? WHERE [Scenario Key]=? AND [Scenario Side]=? AND [Formation ID]=? AND [Formation Ship Key]=?""".format(key), (new_data[key], self.scenario_key, self.side_key, self.formation_key, self.ship_index,))
                data_sent = True
        if data_sent:
            conn.commit()
        close_connection(cursor)

class AircraftFormationScreen(Frame):
    #One day there will be something here

    def __init__(self):
        pass