from tests.base_test_class import BaseTestClass
from bs4 import BeautifulSoup

class TestAdmin(BaseTestClass):

    def test_acceso_admin(self):
        res_login = self.client.post('/login', data={
            'email': 'admin@admin.admin',
            'password': 'admin'
        }, follow_redirects=True)
        self.assertEqual(200, res_login.status_code)
        self.assertIn('token', ''.join(res_login.headers.values()))
        res = self.client.get('/admin')
        self.assertEqual(200, res.status_code)
        page = BeautifulSoup(res.data, features="html.parser")
        admin_boton = page.find('div', class_='btn-group-vertical')
        self.assertIsNotNone(admin_boton)
        self.assertEqual(1, len(admin_boton.find_all('button')))  # Ajustado a 1 botón

    def test_crear_usuario(self):
        res_login = self.client.post('/login', data={
            'email': 'admin@admin.admin',
            'password': 'admin'
        }, follow_redirects=True)
        self.assertEqual(200, res_login.status_code)
        self.assertIn('token', ''.join(res_login.headers.values()))
        res_crear = self.client.post('/gestor_usuarios', data={
            'nombre': 'testman',
            'email': 'testman@test.test',
            'contraseña': '1234',
            'esadmin': 0
        }, follow_redirects=True)
        self.assertEqual(200, res_crear.status_code)
        con = self.app.config['DATABASE']
        cur = con.cursor()
        cur.execute("SELECT * FROM User WHERE name='testman' AND email='testman@test.test' AND admin='0'")
        res_existe = cur.fetchall()
        self.assertNotEqual([], res_existe)

    def test_eliminar_usuario(self):
        # Crear un usuario para eliminar
        res_crear = self.client.post('/gestor_usuarios', data={
            'nombre': 'testman',
            'email': 'testman@test.test',
            'contraseña': '1234',
            'esadmin': 0
        }, follow_redirects=True)
        self.assertEqual(200, res_crear.status_code, f"Error al crear el usuario: {res_crear.data}")
        
        # Obtener el ID del usuario creado
        con = self.app.config['DATABASE']
        cur = con.cursor()
        cur.execute("SELECT id FROM User WHERE name='testman' AND email='testman@test.test'")
        user = cur.fetchone()
        print(f"Usuario creado: {user}")  # Mensaje de depuración
        self.assertIsNotNone(user, "El usuario no se creó correctamente")
        user_id = user['id']
        
        # Eliminar el usuario
        res_eliminar = self.client.post('/eliminar_usuario', data={
            'id': user_id
        }, follow_redirects=True)
        self.assertEqual(200, res_eliminar.status_code, f"Error al eliminar el usuario: {res_eliminar.data}")
        
        # Verificar que el usuario ha sido eliminado
        cur.execute("SELECT * FROM User WHERE id=?", (user_id,))
        res_existe = cur.fetchall()
        self.assertEqual([], res_existe)

    def test_eliminar_usuario(self):
        # Crear un usuario para eliminar
        res_crear = self.client.post('/gestor_usuarios', data={
            'nombre': 'testman',
            'email': 'testman@test.test',
            'contraseña': '1234',
            'esadmin': 0
        }, follow_redirects=True)
        self.assertEqual(200, res_crear.status_code, f"Error al crear el usuario: {res_crear.data}")
        
        # Obtener el ID del usuario creado
        con = self.app.config['DATABASE']
        cur = con.cursor()
        cur.execute("SELECT id FROM User WHERE name='testman' AND email='testman@test.test'")
        user = cur.fetchone()
        print(f"Usuario creado: {user}")  # Mensaje de depuración
        self.assertIsNotNone(user, "El usuario no se creó correctamente")
        user_id = user['id']
        
        # Eliminar el usuario
        res_eliminar = self.client.post('/eliminar_usuario', data={
            'id': user_id
        }, follow_redirects=True)
        self.assertEqual(200, res_eliminar.status_code, f"Error al eliminar el usuario: {res_eliminar.data}")
        
        # Verificar que el usuario ha sido eliminado
        cur.execute("SELECT * FROM User WHERE id=?", (user_id,))
        res_existe = cur.fetchall()
        self.assertEqual([], res_existe)

        
