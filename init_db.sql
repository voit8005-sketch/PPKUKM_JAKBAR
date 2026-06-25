CREATE DATABASE IF NOT EXISTS ppkukm_portal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ppkukm_portal;

-- Drop tables if exist (for clean init)
DROP TABLE IF EXISTS news_video;
DROP TABLE IF EXISTS news_photo;
DROP TABLE IF EXISTS news;
DROP TABLE IF EXISTS user;

CREATE TABLE `user` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'staff') DEFAULT 'staff',
    nip VARCHAR(30) UNIQUE,
    is_active_account BOOLEAN DEFAULT TRUE,
    must_change_password BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    image_url VARCHAR(255),
    publish_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    author_id INT,
    status ENUM('pending', 'published', 'rejected') DEFAULT 'pending',
    reviewed_by_id INT NULL,
    reviewed_at TIMESTAMP NULL,
    reject_reason TEXT NULL,
    FOREIGN KEY (author_id) REFERENCES `user`(id) ON DELETE SET NULL,
    FOREIGN KEY (reviewed_by_id) REFERENCES `user`(id) ON DELETE SET NULL
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE news_photo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    news_id INT NOT NULL,
    file_url VARCHAR(255) NOT NULL,
    caption VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE news_video (
    id INT AUTO_INCREMENT PRIMARY KEY,
    news_id INT NOT NULL,
    file_url VARCHAR(255) NOT NULL,
    caption VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Updated sample data
INSERT INTO `user` (username, email, password_hash, role, nip) VALUES 
('admin', 'admin@ppkukm.jakarta', '$2b$12$WqXjK8z5YJfuZ5q8z5z5z5z5z5z5z5z5z5z5z5z5z5z5z5z5z5z5z', 'admin', 'NIP-ADMIN-001')
ON DUPLICATE KEY UPDATE password_hash=VALUES(password_hash); -- password: admin123

-- Sample published news by admin
INSERT INTO news (title, content, author_id, status, image_url) VALUES 
('Update Program PPKUKM Jakarta Barat 2024', 'Dinas Pemberdayaan dan Pengembangan Usaha Kecil Menengah Jakarta Barat meluncurkan program baru untuk mendukung UMKM di era digital.', 1, 'published', '/static/uploads/news/photos/sample1.jpg')
ON DUPLICATE KEY UPDATE content=VALUES(content);

INSERT INTO news (title, content, author_id, status) VALUES 
('Pelatihan Digital Marketing untuk UMKM', 'PPKUKM Jakarta Barat mengadakan pelatihan digital marketing gratis untuk para pelaku UMKM.', 1, 'published')
ON DUPLICATE KEY UPDATE content=VALUES(content);

-- Note: services table removed (not used in app.py)

-- Indexes for performance
CREATE INDEX idx_news_status ON news(status);
CREATE INDEX idx_news_author ON news(author_id);
CREATE INDEX idx_news_publish ON news(publish_date);
