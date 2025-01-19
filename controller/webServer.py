from datetime import datetime, timedelta

from model import Connection
from .VideoClubController import VideoClubController  # Actualiza el nombre aquí
from .UserControler import UserController
from flask import Flask, render_template, request, make_response, redirect, jsonify, url_for
import sqlite3
import requests

app = Flask(__name__, static_url_path='', static_folder='../view/static', template_folder='../view/')


con = sqlite3.connect("datos.db")
cur = con.cursor()
videoClub = VideoClubController()  # Actualiza el nombre aquí
user_controller = UserController()


@app.before_request
def get_logged_user():
	if '/css' not in request.path and '/js' not in request.path:
		token = request.cookies.get('token')
		time = request.cookies.get('time')
		if token and time:
			request.user = videoClub.get_user_cookies(token, float(time))
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
    already_reviewed = False
    reviews = []
    total_rating = 0
    if request.user:
        user_id = request.user.id
        con = sqlite3.connect("datos.db")
        cur = con.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM Alquiler WHERE user_id = ? AND movie_id = ? AND end_time > ?
        """, (user_id, imdbID, datetime.now()))
        already_rented = cur.fetchone()[0] > 0
        cur.execute("""
            SELECT COUNT(*) FROM Review WHERE user_id = ? AND movie_id = ?
        """, (user_id, imdbID))
        already_reviewed = cur.fetchone()[0] > 0
        cur.execute("""
            SELECT user_id, rating, text FROM Review WHERE movie_id = ?
        """, (imdbID,))
        reviews_data = cur.fetchall()
        for row in reviews_data:
            user_id = row[0]
            cur.execute("""
                SELECT name FROM User WHERE id = ?
            """, (user_id,))
            username = cur.fetchone()[0]
            new_review = {
                'rating': row[1],
                'text': row[2],
                'username': username
            }
            reviews.append(new_review)
            total_rating += row[1]
        con.close()

    reviews = sorted(reviews, key=lambda x: x['rating'], reverse=True)
    average_rating = total_rating / len(reviews) if reviews else 0
    average_rating = round(average_rating, 2)

    return render_template('movie_details.html', movie=movie, already_rented=already_rented, already_reviewed=already_reviewed, reviews=reviews, average_rating=average_rating)


@app.route('/login', methods=['GET', 'POST'])
def login():
	if 'user' in dir(request) and request.user and request.user.token:
		return redirect('/')
	email = request.values.get("email", "")
	password = request.values.get("password", "")
	user = videoClub.get_user(email, password)
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


@app.route('/review/<imdbID>')
def review(imdbID):
	if 'user' not in dir(request) or not request.user or not request.user.token:
		return redirect('/')
	api_key = "5640ad5b"
	url = f"http://www.omdbapi.com/?i={imdbID}&apikey={api_key}"
	response = requests.get(url)
	movie = response.json()
	return render_template('review.html', movie=movie)

@app.route('/post-review', methods=['POST'])
def post_review():
    data = request.get_json()
    user_id = data['userId']
    movie_id = data['movieId']

    # Check if the user has already written a review for this movie
    con = sqlite3.connect("datos.db")
    cur = con.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM Review WHERE user_id = ? AND movie_id = ?
    """, (user_id, movie_id))
    review_count = cur.fetchone()[0]
    con.close()

    if review_count > 0:
        return "You have already written a review for this movie", 403

    resultado = videoClub.save_review(user_id, movie_id, data['punctuation'], data['review_text'])
    if resultado == 1:
        return redirect('/catalogue')
    else:
        return "Failed to save review", 500



@app.template_filter('formatdatetime')
def format_datetime(value):
	if value is None:
		return ""

	datetime_object = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
	return datetime_object.strftime('%B %d %Y, %H:%M:%S')

@app.route('/edit-review')
def edit_review():
    reviewId = request.args.get('reviewId', type=int)
    review = videoClub.get_review_by_id(reviewId)
    movie_id = review[2]
    
    # Obtener detalles de la película desde la API de OMDB
    api_key = "5640ad5b"
    url = f"http://www.omdbapi.com/?i={movie_id}&apikey={api_key}"
    response = requests.get(url)
    movie = response.json()
    
    return render_template('edit_review.html', review=review, movie=movie)

@app.route('/delete-review')
def delete_review():
    reviewId = request.args.get('reviewId', type=int)
    user_id = request.user.id  # Assuming you have the user ID in the session
    review = videoClub.get_review_by_id(reviewId)
    if videoClub.delete_review(reviewId, user_id):
        return redirect(url_for('perfil'))  # Redirect to profile after deleting the review
    else:
        return "You do not have permission to delete this review", 403

@app.route('/update-review', methods=['POST'])
def update_review():
    data = request.get_json()
    user_id = request.user.id  # Asumiendo que tienes el ID del usuario en la sesión
    if videoClub.edit_review(data['id'], user_id, data['rating'], data['review_text']):
        return redirect(url_for('movie_details', imdbID=data['movie_id']))
    else:
        return "No tienes permiso para editar esta reseña", 403

@app.route('/perfil')
def perfil():
    if not request.user:
        return redirect('/login')

    user_id = request.user.id
    username = request.user.name

    # Obtener las reseñas del usuario
    reviews = videoClub.get_reviews_by_user(user_id)

    # Obtener detalles de las películas desde la API de OMDB
    movies = []
    api_key = "5640ad5b"
    for review in reviews:
        review_id, movie_id, rating, text = review
        url = f"http://www.omdbapi.com/?i={movie_id}&apikey={api_key}"
        response = requests.get(url)
        movie = response.json()
        movie['rating'] = rating
        movie['text'] = text
        movie['review_id'] = review_id
        movies.append(movie)

    return render_template('perfil.html', perfil_username=username, movies=movies, user_id=user_id, current_user=request.user)

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
    if not request.user:
        return redirect('/login')
    if request.method == 'POST':
        user_id = request.user.id
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            return render_template('edit_profile.html', user=request.user, error="Passwords do not match")

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

    movies = []
    api_key = "5640ad5b"
    for rental in rentals:
        movie_id, end_time = rental
        url = f"http://www.omdbapi.com/?i={movie_id}&apikey={api_key}"
        response = requests.get(url)
        movie = response.json()
        movie['end_time'] = end_time

        # Check if the user has already written a review for this movie
        cur.execute("""
            SELECT id FROM Review WHERE user_id = ? AND movie_id = ?
        """, (user_id, movie_id))
        review = cur.fetchone()
        if review:
            movie['already_reviewed'] = True
            movie['review_id'] = review[0]
        else:
            movie['already_reviewed'] = False

        movies.append(movie)
    con.close()

    return render_template('my_rentals.html', movies=movies)