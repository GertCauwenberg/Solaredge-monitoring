#!/usr/bin/python3
from solaredge_local import SolarEdge
import MySQLdb as mdb
from datetime import date, datetime
import sys
import common
from config import inverter

# Read inverter data
def read_inverter(client):
    status = client.get_status()
    inverter = status.inverters.primary
    data = {}
    data["temp"] = inverter.temperature.value
    data["serial"] = inverter.dspSn
    data["power"] = status.powerWatt
    data["e_day"] = status.energy.today
    data["e_total"] = status.energy.total
    data["u_ac"] = status.voltage
    data["u_dc"] = inverter.voltage
    return data


def read_optimizer(opt):
    data = {}
    data["serial"] = opt.serialNumber
    t = opt.lastReport
    data["timestamp"] = "{0}-{1}-{2} {3}:{4}:{5}".format(
        t.year, t.month, t.day, t.hour, t.minute, t.second
    )
    data["u_out"] = opt.outputV
    data["u_in"] = opt.inputV
    data["temp"] = opt.temperature.value
    return data


def read_optimizers(client):
    maintenance = client.get_maintenance()
    data = {}
    optimizers = maintenance.diagnostics.inverters.primary.optimizer
    for opt in optimizers:
        if opt.online:
            opt_data = read_optimizer(opt)
            data[str(opt_data["serial"])] = opt_data
    return data


def connect_inverter():
    try:
        return SolarEdge("http://{0}".format(inverter))
    except TimeoutError:
        print("Can't connect to inverter - check network settings\n")
        sys.exit(1)


# Retrieves the energy generated since the
# previous run
def get_energy_delta(dbh, inv):
    sql = """SELECT E_day, updated FROM inverter
              ORDER BY updated DESC
              LIMIT 1"""
    cursor = dbh.cursor()
    try:
        cursor.execute(sql)
        (E_day_prev, updated) = cursor.fetchone()
    except TypeError:  # When database is empty
        return inv["e_day"]
    except mdb.MySQLError as e:
        print("Error selecting last inverter data: {0}".format(e))
        sys.exit(1)

    if updated.date() != date.today():
        delta = inv["e_day"]
    else:
        delta = inv["e_day"] - E_day_prev

    print("Since last run we produced {:7.2f} Wh".format(delta))
    return delta


# Fetch for each optimizer the last recorded data
def get_last_optimizer_data(dbh):
    sql = """SELECT serial, updated, U_out, E_day, E_total 
              FROM optimizer
              WHERE (serial, updated) IN
              (SELECT serial, max(updated) 
              FROM optimizer GROUP BY serial);"""
    cursor = dbh.cursor()

    try:
        cursor.execute(sql)
        result = cursor.fetchall()
    except mdb.MySQLError as e:
        print("Error selecting last optimizer data: {0}".format(e))
        sys.exit(1)

    return result


# Distribute the energy reported by the inverter over the optimizers
# Of course this is at best an aproximation
def calculate_energy(dbh, inv, optimizers):
    inv["i_dc"] = inv["power"] / inv["u_dc"]

    E_delta = get_energy_delta(dbh, inv)

    U_total = 0
    for key in optimizers:
        opt = optimizers[key]
        U_total += opt["u_out"]

    last = get_last_optimizer_data(dbh)
    for row in last:
        (serial, updated, u_out, e_day, e_total) = row
        try:
            opt = optimizers[str(serial)]
            opt_delta = opt["u_out"] / U_total * E_delta
            opt["e_total"] = e_total + opt_delta

            if updated.date() == date.today():
                opt["e_day"] = e_day + opt_delta
            else:
                opt["e_day"] = opt_delta
        except KeyError:
            pass


# Save the data for inverter and optimizers in the database
def save_data(dbh, inv, optimizers, now):
    sql1 = """INSERT INTO inverter
         (updated, power, U_ac, U_dc, I_dc, E_day, E_total, temp) 
         VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    sql2 = """INSERT INTO optimizer
         (updated, serial, reported, power, U_out, U_in, E_day, E_total, temp) 
         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""

    cursor = dbh.cursor()
    try:
        cursor.execute(
            sql1,
            (
                now,
                inv["power"],
                inv["u_ac"],
                inv["u_dc"],
                inv["i_dc"],
                inv["e_day"],
                inv["e_total"],
                inv["temp"],
            ),
        )
    except mdb.MySQLError as e:
        print("Error inserting inverter data: {0}".format(e))

    for key in optimizers:
        opt = optimizers[key]
        try:
            cursor.execute(
                sql2,
                (
                    now,
                    opt["serial"],
                    opt["timestamp"],
                    opt["u_out"] * inv["i_dc"],
                    opt["u_out"],
                    opt["u_in"],
                    opt["e_day"],
                    opt["e_total"],
                    opt["temp"],
                ),
            )
        except KeyError:  # When database empty
            cursor.execute(
                sql2,
                (
                    now,
                    opt["serial"],
                    opt["timestamp"],
                    opt["u_out"] * inv["i_dc"],
                    opt["u_out"],
                    opt["u_in"],
                    0,
                    0,
                    opt["temp"],
                ),
            )
        except mdb.MySQLError as e:
            code, msg = e.args
            print("Error inserting optimizer data: code {0}, msg {1}".format(code, msg))
    dbh.commit()
    return


now = datetime.now()
print("Running at {0}".format(now))
client = connect_inverter()
inverter_data = read_inverter(client)
optimizer_data = read_optimizers(client)
if inverter_data["power"] > 0:
    db = common.connect_database()
    calculate_energy(db, inverter_data, optimizer_data)
    save_data(db, inverter_data, optimizer_data, now)
    db.close()
