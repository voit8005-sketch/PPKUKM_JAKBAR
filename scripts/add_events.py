import sqlite3
import datetime
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'instance'/'ppkukm.db'
conn=sqlite3.connect(str(p))
c=conn.cursor()
now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
items=[('jakarta move with her','',now,'published','event'),('kartini repower','',now,'published','event')]
for title,content,pub,status,cat in items:
    c.execute('INSERT INTO news (title, content, publish_date, status, category) VALUES (?,?,?,?,?)', (title,content,pub,status,cat))
conn.commit()
print('Inserted', len(items))
for row in c.execute("SELECT category, COUNT(*) FROM news WHERE status='published' GROUP BY category"):
    print(row)
for row in c.execute("SELECT id, title, category, status FROM news WHERE title IN ('jakarta move with her','kartini repower')"):
    print(row)
conn.close()
