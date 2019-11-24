#!/usr/bin/python3

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
from datetime import date, datetime
import requests
import sys
import common
from config import pvoutput_api


def get_systems(dbh):
    sql = """SELECT pvo_systemid, pvo_last_live from live_update"""
    cursor = dbh.cursor()

    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        if not result:
            init_layout_tables(dbh)
            result = get_systems(dbh)  # Try one more time
    except mdb.MySQLError as e:
        print("Error selecting output data: {0}".format(e))
        sys.exit(1)

    return result


def get_last_output_data(dbh, system):
    sql = """SELECT updated, sum(E_day), sum(power), max(temp)
             FROM optimizer JOIN layout ON layout.serial = optimizer.serial
             WHERE pvo_systemid = %s  AND updated > %s
             GROUP BY updated
             ORDER BY updated
             LIMIT 30"""
    cursor = dbh.cursor()

    try:
        cursor.execute(sql, system)
        result = cursor.fetchall()
    except mdb.MySQLError as e:
        print("Error selecting output data: {0}".format(e))
        sys.exit(1)

    return result


def create_csv(data):
    rows = []
    for output in data:
        row = (
            output[0].strftime("%Y%m%d"),
            output[0].strftime("%H:%M"),
            str(int(output[1])),
            str(int(output[2])),
        )
        rows.append(",".join(row))
    return ";".join(rows)


# Save the last updated timestamp in the live_update table
def save_last(dbh, system, last):
    sql = """UPDATE live_update
         SET pvo_last_live = %s
         WHERE pvo_systemid = %s
         """
    cursor = dbh.cursor()
    try:
        cursor.execute(sql, (last, system[0]))
    except mdb.MySQLError as e:
        print("Error inserting live_upload data: {0}".format(e))

    dbh.commit()
    return


def find_last(data):
    row = data[-1]
    return row[0]


def pvoutput_update(system, output):
    headers = {
        "X-Pvoutput-Apikey": str(pvoutput_api),
        "X-Pvoutput-systemid": str(system[0]),
    }

    data = {"data": output}

    response = requests.post(
        "https://pvoutput.org/service/r2/addbatchstatus.jsp",
        headers=headers,
        data=data
    )

    if response.status_code != 200:
        print("Received status code {}, {}".format(response.status_code, response.text))
        return False

    return True


def get_input(question, default, index):
    answer = input(question + " (default {0})? ".format(default[index]))
    if answer:
        try:
            answer = int(answer)
            default[index] = answer
        except ValueError:
            print("Please give me an integer")
            get_input(question, default, index)
    return default[index]


def add_panel(dbh, panel, default):
    print("We found a new panel with serial {0}".format(panel))
    print("Please answer a few questions about this panel")
    correct = ""
    while correct != "y":
        correct = ""
        sysid = get_input("What is the PVOutput System Id", default, 0)
        orientation = get_input(
            "What is the orientation (0 = North, 180 = South)", default, 1
        )
        inclination = get_input(
            "What is the inclination (0 = Flat, 90 = Vertical)", default, 2
        )
        print("We recorded these settings:")
        print("Panel serial:       {0}".format(panel))
        print("PVOutput System Id: {0}".format(sysid))
        print("Orientation:        {0}".format(orientation))
        print("Inclination:        {0}".format(inclination))
        while (correct != "y") and (correct != "n"):
            correct = input("Is this correct (Y/N)? ").lower()
            if correct:
                correct = correct[0]

    cursor = dbh.cursor()
    sql = """INSERT INTO layout
             (serial, pvo_systemid, orientation, inclination)
             VALUES (%s, %s, %s, %s)"""
    try:
        cursor.execute(sql, (panel, sysid, orientation, inclination))
    except mdb.MySQLError as e:
        print("Error inserting layout data: {0}".format(e))


def check_panel(dbh, panel, default):
    cursor = dbh.cursor()
    sql = """SELECT serial, pvo_systemid
             FROM layout WHERE serial = %s"""
    try:
        cursor.execute(sql, (panel,))
        if not cursor.rowcount:
            add_panel(dbh, panel, default)
            id = default[0]
        else:
            row = cursor.fetchone()
            id = row[1]
    except mdb.MySQLError as e:
        print("Error selecting serial {1}: {0}".format(e, panel))
        sys.exit(1)

    sql = """SELECT pvo_systemid
             FROM live_update WHERE pvo_systemid = %s"""
    try:
        cursor.execute(sql, (id,))
        if not cursor.rowcount:
            cursor.execute("INSERT INTO live_update (pvo_systemid) VALUES (%s)", (id,))
    except mdb.MySQLError as e:
        print("Error inserting systemid {1}: {0}".format(e, id))
        sys.exit(1)


def init_layout_tables(dbh):
    sql = """SELECT distinct(serial) from optimizer"""
    cursor = dbh.cursor()
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        if not rows:
            print("Run first fetch.py, then try this script again")
            sys.exit(1)
        default = [0, 0, 0]
        for row in rows:
            check_panel(dbh, row[0], default)
    except mdb.MySQLError as e:
        print("Error selecting serials: {0}".format(e))
        sys.exit(1)

    dbh.commit()


now = datetime.now()
print("Running at {0}".format(now))
db = common.connect_database()
systems = get_systems(db)
for system in systems:
    data = get_last_output_data(db, system)
    if len(data) > 0:
        csv = create_csv(data)
        print(
            "Uploading {0} results to pvupload for system {1}".format(
                len(data), system[0]
            )
        )
        res = pvoutput_update(system, csv)
        if res:
            last = find_last(data)
            save_last(db, system, last)
db.close()
