import aiotask_context as context  # type: ignore
import atexit
from io import StringIO
import json
import logging
import logging.config
import yaml
import tornado
from tornado.ioloop import IOLoop
import tornado.testing
from recipeservice.tornado.app import make_recipeservice_app
from data import recipes_data_suite
from recipeservice import LOGGER_NAME

IN_MEMORY_CFG_TXT = '''
service:
  name: Recipe Test

recipes-db:
  memory: null

logging:
  version: 1
  root:
    level: ERROR
'''

with StringIO(IN_MEMORY_CFG_TXT) as f:
    TEST_CONFIG = yaml.load(f.read(), Loader=yaml.SafeLoader)


class RecipeServiceTornadoAppTestSetup(
    tornado.testing.AsyncHTTPTestCase
):
    def setUp(self) -> None:
        super().setUp()
        self.headers = {'Content-Type': 'application/json; charset=UTF-8'}
        recipes_data = recipes_data_suite()
        keys = list(recipes_data.keys())
        self.assertGreaterEqual(len(keys), 2)
        self.recipe0 = recipes_data[keys[0]]
        self.recipe1 = recipes_data[keys[1]]

    def get_app(self) -> tornado.web.Application:
        logging.config.dictConfig(TEST_CONFIG['logging'])
        logger = logging.getLogger(LOGGER_NAME)

        recipe_service, app = make_recipeservice_app(
            config=TEST_CONFIG,
            debug=True,
            logger=logger
        )
        recipe_service.start()

        atexit.register(lambda: recipe_service.stop())
        return app

    def get_new_ioloop(self):
        instance = IOLoop.current()
        instance.asyncio_loop.set_task_factory(context.task_factory)
        return instance


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
