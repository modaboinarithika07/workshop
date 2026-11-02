import sqlite3

conn = sqlite3.connect("load_manager.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS loads (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Wattage INTEGER NOT NULL,
    Priority INTEGER NOT NULL,
    Status TEXT NOT NULL DEFAULT 'off',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
INSERT INTO loads (Name, Wattage, Priority, Status)
VALUES (?, ?, ?, ?)
""", ("Fridge", 300, 1, "off"))


conn.commit()
conn.close()

print("database is created successfully")