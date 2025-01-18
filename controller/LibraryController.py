from model import Connection,User
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
			return User(user[0][0], user[0][1], user[0][2],None, user[0][4])
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
			return User(user[0][0], user[0][1], user[0][2],None,user[0][4])
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
			print(f"Error añadiendo libros: {e}")
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
		#if len(temas) > 0:
		return temas, len(temas)
		#else:
		#	return 0

	def crear_tema(self, titulo, pm, iduser):
		ultimotemaid = db.select("SELECT tema_id FROM Tema WHERE tema_id=(SELECT max(tema_id) FROM Tema)")
		#print(ultimotemaid)
		uti = ultimotemaid[0][0]
		#print(uti)
		idtema = uti + 1
		exito = db.insert("INSERT INTO Tema VALUES (?,?,?)",(idtema,titulo, iduser))
		#db.select("SELECT tema_id FROM Tema WHERE titulo=?", (titulo))
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
		#mensajes = db.select("SELECT * FROM TemaMensaje WHERE idtema=?", (idtema))
		#mensajes = db.select("SELECT TM1.mensaje_id, TM1.texto, TM1.autor_id, TM1.idtema, TM1.mensaje_resp, TM2.texto AS texto_respuesta FROM TemaMensaje TM1 LEFT JOIN TemaMensaje TM2 ON TM1.mensaje_resp = TM2.mensaje_id WHERE TM1.idtema=?", idtema)
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
		print("nuevo mensaje respondido")
		print(idcita)
		print(idtema)
		if resultado:
			return 1
		else:
			return 0
		
	def add_usuario(self, nombre, email, contraseña, esadmin):
		try:
			hpass = hash_password(contraseña)
			db.insert("""
		             INSERT INTO User (name, email, password, admin)
		             VALUES ( ?, ?, ?, ?)
		        """, (nombre, email, hpass, esadmin,))

		except Exception as e:
			print(f"Error añadiendo libros: {e}")

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

	def get_reviews_by_book_id(self, book_id):
		query = "SELECT * FROM Reviews WHERE book_id = ? ORDER BY date_time DESC"
		reviews = db.select(query, (book_id,))
		return reviews

	def get_review_by_id(self, review_id):
		query = "SELECT * FROM Reviews WHERE id = ?"
		review = db.select(query, (review_id,))
		return review[0] if len(review) > 0 else None
	
	def edit_review(self, review_id, rating, review_text):
		try:
			db.update("""
			          UPDATE Reviews
			          SET rating = ?, review_text = ?
			          WHERE id = ?
			      """, (rating, review_text, review_id,))
		except Exception as e:
			print(f"Error editando review: {e}")

	
	def delete_review(self, review_id):
		try:
			db.delete("""
			          DELETE FROM Reviews
			          WHERE id = ?
			      """, (review_id,))
		except Exception as e:
			print(f"Error borrando review: {e}")


	def get_reviews_by_user(self, user_email):
		query = "SELECT * FROM Reviews WHERE user_email = ? ORDER BY date_time DESC"
		reviews = db.select(query, (user_email,))
		return reviews

	def get_reservas_by_user(self, user_id):
		query = "SELECT * FROM reserva WHERE user_id = ?"
		reservas = db.select(query, (user_id,))
		return reservas

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

	def solicitarAmistad(self, solicitante, solicitado):
		try:
			db.insert("""
		             INSERT INTO Amistad (user1_id, user2_id, aceptada, fecha_inicio)
		             VALUES ( ?, ?, ?, ?)
		        """, (solicitado, solicitante, False, datetime.datetime.now(),))
		except Exception as e:
			print(f"Error añadiendo amistad: {e}")

	def comprobarExisteAmistad(self, iduser, iduser2):
		query = """
			SELECT * FROM Amistad WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
		"""
		amistad = db.select(query, (iduser, iduser2, iduser2, iduser))
		return True if len(amistad) > 0 else False

	def aceptarAmistad(self, iduser, iduser2):
		try:
			db.update("""
			          UPDATE Amistad
			          SET aceptada = TRUE
					  WHERE (user1_id = ? AND user2_id = ?) 
			      """, (iduser, iduser2))
		except Exception as e:
			print(f"Error aceptando amistad: {e}")

	def rechazarAmistad(self, solicitado, solicitante):
		try:
			db.delete("""
			          DELETE FROM Amistad
					  WHERE (user1_id = ? AND user2_id = ?)
			      """, (solicitado, solicitante))
		except Exception as e:
			print(f"Error rechazando amistad: {e}")
	
	def get_solicitudes(self, iduser):
		query = """
            SELECT u.name, a.fecha_inicio FROM Amistad as a INNER JOIN User as u ON a.user2_id = u.id
            WHERE a.user1_id = ? AND a.aceptada = FALSE
        """
		solicitudes = db.select(query, (iduser,))
		return solicitudes
	
	def get_amigos(self, iduser):
		query = """
			SELECT u2.name, a.fecha_inicio FROM Amistad as a INNER JOIN User as u ON a.user1_id = u.id INNER JOIN User as u2 ON a.user2_id = u2.id
			WHERE (a.user1_id = ? OR a.user2_id = ?) AND a.aceptada = TRUE
			"""
		amigos = db.select(query, (iduser, iduser))
		return amigos

	def get_book(self, book_id):
		book = db.select("SELECT * from Book WHERE id = ?", (book_id,))
		if len(book) > 0:
			return Book(book[0][0], book[0][1], book[0][2], book[0][3], book[0][4])
		else:
			return None

	def get_all_books(self):
		books = db.select("SELECT * from Book")
		if len(books) > 0:
			return books
		else:
			return None

	def get_author(self, author_id):
		author = db.select("SELECT * from Author WHERE id = ?", (author_id,))
		if len(author) > 0:
			return Author(author[0][0], author[0][1])
		else:
			return None

	def get_all_authors(self):
		authors = db.select("SELECT * from Author")
		if len(authors) > 0:
			return authors
		else:
			return None

	def add_author(self, name):
		try:
			db.insert("""
				INSERT INTO Author (name)
				VALUES (?)
			""", (name,))
		except Exception as e:
			print(f"Error adding author: {e}")

	def delete_author(self, author_id):
		try:
			db.delete("""
				DELETE FROM Author
				WHERE id = ?
			""", (author_id,))
		except Exception as e:
			print(f"Error deleting author: {e}")

	def get_reservation(self, reservation_id):
		reservation = db.select("SELECT * from Reservation WHERE id = ?", (reservation_id,))
		if len(reservation) > 0:
			return Reservation(reservation[0][0], reservation[0][1], reservation[0][2], reservation[0][3], reservation[0][4])
		else:
			return None

	def get_all_reservations(self):
		reservations = db.select("SELECT * from Reservation")
		if len(reservations) > 0:
			return reservations
		else:
			return None

	def add_reservation(self, user_id, book_id, start_date, end_date):
		try:
			db.insert("""
				INSERT INTO Reservation (user_id, book_id, start_date, end_date)
				VALUES (?, ?, ?, ?)
			""", (user_id, book_id, start_date, end_date,))
		except Exception as e:
			print(f"Error adding reservation: {e}")

	def delete_reservation(self, reservation_id):
		try:
			db.delete("""
				DELETE FROM Reservation
				WHERE id = ?
			""", (reservation_id,))
		except Exception as e:
			print(f"Error deleting reservation: {e}")

	def get_tema(self, tema_id):
		tema = db.select("SELECT * from Tema WHERE id = ?", (tema_id,))
		if len(tema) > 0:
			return Tema(tema[0][0], tema[0][1], tema[0][2])
		else:
			return None

	def get_all_temas(self):
		temas = db.select("SELECT * from Tema")
		if len(temas) > 0:
			return temas
		else:
			return None

	def add_tema(self, name, user_id):
		try:
			db.insert("""
				INSERT INTO Tema (name, user_id)
				VALUES (?, ?)
			""", (name, user_id,))
		except Exception as e:
			print(f"Error adding tema: {e}")

	def delete_tema(self, tema_id):
		try:
			db.delete("""
				DELETE FROM Tema
				WHERE id = ?
			""", (tema_id,))
		except Exception as e:
			print(f"Error deleting tema: {e}")

	def get_tema_mensaje(self, tema_mensaje_id):
		tema_mensaje = db.select("SELECT * from TemaMensaje WHERE id = ?", (tema_mensaje_id,))
		if len(tema_mensaje) > 0:
			return TemaMensaje(tema_mensaje[0][0], tema_mensaje[0][1], tema_mensaje[0][2], tema_mensaje[0][3], tema_mensaje[0][4])
		else:
			return None

	def get_all_tema_mensajes(self):
		tema_mensajes = db.select("SELECT * from TemaMensaje")
		if len(tema_mensajes) > 0:
			return tema_mensajes
		else:
			return None

	def add_tema_mensaje(self, content, tema_id, user_id, parent_id):
		try:
			db.insert("""
				INSERT INTO TemaMensaje (content, tema_id, user_id, parent_id)
				VALUES (?, ?, ?, ?)
			""", (content, tema_id, user_id, parent_id,))
		except Exception as e:
			print(f"Error adding tema mensaje: {e}")

	def delete_tema_mensaje(self, tema_mensaje_id):
		try:
			db.delete("""
				DELETE FROM TemaMensaje
				WHERE id = ?
			""", (tema_mensaje_id,))
		except Exception as e:
			print(f"Error deleting tema mensaje: {e}")