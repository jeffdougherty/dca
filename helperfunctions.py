import _sqlite3
"""
Helper functions I decided I wanted to be able to access from more than one Python file.  Easier to find this way.
Also includes an expanded class, because it ended up being a reused invisible widget
"""

def connect_to_db(returnConnection=False):
    conn = _sqlite3.connect('webcasdata2016.sqlite')
    c = conn.cursor()
    if returnConnection:
        return c, conn
    else:
        return c

def close_connection(cursor):
    #Helper function to make sure things get packed away neatly.
    conn = cursor.connection
    cursor.close()
    conn.close()

def column_name_to_label(column_name):
    #Completely trivial function that I'm putting here just so I can access it from multiple files
    if column_name == 'Scenario Side':
        return 'Side Key'
    else:
        return column_name.replace('_', ' ')

def generate_data_set(db_dump, column_name_list, column_types_dict):
    # Takes the generated data from a database and a list of the column names and puts it into the dictionary format that tkintertable likes
    # columns will be put on the table in the order they are listed in column_name_list
    # column_types_dict is a dictionary of the format {<column_name>: <type>}, takes {'default': <type>} for all names not specifically listed.
    #works as long as you want a table with all columns in the table listed.
    column_names = {}
    for i in range(1, len(column_name_list) + 1):
        if column_name_list[i - 1][0] == 'u': #should be '
            column_names[i] = column_name_list[i - 1][1:]
        else:
            column_names[i] = column_name_list[i - 1]
    the_data = {}
    if len(db_dump) > 0:
        record_number = 1
        for this_record in db_dump:
            the_record = {}
            record_title = str(record_number)
            record_number += 1
            column_number = 1
            for item in this_record:
                column_title = column_names[column_number]
                the_record[column_title] = item
                column_number += 1
            the_data[record_title] = the_record
    num_records = len(the_data)
    # Now add the bits TableModel needs for formatting
    column_labels = {}
    column_types = {}
    for key in column_names.keys():

        column_labels[column_names[key]] = column_name_to_label(column_names[key])
        if column_names[key] in column_types.keys():
            column_types[column_names[key]] = column_types_dict[key]
        else:
            try:
                column_types[column_names[key]] = column_types_dict['default']
            except:
                print "No column type found for " + str(column_names[key])
    the_data['columnlabels'] = column_labels
    the_data['columnorder'] = column_names
    the_data['columntypes'] = column_types
    return (the_data, num_records)

def generate_blank_data_set(cursor, table_name, column_types_dict, column_names_list=None):
    #generates a table based on the specified table name with the specified database cursor.  Does this by generating a blank data set and then feeding it to generate_data_set
    #needs column_types_dict because trying to translate the SQL result for column type to a tkintertable column type leads to extreme communism
    cmd_string = """PRAGMA table_info('""" + str(table_name) + """');"""
    raw_info = cursor.execute(cmd_string)
    db_dump = raw_info.fetchall()
    if column_names_list == None:
        column_names_list = []
        dummy_data = []
        for record in db_dump:
            column_names_list.insert(record[0], record[1])
            dummy_data.append('')
        dummy_data = [dummy_data]
    else:
        dummy_data = [['' for record in range(len(column_names_list))]]
    num_columns = len(column_names_list)
    the_data, num_records = generate_data_set(dummy_data, column_names_list, column_types_dict)
    return (the_data, num_records, num_columns)

def generate_restricted_data_set(db_dump, column_names_dict, column_types_dict):
    the_data = {}
    column_name_list = []
    if len(db_dump) > 0:
        record_number = 1
        for this_record in db_dump:
            the_record = {}
            record_title = str(record_number)
            record_number += 1
            column_number = 1
            for item in this_record:
                if column_number in column_names_dict.keys():
                    the_record[column_names_dict[column_number]] = item
                column_number += 1
            the_data[record_title] = the_record
    num_records = len(the_data)
    column_labels_output = {}
    column_types_output = {}
    for key in column_names_dict.keys():
        this_column_name = column_names_dict[key]
        column_name_list.append(this_column_name)
        column_labels_output[this_column_name] = column_name_to_label(this_column_name)
        if this_column_name in column_types_dict.keys():
            column_types_output[this_column_name] = column_types_dict[this_column_name]
        else:
            try:
                column_types_output[this_column_name] = column_types_dict['default']
            except:
                print "No column type found for " + str(this_column_name)
    the_data['columnorder'] = column_names_dict
    the_data['columnlabels'] = column_labels_output
    the_data['columntypes'] = column_types_output
    return (the_data, num_records)

def determine_index(this_data):
    #Determines what the first open index is in a table.  Returns either the first number missing from the sequence, or the highest number in the sequence + 1
    #Argument should be a list of indexes
    if is_empty(this_data):
        return 1
    highest_index = max(this_data)
    for this_number in xrange(1, highest_index): #sqlite indexes do not use 0!
        if this_number not in this_data:
            return this_number
    return highest_index + 1

def generate_column_names_dict(descriptions, column_names_list=None, alias_dict=None):
    column_names_dict = {}
    for i in xrange(1, len(descriptions) + 1):
        this_description = descriptions[i - 1]
        this_name = this_description[0]
        if this_name[0] == 'u':  # Should be ' character unless we have one of those annoying leading 'u's
            this_name = this_name[1:]
        if column_names_list == None:
            column_names_dict[i] = this_name
        elif this_name in column_names_list:
            column_names_dict[i] = this_name
            del column_names_list[column_names_list.index(this_name)] #Used to check and see if we have any columns left that aren't directly from the database at the end
        #if type(alias_dict) == dict and this_name in alias_dict.keys(): #May overwrite previously assigned value
        #    column_names_dict[i] = alias_dict[this_name]
    #Now add any additional columns that will be in the data table, but are not directly taken from the database
    if type(column_names_list) == list and len(column_names_list) > 0:
        max_key = max(column_names_dict.keys())
        for this_name in column_names_list:
            max_key += 1
            column_names_dict[max_key] = this_name
    return column_names_dict

def is_empty(this_list):
    if len(this_list) == 1 and this_list[0] == '':
        return True
    else:
        return False

def deepcopy(this_dict):
    output_dictionary = {}
    for key in this_dict.keys():
        output_dictionary[key] = this_dict[key]
    return output_dictionary

def create_names_dict(scenario_key):
    #Returns a dictionary of the format side key:side name for a given scenario key
    names_dict = {}
    cursor = connect_to_db()
    cursor.execute("""SELECT * FROM 'Scenario Side' WHERE [Scenario Key]=?;""",(scenario_key,))
    column_headers = [description[0] for description in cursor.description]
    side_key_index = column_headers.index('Side Key')
    side_name_index = column_headers.index('Side Name')
    for this_record in cursor.fetchall():
        if this_record[side_name_index][0] == 'u':
            names_dict[this_record[side_key_index]] = this_record[side_name_index][1:]
        else:
            names_dict[this_record[side_key_index]] = this_record[side_name_index]
    return names_dict

def to_precision(x,p):
    """
    returns a string representation of x formatted with a precision of p
    Based on the webkit javascript implementation taken from here:
    https://code.google.com/p/webkit-mirror/source/browse/JavaScriptCore/kjs/number_object.cpp
    Written by Randle Taylor, posted on GitHub- thanks!
    """


    import math
    x = float(x)

    if x == 0.:
        return "0." + "0"*(p-1)

    out = []

    if x < 0:
        out.append("-")
        x = -x

    e = int(math.log10(x))
    tens = math.pow(10, e - p + 1)
    n = math.floor(x/tens)

    if n < math.pow(10, p - 1):
        e = e -1
        tens = math.pow(10, e - p+1)
        n = math.floor(x / tens)

    if abs((n + 1.) * tens - x) <= abs(n * tens -x):
        n = n + 1

    if n >= math.pow(10,p):
        n = n / 10.
        e = e + 1


    m = "%.*g" % (p, n)

    if e < -2 or e >= p:
        out.append(m[0])
        if p > 1:
            out.append(".")
            out.extend(m[1:p])
        out.append('e')
        if e > 0:
            out.append("+")
        out.append(str(e))
    elif e == (p -1):
        out.append(m)
    elif e >= 0:
        out.append(m[:e+1])
        if e+1 < len(m):
            out.append(".")
            out.extend(m[e+1:])
    else:
        out.append("0.")
        out.extend(["0"]*-(e+1))
        out.append(m)

    return "".join(out)


def parse_comma_separated_numbers(number_list):
    # Takes a string of numbers separated by commas and turns them into a list of integers
    start = 0
    digits = []
    while len(number_list) > 0:
        try:
            comma_posit = number_list.index(',')
        except:
            comma_posit = len(number_list)  # No comma, so we're at the end of the string
        next_digit = number_list[start:comma_posit]
        if str.isnumeric(next_digit):
            digits.append(int(next_digit))
        number_list = number_list[comma_posit + 1:]
    return digits