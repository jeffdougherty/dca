#Show/edit information associated with a side.
#Editing formations is done in a separate window linked from EditScenario
from tkintertable import *
from helperfunctions import connect_to_db, close_connection

class SideInfoWindow(Frame):

    def __init__(self, parent, column_name_list, data = None, new_record_index=None):
        #Lifted from the EditScenarioWindow constructor with side_key added in
        self.parent = parent
        Frame.__init__(self, parent, background='white')
        self.pack(fill=BOTH, expand=1)
        self.update_geometry()
        #column_name_list is actually a dictionary, need to convert
        self.column_name_list = []
        for key in column_name_list.keys():
            self.column_name_list.append(column_name_list[key])
        self.field_values = []
        self.scenario_key = parent.get_scenario_key()
        self.field_values.append(self.scenario_key)
        if data != None:
            print data
            self.is_new_record = False
            self.side_key = data['Side Key']
            self.field_values.append(self.side_key)
            for index in range(2, len(self.column_name_list)):
                this_column_name = self.column_name_list[index]
                print "Value for" + self.column_name_list[index] + "= " + str(data[this_column_name])

                self.field_values.insert(index, str(data[this_column_name]))
        else:
            self.is_new_record = True
            self.side_key = new_record_index
            self.field_values.append(self.side_key)
            for i in range(2, len(self.column_name_list)): #start point needs to be adjusted depending on how many fixed parameters there are
                self.field_values.append('')
            print self.field_values
        self.draw_entry_fields()
        self.draw_buttons()

    def update_geometry(self):
        self.width = self.parent.winfo_width()
        self.height = self.parent.winfo_toplevel().winfo_height()
        self.parent.geometry = self.winfo_toplevel().winfo_geometry()

    def draw_entry_fields(self):
        # Using a combination of frames and pack()
        self.screen_frames = []
        self.text_fields_on_screen = []
        for i in xrange(10):
            thisFrame = Frame(self, width=self.width, height=(self.height / 16))
            self.screen_frames.append(thisFrame)
            thisFrame.grid(row=i, column=1)
        #Add in the fields
        for i in xrange(len(self.field_values)):
            #First row: Scenario Key, Side Key, Side Name
            if i <= 1: #Scenario Key, Side Key
                parent_frame = self.screen_frames[0]
                thisDataLabel = Label(parent_frame, text=self.column_name_list[i], width=0)

                thisDataValue = Entry(parent_frame)
                thisDataValue.config(width=2, justify=CENTER)
                thisDataValue.insert(0, self.field_values[i])
                thisDataValue.config(state=DISABLED)
            elif i == 2: #Side Name
                parent_frame = self.screen_frames[0]
                thisDataLabel = Label(parent_frame, text=self.column_name_list[i], width=0)

                thisDataValue = Entry(parent_frame)
                thisDataValue.config(width=8, justify=LEFT)
                thisDataValue.insert(0, self.field_values[i])
            # Second through fourth rows: Longer text fields for sitrep, orders, and victory conditions
            elif i <= 5:
                if i == 3:
                    parent_frame = self.screen_frames[2]
                if i == 4:
                    parent_frame = self.screen_frames[4]
                if i == 5:
                    parent_frame = self.screen_frames[6]
                thisDataLabel = Label(parent_frame, text=self.column_name_list[i], width=0)
                thisDataValue = Text(parent_frame, width=64, height=4, highlightbackground='black', highlightthickness=1, wrap=WORD)
                if self.is_new_record:
                    print self.field_values[i]
                thisDataValue.insert(INSERT, self.field_values[i])
            else:
                break

            if i <= 1:
                thisDataValue.config(state=DISABLED)
            self.text_fields_on_screen.insert(i, thisDataValue)
            thisDataLabel.pack(side='left')
            thisDataValue.pack(side='left')

    def draw_buttons(self):
        buttonFrame = Frame(self.screen_frames[9])
        buttonFrame.pack(fill=Y,expand=1)
        saveAndCloseButton = Button(buttonFrame, text="Save and Close", command=lambda: self.save_and_close_window())
        saveAndCloseButton.pack(side='bottom')

    def close_window(self):
        self.master.force_refresh()  # going to need one of these in EditScenarioWindow
        self.destroy()
        self.parent.destroy()  # Have to take out that TopLayer canvas as well

    def save_and_close_window(self):
        new_values = self.get_new_values()
        if self.is_new_record:
            for i in range(len(new_values)):
                if new_values[i] == '':  # Effectively a null result
                    new_values[i] = "NULL"
            new_values = tuple(new_values)
            cursor = connect_to_db()
            cursor.execute("""INSERT INTO 'Scenario Side' VALUES(?,?,?,?,?,?)""", (new_values[0], new_values[1], new_values[2], new_values[3], new_values[4], new_values[5]))
            cursor.connection.commit()
            close_connection(cursor)
        else:
            changes_to_commit = {}
            for i in range(len(self.field_values)):
                if new_values[i] != self.field_values[i]:
                    changes_to_commit[self.column_name_list[i]] = new_values[i]
            if len(changes_to_commit) > 0:
                cursor = connect_to_db()
                for key in changes_to_commit:
                    if key == 'Scenario Key' or key == 'Side Key':  # Final wall against the scenario or side keys ever, ever being changed
                        pass
                    else:
                        new_val = changes_to_commit[key]
                        cursor.execute("""UPDATE 'Scenario Side' SET [{}]=? WHERE [Scenario Key]=? AND [Side Key]=?;""".format(key),
                                       (new_val, self.scenario_key, self.side_key))
                        cursor.connection.commit()
                close_connection(cursor)
        #Will end with
        self.close_window()

    def get_new_values(self):
        # Returns a list consisting of all the field values currently on screen.
        self.update()
        self.update_idletasks()  # pure defensive programming
        new_values = []
        for i in range(len(self.field_values)):
            if i == 0:
                new_values.append(self.scenario_key)
            elif i == 1:
                new_values.append(self.side_key)
            elif i == 2:
                new_values.append(self.text_fields_on_screen[i].get())
            else:
                new_values.append(self.text_fields_on_screen[i].get(1.0, END))
        return new_values