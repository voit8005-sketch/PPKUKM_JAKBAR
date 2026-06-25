from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://' + os.getenv('DB_USER', 'root') + ':' + os.getenv('DB_PASS', '') + '@localhost/ppkukm_portal'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    publish_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref='news')

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

def add_sample_data():
    with app.app_context():
        # Create tables
        db.create_all()

        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@ppkukm.jakarta',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()

        # Add sample news if not exists
        if News.query.count() == 0:
            sample_news = [
                {
                    'title': 'Update Program PPKUKM Jakarta Barat 2024',
                    'content': 'Dinas Pemberdayaan dan Pengembangan Usaha Kecil Menengah Jakarta Barat meluncurkan program baru untuk mendukung UMKM di era digital. Program ini mencakup pelatihan online, pendampingan bisnis, dan akses permodalan yang lebih mudah.',
                    'author_id': admin.id
                },
                {
                    'title': 'Pelatihan Digital Marketing untuk UMKM',
                    'content': 'PPKUKM Jakarta Barat mengadakan pelatihan digital marketing gratis untuk para pelaku UMKM. Pelatihan ini akan mencakup strategi pemasaran online, penggunaan media sosial, dan teknik SEO dasar.',
                    'author_id': admin.id
                },
                {
                    'title': 'Bantuan Modal Usaha untuk Warga Terdampak Pandemi',
                    'content': 'Program bantuan modal usaha senilai Rp 50 juta per UMKM telah dibuka untuk warga Jakarta Barat yang terdampak pandemi. Pendaftaran dapat dilakukan melalui aplikasi online PPKUKM.',
                    'author_id': admin.id
                },
                {
                    'title': 'Workshop Kewirausahaan untuk Pemuda Jakarta Barat',
                    'content': 'Dalam rangka meningkatkan semangat kewirausahaan di kalangan pemuda, PPKUKM Jakarta Barat menyelenggarakan workshop kewirausahaan dengan tema "Memulai Bisnis di Era Digital".',
                    'author_id': admin.id
                },
                {
                    'title': 'Kolaborasi dengan Bank BUMN untuk Kredit UMKM',
                    'content': 'PPKUKM Jakarta Barat berkolaborasi dengan Bank BUMN untuk memberikan kredit usaha dengan bunga rendah khusus untuk UMKM di wilayah Jakarta Barat.',
                    'author_id': admin.id
                },
                {
                    'title': 'Pameran Produk UMKM Jakarta Barat 2024',
                    'content': 'Pameran produk UMKM terbesar di Jakarta Barat akan diselenggarakan bulan depan. Acara ini akan menampilkan berbagai produk inovatif dari pelaku UMKM lokal.',
                    'author_id': admin.id
                }
            ]

            for news_data in sample_news:
                news = News(**news_data)
                db.session.add(news)

        # Add sample services if not exists
        if Service.query.count() == 0:
            sample_services = [
                {
                    'title': 'Layanan Konsultasi Bisnis',
                    'description': 'Konsultasi gratis untuk perencanaan dan pengembangan bisnis UMKM. Kami siap membantu Anda menyusun strategi bisnis yang efektif dan berkelanjutan.',
                    'category': 'Konsultasi'
                },
                {
                    'title': 'Pendampingan Teknis Produksi',
                    'description': 'Bantuan teknis untuk meningkatkan kualitas produksi dan efisiensi proses bisnis. Termasuk pelatihan penggunaan teknologi produksi modern.',
                    'category': 'Teknis'
                },
                {
                    'title': 'Akses Permodalan',
                    'description': 'Fasilitasi akses permodalan melalui berbagai skema kredit dan bantuan dari pemerintah dan lembaga keuangan. Kami membantu proses pengajuan hingga pencairan.',
                    'category': 'Keuangan'
                },
                {
                    'title': 'Pelatihan dan Pengembangan SDM',
                    'description': 'Program pelatihan untuk meningkatkan kompetensi sumber daya manusia UMKM. Mulai dari keterampilan teknis hingga manajemen bisnis.',
                    'category': 'Pelatihan'
                },
                {
                    'title': 'Pemasaran dan Promosi',
                    'description': 'Bantuan pemasaran produk UMKM melalui berbagai kanal, termasuk online marketplace, pameran, dan media sosial. Tingkatkan jangkauan pasar Anda.',
                    'category': 'Pemasaran'
                },
                {
                    'title': 'Sertifikasi Produk dan Standarisasi',
                    'description': 'Bantuan proses sertifikasi produk untuk memenuhi standar nasional dan internasional. Pastikan produk Anda berkualitas dan terpercaya.',
                    'category': 'Sertifikasi'
                }
            ]

            for service_data in sample_services:
                service = Service(**service_data)
                db.session.add(service)

        db.session.commit()
        print("Sample data added successfully!")

if __name__ == '__main__':
    add_sample_data()