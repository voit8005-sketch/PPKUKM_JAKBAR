from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# Use the same database config as app.py
db_uri = os.getenv('DATABASE_URL', 'sqlite:///ppkukm.db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='staff')
    nip = db.Column(db.String(30), unique=True, nullable=True)
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    must_change_password = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: __import__('datetime').datetime.utcnow)

ADMIN_USERNAME = 'admin'
ADMIN_EMAIL = 'ppkukmadmin@gmail.com'
ADMIN_PASSWORD = 'Admin@PPKUKM2026'

def reset_admin():
    with app.app_context():
        # Create tables if not exist
        db.create_all()
        
        hashed = generate_password_hash(ADMIN_PASSWORD, method='pbkdf2:sha256', salt_length=32)

        admin = User.query.filter_by(username=ADMIN_USERNAME).first()
        if admin:
            admin.email = ADMIN_EMAIL
            admin.password_hash = hashed
            admin.role = 'admin'
            admin.is_active_account = True
            admin.must_change_password = False
            action = 'diperbarui'
        else:
            admin = User(
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                password_hash=hashed,
                role='admin',
                is_active_account=True,
                must_change_password=False
            )
            db.session.add(admin)
            action = 'dibuat'

        db.session.commit()

        print('=' * 50)
        print(f'[OK] Admin berhasil {action}!')
        print('=' * 50)
        print(f'Username : {ADMIN_USERNAME}')
        print(f'Email    : {ADMIN_EMAIL}')
        print(f'Password : {ADMIN_PASSWORD}')
        print(f'Role     : admin')
        print('=' * 50)
        print(f'Database : {db_uri}')
        print('=' * 50)

if __name__ == '__main__':
    reset_admin()
