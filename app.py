from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from sqlalchemy import text, func, or_, and_, not_
import os
import datetime
# import imghdr  # deprecated Python 3.13
import hashlib
import secrets
from security_utils import validate_email_address
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
db_uri = os.getenv('DATABASE_URL', 'sqlite:///ppkukm.db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
print(f'Using DB: {db_uri}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER_PHOTOS'] = os.path.join(os.path.dirname(__file__), 'static/uploads/news/photos')
app.config['UPLOAD_FOLDER_VIDEOS'] = os.path.join(os.path.dirname(__file__), 'static/uploads/news/videos')
app.config['MAX_CONTENT_LENGTH'] = 300 * 1024 * 1024  # 300MB to accommodate video uploads

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov'}

MAX_IMAGE_SIZE = 10 * 1024 * 1024        # 10MB per photo
MAX_VIDEO_SIZE = 200 * 1024 * 1024       # 200MB per video

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='staff')  # 'admin' | 'staff'
    nip = db.Column(db.String(30), unique=True, nullable=True)
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    must_change_password = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    publish_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', foreign_keys=[author_id], backref='news')
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending' | 'published' | 'rejected'
    category = db.Column(db.String(50), default='event', nullable=False)  # 'pelatihan' | 'promosi' | 'event' | 'ukm' | 'kalender'
    # Optional event details
    registration_start_date = db.Column(db.DateTime, nullable=True)
    registration_end_date = db.Column(db.DateTime, nullable=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    participant_count = db.Column(db.Integer, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    # Review fields
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reviewer = db.relationship('User', foreign_keys=[reviewed_by_id])
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reject_reason = db.Column(db.Text, nullable=True)
    photos = db.relationship('NewsPhoto', backref='news', cascade='all, delete-orphan', lazy='select')
    videos = db.relationship('NewsVideo', backref='news', cascade='all, delete-orphan', lazy='select')

class NewsPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    news_id = db.Column(db.Integer, db.ForeignKey('news.id'), nullable=False)
    file_url = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class NewsVideo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    news_id = db.Column(db.Integer, db.ForeignKey('news.id'), nullable=False)
    file_url = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_required(f):
    """Only admin users may access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Halaman ini khusus admin.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def staff_required(f):
    """Only staff users (not admin) may access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'staff':
            flash('Halaman ini khusus staff.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def _redirect_home_by_role(user):
    if user.role == 'admin':
        return redirect(url_for('dashboard'))
    return redirect(url_for('staff_dashboard'))


def _get_ext(filename):
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


def validate_image(file):
    if not file or file.filename == '':
        return False, "File gambar kosong"

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)

    if size == 0:
        return False, "File gambar kosong tidak diizinkan"
    if size > MAX_IMAGE_SIZE:
        return False, f"Ukuran foto maksimal {MAX_IMAGE_SIZE // (1024*1024)}MB"

    ext = _get_ext(file.filename)
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, "Format foto harus png, jpg, jpeg, gif, atau webp"

    allowed_mimes = {
        'png': ['image/png'],
        'jpg': ['image/jpeg'],
        'jpeg': ['image/jpeg'],
        'gif': ['image/gif'],
        'webp': ['image/webp'],
    }
    if file.content_type not in allowed_mimes.get(ext, []):
        return False, f"MIME type tidak valid untuk foto {ext}"

    header = file.read(512)
    file.seek(0)

    if ext == 'webp':
        if not (header[:4] == b'RIFF' and header[8:12] == b'WEBP'):
            return False, "File WEBP tidak valid"
    else:
        # Fallback without imghdr (deprecated)
        if ext == 'png':
            if not header.startswith(b'\x89PNG\r\n\x1a\n'):
                return False, "File PNG tidak valid"
        elif ext in ['jpg', 'jpeg']:
            if not (header.startswith(b'\xff\xd8\xff') or b'\xff\xd8\xff\xe0' in header[:4]):
                return False, "File JPEG tidak valid"
        elif ext == 'gif':
            if header[:6] not in [b'GIF87a', b'GIF89a']:
                return False, "File GIF tidak valid"
        elif ext == 'webp':
            if not (header[:4] == b'RIFF' and header[8:12] == b'WEBP'):
                return False, "File WEBP tidak valid"
        else:
            return False, "File gambar tidak valid atau rusak"

    return True, "Valid"


def validate_video(file):
    if not file or file.filename == '':
        return False, "File video kosong"

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)

    if size == 0:
        return False, "File video kosong tidak diizinkan"
    if size > MAX_VIDEO_SIZE:
        return False, f"Ukuran video maksimal {MAX_VIDEO_SIZE // (1024*1024)}MB"

    ext = _get_ext(file.filename)
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        return False, "Format video harus mp4, webm, atau mov"

    allowed_mimes = {
        'mp4': ['video/mp4'],
        'webm': ['video/webm'],
        'mov': ['video/quicktime', 'video/mp4'],
    }
    if file.content_type not in allowed_mimes.get(ext, []):
        return False, f"MIME type tidak valid untuk video {ext}"

    header = file.read(32)
    file.seek(0)

    # Magic-number check
    # MP4 / MOV: bytes 4..8 == b'ftyp'
    # WebM:      first 4 bytes == 1A 45 DF A3
    if ext in ('mp4', 'mov'):
        if len(header) < 12 or header[4:8] != b'ftyp':
            return False, "File video tidak valid (signature ftyp tidak ditemukan)"
    elif ext == 'webm':
        if header[:4] != b'\x1a\x45\xdf\xa3':
            return False, "File WEBM tidak valid"

    return True, "Valid"


def save_media_file(file, folder, kind):
    """Validate then save a single media file. Returns (filename_or_None, message)."""
    validator = validate_image if kind == 'image' else validate_video
    is_valid, message = validator(file)
    if not is_valid:
        return None, message

    try:
        ext = _get_ext(secure_filename(file.filename))
        timestamp = datetime.datetime.now().timestamp()
        digest = hashlib.sha256(f"{timestamp}_{file.filename}".encode()).hexdigest()[:20]
        name = f"{int(timestamp)}_{digest}.{ext}"

        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, name)
        file.save(path)

        if not os.path.exists(path):
            return None, "Gagal menyimpan file"
        return name, "Berhasil"
    except Exception as e:
        return None, f"Error: {e}"


@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' cdn.tailwindcss.com cdn.jsdelivr.net unpkg.com; "
        "style-src 'self' 'unsafe-inline' fonts.googleapis.com; "
        "font-src 'self' fonts.gstatic.com; "
        "img-src 'self' data: images.unsplash.com; "
        "media-src 'self'; "
        "connect-src 'self'"
    )
    return response


@app.route('/')
def index():
    # Show non-calendar published news; for `event` category only include
    # the two specific titles the user requested.
    allowed_event_titles = ['Jakarta Barat Move with her', 'Kartini RE:Power']
    news = News.query.filter(
        News.status == 'published',
        News.category != 'kalender',
        or_(News.category != 'event', News.title.in_(allowed_event_titles))
    ).order_by(News.publish_date.desc()).all()
    # Event count should reflect only the two visible events
    event_count = News.query.filter(News.status == 'published', News.category == 'event', News.title.in_(allowed_event_titles)).count()
    cat_counts = {
        'semua':    len(news),
        'event':    event_count,
        'pelatihan':sum(1 for n in news if n.category == 'pelatihan'),
        'promosi':  sum(1 for n in news if n.category == 'promosi'),
        'ukm':      sum(1 for n in news if n.category == 'ukm'),
    }
    return render_template('index.html', news=news, cat_counts=cat_counts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_home_by_role(current_user)

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        email_valid, email_msg = validate_email_address(email)
        if not email_valid:
            flash(f'Email tidak valid: {email_msg}', 'error')
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash('Email atau password salah', 'error')
            return render_template('login.html')

        if user.role not in ('admin', 'staff'):
            flash('Akses ditolak.', 'error')
            return render_template('login.html')

        if not user.is_active_account:
            flash('Akun Anda telah dinonaktifkan. Hubungi admin.', 'error')
            return render_template('login.html')

        login_user(user)

        if user.must_change_password:
            flash('Harap ganti kata sandi sementara Anda sebelum melanjutkan.', 'warning')
            return redirect(url_for('change_password'))

        flash(f'Selamat datang, {user.username}!', 'success')
        return _redirect_home_by_role(user)

    return render_template('login.html')


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pw = request.form.get('current_password', '')
        new_pw = request.form.get('new_password', '')
        confirm_pw = request.form.get('confirm_password', '')

        if not check_password_hash(current_user.password_hash, current_pw):
            flash('Kata sandi saat ini salah.', 'error')
            return render_template('change_password.html')

        if len(new_pw) < 8:
            flash('Kata sandi baru minimal 8 karakter.', 'error')
            return render_template('change_password.html')

        if new_pw != confirm_pw:
            flash('Konfirmasi kata sandi tidak cocok.', 'error')
            return render_template('change_password.html')

        current_user.password_hash = generate_password_hash(new_pw, method='pbkdf2:sha256', salt_length=32)
        current_user.must_change_password = False
        db.session.commit()
        flash('Kata sandi berhasil diperbarui.', 'success')
        return _redirect_home_by_role(current_user)

    return render_template('change_password.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/dashboard')
@admin_required
def dashboard():
    news_list = News.query.filter_by(status='published').order_by(News.publish_date.desc()).all()
    pending_count = News.query.filter(News.status == 'pending', News.category != 'kalender').count()
    calendar_pending_count = News.query.filter_by(status='pending', category='kalender').count()
    return render_template('dashboard.html', news=news_list, pending_count=pending_count, calendar_pending_count=calendar_pending_count)


@app.route('/profil-organisasi')
def profil_organisasi():
    return render_template('profil_organisasi.html')


@app.route('/regulasi')
def regulasi():
    return render_template('regulasi.html')


@app.route('/berita/bimtek-sertifikat-halal')
def berita_bimtek():
    return render_template('berita_bimtek.html')


@app.route('/berita/semarak-bazar-pangan-ramadan')
def berita_bazar():
    return render_template('berita_bazar.html')


@app.route('/berita/<int:news_id>')
def berita_detail(news_id):
    item = News.query.get_or_404(news_id)

    # Kalender hanya ditampilkan di halaman kalender.
    if item.category in ('event', 'kalender') and item.status == 'published':
        return redirect(url_for('calendar_detail', event_id=item.id))

    if item.status != 'published':
        # Only the author (staff) or any admin may preview non-published news
        if not current_user.is_authenticated or (
            current_user.role != 'admin' and current_user.id != item.author_id
        ):
            abort(404)

    return render_template('berita_detail.html', item=item)



@app.route('/profil-organisasi/subbagian-tata-usaha')
def subbagian_tata_usaha():
    return render_template('subbagian_tata_usaha.html')


@app.route('/profil-organisasi/seksi-perindustrian')
def seksi_perindustrian():
    return render_template('seksi_perindustrian.html')


@app.route('/profil-organisasi/seksi-perdagangan')
def seksi_perdagangan():
    return render_template('seksi_perdagangan.html')


@app.route('/profil-organisasi/seksi-koperasi-ukm')
def seksi_koperasi_ukm():
    return render_template('seksi_koperasi_ukm.html')


@app.route('/layanan')
def layanan():
    return render_template('layanan.html')


@app.route('/manfaat-pelatihan')
def manfaat_pelatihan():
    return render_template('manfaat_pelatihan.html')


@app.route('/calendar')
def calendar():
    today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    if month and not year:
        year = datetime.date.today().year

    # Reserve two event titles to appear only in Berita Terkini
    reserved_event_titles = ['Jakarta Barat Move with her', 'Kartini RE:Power']

    query = News.query.filter(
        News.status == 'published',
        News.category.in_(['event', 'kalender']),
        # Exclude the reserved `event` titles from the calendar listing so
        # they remain visible only in the Berita Terkini section.
        not_(and_(News.category == 'event', News.title.in_(reserved_event_titles)))
    )

    if month and year:
        query = query.filter(
            func.strftime('%m', News.start_date) == f"{month:02d}",
            func.strftime('%Y', News.start_date) == str(year),
        )
    elif year and not month:
        query = query.filter(func.strftime('%Y', News.start_date) == str(year))
    # else: no date filtering so both past and future events appear

    events = query.order_by(News.start_date.asc()).all()
    current_year = datetime.date.today().year
    years = [current_year - 1, current_year, current_year + 1]
    month_names = [
        'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ]
    return render_template(
        'calendar.html',
        events=events,
        selected_month=month,
        selected_year=year,
        month_names=month_names,
        years=years,
    )


@app.route('/calendar/<int:event_id>')
def calendar_detail(event_id):
    event = News.query.filter(
        News.id == event_id,
        News.category.in_(['event', 'kalender']),
        News.status == 'published'
    ).first_or_404()
    return render_template('calendar_detail.html', event=event)


@app.route('/calendar/new', methods=['GET', 'POST'])
@login_required
def calendar_new():
    if current_user.role not in ('staff', 'admin'):
        flash('Halaman ini hanya untuk staf atau admin.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        content = (request.form.get('content') or '').strip()
        location = (request.form.get('location') or '').strip() or None
        participant_count = None
        start_date = None
        end_date = None
        registration_start_date = None
        registration_end_date = None

        if not title:
            flash('Judul acara wajib diisi.', 'error')
            return render_template('calendar_form.html')

        start_date_str = request.form.get('start_date', '').strip()
        end_date_str = request.form.get('end_date', '').strip()
        participant_str = request.form.get('participant_count', '').strip()
        reg_start_str = request.form.get('registration_start_date', '').strip()
        reg_end_str = request.form.get('registration_end_date', '').strip()

        if start_date_str:
            try:
                start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Format tanggal pelaksanaan tidak valid.', 'error')
                return render_template('calendar_form.html')

        if end_date_str:
            try:
                end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Format tanggal selesai pelaksanaan tidak valid.', 'error')
                return render_template('calendar_form.html')
        elif start_date:
            end_date = start_date

        if reg_start_str:
            try:
                registration_start_date = datetime.datetime.strptime(reg_start_str, '%Y-%m-%d')
            except ValueError:
                flash('Format tanggal mulai pendaftaran tidak valid.', 'error')
                return render_template('calendar_form.html')

        if reg_end_str:
            try:
                registration_end_date = datetime.datetime.strptime(reg_end_str, '%Y-%m-%d')
            except ValueError:
                flash('Format tanggal selesai pendaftaran tidak valid.', 'error')
                return render_template('calendar_form.html')
        elif registration_start_date:
            registration_end_date = registration_start_date

        if participant_str:
            try:
                participant_count = int(participant_str)
            except ValueError:
                flash('Jumlah peserta harus berupa angka.', 'error')
                return render_template('calendar_form.html')

        event = News(
            title=title,
            content=content,
            category='kalender',
            author_id=current_user.id,
            status='pending',
            registration_start_date=registration_start_date,
            registration_end_date=registration_end_date,
            start_date=start_date,
            end_date=end_date,
            participant_count=participant_count,
            location=location,
        )
        db.session.add(event)
        db.session.flush()

        try:
            ok, err = _save_news_media(event)
            if not ok:
                db.session.rollback()
                flash(err, 'error')
                return render_template('calendar_form.html')

            db.session.commit()
            flash('Kalender acara dikirim. Menunggu review admin kalender.', 'success')
            return redirect(url_for('staff_dashboard') if current_user.role == 'staff' else url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Terjadi kesalahan: {e}', 'error')
            return render_template('calendar_form.html')

    return render_template('calendar_form.html')


@app.route('/register', methods=['GET'])
def register():
    return render_template('register.html')


@app.route('/register', methods=['POST'])
@login_required
@admin_required
def register_post():
    flash('Pendaftaran staff dilakukan oleh admin melalui dashboard.', 'warning')
    return redirect(url_for('dashboard'))


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@app.route('/complete-profile', methods=['GET', 'POST'])
@login_required
def complete_profile():
    if request.method == 'POST':
        current_user.nip = request.form.get('nip', '').strip() or None
        current_user.must_change_password = False  # assume complete after profile
        db.session.commit()
        flash('Profil lengkap. Anda bisa gunakan dashboard sekarang.', 'success')
        return _redirect_home_by_role(current_user)
    
    if current_user.nip:  # already complete
        return _redirect_home_by_role(current_user)
    
    return render_template('complete_profile.html')


@app.route('/admin/news/add', methods=['GET', 'POST'])
@admin_required
def add_news():
    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        content = (request.form.get('content') or '').strip()
        category = (request.form.get('category') or 'event').strip()

        if not title:
            flash('Judul berita wajib diisi.', 'error')
            return render_template('add_news.html', item=None, mode='add')

        # Parse optional event details
        start_date = None
        end_date = None
        participant_count = None
        location = None

        start_date_str = request.form.get('start_date', '').strip()
        end_date_str = request.form.get('end_date', '').strip()
        participant_str = request.form.get('participant_count', '').strip()
        location = request.form.get('location', '').strip() or None

        if start_date_str:
            try:
                start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
                if end_date_str:
                    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
                else:
                    end_date = start_date
            except ValueError:
                pass

        if participant_str:
            try:
                participant_count = int(participant_str)
            except ValueError:
                pass

        news = News(
            title=title,
            content=content,
            category=category,
            author_id=current_user.id,
            status='published',
            reviewed_by_id=current_user.id,
            reviewed_at=datetime.datetime.utcnow(),
            start_date=start_date,
            end_date=end_date,
            participant_count=participant_count,
            location=location,
        )
        db.session.add(news)
        db.session.flush()  # get news.id before saving children

        photo_files = request.files.getlist('photos')
        video_files = request.files.getlist('videos')

        saved_photo_urls = []
        saved_video_urls = []

        try:
            for f in photo_files:
                if not f or f.filename == '':
                    continue
                name, msg = save_media_file(f, app.config['UPLOAD_FOLDER_PHOTOS'], 'image')
                if not name:
                    db.session.rollback()
                    flash(f'Gagal mengunggah foto ({f.filename}): {msg}', 'error')
                    return render_template('add_news.html', item=None, mode='add')
                url = f"/static/uploads/news/photos/{name}"
                saved_photo_urls.append(url)
                db.session.add(NewsPhoto(news_id=news.id, file_url=url))

            for f in video_files:
                if not f or f.filename == '':
                    continue
                name, msg = save_media_file(f, app.config['UPLOAD_FOLDER_VIDEOS'], 'video')
                if not name:
                    db.session.rollback()
                    flash(f'Gagal mengunggah video ({f.filename}): {msg}', 'error')
                    return render_template('add_news.html', item=None, mode='add')
                url = f"/static/uploads/news/videos/{name}"
                saved_video_urls.append(url)
                db.session.add(NewsVideo(news_id=news.id, file_url=url))

            if saved_photo_urls:
                news.image_url = saved_photo_urls[0]

            db.session.commit()
            flash('Berita berhasil ditambahkan.', 'success')
            return redirect(url_for('berita_detail', news_id=news.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Terjadi kesalahan: {e}', 'error')
            return render_template('add_news.html', item=None, mode='add')

    return render_template('add_news.html', item=None, mode='add')


@app.route('/admin/news/<int:news_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_news_edit(news_id):
    item = News.query.get_or_404(news_id)
    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        content = (request.form.get('content') or '').strip()
        category = (request.form.get('category') or 'event').strip()
        if not title:
            flash('Judul berita wajib diisi.', 'error')
            return render_template('add_news.html', mode='edit', item=item)

        start_date = None
        end_date = None
        participant_count = None
        location = request.form.get('location', '').strip() or None

        start_date_str = request.form.get('start_date', '').strip()
        end_date_str = request.form.get('end_date', '').strip()
        participant_str = request.form.get('participant_count', '').strip()

        if start_date_str:
            try:
                start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else start_date
            except ValueError:
                start_date = None
                end_date = None

        if participant_str:
            try:
                participant_count = int(participant_str)
            except ValueError:
                participant_count = None

        item.title = title
        item.content = content
        item.category = category
        item.start_date = start_date
        item.end_date = end_date
        item.participant_count = participant_count
        item.location = location
        item.status = 'published'
        item.reviewed_by_id = current_user.id
        item.reviewed_at = datetime.datetime.utcnow()

        try:
            ok, err = _save_news_media(item)
            if not ok:
                db.session.rollback()
                flash(err, 'error')
                return render_template('add_news.html', mode='edit', item=item)
            db.session.commit()
            flash('Berita berhasil diperbarui.', 'success')
            return redirect(url_for('berita_detail', news_id=item.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Terjadi kesalahan: {e}', 'error')
            return render_template('add_news.html', mode='edit', item=item)

    return render_template('add_news.html', mode='edit', item=item)


# ---------------------------------------------------------------------------
# Admin — Review queue (approve/reject submissions from staff)
# ---------------------------------------------------------------------------

@app.route('/admin/reviews')
@admin_required
def admin_reviews():
    pending = News.query.filter(News.status == 'pending', ~News.category.in_(['event', 'kalender'])).order_by(News.publish_date.asc()).all()
    rejected = News.query.filter(News.status == 'rejected', ~News.category.in_(['event', 'kalender'])).order_by(News.publish_date.desc()).all()
    return render_template('admin_reviews.html', pending=pending, rejected=rejected, review_type='news')


@app.route('/admin/reviews/calendar')
@admin_required
def admin_calendar_reviews():
    pending = News.query.filter(News.status == 'pending', News.category.in_(['event', 'kalender'])).order_by(News.publish_date.asc()).all()
    rejected = News.query.filter(News.status == 'rejected', News.category.in_(['event', 'kalender'])).order_by(News.publish_date.desc()).all()
    return render_template('admin_reviews.html', pending=pending, rejected=rejected, review_type='calendar')


@app.route('/admin/reviews/<int:news_id>/approve', methods=['POST'])
@admin_required
def admin_review_approve(news_id):
    item = News.query.get_or_404(news_id)
    if item.category in ('event', 'kalender'):
        flash('Gunakan halaman review kalender untuk mempublikasikan acara.', 'warning')
        return redirect(url_for('admin_calendar_reviews'))
    if item.status not in ('pending', 'rejected'):
        flash('Berita ini sudah dipublikasi.', 'warning')
        return redirect(url_for('admin_reviews'))
    item.status = 'published'
    item.reviewed_by_id = current_user.id
    item.reviewed_at = datetime.datetime.utcnow()
    item.reject_reason = None
    db.session.commit()
    flash(f'Berita "{item.title}" berhasil dipublikasi.', 'success')
    return redirect(url_for('admin_reviews'))


@app.route('/admin/reviews/<int:news_id>/reject', methods=['POST'])
@admin_required
def admin_review_reject(news_id):
    item = News.query.get_or_404(news_id)
    if item.category in ('event', 'kalender'):
        flash('Gunakan halaman review kalender untuk menolak acara.', 'warning')
        return redirect(url_for('admin_calendar_reviews'))
    if item.status == 'published':
        flash('Tidak dapat menolak berita yang sudah dipublikasi.', 'error')
        return redirect(url_for('admin_reviews'))
    reason = (request.form.get('reason') or '').strip()
    if not reason:
        flash('Alasan penolakan wajib diisi.', 'error')
        return redirect(url_for('admin_reviews'))
    item.status = 'rejected'
    item.reviewed_by_id = current_user.id
    item.reviewed_at = datetime.datetime.utcnow()
    item.reject_reason = reason
    db.session.commit()
    flash(f'Berita "{item.title}" ditolak dan dikembalikan ke staff.', 'success')
    return redirect(url_for('admin_reviews'))


@app.route('/admin/reviews/calendar/<int:news_id>/approve', methods=['POST'])
@admin_required
def admin_calendar_review_approve(news_id):
    item = News.query.get_or_404(news_id)
    if item.category not in ('event', 'kalender'):
        flash('Gunakan halaman review berita untuk mempublikasikan konten non-event.', 'warning')
        return redirect(url_for('admin_reviews'))
    if item.status not in ('pending', 'rejected'):
        flash('Acara ini sudah dipublikasi.', 'warning')
        return redirect(url_for('admin_calendar_reviews'))
    item.status = 'published'
    item.reviewed_by_id = current_user.id
    item.reviewed_at = datetime.datetime.utcnow()
    item.reject_reason = None
    db.session.commit()
    flash(f'Acara "{item.title}" berhasil dipublikasi.', 'success')
    return redirect(url_for('admin_calendar_reviews'))


@app.route('/admin/reviews/calendar/<int:news_id>/reject', methods=['POST'])
@admin_required
def admin_calendar_review_reject(news_id):
    item = News.query.get_or_404(news_id)
    if item.category not in ('event', 'kalender'):
        flash('Gunakan halaman review berita untuk menolak konten non-event.', 'warning')
        return redirect(url_for('admin_reviews'))
    if item.status == 'published':
        flash('Tidak dapat menolak acara yang sudah dipublikasi.', 'error')
        return redirect(url_for('admin_calendar_reviews'))
    reason = (request.form.get('reason') or '').strip()
    if not reason:
        flash('Alasan penolakan wajib diisi.', 'error')
        return redirect(url_for('admin_calendar_reviews'))
    item.status = 'rejected'
    item.reviewed_by_id = current_user.id
    item.reviewed_at = datetime.datetime.utcnow()
    item.reject_reason = reason
    db.session.commit()
    flash(f'Acara "{item.title}" ditolak dan dikembalikan ke staff.', 'success')
    return redirect(url_for('admin_calendar_reviews'))


# ---------------------------------------------------------------------------
# Admin — Staff account management
# ---------------------------------------------------------------------------

@app.route('/admin/staff')
@admin_required
def admin_staff_list():
    staff_users = User.query.filter_by(role='staff').order_by(User.created_at.desc()).all()
    return render_template('admin_staff_list.html', staff_users=staff_users)


@app.route('/admin/staff/new', methods=['GET', 'POST'])
@admin_required
def admin_staff_new():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        nip = (request.form.get('nip') or '').strip() or None

        if not username or not email:
            flash('Username dan email wajib diisi.', 'error')
            return render_template('admin_staff_new.html')

        email_valid, email_msg = validate_email_address(email)
        if not email_valid:
            flash(f'Email tidak valid: {email_msg}', 'error')
            return render_template('admin_staff_new.html')

        if User.query.filter_by(username=username).first():
            flash('Username sudah dipakai.', 'error')
            return render_template('admin_staff_new.html')
        if User.query.filter_by(email=email).first():
            flash('Email sudah terdaftar.', 'error')
            return render_template('admin_staff_new.html')
        if nip and User.query.filter_by(nip=nip).first():
            flash('NIP sudah terdaftar.', 'error')
            return render_template('admin_staff_new.html')

        temp_password = secrets.token_urlsafe(9)  # ~12 chars
        new_user = User(
            username=username,
            email=email,
            nip=nip,
            role='staff',
            is_active_account=True,
            must_change_password=True,
            password_hash=generate_password_hash(temp_password, method='pbkdf2:sha256', salt_length=32),
        )
        db.session.add(new_user)
        db.session.commit()
        flash(
            f'Akun staff dibuat. Password sementara untuk <b>{username}</b>: '
            f'<code>{temp_password}</code> — berikan ke staff, dia wajib ganti saat login pertama.',
            'success',
        )
        return redirect(url_for('admin_staff_list'))

    return render_template('admin_staff_new.html')


@app.route('/admin/staff/<int:user_id>/disable', methods=['POST'])
@admin_required
def admin_staff_disable(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != 'staff':
        flash('Hanya staff yang dapat dinonaktifkan melalui menu ini.', 'error')
        return redirect(url_for('admin_staff_list'))
    user.is_active_account = False
    db.session.commit()
    flash(f'Akun {user.username} telah dinonaktifkan.', 'success')
    return redirect(url_for('admin_staff_list'))


@app.route('/admin/staff/<int:user_id>/enable', methods=['POST'])
@admin_required
def admin_staff_enable(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != 'staff':
        flash('Hanya akun staff yang dikelola di sini.', 'error')
        return redirect(url_for('admin_staff_list'))
    user.is_active_account = True
    db.session.commit()
    flash(f'Akun {user.username} diaktifkan kembali.', 'success')
    return redirect(url_for('admin_staff_list'))


@app.route('/admin/staff/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def admin_staff_reset_password(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != 'staff':
        flash('Hanya akun staff yang dapat di-reset di sini.', 'error')
        return redirect(url_for('admin_staff_list'))
    temp_password = secrets.token_urlsafe(9)
    user.password_hash = generate_password_hash(temp_password, method='pbkdf2:sha256', salt_length=32)
    user.must_change_password = True
    db.session.commit()
    flash(
        f'Password <b>{user.username}</b> di-reset. Password sementara: '
        f'<code>{temp_password}</code>',
        'success',
    )
    return redirect(url_for('admin_staff_list'))


# ---------------------------------------------------------------------------
# Staff — dashboard, submit, edit
# ---------------------------------------------------------------------------

@app.route('/staff/dashboard')
@staff_required
def staff_dashboard():
    my_news = News.query.filter_by(author_id=current_user.id).order_by(News.publish_date.desc()).all()
    counts = {
        'pending': sum(1 for n in my_news if n.status == 'pending'),
        'published': sum(1 for n in my_news if n.status == 'published'),
        'rejected': sum(1 for n in my_news if n.status == 'rejected'),
    }
    return render_template('staff_dashboard.html', news=my_news, counts=counts)


def _save_news_media(news):
    """Shared helper: save uploaded photos+videos, return (ok, err_message)."""
    photo_files = request.files.getlist('photos')
    video_files = request.files.getlist('videos')
    saved_photo_urls = []

    for f in photo_files:
        if not f or f.filename == '':
            continue
        name, msg = save_media_file(f, app.config['UPLOAD_FOLDER_PHOTOS'], 'image')
        if not name:
            return False, f'Gagal mengunggah foto ({f.filename}): {msg}'
        url = f"/static/uploads/news/photos/{name}"
        saved_photo_urls.append(url)
        db.session.add(NewsPhoto(news_id=news.id, file_url=url))

    for f in video_files:
        if not f or f.filename == '':
            continue
        name, msg = save_media_file(f, app.config['UPLOAD_FOLDER_VIDEOS'], 'video')
        if not name:
            return False, f'Gagal mengunggah video ({f.filename}): {msg}'
        url = f"/static/uploads/news/videos/{name}"
        db.session.add(NewsVideo(news_id=news.id, file_url=url))

    if saved_photo_urls and not news.image_url:
        news.image_url = saved_photo_urls[0]
    return True, None


def _delete_news_media_files(news):
    for media in list(news.photos) + list(news.videos):
        if not media.file_url:
            continue
        local_path = media.file_url.lstrip('/').replace('/', os.sep)
        full_path = os.path.join(os.path.dirname(__file__), local_path)
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
        except Exception:
            pass


@app.route('/staff/news/new', methods=['GET', 'POST'])
@staff_required
def staff_news_new():
    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        content = (request.form.get('content') or '').strip()
        category = (request.form.get('category') or 'event').strip()
        if not title:
            flash('Judul berita wajib diisi.', 'error')
            return render_template('staff_news_form.html', mode='new', item=None)

        # Parse optional event details
        start_date = None
        end_date = None
        participant_count = None
        location = None

        start_date_str = request.form.get('start_date', '').strip()
        end_date_str = request.form.get('end_date', '').strip()
        participant_str = request.form.get('participant_count', '').strip()
        location = request.form.get('location', '').strip() or None

        if start_date_str:
            try:
                start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
                if end_date_str:
                    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
                else:
                    end_date = start_date
            except ValueError:
                pass

        if participant_str:
            try:
                participant_count = int(participant_str)
            except ValueError:
                pass

        news = News(
            title=title,
            content=content,
            category=category,
            author_id=current_user.id,
            status='pending',
            start_date=start_date,
            end_date=end_date,
            participant_count=participant_count,
            location=location,
        )
        db.session.add(news)
        db.session.flush()
        try:
            ok, err = _save_news_media(news)
            if not ok:
                db.session.rollback()
                flash(err, 'error')
                return render_template('staff_news_form.html', mode='new', item=None)
            db.session.commit()
            flash('Berita dikirim. Menunggu review admin.', 'success')
            return redirect(url_for('staff_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Terjadi kesalahan: {e}', 'error')
            return render_template('staff_news_form.html', mode='new', item=None)

    return render_template('staff_news_form.html', mode='new', item=None)


@app.route('/admin/news/<int:news_id>/delete', methods=['POST'])
@admin_required
def admin_news_delete(news_id):
    item = News.query.get_or_404(news_id)
    try:
        _delete_news_media_files(item)
        db.session.delete(item)
        db.session.commit()
        flash('Berita berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus berita: {e}', 'error')
    return redirect(url_for('dashboard'))


@app.route('/staff/news/<int:news_id>/delete', methods=['POST'])
@staff_required
def staff_news_delete(news_id):
    item = News.query.get_or_404(news_id)
    if item.author_id != current_user.id:
        abort(403)
    try:
        _delete_news_media_files(item)
        db.session.delete(item)
        db.session.commit()
        flash('Berita berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus berita: {e}', 'error')
    return redirect(url_for('staff_dashboard'))


@app.route('/staff/news/<int:news_id>/edit', methods=['GET', 'POST'])
@staff_required
def staff_news_edit(news_id):
    item = News.query.get_or_404(news_id)
    if item.author_id != current_user.id:
        abort(403)
    if item.status == 'published':
        flash('Berita yang sudah dipublikasi tidak dapat diedit. Hubungi admin.', 'error')
        return redirect(url_for('staff_dashboard'))

    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        content = (request.form.get('content') or '').strip()
        if not title:
            flash('Judul berita wajib diisi.', 'error')
            return render_template('staff_news_form.html', mode='edit', item=item)

        # Parse optional event details
        start_date_str = request.form.get('start_date', '').strip()
        end_date_str = request.form.get('end_date', '').strip()
        participant_str = request.form.get('participant_count', '').strip()
        location = request.form.get('location', '').strip() or None

        if start_date_str:
            try:
                item.start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
                if end_date_str:
                    item.end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
                else:
                    item.end_date = item.start_date
            except ValueError:
                item.start_date = None
                item.end_date = None
        else:
            item.start_date = None
            item.end_date = None

        if participant_str:
            try:
                item.participant_count = int(participant_str)
            except ValueError:
                item.participant_count = None
        else:
            item.participant_count = None

        item.location = location
        item.title = title
        item.content = content
        item.status = 'pending'
        item.reject_reason = None
        try:
            ok, err = _save_news_media(item)
            if not ok:
                db.session.rollback()
                flash(err, 'error')
                return render_template('staff_news_form.html', mode='edit', item=item)
            db.session.commit()
            flash('Berita dikirim ulang. Menunggu review admin.', 'success')
            return redirect(url_for('staff_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Terjadi kesalahan: {e}', 'error')
            return render_template('staff_news_form.html', mode='edit', item=item)

    return render_template('staff_news_form.html', mode='edit', item=item)


@app.errorhandler(413)
def too_large(_e):
    flash('Ukuran unggahan melebihi batas total (300MB).', 'error')
    return redirect(request.referrer or url_for('index'))


def init_db():
    """Safe DB init - create if not exists and migrate optional columns."""
    with app.app_context():
        from sqlalchemy import inspect
        insp = inspect(db.engine)
        if not insp.has_table('user'):
            db.create_all()
            flash('Database created. Run init_db.sql manually if needed.', 'info')
        else:
            print('DB tables exist')
            if insp.has_table('news'):
                existing_columns = {col['name'] for col in insp.get_columns('news')}
                extra_columns = []
                if 'registration_start_date' not in existing_columns:
                    extra_columns.append('registration_start_date DATETIME')
                if 'registration_end_date' not in existing_columns:
                    extra_columns.append('registration_end_date DATETIME')
                for col_def in extra_columns:
                    db.session.execute(text(f'ALTER TABLE news ADD COLUMN {col_def}'))
                if extra_columns:
                    db.session.commit()
                    print(f'Migrated news table, added columns: {extra_columns}')


@app.route('/health')
def health():
    try:
        with app.app_context():
            db.session.execute('SELECT 1')
        return {'status': 'healthy', 'user_count': User.query.count()}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500


if __name__ == '__main__':
    init_db()
    app.run(debug=os.getenv('FLASK_DEBUG', 'true').lower() == 'true', host='0.0.0.0')
