from flask import Flask, render_template, request, redirect, session, url_for
from db import get_connection as get_db_connection  # Make sure db.py has get_db_connection()
import os

app = Flask(__name__)
app.secret_key = "secretkey"
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# -------------------- HOME PAGE --------------------
@app.route('/')
def home():
    return render_template("index.html")

# -------------------- USER LOGIN --------------------
@app.route('/login_user', methods=['POST'])
def login_user():
    email = request.form['email']
    password = request.form['password']
    captcha = request.form['captcha']

    if captcha != "1234":  # Simple captcha, can improve later
        return "Captcha incorrect"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s AND role='user'", (email, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        return redirect('/user_dashboard')
    else:
        return "Invalid user credentials"

# -------------------- ADMIN LOGIN --------------------
@app.route('/login_admin', methods=['POST'])
def login_admin():
    email = request.form['email']
    password = request.form['password']
    captcha = request.form['captcha']

    if captcha != "1234":
        return "Captcha incorrect"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s AND role='admin'", (email, password))
    admin = cursor.fetchone()
    conn.close()

    if admin:
        session['admin_id'] = admin['id']
        session['admin_name'] = admin['username']
        return redirect('/admin_dashboard')
    else:
        return "Invalid admin credentials"

# -------------------- LOGOUT --------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# -------------------- REGISTER --------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        address = request.form['address']
        role = 'user'

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, email, password, phone, address, role) VALUES (%s,%s,%s,%s,%s,%s)",
                       (username, email, password, phone, address, role))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('register.html')

# -------------------- USER DASHBOARD --------------------
@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Show only approved pets
    cursor.execute("SELECT * FROM pets WHERE status='Accepted' OR type='Adoption'")
    pets = cursor.fetchall()
    conn.close()
    return render_template('user_dashboard.html', pets=pets, user={'username': session['username']})

# -------------------- ADD PET --------------------
@app.route('/add_pet', methods=['GET', 'POST'])
def add_pet():
    if 'user_id' not in session:
        return redirect('/')
    if request.method == 'POST':
        name = request.form['name']
        breed = request.form['breed']
        age = request.form['age']
        gender = request.form['gender']
        type_pet = request.form['type']
        description = request.form['description']
        photo_file = request.files.get('photo')
        photo_filename = None
        if photo_file and photo_file.filename != '':
            photo_filename = photo_file.filename
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
            photo_file.save(photo_path)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pets (user_id, name, breed, age, gender, type, description, photo, status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (session['user_id'], name, breed, age, gender, type_pet, description, photo_filename, 'Pending')
        )
        conn.commit()
        conn.close()
        return redirect('/user_dashboard')
    return render_template('add_pet.html')

# -------------------- ADMIN DASHBOARD --------------------
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT pets.*, users.username FROM pets JOIN users ON pets.user_id = users.id")
    pets = cursor.fetchall()
    conn.close()
    return render_template('admin_dashboard.html', pets=pets)

# -------------------- UPDATE PET STATUS --------------------
@app.route('/update_pet/<int:pet_id>/<status>')
def update_pet(pet_id, status):
    if 'admin_id' not in session:
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE pets SET status=%s WHERE id=%s", (status, pet_id))
    conn.commit()
    conn.close()
    return redirect('/admin_dashboard')

# -------------------- REQUEST ADOPTION --------------------
@app.route('/request_adoption/<int:pet_id>')
def request_adoption(pet_id):
    if 'user_id' not in session:
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor()
    # Mark adoption request
    cursor.execute("UPDATE pets SET type='Adoption Request' WHERE id=%s", (pet_id,))
    conn.commit()
    conn.close()
    return redirect('/user_dashboard')

# -------------------- APPROVE ADOPTION --------------------
@app.route('/approve_adoption/<int:pet_id>')
def approve_adoption(pet_id):
    if 'admin_id' not in session:
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor()
    # Once approved, hide from user dashboard
    cursor.execute("UPDATE pets SET status='Adoption Accepted' WHERE id=%s", (pet_id,))
    conn.commit()
    conn.close()
    return redirect('/admin_dashboard')

# -------------------- RUN APP --------------------
if __name__ == '__main__':
    app.run(debug=True)
