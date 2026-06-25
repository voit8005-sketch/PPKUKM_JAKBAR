@echo off
echo Installing MySQL client via chocolatey (if needed)...
choco install mysql -y

echo.
echo Manual MySQL setup needed:
echo 1. Install MySQL Workbench or mysql client
echo 2. Run: mysql -u root -p ppkukm_portal ^< init_db.sql
echo 3. Enter your root password when prompted
echo.
echo OR use phpMyAdmin / XAMPP / WAMP MySQL GUI
echo.
pause
