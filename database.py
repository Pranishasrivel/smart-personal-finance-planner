import sqlite3


def init_db():
    # Connect to database (creates file if it doesn't exist)
    conn = sqlite3.connect("budget_tracker.db")
    cursor = conn.cursor()
   
    # 1. Create Categories Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            monthly_limit REAL
        )
    ''')
   
    # 2. Create Expenses Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            amount REAL,
            date TEXT,
            description TEXT,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    ''')
   
    # 3. Create Users Table (Our New Secure Login Feature!)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
   
    # Seed default tracking categories if they don't exist
    categories = [('Food', 5000.0), ('Travel', 2000.0), ('Education', 10000.0), ('Entertainment', 3000.0)]
    cursor.executemany("INSERT OR IGNORE INTO categories (name, monthly_limit) VALUES (?, ?)", categories)
   
    # Seed default login account (Username: admin | Password: admin123)
    cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES ('admin', 'admin123')")
   
    # Commit changes and close connection safely inside the function
    conn.commit()
    conn.close()
    print("Database initialized successfully with security layers!")


if __name__ == "__main__":
    init_db()
