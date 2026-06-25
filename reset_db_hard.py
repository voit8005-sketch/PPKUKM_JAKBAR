#!/usr/bin/env python3
import pymysql
from app import app
import os

# Hard reset - direct MySQL commands
DB_CONFIG = {
    'host': 'localhost',
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASS', ''),
    'database': 'ppkukm_portal',
    'charset': 'utf8mb4'
}

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

# Drop database and recreate
cursor.execute("DROP DATABASE IF EXISTS ppkukm_portal")
cursor.execute("CREATE DATABASE ppkukm_portal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
cursor.execute("USE ppkukm_portal")

# Load updated schema
with open('init_db.sql', 'r', encoding='utf-8') as f:
    sql = f.read()
cursor.executescript(sql)

conn.commit()
cursor.close()
conn.close()

print('✅ HARD RESET COMPLETE! DB recreated from init_db.sql')
print('Run: python app.py')
