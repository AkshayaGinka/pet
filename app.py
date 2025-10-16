from flask import Flask, render_template, request, redirect, session, url_for
from db import get_connection
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["UPLOAD_FOLDER"] = "static/uploads"

# Home Page
@app.route("/")
def index():
    return render_template("index.html")

# User Registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]
        address = request.form["address"]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username,email,password,phone,address) VALUES (%s,%s,%s,%s,%s)",
                       (username,email,password,phone,address))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect("/login")
    return render_template("register.html")

# User Login
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email,password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            if user["role"] == "admin":
                return redirect("/admin_dashboard")
            else:
                return redirect("/user_dashboard")
        else:
            return "Invalid Credentials"
    return render_template("login.html")

# User Dashboard
@app.route("/user_dashboard")
def user_dashboard():
    if "user_id" not in session:
        return redirect("/login")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM pets WHERE status='Accepted'")
    pets = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("user_dashboard.html", pets=pets)

# Add Pet
@app.route("/add_pet", methods=["GET","POST"])
def add_pet():
    if "user_id" not in session:
        return redirect("/login")
    
    if request.method == "POST":
        name = request.form["name"]
        breed = request.form["breed"]
        age = request.form["age"]
        gender = request.form["gender"]
        description = request.form["description"]
        type_pet = request.form["type"]
        photo_file = request.files["photo"]

        filename = None
        if photo_file:
            filename = secure_filename(photo_file.filename)
            photo_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pets (user_id,name,breed,age,gender,description,photo,type)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (session["user_id"], name, breed, age, gender, description, filename, type_pet))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect("/user_dashboard")
    return render_template("add_pet.html")

# Admin Dashboard
@app.route("/admin_dashboard")
def admin_dashboard():
    if "role" not in session or session["role"] != "admin":
        return redirect("/login")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT pets.*, users.username FROM pets JOIN users ON pets.user_id = users.id")
    pets = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("admin_dashboard.html", pets=pets)

# Approve or Reject Pet
@app.route("/update_pet/<int:pet_id>/<status>")
def update_pet(pet_id, status):
    if "role" not in session or session["role"] != "admin":
        return redirect("/login")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE pets SET status=%s WHERE id=%s", (status, pet_id))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect("/admin_dashboard")

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
