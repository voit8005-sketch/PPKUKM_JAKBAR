import sqlite3
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'instance'/'ppkukm.db'
conn=sqlite3.connect(str(p))
c=conn.cursor()
reserved = ('Jakarta Barat Move with her','Kartini RE:Power')
q = "SELECT id,title,category,status,start_date FROM news WHERE status='published' AND category IN ('event','kalender') AND NOT (category='event' AND title IN (?,?)) ORDER BY start_date ASC"
for r in c.execute(q, reserved):
    print(r)
print('count:', c.execute("SELECT COUNT(*) FROM news WHERE status='published' AND category IN ('event','kalender') AND NOT (category='event' AND title IN (?,?))", reserved).fetchone()[0])
conn.close()
