import atexit
from io import StringIO
import json
import yaml
import tornado
from tornado.ioloop import IOLoop
import tornado.testing
from recipeservice.tornado.app import make_recipeservice_app

IN_MEMORY_CFG_TXT = '''
service:
  name: Recipe Test
'''

with StringIO(IN_MEMORY_CFG_TXT) as f:
    TEST_CONFIG = yaml.load(f.read(), Loader=yaml.SafeLoader)

class RecipeServiceTornadoAppTestSetup(
    tornado.testing.AsyncHTTPTestCase
):
  def setUp(self) -> None:
      super().setUp()
      self.headers = {'Content-Type': 'application/json; charset=UTF-8'}

  def get_app(self) -> tornado.web.Application:
      recipe_service, app = make_recipeservice_app(
          config=TEST_CONFIG,
          debug=True
      )
      recipe_service.start()
      atexit.register(lambda: recipe_service.stop())
      return app
  def get_new_ioloop(self):
      return IOLoop.current()

class RecipeServiceTornadoAppUnitTests(
    RecipeServiceTornadoAppTestSetup
):
  def test_default_handler(self):
      r = self.fetch(
          '/does-not-exist',
          method='GET',
          headers=None,
      )
      info = json.loads(r.body.decode('utf-8'))
      self.assertEqual(r.code, 404, info)
      self.assertEqual(info['code'], 404)
      self.assertEqual(info['message'], 'Unknown Endpoint')

if __name__ == '__main__':
    tornado.testing.main()