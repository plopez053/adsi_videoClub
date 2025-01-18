import hashlib
import sqlite3
import json
import os

salt = "library"

con = sqlite3.connect("datos.db")
cur = con.cursor()

### Create tables

cur.execute("""
    CREATE TABLE IF NOT EXISTS User(
        id integer primary key AUTOINCREMENT,
        name varchar(20),
        email varchar(30),
        password varchar(32),
        admin boolean
    )
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS Session(
        session_hash varchar(32) primary key,
        user_id integer,
        last_login integer,
        FOREIGN KEY(user_id) REFERENCES User(id)
    )
""")
### Insert users

# Use an absolute path to ensure the file is found
usuarios_file = os.path.join(os.path.dirname(__file__), 'usuarios.json')
with open(usuarios_file, 'r') as f:
    usuarios = json.load(f)['usuarios']

for user in usuarios:
    dataBase_password = user['password'] + salt
    hashed = hashlib.md5(dataBase_password.encode())
    dataBase_password = hashed.hexdigest()
    cur.execute(f"""INSERT INTO User VALUES (NULL, '{user['nombres']}', '{user['email']}', '{dataBase_password}', '{user['admin']}')""")
    con.commit()

