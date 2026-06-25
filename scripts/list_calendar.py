import sqlite3
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'instance'/'ppkukm.db'
conn=sqlite3.connect(str(p))
c=conn.cursor()
for row in c.execute("SELECT id,title,category,status, start_date FROM news WHERE category IN ('event','kalender') ORDER BY start_date DESC, id DESC"):
    print(row)
conn.close()
