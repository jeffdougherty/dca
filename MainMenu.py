from tkintertable import *
from helperclasses import ToplevelUpdate, DataTable
from helperfunctions import connect_to_db
from ListScenariosScreen import ScenariosScreen
from GameManagement import NewGamePicker, LoadGamePicker
import tkFont

SHIP_TABLE_HEADINGS = []

class ApplicationMainMenu(Frame):

    def __init__(self, parent):
        self.parent = parent
        Frame.__init__(self, parent, background='white')
        self.app_window = self.master
        self.width = 256
        self.height = 512
        self.title = "Scenarios"
        self.pack(fill=BOTH, expand=1)
        self.center_window()
        self.screen_frames = []
        self.default_font = tkFont.Font(font={'family':'.SF NS Text', 'weight': 'normal', 'slant': 'roman', 'overstrike': 0, 'underline': 0, 'size': 13})
        self.title_font = tkFont.Font(font={'family':'.SF NS Text', 'weight': 'normal', 'slant': 'roman', 'overstrike': 0, 'underline': 0, 'size': 24})
        self.draw_main_menu()
        self.draw_title_label()

    def center_window(self):
        w, h = self.width, self.height
        self.sw = self.parent.winfo_screenwidth()
        self.sh = self.parent.winfo_screenheight()
        x = (self.sw - self.width) / 2
        y = (self.sh - self.height) / 2
        self.parent.geometry('%dx%d+%d+%d' % (w, h, x, y))

    def draw_main_menu(self):
        for i in xrange(3):
            #create frames to divide the screen into horizontal bands
            thisFrame = Frame(self, width=self.width, height = self.height/3)
            self.screen_frames.append(thisFrame)
            thisFrame.pack(fill='y')
        edit_scenario_button = Button(self.screen_frames[1], text="Create/Edit Scenario", command=lambda: self.open_scenarios_window())
        edit_scenario_button.pack(side='top')
        start_new_game_button = Button(self.screen_frames[1], text="Start New Game", command=lambda: self.start_new_game())
        start_new_game_button.pack(side='top')
        continue_game_button = Button(self.screen_frames[1], text="Load Existing Game", command=lambda: self.load_existing_game())
        continue_game_button.pack(side='top')
        quit_button = Button(self.screen_frames[1], text='Quit', command=self.quit)
        quit_button.pack(side='bottom')

    def open_scenarios_window(self):
        scenariosWindow = ScenariosScreen(self.parent)
        self.destroy()

    def draw_title_label(self):
        MenuTitleLabel = Label(self.screen_frames[0], text = "Main Menu", font=self.title_font)
        MenuTitleLabel.pack(side='top')

    def start_new_game(self):
        GamePickerWindow = Toplevel(self.parent, width = 720, height=96)
        GamePicker = NewGamePicker(parent=GamePickerWindow, from_main_menu=True)

    def load_existing_game(self):
        GamePickerWindow = Toplevel(self.parent, width=720, height=96)
        GamePickerWindow = LoadGamePicker(parent=GamePickerWindow, from_main_menu=True)

def main():
    """
    cursor = connect_to_db()
    cursor.execute("SELECT * FROM Scenario")
    print cursor.fetchall()
    """
    cursor = connect_to_db()
    cursor.execute(
        """SELECT * FROM 'Ship' WHERE [Ship Key]=309""")  # Get an example record so we can get the column headings.
    record_retrieved = cursor.fetchall()
    global SHIP_TABLE_HEADINGS
    SHIP_TABLE_HEADINGS = [description[0] for description in cursor.description]

    root = Tk()

    ex = ApplicationMainMenu(root)
    root.mainloop()

if __name__ == '__main__':
    main()