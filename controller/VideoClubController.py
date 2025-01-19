from model import Connection, User
from model.tools import hash_password

db = Connection()

class VideoClubController:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(VideoClubController, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance


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

    def delete_usuario(self, id, nombre, email, contraseña, esadmin):
        try:
            db.delete("""
                DELETE FROM User
                WHERE id = ? AND name = ? AND email = ? AND password = ? AND admin = ?
            """, (id, nombre, email, contraseña, esadmin,))
        except Exception as e:
            print(f"Error borrando usuario: {e}")



    def save_review(self, userID, movieID, rating, review_text):
        exito = db.insert("INSERT INTO Review (user_id, movie_id, rating, text) VALUES ( ?, ?, ?, ?)", (userID, movieID, rating, review_text))
        return 1 if exito else 0

    def get_review_by_id(self, review_id):
        query = "SELECT * FROM Review WHERE id = ?"
        review = db.select(query, (review_id,))
        return review[0] if len(review) > 0 else None

    def edit_review(self, review_id, user_id, rating, review_text):
        try:
            review = self.get_review_by_id(review_id)
            if review and review[1] == user_id:  # Verifica que el usuario es el autor de la reseña
                db.update("""
                    UPDATE Review
                    SET rating = ?, text = ?
                    WHERE id = ?
                """, (rating, review_text, review_id,))
                return True
            return False
        except Exception as e:
            print(f"Error editando review: {e}")
            return False

    def delete_review(self, review_id, user_id):
        try:
            review = self.get_review_by_id(review_id)
            if review and review[1] == user_id:  # Verifica que el usuario es el autor de la reseña
                db.delete("""
                    DELETE FROM Review
                    WHERE id = ?
                """, (review_id,))
                return True
            return False
        except Exception as e:
            print(f"Error borrando review: {e}")
            return False

    def get_reviews_by_user(self, user_id):
        query = """
            SELECT id, movie_id, rating, text
            FROM Review
            WHERE user_id = ?
        """
        reviews = db.select(query, (user_id,))
        return reviews

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