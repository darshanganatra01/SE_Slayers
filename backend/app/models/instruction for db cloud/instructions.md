Just two commands every time you change a model:

# 1. Generate a migration (detects what changed)
.\venv\Scripts\python.exe -m flask db migrate -m "describe what you changed"

# 2. Apply it to Neon
.\venv\Scripts\python.exe -m flask db upgrade


Example workflow:
Say you add a phone column to the User model:

Edit the model (app/models/user.py) — add phone = db.Column(db.String)
Run: flask db migrate -m "add phone to users" (1st Command) → generates a migration file in migrations/versions/

Run: flask db upgrade (2nd command) → applies it to Neon

Key points:
**Commit the migrations/ folder to Git — this is how teammates stay in sync**

When a teammate pulls new migration files, they just run flask db upgrade to update their shared Neon DB

If someone else already ran the upgrade on Neon, running it again is safe — it skips already-applied migrations