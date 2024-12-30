import sqlite3

def create_tables():
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # Создание таблиц
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user'
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        createdDate TEXT DEFAULT CURRENT_TIMESTAMP,
        owner_id INTEGER NOT NULL,
        FOREIGN KEY (owner_id) REFERENCES users(id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'in_progress',
        dueDate TEXT NOT NULL,
        assignedTo INTEGER NOT NULL,
        project_id INTEGER NOT NULL,
        FOREIGN KEY (assignedTo) REFERENCES users(id),
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        author_id INTEGER NOT NULL,
        chat_id INTEGER NOT NULL,
        FOREIGN KEY (author_id) REFERENCES users(id),
        FOREIGN KEY (chat_id) REFERENCES chats(id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        size INTEGER NOT NULL,
        uploadedBy_id INTEGER NOT NULL,
        FOREIGN KEY (uploadedBy_id) REFERENCES users(id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    conn.commit()
    conn.close()

# Вызов функции для создания таблиц
create_tables()
