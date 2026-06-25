#!/usr/bin/env python3
from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.drop_all()
    db.create_all()
    
    # Create admin
    admin = User(
        username='admin',
        email='admin@ppkukm.jakarta',
        password_hash=generate_password_hash('admin123'),
        role='admin',
        nip='NIP-ADMIN-001'
    )
    db.session.add(admin)
    db.session.commit()
    
    print('✅ DB reset complete!')
    print('Admin: admin@ppkukm.jakarta / admin123')
    print('Run: python app.py')
