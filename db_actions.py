# Cameron Ela, ceela@usc.edu
# This file creates a usable database from UEFA Champions League data
# from 2003-2018.

import sqlite3 as sl

db = "champions-league-data.db"


def create(fn):
    f = open(fn, "r")
    header = f.readline().strip().split(",")
    for i in range(len(header)):
        header[i] = "\'" + header[i] + "\'"
    header = ", ".join(header)
    f.close()

    conn = sl.connect(db)
    curs = conn.cursor()
    curs.execute("DROP TABLE IF EXISTS ucl_data")
    stmt = "CREATE TABLE ucl_data (" + header + ")"

    curs.execute(stmt)
    conn.commit()

    stmts = ["SELECT name FROM sqlite_master WHERE type='table'",
             "pragma table_info(ucl_data)"
             ]
    for stmt in stmts:
        result = curs.execute(stmt)
        for item in result:
            print(item)

    conn.close()


def store_data(fn, table):
    conn = sl.connect(db)
    curs = conn.cursor()

    f = open(fn, "r")
    header = f.readline().strip().split(",")
    n = 0
    for line in f:
        line = line.strip()
        values = line.split(",")
        stmt = "INSERT INTO " + table + " VALUES (" + ",".join(["?"] * len(values)) + ")"
        curs.execute(stmt, values)
        print(n, values)
        n += 1

    f.close()
    conn.commit()
    conn.close()


def main():
    create("csv/UCL Club Stats 2004-2018 copy.csv")
    store_data("csv/UCL Club Stats 2004-2018 copy.csv", "ucl_data")


if __name__ == "__main__":
    main()
