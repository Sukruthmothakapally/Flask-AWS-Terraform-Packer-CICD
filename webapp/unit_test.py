# test_app4.py
import os
import unittest

os.environ['DISABLE_DATABASE'] = 'true'

from app import app

class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_healthz(self):
        response = self.app.get('/healthz')
        self.assertEqual(response.status_code, 200, msg='Expected status code 200')
        self.assertEqual(response.data, b'Ok', msg='Expected response data to be b"Ok"')

if __name__ == '__main__':
    unittest.main()
