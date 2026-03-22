# Fixed Local Setup (SQLite + All Features)

1. **Root or Inner Venv**
```powershell
# Root (recommended)
pip install -r requirements.txt
python app.py  # PORT-aware

# OR Inner (dev)
cd student_club_management
python -m venv venv
venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python run_fixed.py  # Fixed app.py factory
```

2. **DB Init** (SQLite auto)
```powershell
python student_club_management/init_all.py
```

3. **Seed Data + Admin**
```powershell
python student_club_management/seed_db.py
python student_club_management/create_admin.py
```

**Features Verified:**
- CSRF on all forms ✓
- Chat start (no Bad Request) ✓
- Announcements API (no 500) ✓
- Events calendar loads ✓
- Dark/light toggle ✓
- Admin/leader dashboards ✓

**localhost:5000** - Full functional! 🚀
