import sqlite3
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'instance'/'ppkukm.db'
conn=sqlite3.connect(str(p))
c=conn.cursor()
# Update the two inserted rows to exact titles
# Update by known IDs if present (safer)
c.execute("UPDATE news SET title=? WHERE id=?", ('Jakarta Barat Move with her', 28))
c.execute("UPDATE news SET title=? WHERE id=?", ('Kartini RE:Power', 29))
conn.commit()
print('Updated rows:', conn.total_changes)
for row in c.execute("SELECT id, title FROM news WHERE title IN ('Jakarta Barat Move with her','Kartini RE:Power')"):
    print(row)
conn.close()
