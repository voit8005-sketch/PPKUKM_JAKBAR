import sqlite3
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'instance'/'ppkukm.db'
conn=sqlite3.connect(str(p))
c=conn.cursor()
for row in c.execute("SELECT id, title, category, status FROM news WHERE category='event' ORDER BY id DESC LIMIT 10"):
    print(row)
conn.close()
