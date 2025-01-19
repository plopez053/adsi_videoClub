from tests.base_test_class import BaseTestClass
from bs4 import BeautifulSoup

class TestLogin(BaseTestClass):

    def test_login_page_unauthenticated(self):
        res = self.client.get('/login')
        self.assertEqual(200, res.status_code)
        self.assertNotIn('token', ''.join(res.headers.values()))
        self.assertNotIn('time', ''.join(res.headers.values()))
        page = BeautifulSoup(res.data, features="html.parser")
        self.assertIsNotNone(page.find('form').find('input', type='email'))
        self.assertIsNotNone(page.find('form').find('input', type='password'))
        self.assertIsNotNone(page.find('form').find('button', type='submit'))

    def test_login_success(self):
        res = self.client.post('/login', data={
            'email': 'd@eugenio.com',
            'password': '1234'
        }, follow_redirects=False)
        self.assertEqual(302, res.status_code)
        self.assertEqual('/', res.location)
        self.assertIn('token', ''.join(res.headers.values()))
        self.assertIn('time', ''.join(res.headers.values()))
        token = [x.split("=")[1].split(";")[0] for x in res.headers.values() if 'token' in x][0]
        time = float([x.split("=")[1].split(";")[0] for x in res.headers.values() if 'time' in x][0])
        
        # Usar un cursor para ejecutar la consulta SQL
        con = self.app.config['DATABASE']
        cur = con.cursor()
        cur.execute(f"SELECT user_id FROM Session WHERE session_hash='{token}' AND last_login={time}")
        res = cur.fetchall()
        
        self.assertEqual(1, len(res))
        self.assertEqual(21, res[0][0])
        
        res2 = self.client.get('/')
        page = BeautifulSoup(res2.data, features="html.parser")
        self.assertEqual('Mis Alquileres', page.find('header').find('ul').find_all('li')[-3].get_text())

    def test_login_failure(self):
        res = self.client.post('/login', data={
            'email': 'd@eugenio.com',
            'password': '12345'
        }, follow_redirects=True)
        self.assertEqual(200, res.status_code)
        self.assertIn('Invalid credentials', res.data.decode())
        page = BeautifulSoup(res.data, features="html.parser")
        self.assertIsNotNone(page.find('form').find('input', type='email'))
        self.assertIsNotNone(page.find('form').find('input', type='password'))
        self.assertIsNotNone(page.find('form').find('button', type='submit'))