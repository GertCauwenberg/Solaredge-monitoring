# Copyright Gert Cauwenberg 2019

# This file is part of Solaredge-monitoring

# Solaredge-monitoring is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Solaredge-monitoring is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import MySQLdb as mdb

try:
    from config import dbhost, dbuser, dbpassword, dbname
except ModuleNotFoundError:
    print("Please copy config-sample.py to config.py")
    print("and fill in the correct values for your environment")
    sys.exit(1)


def connect_database():
    try:
        dbh = mdb.connect(dbhost, dbuser, dbpassword, dbname)
    except mdb.MySQLError:
        print("Can't connect to database - check database settings\n")
        sys.exit(1)
    cursor = dbh.cursor()
    cursor.execute("show tables")
    if cursor.rowcount < 4:
        print("Have you created your database tables?")
        print("Run mysql -u {0} -p {1} < database.sql".format(dbuser, dbname))
        sys.exit(1)
    return dbh
