import unittest
from controller.webServer import app

class BaseTestClass(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.db = self.app.config['DATABASE']