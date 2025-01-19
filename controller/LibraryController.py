from model import Connection, User
from model.tools import hash_password

db = Connection()

class LibraryController:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(LibraryController, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def search_books(self, title="", author="", limit=6, page=0):
        count = db.select("""
                SELECT count() 
                FROM Book b, Author a 
                WHERE b.author=a.id 
                    AND b.title LIKE ? 
                    AND a.name LIKE ? 
        """, (f"%{title}%", f"%{author}%"))[0][0]
        res = db.select("""
                SELECT b.* 
                FROM Book b, Author a 
                WHERE b.author=a.id 
                    AND b.title LIKE ? 
                    AND a.name LIKE ? 
                LIMIT ? OFFSET ?
        """, (f"%{title}%", f"%{author}%", limit, limit*page))
        books = [
            Book(b[0],b[1],b[2],b[3],b[4])
            for b in res
        ]
        return books, count

    def search_book_by_id(self, book_id):
        res = db.select("""
                SELECT b.* 
                FROM Book b
                WHERE b.id = ?
        """, (book_id,))
        if len(res) > 0:
            book = Book(res[0][0], res[0][1], res[0][2], res[0][3], res[0][4])
            return book
        else:
            return None

    def add_book(self, title, author_id, published_date, isbn):
        try:
            db.insert("""
                INSERT INTO Book (title, author_id, published_date, isbn)
                VALUES (?, ?, ?, ?)
            """, (title, author_id, published_date, isbn,))
        except Exception as e:
            print(f"Error adding book: {e}")

    def delete_book(self, book_id):
        try:
            db.delete("""
                DELETE FROM Book
                WHERE id = ?
            """, (book_id,))
        except Exception as e:
            print(f"Error deleting book: {e}")

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

    def listar_temas(self):
        temas = db.select("SELECT titulo,tema_id FROM Tema")
        return temas, len(temas)

    def crear_tema(self, titulo, pm, iduser):
        ultimotemaid = db.select("SELECT tema_id FROM Tema WHERE tema_id=(SELECT max(tema_id) FROM Tema)")
        uti = ultimotemaid[0][0]
        idtema = uti + 1
        exito = db.insert("INSERT INTO Tema VALUES (?,?,?)",(idtema,titulo, iduser))
        if exito:
            ultimomensajeid = db.select("SELECT mensaje_id FROM TemaMensaje WHERE mensaje_id=(SELECT max(mensaje_id) FROM TemaMensaje)")
            umi = ultimomensajeid[0][0]
            exito = db.insert("INSERT INTO TemaMensaje VALUES (?,?,?,?, NULL)",(umi+1,pm, iduser, idtema))
            if exito:
                return 1
            else:
                return 0
        else:
            return 0

    def listar_mensajes(self, idtema):
        mensajes = db.select("SELECT TM1.mensaje_id, TM1.texto, TM1.autor_id, TM1.idtema, TM1.mensaje_resp, TM2.texto AS texto_respuesta, U2.name AS nombre_respondido, U1.name AS nombre_autor FROM TemaMensaje TM1 LEFT JOIN User U1 ON TM1.autor_id = U1.id LEFT JOIN TemaMensaje TM2 ON TM1.mensaje_resp = TM2.mensaje_id LEFT JOIN User U2 ON TM2.autor_id = U2.id WHERE TM1.idtema = ?;", idtema)
        foreros = []
        for mensaje in mensajes:
            idmnsj = mensaje[2]
            nuevoforero = db.select("SELECT name FROM User WHERE id=?", (idmnsj,))
            foreros.append(nuevoforero[0][0])
        return mensajes, foreros

    def anadir_mensaje(self, idtema, iduser, texto):
        ultimomensajeid = db.select("SELECT mensaje_id FROM TemaMensaje WHERE mensaje_id=(SELECT max(mensaje_id) FROM TemaMensaje)")
        umi = ultimomensajeid[0][0]
        resultado = db.insert("INSERT INTO TemaMensaje VALUES (?,?,?,?, NULL)",(umi+1,texto,iduser,idtema))
        if resultado:
            return 1
        else:
            return 0

    def responder_mensaje(self, idtema, iduser, texto, idcita):
        ultimomensajeid = db.select("SELECT mensaje_id FROM TemaMensaje WHERE mensaje_id=(SELECT max(mensaje_id) FROM TemaMensaje)")
        umi = ultimomensajeid[0][0]
        resultado = db.insert("INSERT INTO TemaMensaje VALUES (?,?,?,?,?)",(umi+1,texto,iduser,idtema,idcita))
        if resultado:
            return 1
        else:
            return 0

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