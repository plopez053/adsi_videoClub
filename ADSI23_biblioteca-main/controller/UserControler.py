from model import Connection, User
from model.tools import hash_password

db = Connection()

class UserController:
    def get_user(self, email, password):
        user = db.select("SELECT * from User WHERE email = ? AND password = ?", (email, hash_password(password)))
        if len(user) > 0:
            return User(user[0][0], user[0][1], user[0][2], None, user[0][4])
        else:
            return None

    def get_all_users(self):
        user = db.select("SELECT * from User")
        if len(user) > 0:
            return user
        else:
            return None

    def get_user_cookies(self, token, time):
        user = db.select("SELECT u.* from User u, Session s WHERE u.id = s.user_id AND s.last_login = ? AND s.session_hash = ?", (time, token))
        if len(user) > 0:
            return User(user[0][0], user[0][1], user[0][2], None, user[0][4])
        else:
            return None

    def add_usuario(self, nombre, email, contraseña, esadmin):
        try:
            hpass = hash_password(contraseña)
            db.insert("""
                     INSERT INTO User (name, email, password, admin)
                     VALUES ( ?, ?, ?, ?)
                """, (nombre, email, hpass, esadmin,))
        except Exception as e:
            print(f"Error añadiendo usuario: {e}")

    def delete_usuario(self, user_id):
        try:
            db.delete("DELETE FROM User WHERE id = ?", (user_id,))
        except Exception as e:
            print(f"Error deleting user: {e}")

    def get_email_by_username(self, username):
        query = "SELECT email FROM User WHERE name = ?"
        email = db.select(query, (username,))
        return email[0][0] if len(email) > 0 else None

    def get_username_by_email(self, email):
        query = "SELECT name FROM User WHERE email = ?"
        username = db.select(query, (email,))
        return username[0][0] if len(username) > 0 else None

    def get_id_by_email(self, email):
        query = "SELECT id FROM User WHERE email = ?"
        id = db.select(query, (email,))
        return id[0][0] if len(id) > 0 else None

    def update_user(self, user_id, username, email, password):
        try:
            hpass = hash_password(password) if password else None
            if hpass:
                db.update("""
                    UPDATE User
                    SET name = ?, email = ?, password = ?
                    WHERE id = ?
                """, (username, email, hpass, user_id))
            else:
                db.update("""
                    UPDATE User
                    SET name = ?, email = ?
                    WHERE id = ?
                """, (username, email, user_id))
        except Exception as e:
            print(f"Error updating user: {e}")

    def get_user_by_id(self, user_id):
        user = db.select("SELECT * from User WHERE id = ?", (user_id,))
        if len(user) > 0:
            return User(user[0][0], user[0][1], user[0][2], None, user[0][4])
        else:
            return None