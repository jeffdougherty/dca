from tkintertable import *
from helperfunctions import *
from Tkinter import _cnfmerge #Used in ToplevelUpdate

class DataTable(Frame):
    #Generic class for data tables.  Want it to be able to handle any data except the main scenario screen, so can assume it has a side_key as well as a scenario_key
    def __init__(self, parent, scenario_key, column_types_dict, table_name, names_column_title=None, is_new_record=False, column_names_list=None, additional_keys=None, sig_figs=None, column_title_alias_dict = None, names_dict=None):
        #column_names_list needs to be a list of columns in the given table, in the order you want them to appear in the finished data table.
        #If you want a column giving the number of related items in a lower level DB table, count_column needs to be in the following format:
        #(<name of table to count records on>, <string name for the count column>)  Must be a tuple or computer will barf

        #column_title_alias_dict allows you to substitute the name of a column with another name.  Must be dict in format original_col_name:new_col_name

        #names_dict is a provided names dictionary in the format Side Index: Side Name

        self.parent = parent
        Frame.__init__(self, parent, background='white')
        self.scenario_key = scenario_key
        self.column_names_list = column_names_list
        self.column_types_dict = column_types_dict
        self.table_name = table_name
        self.is_new_record = is_new_record
        self.additional_keys = additional_keys
        self.has_count_column = False
        if names_dict != None:
            self.names_dict = names_dict
        else:
            self.names_dict = {}
        self.column_title_alias_dict = column_title_alias_dict
        raw_data, column_headings, cursor = self.get_data_values()
        if sig_figs != None:
            for j in range(len(raw_data)):
                data_entry = list(raw_data[j])
                for i in range(len(data_entry)):
                    if type(data_entry[i]) == float:
                        data_entry[i] = to_precision(data_entry[i], sig_figs)
                raw_data[j] = tuple(data_entry)
        self.setup_model(raw_data, column_headings, cursor)
        self.draw_table()
        if names_column_title != None:
            self.create_names_dict(names_column = names_column_title)
        self.hidden_columns = []

    def get_data_values(self):
        #Retrieves the data for the table from the database
        cursor = connect_to_db()
        cmd_string = """SELECT * FROM '""" + str(self.table_name) + """' WHERE [Scenario Key]=?"""
        reference_values = [self.scenario_key]
        additional_cmd_string = "" #Used if you want to specify more than a scenario_key and side_key
        if self.additional_keys != None:
            for key in self.additional_keys.keys():
                additional_cmd_string += """ AND [""" + key + """]=?"""
                reference_values.append(self.additional_keys[key])
            cmd_string += additional_cmd_string
        reference_values = tuple(reference_values)
        cursor.execute(cmd_string, reference_values)
        raw_data = cursor.fetchall()
        raw_column_headings = cursor.description
        return raw_data, raw_column_headings, cursor

    def setup_model(self, raw_data, raw_column_headings, cursor, count_column=None):
        if self.is_new_record or len(raw_data) == 0:
            self.column_names_dict = {}
            if self.column_names_list == None: #Don't need to exclude any of the column headings from the finished table
                dummy_data, num_records, num_columns = generate_blank_data_set(cursor, self.table_name, self.column_types_dict)
            else: #Need to exclude some columns
                dummy_data, num_records, num_columns = generate_blank_data_set(cursor, self.table_name, self.column_types_dict, self.column_names_list)
            for i in range(1, num_columns + 1):
                self.column_names_dict[i] = dummy_data['columnorder'][i]
            self.thisModel = TableModel(newdict=dummy_data, rows=1, columns=num_columns)
            if self.column_title_alias_dict != None:
                for this_key in self.column_title_alias_dict.keys():
                    self.thisModel.relabel_Column(self.thisModel.getColumnIndex(this_key), self.column_title_alias_dict[this_key])
        else:
            if self.column_names_list == None: #Don't need to exclude any of the column headings from the finished table
                self.column_names_list = [description[0] for description in raw_column_headings]
                self.column_names_dict = generate_column_names_dict(raw_column_headings, alias_dict=self.column_title_alias_dict)
                the_data, num_records = generate_data_set(raw_data, self.column_names_list, self.column_types_dict)
            else:
                self.column_names_dict = generate_column_names_dict(raw_column_headings, self.column_names_list, alias_dict=self.column_title_alias_dict)
                the_data, num_records = generate_restricted_data_set(raw_data, self.column_names_dict, self.column_types_dict)
            self.thisModel = TableModel(newdict=the_data)
            if self.column_title_alias_dict != None:
                for this_key in self.column_title_alias_dict.keys():
                    self.thisModel.relabel_Column(self.thisModel.getColumnIndex(this_key), self.column_title_alias_dict[this_key])
        close_connection(cursor)

    def draw_table(self):
        #First put the framing objects on screen
        num_records = self.thisModel.getRowCount()
        num_columns = self.thisModel.getColumnCount()
        #Now we can draw the actual table
        self.thisTable = TableCanvasWithHide(parent=self.parent, model=self.thisModel, width=num_columns * 70, editable=False, height=num_records * 20)
        #self.thisTable = TableCanvas(parent=self.parent, model=self.thisModel, width=num_columns * 170,
        #                                     editable=False)
        #self.thisTable.height = 15 * num_records
        self.thisTable.createTableFrame()
        self.thisTable.autoResizeColumns()
        self.thisTable.redrawTable()

    def add_count_column(self, scenario_key, table=None, count_column_title=None, keys_to_iterate=None, additional_keys=None, force_refresh=False):
        assert force_refresh==True or (table != None and count_column_title != None and keys_to_iterate != None), "Missing data to add count column!"
        if not force_refresh:
            self.thisModel.addColumn(count_column_title, "number")
            self.has_count_column = True
            self.count_column_title = count_column_title
            self.count_column_table = table
            self.count_table_keys_to_iterate = keys_to_iterate
            self.count_table_additional_keys = additional_keys

        else:
            self.thisModel.addColumn(self.count_column_title, "number")
        output_column = self.thisModel.getColumnIndex(self.count_column_title)
        if self.is_new_record and not force_refresh:
            for i in xrange(self.thisModel.getRowCount()):
                self.thisModel.setValueAt(0, i, output_column)
        else:
            cursor = connect_to_db()
            for i in xrange(self.thisModel.getRowCount()):
                this_scenario_key = scenario_key
                cmd_string = """SELECT * FROM \'""" + str(self.count_column_table) + """\' WHERE [Scenario Key]=?"""
                reference_values = [this_scenario_key]
                for key in self.count_table_keys_to_iterate:
                    try:
                        key_column = self.thisModel.getColumnIndex(key)
                    except:
                        if key == 'Scenario Side':
                            try:
                                key_column = self.thisModel.getColumnIndex('Side Key')
                            except:
                                print "Cannot find key column!"
                    additional_cmd_string = """ AND [""" + str(key) + """]=?"""
                    cmd_string += additional_cmd_string
                    reference_values.append(self.thisModel.getCellRecord(i, key_column))
                if self.count_table_additional_keys != None:
                    for key in self.count_table_additional_keys.keys():
                        additional_cmd_string += """ AND [""" + key + """]=?"""
                        reference_values.append(additional_keys[i])
                    cmd_string += additional_cmd_string
                reference_values = tuple(reference_values)
                cursor.execute(cmd_string, reference_values)
                the_count = len(cursor.fetchall())
                self.thisModel.setValueAt(the_count, i, output_column)
            close_connection(cursor)

    def create_names_dict(self, names_column):
        try:
            side_index_list = self.return_column_data(modelName= self.thisModel, columnName='Side Key')
        except:
            try:
                side_index_list = self.return_column_data(modelName= self.thisModel, columnName=u'Side Key')
            except:
                try:
                    side_index_list = self.return_column_data(modelName= self.thisModel, columnName='Scenario Side')
                except:
                    pass
        side_name_list = self.return_column_data(modelName=self.thisModel, columnName=names_column)
        assert len(side_index_list) == len(side_name_list), "Side index list does not match side name list!"
        for i in xrange(len(side_index_list)):
            this_side_index = side_index_list[i]
            if not this_side_index in self.names_dict.keys():
                self.names_dict[this_side_index] = side_name_list[i]

    def get_model(self):
        return self.thisModel

    def get_table(self):
        return self.thisTable

    def get_column_names_dict(self):
        try:
            return self.column_names_dict
        except: #We haven't generated one
            return generate_column_names_dict()

    def get_currentRecord(self):
        # type: () -> object
        #Mimics the function in the base tkintertable TableCanvas class
        try:
            return self.thisTable.get_currentRecord()
        except:
            tkMessageBox.showerror(title="Error!", message="Please select a valid record")
            return

    def get_names_dict(self):
        try:
            return self.names_dict
        except:
            print "No names dictionary associated with this data table!"

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

    def hide_column(self, column_to_hide):
        self.thisTable.hide_column(column_to_hide)

    def sort_data(self, columnName, reverse=0):
        self.thisModel.setSortOrder(columnName=columnName, reverse=reverse)


class ToplevelUpdate(Toplevel):
    #Parent must be of class ScenariosScreen for this function to work
    #Identical to Toplevel widget, except that it can reach up and call the force_refresh() function
    def __init__(self, parent, orig_screen, width=None, height=None, cnf={}, **kw):
        self.parent = parent
        self.orig_screen = orig_screen
        if width != None:
            self.width = width
        if height != None:
            self.height = height
        if kw:
            cnf = _cnfmerge((cnf, kw))
        extra = ()
        for wmkey in ['screen', 'class_', 'class', 'visual',
                      'colormap']:
            if wmkey in cnf:
                val = cnf[wmkey]
                # TBD: a hack needed because some keys
                # are not valid as keyword arguments
                if wmkey[-1] == '_':
                    opt = '-' + wmkey[:-1]
                else:
                    opt = '-' + wmkey
                extra = extra + (opt, val)
                del cnf[wmkey]
        Toplevel.__init__(self, parent, cnf=cnf)

    def center_window(self):
        w, h = self.width, self.height
        self.sw = self.parent.winfo_screenwidth()
        self.sh = self.parent.winfo_screenheight()
        x = (self.sw - self.width) / 2
        y = (self.sh - self.height) / 2
        #self.parent.geometry('%dx%d+%d+%d' % (w, h, x, y))

    def force_refresh_data_tables(self):
        self.orig_screen.force_refresh()

    def force_refresh(self):
        self.orig_screen.force_refresh()

    def get_scenario_key(self):
        try:
            return self.orig_screen.get_scenario_key() #Parent should have this method...
        except:
            tkMessageBox.showerror(title="Error!", message="No scenario associated with this object's parent screen!") #...but accidents do happen.

    def refresh_master_screen(self):
        self.orig_screen.update_screen()

    def get_master_screen(self):
        return self.orig_screen

    def get_parent(self):
        return self.parent

    #def open_new_ship_formation_record(self):

class TableCanvasWithHide(TableCanvas):

    def __init__(self, parent=None, model=None, width=None, height=None, rows=10, cols=5, **kwargs):
        this_parent = parent
        this_model = model
        this_width = width
        this_height = height
        this_rows = rows
        this_cols = cols
        TableCanvas.__init__(self, parent=this_parent, model=this_model, width=this_width, height=this_height, rows=this_rows, cols=this_cols, **kwargs)
        self.hidden_columns = []

    def redrawVisible(self, event=None, callback=None):
        """Redraw the visible portion of the canvas"""

        model = self.model
        self.rows = self.model.getRowCount()
        self.cols = self.model.getColumnCount()
        #self.cols -= len(self.hidden_columns)

        self.tablewidth = (self.cellwidth) * self.cols
        self.configure(bg=self.cellbackgr)
        self.setColPositions()

        # are we drawing a filtered subset of the recs?
        if self.filtered == True and self.model.filteredrecs != None:
            self.rows = len(self.model.filteredrecs)
            self.delete('colrect')

        self.rowrange = range(0, self.rows)
        self.configure(scrollregion=(0, 0, self.tablewidth + self.x_start,
                                     self.rowheight * self.rows + 10))

        x1, y1, x2, y2 = self.getVisibleRegion()
        startvisiblerow, endvisiblerow = self.getVisibleRows(y1, y2)
        self.visiblerows = range(startvisiblerow, endvisiblerow)
        startvisiblecol, endvisiblecol = self.getVisibleCols(x1, x2)
        self.visiblecols = list(range(startvisiblecol, endvisiblecol)) #Added in the list() just in case this ever goes to Python 3.x
        #if len(self.hidden_columns) > 0:
        #    for index in self.hidden_columns:
        #        if index in self.visiblecols:
        #            self.visiblecols.remove(index)

        if self.cols == 0 or self.rows == 0:
            self.delete('entry')
            self.delete('rowrect')
            self.delete('currentrect')
            self.delete('gridline', 'text')
            self.tablerowheader.redraw()
            return

        self.drawGrid(startvisiblerow, endvisiblerow)
        align = self.align
        self.delete('fillrect')
        for row in self.visiblerows:
            if callback != None:
                callback()
            for col in self.visiblecols:
                colname = model.getColumnName(col)
                bgcolor = model.getColorAt(row, col, 'bg')
                fgcolor = model.getColorAt(row, col, 'fg')
                text = model.getValueAt(row, col)
                self.drawText(row, col, text, fgcolor, align)
                if bgcolor != None:
                    self.drawRect(row, col, color=bgcolor)

        # self.drawSelectedCol()
        self.tablecolheader.redraw()
        self.tablerowheader.redraw(align=self.align, showkeys=self.showkeynamesinheader)
        # self.setSelectedRow(self.currentrow)
        self.drawSelectedRow()
        self.drawSelectedRect(self.currentrow, self.currentcol)
        # print self.multiplerowlist

        if len(self.multiplerowlist) > 1:
            self.tablerowheader.drawSelectedRows(self.multiplerowlist)
            self.drawMultipleRows(self.multiplerowlist)
            self.drawMultipleCells()
        if len(self.hidden_columns) > 1:
            for column in self.hidden_columns:
                self.hide_column(column)
        return

    def createTableFrame(self, callback=None):
        """Adds column header and scrollbars and combines them with
           the current table adding all to the master frame provided in constructor.
           Table is then redrawn."""

        # Add the table and header to the frame
        self.tablerowheader = RowHeader(self.parentframe, self, width=self.rowheaderwidth)
        self.tablecolheader = ColumnHeaderWithHide(self.parentframe, self)
        self.Yscrollbar = AutoScrollbar(self.parentframe, orient=VERTICAL, command=self.set_yviews)
        self.Yscrollbar.grid(row=1, column=2, rowspan=1, sticky='news', pady=0, ipady=0)
        self.Xscrollbar = AutoScrollbar(self.parentframe, orient=HORIZONTAL, command=self.set_xviews)
        self.Xscrollbar.grid(row=2, column=1, columnspan=1, sticky='news')
        self['xscrollcommand'] = self.Xscrollbar.set
        self['yscrollcommand'] = self.Yscrollbar.set
        self.tablecolheader['xscrollcommand'] = self.Xscrollbar.set
        self.tablerowheader['yscrollcommand'] = self.Yscrollbar.set
        self.parentframe.rowconfigure(1, weight=1)
        self.parentframe.columnconfigure(1, weight=1)

        self.tablecolheader.grid(row=0, column=1, rowspan=1, sticky='news', pady=0, ipady=0)
        self.tablerowheader.grid(row=1, column=0, rowspan=1, sticky='news', pady=0, ipady=0)
        self.grid(row=1, column=1, rowspan=1, sticky='news', pady=0, ipady=0)

        self.adjustColumnWidths()
        self.redrawTable(callback=callback)
        self.parentframe.bind("<Configure>", self.redrawVisible)
        self.tablecolheader.xview("moveto", 0)
        self.xview("moveto", 0)
        return

    def updateModel(self, model):
        """Call this method to update the table model"""
        self.model = model
        self.rows = self.model.getRowCount()
        self.cols = self.model.getColumnCount() - len(self.hidden_columns)
        self.tablewidth = (self.cellwidth) * self.cols
        self.tablecolheader = ColumnHeaderWithHide(self.parentframe, self)
        self.tablerowheader = RowHeader(self.parentframe, self)
        self.createTableFrame()
        return

    def hide_column(self, column_to_hide):
        if column_to_hide not in self.hidden_columns:
            self.hidden_columns.append(column_to_hide)
        if column_to_hide not in self.model.columnwidths.keys() or self.model.columnwidths[column_to_hide] != 0:
            #if self.model.columnwidths[column_to_hide] != 0:
            self.model.columnwidths[column_to_hide] = 0

    def show_column(self, column_to_show):
        self.hidden_columns.remove(column_to_show)
        del self.model.columnwidths[column_to_show]
        self.redrawVisible()

    def get_hidden_columns(self):
        return self.hidden_columns

class ColumnHeaderWithHide(ColumnHeader):

    def __init__(self, parent=None, table=None):
        ColumnHeader.__init__(self, parent=parent, table=table)
        self.hidden_columns = table.get_hidden_columns()
        if len(self.hidden_columns) > 0:
            for this_column in self.hidden_columns:
                if this_column in self.columnlabels.keys():
                    del self.columnlabels[this_column]