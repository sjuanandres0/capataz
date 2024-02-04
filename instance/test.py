import sqlite3
con = sqlite3.connect("instance/capataz.db")
cur = con.cursor()
res = cur.execute("SELECT * FROM establishment;")
# res.fetchone()
# res.fetchall()
# print(res)
for r in res:
    print(r)