from backend.src.db.database import engine
from sqlalchemy import text

with engine.begin() as conn:
    try:
        conn.execute(text("ALTER TABLE avatars_pedagogiques ADD COLUMN face_id VARCHAR(255);"))
        print("Column face_id added successfully.")
    except Exception as e:
        print(f"Error (maybe column already exists): {e}")
