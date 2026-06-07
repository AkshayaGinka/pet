import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",      # keep empty for XAMPP default
        database="pet_rescue_management"
    )
