To run the program, open MainMenu.py and run the MainMenu() function.  Most of the other .py files are designed to be called from the main menu and will throw errors if you try to run them on their own.

To quickly revert any Game files you have created (Game, Game Scenario Formation, Game Scenario Formation Ship, etc), open cleanup.py and run.

NOTE: DCA is written in Python 2.7 to take advantage of some older packages that haven't yet been updated.  Make sure you're using the correct version of Python to run it

External dependencies: tkintertable-1.2-py2.7 (https://pypi.python.org/pypi/tkintertable), python-docx (https://python-docx.readthedocs.io/en/latest/user/install.html).

For a current list of parts of the CaS rules DCA does not currently support, see ExcludedCases.rtf

Legalese:

Damage Control Assistant is free software.  It is released in accordance with the GNU Lesser General Public License v 3.0 (GNU LGPL), with source code freely available on GitHub.  You may freely copy, distribute, and modify the code as long as the GNU License is distributed with it and you make the source code of any derivative works freely available.

Command at Sea is written by Larry Bond, Chris Carlson, and Ed Kettler, and is copyright 2008 Clash of Arms Games.  This program is intended as a play aid and is NOT a substitute for a full set of the Command at Sea rules.  A full set of Command at Sea, 4th Edition rules is required to play the game and generate meaningful input for the program.

To work with the Command at Sea rules, the software requires a proprietary MySQLite database containing game statistics for the ships used in each scenario.  This is treated as an "external library" under the meaning of the LGPL 3.0, and is not distributed with the source code.

A copy of the full, proprietary database will be made available to approved project contributors upon request.

A blank copy of the database (containing schema only) is made available for users who wish to enter data from their Command at Sea products or simply insert their own values.

Users may substitute their own MySQLite database by altering the DATABASE_NAME parameter in helperfunctions.py.  This will automatically redirect all database queries to your database.
