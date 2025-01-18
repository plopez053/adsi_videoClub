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

cur.execute("""
    CREATE TABLE IF NOT EXISTS Alquiler(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        movie_id TEXT,
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES User(id)
    )
""")

### Insert users

# Usar la ruta absoluta al archivo usuarios.json
usuarios_path = os.path.join(os.path.dirname(__file__), '../usuarios.json')
with open(usuarios_path, 'r') as f:
    usuarios = json.load(f)['usuarios']

for user in usuarios:
    dataBase_password = user['password'] + salt
    hashed = hashlib.md5(dataBase_password.encode())
    dataBase_password = hashed.hexdigest()
    cur.execute(f"""INSERT INTO User VALUES (NULL, '{user['nombres']}', '{user['email']}', '{dataBase_password}', '{user['admin']}')""")
    con.commit()

con.commit()
con.close()







