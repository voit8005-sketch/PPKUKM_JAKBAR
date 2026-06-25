#!/usr/bin/env python3
from app import app, db, News, User
from werkzeug.security import generate_password_hash
import datetime

with app.app_context():
    # Add sample admin if not exists
    admin_email = 'admin@ppkukm.jakarta'
    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            username='Admin',
            email=admin_email,
            password_hash=generate_password_hash('admin123'),
            role='admin',
            nip='ADMIN001'
        )
        db.session.add(admin)
    
    db.session.commit()
    admin = User.query.filter_by(email=admin_email).first()

# Sample news
    sample_news = [
        {
            'title': 'Semarak Bazar dan Pangan Ramadan 1447 H',
            'content': 'Pemerintah Kota Administrasi Jakarta Barat menggelar Semarak Bazar dan Pangan Ramadan selama tiga hari di Parkir Selatan Kantor Walikota. Diikuti 40 peserta termasuk 30 UMKM binaan.',
            'status': 'published',
            'category': 'event'
        },
        {
            'title': 'Bimbingan Teknis Sertifikat Halal Jakarta Barat',
            'content': 'Berkolaborasi dengan LPPOM MUI DKI Jakarta, dilaksanakan di 8 Kecamatan, diikuti 200 pelaku usaha.',
            'status': 'published',
            'category': 'pelatihan'
        },
        {
            'title': 'Pelatihan Digital Marketing untuk UMKM Jakarta Barat',
            'content': 'Program pelatihan gratis untuk meningkatkan kompetensi digital pelaku UMKM di era digital.',
            'status': 'published',
            'category': 'pelatihan'
        },
        {
            'title': 'Grand Opening Bazar UKM Jakarta Barat',
            'content': 'Bazar menampilkan puluhan produk khas UKM Jakarta Barat dengan harga terjangkau.',
            'status': 'published',
            'category': 'promosi'
        },
        {
            'title': 'Produk Unggulan Kopi Robusta Jakarta Barat',
            'content': 'Kopi Robusta dari petani lokal Jakarta Barat semakin banyak peminatnya.',
            'status': 'published',
            'category': 'ukm'
        }
    ]

    for data in sample_news:
        if not News.query.filter_by(title=data['title']).first():
            news = News(
                title=data['title'],
                content=data['content'],
                author_id=admin.id,
                status=data['status'],
                category=data.get('category', 'event'),
                reviewed_by_id=admin.id,
                reviewed_at=datetime.datetime.utcnow()
            )
            db.session.add(news)
    
    db.session.commit()
    print('✅ Sample news added!')
    print('Run: python app.py')
    print('Visit: http://localhost:5000')

