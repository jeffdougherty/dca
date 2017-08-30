from helperfunctions import *
from tkintertable import *
from ttk import *
from InGameWindow import GameWindow

class TestDummy():

    def __init__(self):

        cursor = connect_to_db()
        cursor.execute("""SELECT * FROM 'Ship'""")
        ship_table_headings = [description[0] for description in cursor.description]
        db_dump = cursor.fetchall()
        self.ship_types = list(set(result[ship_table_headings.index('Ship Type')] for result in db_dump))
        self.countries = list(set(result[ship_table_headings.index('Country')] for result in db_dump))
        self.classes = list(set(result[ship_table_headings.index('Class')] for result in db_dump))
        self.class_variants = list(set(result[ship_table_headings.index('Class Variant')] for result in db_dump))
        print self.ship_types

#crash_test_dummy = TestDummy()

class TestFrame(Frame):

    def __init__(self, parent):
        self.parent = parent
        Frame.__init__(self, parent)
        self.app_window = self.master
        self.width = 1024
        self.height = 768
        self.title = "Scenarios"
        self.pack(fill=BOTH, expand=1)
        self.center_window()
        self.first_list = ['Alpha','Bravo','Charlie','Delta','Echo','Foxtrot']
        self.second_list = ['Able', 'Baker', 'Charlie', 'Dog', 'Easy', 'Fox']
        box_var = StringVar
        self.the_box = Combobox(textvariable=box_var, values=self.first_list)
        self.the_box.pack(side="left")
        the_button = Button(text="Switch", command=lambda: self.switch_lists(self.second_list))
        the_button.pack(side="left")
        quitButton = Button(self, text="Quit", command=self.quit)
        quitButton.pack(side="left")


    def center_window(self):
        w, h = self.width, self.height
        self.sw = self.parent.winfo_screenwidth()
        self.sh = self.parent.winfo_screenheight()
        x = (self.sw - self.width) / 2
        y = (self.sh - self.height) / 2
        self.parent.geometry('%dx%d+%d+%d' % (w, h, x, y))

    def switch_lists(self, new_list):
        self.the_box['values'] = new_list

def main():
    """
    cursor = connect_to_db()
    cursor.execute("SELECT * FROM Scenario")
    print cursor.fetchall()
    """
    root = Tk()

    ex = TestFrame(root)
    root.mainloop()

#if __name__ == '__main__':
#    main()

def db_test():
    cursor = connect_to_db()
    key_value = 309
    query_parameters = tuple([key_value])
    cursor.execute("SELECT * FROM 'Ship' WHERE [Ship Key]=?",query_parameters)
    b = cursor.fetchall()
    print b
    cursor.execute("""SELECT * FROM 'Ship' WHERE [Ship Key]={};""".format(key_value))
    a = cursor.fetchall()
    print a
    cursor.execute("""SELECT * FROM 'Ship Gun Mount' WHERE [Ship Key]=?""",(key_value,))
    f = len(cursor.fetchall())
    c = cursor.fetchall()
    print c
#db_test()

def file_testing():
    import os
    current_dir = os.getcwd()
    print current_dir
    print os.name
    print platform.system()
    #os.chdir("/~/Documents")
    if platform.system() == 'Darwin':
        if "/Users/" in os.getcwd():
            os_path = os.getcwd()
            users_dex = os_path.index("Users")
            next_slash = os_path.index("/", users_dex)
            start_dex = next_slash + 1
            end_dex = os_path.index("/", start_dex)
            user_name = os_path[start_dex:end_dex] #My god, it worked
            print user_name

#file_testing()

def game_log_testing():
    cursor = connect_to_db()
    cursor.execute("""SELECT * FROM [Game Log] WHERE [Game ID] = 1;""")
    print cursor.fetchall()

#game_log_testing()

def get_ship_types():
    cursor = connect_to_db()
    cursor.execute("""SELECT * FROM Ship""")
    headings = [description[0] for description in cursor.description]
    types = set([record[headings.index('Ship Type')] for record in cursor.fetchall()])
    print types
    print("Num Types: " + str(len(types)))

    #Aviation types: CVL, CV, CVE, AV, AVP, AVT, AVM
#et_ship_types()

def string_tests():
    number_list = '14, 20, 17, '
    start = 0
    digits = []
    while len(number_list) > 0:
        try:
            comma_posit = number_list.index(',')
        except:
            comma_posit = len(number_list) #No comma, so we're at the end of the string
        next_digit = number_list[start:comma_posit]
        if str.isdigit(next_digit):
            digits.append(int(next_digit))
        number_list = number_list[comma_posit+1:]
    return digits


#print string_tests()

def fire_flood_test():
    cursor = connect_to_db()
    cursor.execute("""SELECT * FROM 'Game Ship Fire/Flood' WHERE [Turns Remaining] > 0;""")
    a = cursor.fetchall()
    print a

#fire_flood_test()

def test_isnumeric():
    str1 = "When in the course of human events,"
    str2 = "12345"
    str3 = "Wh3n, in t3h c0u4s3 0f hum4n 3v3nt5,"
    for this_string in [str1, str2, str3]:
        print str.isdigit(this_string)

#test_isnumeric()

def test_iteration():
    a = 2
    b = 5
    c = 7
    for i in [a, b, c]:
        i += 2
    print a, b, c

#test_iteration()

def test_iteration_2():
    a = 2
    b = 5
    c = 7
    the_list = [a, b, c]
    for i in xrange(len(the_list)):
        the_list[i] = the_list[i] + 2
    print(the_list)

#test_iteration_2()

def test_toggle():
    a = True
    print(a)
    a = not a
    print(a)
    a = not a
    print(a)

test_toggle()
