# Copyright (c) 2020. All rights reserved.

import asynctest  # type: ignore
from io import StringIO
import logging
import logging.config
import unittest
import yaml

from recipeservice import LOGGER_NAME
from recipeservice.datamodel import RecipeEntry
from recipeservice.service import RecipeService
from data import recipes_data_suite

IN_MEMORY_CFG_TXT = '''
service:
  name: Recipe Test

recipe-db:
  memory: null

logging:
  version: 1
  root:
    level: ERROR
'''

with StringIO(IN_MEMORY_CFG_TXT) as f:
    TEST_CONFIG = yaml.load(f.read(), Loader=yaml.SafeLoader)


class RecipeServiceWithInMemoryDBTest(asynctest.TestCase):
    async def setUp(self) -> None:
        logging.config.dictConfig(TEST_CONFIG['logging'])
        logger = logging.getLogger(LOGGER_NAME)

        self.service = RecipeService(
            config=TEST_CONFIG,
            logger=logger
        )
        self.service.start()

        self.recipe_data = recipes_data_suite()
        for key, val in self.recipe_data.items():
            recipe = RecipeEntry.from_api_dm(val)
            await self.service.recipes_db.create_recipe(recipe, key)

    async def tearDown(self) -> None:
        self.service.stop()

    @asynctest.fail_on(active_handles=True)
    async def test_get_recipe(self) -> None:
        for key, recipe in self.recipe_data.items():
            value = await self.service.get_recipe(key)
            self.assertEqual(recipe, value)

    @asynctest.fail_on(active_handles=True)
    async def test_get_all_recipes(self) -> None:
        all_recipes = {}
        async for key, recipe in self.service.get_all_recipes():
            all_recipes[key] = recipe
        self.assertEqual(len(all_recipes), 2)

    @asynctest.fail_on(active_handles=True)
    async def test_crud_recipes(self) -> None:
        keys = list(self.recipe_data.keys())
        self.assertGreaterEqual(len(keys), 2)

        recipe0 = self.recipe_data[keys[0]]
        key = await self.service.create_recipe(recipe0)
        val = await self.service.get_recipe(key)
        self.assertEqual(recipe0, val)

        recipe1 = self.recipe_data[keys[1]]
        await self.service.update_recipe(key, recipe1)
        val = await self.service.get_recipe(key)
        self.assertEqual(recipe1, val)

        await self.service.delete_recipe(key)

        with self.assertRaises(KeyError):
            await self.service.get_recipe(key)


if __name__ == '__main__':
    unittest.main()
