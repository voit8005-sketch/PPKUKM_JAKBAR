import sqlite3
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'instance'/'ppkukm.db'
conn=sqlite3.connect(str(p))
c=conn.cursor()
allowed = ('Jakarta Barat Move with her','Kartini RE:Power')
q="SELECT id,title,category,status FROM news WHERE status='published' AND category!='kalender' AND (category!='event' OR title IN (?,?)) ORDER BY publish_date DESC"
for r in c.execute(q, allowed):
    print(r)
print('event count:', c.execute("SELECT COUNT(*) FROM news WHERE status='published' AND category='event' AND title IN (?,?)", allowed).fetchone()[0])
conn.close()
