from datetime import datetime, timedelta

from model import Connection
from .LibraryController import LibraryController
from .UserControler import UserController  # Asegúrate de importar UserController
from flask import Flask, render_template, request, make_response, redirect, jsonify, url_for
import sqlite3
import requests

app = Flask(__name__, static_url_path='', static_folder='../view/static', template_folder='../view/')


con = sqlite3.connect("datos.db")
cur = con.cursor()
library = LibraryController()
user_controller = UserController()


@app.before_request
def get_logged_user():
	if '/css' not in request.path and '/js' not in request.path:
		token = request.cookies.get('token')
		time = request.cookies.get('time')
		if token and time:
			request.user = library.get_user_cookies(token, float(time))
			if request.user:
				request.user.token = token
		else:
			request.user = None



@app.after_request
def add_cookies(response):
	if 'user' in dir(request) and request.user and request.user.token:
		session = request.user.validate_session(request.user.token)
		response.set_cookie('token', session.hash)
		response.set_cookie('time', str(session.time))
	return response


@app.route('/')
def index():
	return render_template('index.html')


@app.route('/admin')
def admin():
    if not request.user or not request.user.admin:
        return redirect('/login')

    users = user_controller.get_all_users()
    return render_template('admin.html', users=users)

@app.route('/gestor_libros',methods=['GET', 'POST'])
def gestor_libros():
	titulo = request.values.get("titulo", "")
	autor = request.values.get("autor", "")
	portada = request.values.get("portada", "")
	descripcion = request.values.get("descripcion", "")
	if titulo != "" and autor != "" and portada != "" and descripcion != "":
		library.add_book(titulo, autor, portada, descripcion)
	return render_template('gestor_libros.html')

@app.route('/gestor_usuarios')
def gestor_usuarios():
    if not request.user or not request.user.admin:
        return redirect('/login')

    users = user_controller.get_all_users()
    return render_template('gestor_usuarios.html', usuarios=users)

@app.route('/catalogue')
def catalogue():
    title = request.values.get("title", "")
    page = int(request.values.get("page", 1))
    movies = []
    total_pages = 1

    if title:
        api_key = "5640ad5b"
        url = f"http://www.omdbapi.com/?s={title}&apikey={api_key}&page={page}"
        response = requests.get(url)
        data = response.json()

        if data['Response'] == 'True':
            movies = data['Search']
            total_results = int(data['totalResults'])
            total_pages = (total_results // 10) + 1

    return render_template('catalogue.html', movies=movies, title=title, current_page=page, total_pages=total_pages, max=max, min=min)

@app.route('/movie/<imdbID>')
def movie_details(imdbID):
    api_key = "5640ad5b"
    url = f"http://www.omdbapi.com/?i={imdbID}&apikey={api_key}"
    response = requests.get(url)
    movie = response.json()

    already_rented = False
    if request.user:
        user_id = request.user.id
        con = sqlite3.connect("datos.db")
        cur = con.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM Alquiler WHERE user_id = ? AND movie_id = ? AND end_time > ?
        """, (user_id, imdbID, datetime.now()))
        already_rented = cur.fetchone()[0] > 0
        con.close()

    return render_template('movie_details.html', movie=movie, already_rented=already_rented)

@app.route('/reserva_exitosa')
def reserva_exitosa():
    return render_template('reserva_exitosa.html')

@app.route('/devolver_exitoso')
def devolver_exitoso():
    return render_template('devolver_exitoso.html')


@app.route('/reserve-book', methods=['POST'])
def reserve_book():
    insertar = Connection()
    user_id = request.form.get('user_id')
    book_id = request.form.get('book_id')

    fecha_inicio = datetime.now()
    fecha_fin = fecha_inicio + timedelta(days=60)
    fecha_ini_str = fecha_inicio.strftime('%Y-%m-%d')
    fecha_fin_str = fecha_fin.strftime('%Y-%m-%d')

    # Preparar los parámetros para la consulta SQL como una tupla
    p = (user_id, book_id, fecha_ini_str, fecha_fin_str)

    # Pasar la sentencia SQL con marcadores de estilo de SQLite y la tupla de parámetros al método insert
    if insertar.insert("INSERT INTO reserva (user_id, book_id, fecha_inicio, fecha_fin) VALUES (?, ?, ?, ?)", p):
        # Reserva exitosa, redirigir o mostrar un mensaje
        return redirect('reserva_exitosa')
    else:
        # Error en la reserva, manejar adecuadamente
        return "Error en la reserva", 400

@app.route('/devolve-book', methods=['POST'])
def devolve_book():
    insertar = Connection()
    user_id = request.form.get('user_id')
    book_id = request.form.get('book_id')

    fecha_inicio = datetime.now()
    fecha_fin = fecha_inicio + timedelta(days=60)
    fecha_ini_str = fecha_inicio.strftime('%Y-%m-%d')
    fecha_fin_str = fecha_fin.strftime('%Y-%m-%d')

    # Preparar los parámetros para la consulta SQL como una tupla
    p = (user_id, book_id, fecha_ini_str, fecha_fin_str)

    # Pasar la sentencia SQL con marcadores de estilo de SQLite y la tupla de parámetros al método insert
    if insertar.delete("DELETE FROM reserva WHERE user_id = ? AND book_id = ?", (user_id, book_id)):
        # Reserva exitosa, redirigir o mostrar un mensaje
        return redirect('devolver_exitoso')
    else:
        # Error en la reserva, manejar adecuadamente
        return "Usted no tiene este libro reservado", 400

@app.route('/login', methods=['GET', 'POST'])
def login():
	if 'user' in dir(request) and request.user and request.user.token:
		return redirect('/')
	email = request.values.get("email", "")
	password = request.values.get("password", "")
	user = library.get_user(email, password)
	if user:
		session = user.new_session()
		resp = redirect("/")
		resp.set_cookie('token', session.hash)
		resp.set_cookie('time', str(session.time))
	else:
		if request.method == 'POST':
			return redirect('/login')
		else:
			resp = render_template('login.html')
	return resp


@app.route('/logout')
def logout():
    resp = redirect('/')
    resp.delete_cookie('token')
    resp.delete_cookie('time')
    if 'user' in dir(request) and request.user and request.user.token:
        request.user.delete_session(request.user.token)
        request.user = None
    return resp

@app.route('/eliminar_usuario', methods=['GET', 'POST'])
def eliminar_usuario():
	library.delete_usuario(request.values.get("id", ""), request.values.get("nombre", ""), request.values.get("email", ""), request.values.get("contraseña",""), request.values.get("esadmin",""))
	return redirect('/gestor_usuarios')

@app.route('/forum')
def forum():
	path = request.values.get("path", "/")
	temas, numtemas = library.listar_temas()
	#debug print(temas[0][0])
	return render_template("forum.html", temas=temas, numtemas=numtemas)

@app.route('/creartema')
def creartema():
	path = request.values.get("path", "/")
	return render_template("creartema.html")

@app.route('/creandotema', methods=['POST'])
def creandotema():
	if request.method == 'POST':
		path = request.values.get("path", "/")
		titulo = request.form["nuevotitulo"]
		pm = request.form["primermansaje"]
		userid = request.form["userid"]
		resultado = library.crear_tema(titulo, pm, userid)
		if resultado:
			return render_template("creandotema.html")
		else:
			return render_template("errorcreandotema.html")
	else:
		return render_template("index.html")

@app.route('/entrartema', methods=['POST'])
def entrartema():
	path = request.values.get("path", "/")
	nomtema = request.form["nomtema"]
	idtema = request.form["idtema"]
	mensajes, foreros = library.listar_mensajes(idtema)
	nummensajes = len(mensajes)
	return render_template("entema.html", mensajes=mensajes, nummensajes=nummensajes, foreros=foreros, nomtema=nomtema, idtema=idtema)

@app.route('/nuevomensajeforo' , methods=['POST'])
def nuevomensajeforo():
	path = request.values.get("path", "/")
	idtema = request.form["idtema"]
	nomtema = request.form["nomtema"]
	return render_template("nuevomensajeforo.html", idtema=idtema, nomtema=nomtema)

@app.route('/mandandomensajeforo', methods=['POST'])
def mandandomensajeforo():
	path = request.values.get("path", "/")
	idtema = request.form["idtema"]
	iduser = request.form["iduser"]
	texto = request.form["nuevomensaje"]
	nomtema = request.form["nomtema"]
	resultado = library.anadir_mensaje(idtema,iduser,texto)
	if resultado:
		return render_template("mandandomensajeforo.html", idtema=idtema, nomtema=nomtema)
	else:
		return render_template("errormensajeforo.html")

@app.route('/respondermensajeforo' , methods=['POST'])
def respondermensajeforo():
	path = request.values.get("path", "/")
	idtema = request.form["idtema"]
	nomuser = request.form["nomuser"]
	cita = request.form["cita"]
	idcita = request.form["idcita"]
	nomtema = request.form["nomtema"]
	return render_template("respondermensajeforo.html", idtema=idtema, nomuser=nomuser, cita=cita, idcita=idcita, nomtema=nomtema)

@app.route('/respondiendomensajeforo' , methods=['POST'])
def respondiendomensajeforo():
	path = request.values.get("path", "/")
	idtema = request.form["idtema"]
	texto = request.form["nuevomensaje"]
	iduser = request.form["iduser"]
	idcita = request.form["idcita"] #id del mensaje al que se responde
	nomtema = request.form["nomtema"]
	resultado = library.responder_mensaje(idtema, iduser, texto, idcita)
	if resultado:
		return render_template("respondiendomensajeforo.html", idtema = idtema, nomtema = nomtema)
	else:
		return render_template("errormensajeforo.html")



@app.route('/review')
def review():
	if 'user' not in dir(request) or not request.user or not request.user.token:
		return redirect('/')
	bookId = request.args.get('bookId', type=int)
	book = library.search_book_by_id(bookId)
	return render_template('review.html', book=book)

@app.route('/post-review', methods=['POST'])
def post_review():
	data = request.get_json()
	resultado = library.save_review(data['book_id'], data['user_email'], data['rating'], data['review_text'])
	if resultado == 1:
		return redirect('/catalogue')
	

@app.route('/read-reviews')
def read_reviews():
	bookId = request.args.get('bookId', type=int)
	book = library.search_book_by_id(bookId)
	reviews = library.get_reviews_by_book_id(bookId)
	return render_template('read_reviews.html', reviews=reviews, book=book)


@app.template_filter('formatdatetime')
def format_datetime(value):
	if value is None:
		return ""

	datetime_object = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
	return datetime_object.strftime('%B %d %Y, %H:%M:%S')

@app.route('/edit-review')
def edit_review():
	reviewId = request.args.get('reviewId', type=int)
	review = library.get_review_by_id(reviewId)
	book = library.search_book_by_id(review[1])
	return render_template('edit_review.html', review=review, book=book)

@app.route('/delete-review')
def delete_review():
	reviewId = request.args.get('reviewId', type=int)
	review = library.get_review_by_id(reviewId)
	library.delete_review(reviewId)
	return redirect(url_for('read_reviews', bookId=review[1]))

@app.route('/update-review', methods=['POST'])
def update_review():
	data = request.get_json()
	library.edit_review(data['id'], data['rating'], data['review_text'])
	return redirect(url_for('read_reviews', bookId=data['book_id']))

@app.route('/perfil')
def perfil():
	username = request.args.get("username", "")
	if "@" in username:
		user_email = username
		username = library.get_username_by_email(username)
	else:
		user_email = library.get_email_by_username(username)
	reviews = library.get_reviews_by_user(user_email)
	return render_template('perfil.html', perfil_username=username, reviews=reviews, user_email=user_email)

@app.route('/solicitarAmistad', methods=['POST'])
def solicitarAmistad():
    email_user = request.form["iduser"]
    email_amigo = request.form["idamigo"]

    iduser = library.get_id_by_email(email_user)
    idamigo = library.get_id_by_email(email_amigo)	
    if not library.comprobarExisteAmistad(iduser, idamigo):
        library.solicitarAmistad(iduser, idamigo)

    return redirect('/perfil?username='+email_amigo)

@app.route('/aceptarAmistad', methods=['POST'])
def aceptarAmistad():
    email_user = request.form["iduser"]
    amigo_username = request.form["idamigo"]

    email_amigo = library.get_email_by_username(amigo_username)

    iduser = library.get_id_by_email(email_user)
    idamigo = library.get_id_by_email(email_amigo)	

    library.aceptarAmistad(iduser, idamigo)

    return redirect('/perfil?username='+email_user)

@app.route('/rechazarAmistad', methods=['POST'])
def rechazarAmistad():
	email_user = request.form["iduser"]
	amigo_username = request.form["idamigo"]

	email_amigo = library.get_email_by_username(amigo_username)

	iduser = library.get_id_by_email(email_user)
	idamigo = library.get_id_by_email(email_amigo)	

	library.rechazarAmistad(iduser, idamigo)

	return redirect('/perfil?username='+email_user)

@app.route('/misSolicitudes')
def misSolicitudes():
    user_email = request.args.get("user_email", "")
    id = library.get_id_by_email(user_email)
    solicitudes = library.get_solicitudes(id)
    return render_template('mis_solicitudes.html', solicitudes=solicitudes, user_email=user_email)

@app.route('/misAmigos')
def misAmigos():
	user_email = request.args.get("user_email", "")
	id = library.get_id_by_email(user_email)
	amigos = library.get_amigos(id)
	return render_template('mis_amigos.html', amigos=amigos, user_email=user_email)

@app.template_filter('formatdatetimef')
def format_datetime(value):
	if value is None:
		return ""

	datetime_object = datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
	return datetime_object.strftime('%B %d %Y, %H:%M:%S')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match")

        user_controller.add_usuario(username, email, password, 0)  # 0 indicates a regular user, not an admin

        # Log in the user automatically after registration
        user = user_controller.get_user(email, password)
        if user:
            response = make_response(redirect('/'))
            session = user.new_session()  # Cambiar create_session a new_session
            response.set_cookie('token', session.hash)
            response.set_cookie('time', str(session.time))
            return response

    return render_template('register.html')

@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if request.method == 'POST':
        user_id = request.user.id
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        user_controller.update_user(user_id, username, email, password)
        return redirect('/perfil?username=' + username)

    return render_template('edit_profile.html', user=request.user)

@app.route('/delete-user', methods=['POST'])
def delete_user():
    if not request.user or not request.user.admin:
        return redirect('/login')

    user_id = request.form['user_id']
    user_controller.delete_usuario(user_id)
    return redirect('/gestor_usuarios')

@app.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if not request.user or not request.user.admin:
        return redirect('/login')

    user = user_controller.get_user_by_id(user_id)
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        user_controller.update_user(user_id, username, email, password)
        return redirect('/gestor_usuarios')

    return render_template('edit_user.html', user=user)

@app.route('/add-user', methods=['POST'])
def add_user():
    if not request.user or not request.user.admin:
        return redirect('/login')

    nombre = request.form['nombre']
    email = request.form['email']
    contraseña = request.form['contraseña']
    esadmin = request.form['esadmin']

    user_controller.add_usuario(nombre, email, contraseña, int(esadmin))
    return redirect('/gestor_usuarios')

@app.route('/rent-movie/<imdbID>', methods=['POST'])
def rent_movie(imdbID):
    if not request.user:
        return redirect('/login')

    user_id = request.user.id
    end_time = datetime.now() + timedelta(hours=48)

    # Crear una nueva conexión a la base de datos
    con = sqlite3.connect("datos.db")
    cur = con.cursor()

    # Verificar si la película ya está alquilada por el usuario
    cur.execute("""
        SELECT COUNT(*) FROM Alquiler WHERE user_id = ? AND movie_id = ? AND end_time > ?
    """, (user_id, imdbID, datetime.now()))
    already_rented = cur.fetchone()[0]

    if already_rented > 0:
        con.close()
        return redirect('/my-rentals')  # O mostrar un mensaje de error

    cur.execute("""
        INSERT INTO Alquiler (user_id, movie_id, end_time)
        VALUES (?, ?, ?)
    """, (user_id, imdbID, end_time))
    con.commit()
    con.close()

    return redirect('/my-rentals')

@app.route('/my-rentals')
def my_rentals():
    if not request.user:
        return redirect('/login')

    user_id = request.user.id
    con = sqlite3.connect("datos.db")
    cur = con.cursor()
    cur.execute("""
        SELECT movie_id, end_time FROM Alquiler WHERE user_id = ? AND end_time > ?
    """, (user_id, datetime.now()))
    rentals = cur.fetchall()
    con.close()

    movies = []
    api_key = "5640ad5b"
    for rental in rentals:
        movie_id, end_time = rental
        url = f"http://www.omdbapi.com/?i={movie_id}&apikey={api_key}"
        response = requests.get(url)
        movie = response.json()
        movie['end_time'] = end_time
        movies.append(movie)

    return render_template('my_rentals.html', movies=movies)