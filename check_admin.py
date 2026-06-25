from app import app, db, User
with app.app_context():
    admins = User.query.filter_by(role='admin').all()
    print("=== ADMIN ACCOUNTS ===")
    for i, u in enumerate(admins):
        print(f"Admin {i+1}: username='{u.username}' email='{u.email}' active={u.is_active_account}")
    if not admins:
        print("No admin found! Run: python reset_admin.py")

