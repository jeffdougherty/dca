#Show a list of scenarios currently in the database, and allow creation of new scenarios

from tkintertable import *
from helperfunctions import connect_to_db, close_connection, generate_data_set, determine_index
from helperclasses import ToplevelUpdate
from NewEditScenarioWindow import ScenarioInfoWindow
from PrintScenarioDocs import DocsPrinter
from GameManagement import NewGamePicker

class ScenariosScreen(Frame):

    def __init__(self, parent):
        self.parent = parent
        Frame.__init__(self, parent, background = 'white')
        self.app_window = self.master
        self.width = 1024
        self.height = 768
        self.title = "Scenarios"
        self.pack(fill = BOTH, expand = 1)
        self.center_window()
        self.scenarios_table()
        self.make_buttons()

    def center_window(self):
        w,h = self.width, self.height
        self.sw = self.parent.winfo_screenwidth()
        self.sh = self.parent.winfo_screenheight()
        x = (self.sw - self.width)/2
        y = (self.sh - self.height)/2
        self.parent.geometry('%dx%d+%d+%d' % (w,h,x,y))


    def scenarios_table(self):
        #This version of the function can import all the data from any table given.  Will need some work on scaling.
        #Intention is to reuse these functions in other windows with minimal code changes.
        #first we import all the data from each scenario
        cursor = connect_to_db()
        avail_scenarios = cursor.execute("SELECT * FROM Scenario")
        avail_scenarios = avail_scenarios.fetchall()
        self.column_name_list = [description[0] for description in cursor.description]
        #Function in the middle takes that name list and generates the data set
        (the_data, num_records) = generate_data_set(avail_scenarios, self.column_name_list, {'Scenario Key': 'number', 'default': 'text'})
        #Now finally draw the thing
        self.tframe = Frame(master=self)
        self.tframe.grid(row=1, column=1)
        self.thisModel = TableModel(newdict=the_data)
        self.thisTable = TableCanvas(parent=self.tframe, model=self.thisModel, width=self.width * 0.88, editable=False)
        self.thisTable.height = self.thisTable.rowheight * num_records
        self.thisTable.createTableFrame()
        self.thisTable.autoResizeColumns()
        close_connection(cursor)

    def force_refresh(self):
        print "force_refresh invoked!"
        #Need to retrieve new data from db.
        cursor = connect_to_db()
        num_records = len(self.thisModel.data)
        print "Current number of records: " + str(num_records)
        avail_scenarios = cursor.execute("SELECT * FROM Scenario")
        avail_scenarios = avail_scenarios.fetchall()
        print "New number of records: " + str(len(avail_scenarios))

        self.column_name_list = [description[0] for description in cursor.description]
        (new_data, num_records) = generate_data_set(avail_scenarios, self.column_name_list, {'Scenario Key': 'number', 'default': 'text'})
        self.thisModel = TableModel(newdict=new_data)
        self.thisTable.setModel(self.thisModel)
        self.thisTable.height = 20 * self.thisTable.rowheight * num_records
        self.thisTable.redrawTable()
        close_connection(cursor)

    def make_buttons(self):

        self.buttonFrame = Frame(self)
        self.buttonFrame.grid(row=2, column = 1)


        quitButton = Button(self, text="Quit", command=self.quit)
        quitButton.grid(row=2, column=3)
        mainMenuButton = Button(self.buttonFrame, text="Main Menu", command=lambda: self.back_to_main_menu())
        mainMenuButton.pack(side='right')
        deleteButton = Button(self.buttonFrame, text = "Delete Scenario", command=lambda: self.delete_this_record())
        deleteButton.pack(side='right')
        newButton = Button(self.buttonFrame, text="New Scenario", command=lambda: self.open_new_scenario_window())
        newButton.pack(side='left')

        editButton = Button(self.buttonFrame, text="Edit Scenario", command=lambda: self.open_edit_scenario_window())
        editButton.pack(side='left')
        prepButton = Button(self.buttonFrame, text="Print Docs", command=lambda: self.prepare_scenario_documents())
        prepButton.pack(side='left')
        gameButton = Button(self.buttonFrame, text="Start New Game", command=lambda: self.start_new_game())
        gameButton.pack(side='left')

    def back_to_main_menu(self):
        from MainMenu import ApplicationMainMenu #Waiting until here to see if it lets the class load successfully
        MainMenuNew = ApplicationMainMenu(self.parent)
        self.destroy()

    def open_edit_scenario_window(self):
        try:
            this_data = self.thisTable.get_currentRecord()
        except:
            tkMessageBox.showerror(title="Error!", message="Please select a valid record")
            return
        windowLayer_width, windowLayer_height = self.width * 0.83, self.height * 0.83
        self.windowLayer = ToplevelUpdate(self.parent, orig_screen = self, width=windowLayer_width, height=windowLayer_height)
        self.update_screen()
        editWindow = ScenarioInfoWindow(parent=self.windowLayer, field_names_list=self.column_name_list, data=this_data) #Turn things over to the edit window

    def open_new_scenario_window(self):
        windowLayer_width, windowLayer_height = self.width * 0.83, self.height * 0.83
        self.windowLayer = ToplevelUpdate(self.parent, orig_screen = self, width=windowLayer_width, height=windowLayer_height)
        self.update_screen()
        this_data = self.return_column_data(columnName='Scenario Key')
        this_index = determine_index(this_data)
        newWindow = ScenarioInfoWindow(parent=self.windowLayer, field_names_list=self.column_name_list, new_record_index=this_index)

    def delete_this_record(self):
        confirm_delete = tkMessageBox.askyesno(title="Confirm delete", message="This will permanently delete the scenario record, possibly causing sides and formations associated with it to be lost.  Are you sure you wish to do this?", default='no')
        if confirm_delete:
            this_data = self.thisTable.get_currentRecord()
            cursor, connection = connect_to_db(return_connection=True)
            this_key = this_data['Scenario Key']
            cursor.execute("""DELETE FROM Scenario WHERE [Scenario Key]=?;""",(this_key,))
            connection.commit()
            #connection.commit()
            close_connection(cursor)
            self.thisTable.setSelectedRow(0)
            self.force_refresh()

    def prepare_scenario_documents(self):
        this_data = self.thisTable.get_currentRecord()
        print this_data
        self.printLayer = ToplevelUpdate(self, orig_screen=self, width = self.width * 0.6, height = self.width * 0.2)
        self.printLayer.center_window()
        self.update_screen()
        prepare_documents = DocsPrinter(parent=self.printLayer, data=this_data)

    def start_new_game(self):
        this_data = self.thisTable.get_currentRecord()
        this_scenario_key = this_data['Scenario Key']
        this_scenario_name = this_data['Scenario Title']
        windowLayer_width, windowLayer_height = self.width * 0.83, self.height * 0.83
        self.windowLayer = ToplevelUpdate(self.parent, orig_screen=self, width=windowLayer_width,
                                          height=windowLayer_height)
        self.update_screen()
        make_new_game = NewGamePicker(parent=self.windowLayer, from_main_menu=False, scenario_key=this_scenario_key, scenario_name=this_scenario_name)

    def update_screen(self):
        self.parent.update()

    def return_column_data(self, columnIndex=None, columnName=None):
        """Return the data in a list for this col,
        filters is a tuple of the form (key,value,operator,bool)"""
        #The version supplied with Tkintertable is broken, so this is my fixed version without the fancy filtering
        if columnIndex != None and columnIndex < len(self.columnNames):
            columnName = self.thisModel.getColumnName(columnIndex)
        coldata = [self.thisModel.data[str(n)][columnName] for n in range(1, self.thisModel.getRowCount() + 1)]
        return coldata