import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import sqlite3
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1000 * 1000
app.secret_key = "your_secret_key"
bcrypt = Bcrypt(app)

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row  # This allows us to work with named columns
    return conn

def get_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return user

# Routes

@app.route('/')
def home():
    if 'user_id' in session:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        projects_ids = conn.execute('SELECT * FROM projects_users WHERE user_id = ?', (user['id'],)).fetchall()
        projects = []
        for project_id in projects_ids:
            project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id['project_id'],)).fetchone()
            print(project_id['id'])
            projects.append(project)
        conn.close()
        print(projects)
        return render_template('dashboard.html', user=user, projects=projects)
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        role = request.form['role']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)', 
                     (name, email, password, role))
        except:
            return redirect(url_for('register'))
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/create_project', methods=['GET', 'POST'])
def create_project():
    if 'user_id' not in session:
        flash('Please login to create a project.', 'warning')
        return redirect(url_for('login'))
    
    user = get_user(session['user_id'])
    if user['role'] == 'user':
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        owner_id = session['user_id']
        members = request.form.getlist('members')
        print(members)

        conn = get_db_connection()
        conn.execute('INSERT INTO projects (name, description, owner_id) VALUES (?, ?, ?)',
                     (name, description, owner_id))
        conn.commit()
        conn.close()

        conn = get_db_connection()
        project_id = conn.execute('SELECT id FROM projects WHERE name = ?', (name, )).fetchone()['id']
        for member in members:
            conn.execute('INSERT INTO projects_users (project_id, user_id) VALUES (?, ?)',
                        (project_id, member))
            conn.execute('INSERT INTO chats (project_id) VALUES (?)', (project_id, ))
        conn.commit()
        conn.close()

        flash('Project created successfully!', 'success')
        return redirect(url_for('home'))

    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    print(users)
    return render_template('create_project.html', users=users)

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    if 'user_id' not in session:
        flash('Please login to create a project.', 'warning')
        return redirect(url_for('login'))
    conn = get_db_connection()
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    users_ids = conn.execute('SELECT user_id FROM projects_users WHERE project_id = ?', (project_id,)).fetchall()
    users = []
    for user_id in users_ids:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id['user_id'],)).fetchone()
        users.append(user)
    owner = conn.execute('SELECT * FROM users WHERE id = ?', (project_id,)).fetchone()
    tasks = conn.execute('SELECT * FROM tasks WHERE project_id = ?', (project_id,)).fetchall()
    files = conn.execute('SELECT * FROM files WHERE project_id = ?', (project_id,)).fetchall()
    conn.close()

    if session['user_id'] not in [user["id"] for user in users]:
        return redirect(url_for('home'))
    
    return render_template('project_detail.html', files=files, project=project, members=users, owner=owner, tasks=tasks)

@app.route('/create_task/<int:project_id>', methods=['GET', 'POST'])
def create_task(project_id):
    if 'user_id' not in session:
        flash('Please login to create a task.', 'warning')
        return redirect(url_for('login'))
    
    user = get_user(session['user_id'])
    if user['role'] == 'user':
        return redirect(url_for('home'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        dueDate = request.form['dueDate']
        assignedTo = request.form['assigned']
        status = request.form['status']

        conn = get_db_connection()
        conn.execute('INSERT INTO tasks (title, description, status, dueDate, assignedTo, project_id) VALUES (?, ?, ?, ?, ?, ?)',
                     (title, description, status, dueDate, assignedTo, project_id))
        conn.commit()
        conn.close()

        flash('Task created successfully!', 'success')
        return redirect(url_for('project_detail', project_id=project_id))

    conn = get_db_connection()
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    users_ids = conn.execute('SELECT user_id FROM projects_users WHERE project_id = ?', (project_id,)).fetchall()
    users = []
    for user_id in users_ids:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id['user_id'],)).fetchone()
        users.append(user)
    conn.close()
    
    return render_template('create_task.html', project=project, users=users)

@app.route('/task/<int:task_id>', methods=['GET', 'POST'])
def task_detail(task_id):
    if 'user_id' not in session:
        flash('Please login to create a project.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (task['project_id'],)).fetchone()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (task['assignedTo'],)).fetchone()
    users_ids = conn.execute('SELECT user_id FROM projects_users WHERE project_id = ?', (project['id'],)).fetchall()
    users = []
    for user_id in users_ids:
        u = conn.execute('SELECT * FROM users WHERE id = ?', (user_id['user_id'],)).fetchone()
        users.append(u)
    conn.close()

    if session['user_id'] not in [u["id"] for u in users]:
        return redirect(url_for('home'))

    if request.method == 'POST':
        status = request.form['status']
        print(status)
        if session['user_id'] != task['assignedTo']:
            return redirect('/task/' + str(task_id))
        
        conn = get_db_connection()
        conn.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id,))
        conn.commit()
        conn.close()
        return redirect('/project/' + str(task['project_id']))

    return render_template('task_detail.html', task=task, project=project, user=user)

@app.route('/chat/<int:project_id>', methods=['GET', 'POST'])
def project_chat(project_id):
    if 'user_id' not in session:
        flash('Please login.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    chat = conn.execute('SELECT * FROM chats WHERE project_id = ?', (project_id,)).fetchone()
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    messages = conn.execute('SELECT * FROM messages WHERE chat_id = ?', (chat['id'],)).fetchall()
    users_ids = conn.execute('SELECT user_id FROM projects_users WHERE project_id = ?', (project_id,)).fetchall()
    users = []
    for user_id in users_ids:
        u = conn.execute('SELECT * FROM users WHERE id = ?', (user_id['user_id'],)).fetchone()
        users.append(u)
    conn.close()

    names = {u['id']: u['name'] for u in users}

    if session['user_id'] not in [u["id"] for u in users]:
        return redirect(url_for('home'))

    if request.method == 'POST':
        content = request.form['content']
        conn = get_db_connection()
        conn.execute('INSERT INTO messages (content, timestamp, author_id, chat_id) VALUES (?, ?, ?, ?)',
                     (content, datetime.now(), session['user_id'], chat['id']))
        conn.commit()
        conn.close()
        return redirect('/chat/' + str(project_id)) 

    return render_template('chat.html', chat=chat, messages=messages, project=project, user=session['user_id'], names=names)

@app.route('/project/<int:project_id>/upload_file', methods=['POST'])
def upload_file(project_id):
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('project_detail', project_id=project_id))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('project_detail', project_id=project_id))
    
    if file:
        # Сохраняем файл в папке 'uploads'
        filename = 'files/' + file.filename
        print(filename)
        file.save(filename)

        # Добавляем файл в базу данных
        conn = get_db_connection()
        conn.execute('INSERT INTO files (name, size, uploadedBy_id, project_id) VALUES (?, ?, ?, ?)',
                     (file.filename, os.stat(filename).st_size, session['user_id'], project_id))
        conn.commit()
        conn.close()

        flash('File uploaded successfully!', 'success')
        return redirect(url_for('project_detail', project_id=project_id))

@app.route('/download_file/<int:file_id>')
def download_file(file_id):
    conn = get_db_connection()
    name = conn.execute('SELECT name FROM files WHERE id = ?', (file_id,)).fetchone()['name']
    conn.close()
    # Предполагаем, что файлы хранятся в папке 'uploads' на сервере
    return send_from_directory('files/', name, as_attachment=True)


@app.route('/project/<int:project_id>/statistics')
def project_statistics(project_id):
    conn = get_db_connection()
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    tasks = conn.execute('SELECT * FROM tasks WHERE project_id = ?', (project_id,)).fetchall()
    conn.close()
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task['status'] == 'Completed')
    incomplete_tasks = total_tasks - completed_tasks

    return render_template(
        'project_statistics.html',
        project=project,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        incomplete_tasks=incomplete_tasks
    )

# Initialize database and tables

if __name__ == '__main__':
    app.run(debug=True)
