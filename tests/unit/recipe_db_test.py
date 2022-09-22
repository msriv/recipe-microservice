# Copyright (c) 2020. All rights reserved.

from abc import ABCMeta, abstractmethod
import asynctest  # type: ignore
from io import StringIO
import os
import tempfile
from typing import Dict
import unittest
import yaml
from utils import _run_coroutine

from recipeservice.database.recipe_db import (
    AbstractRecipeDB, InMemoryRecipeDB, FileSystemRecipeDB, SQLRecipeDB
)
from recipeservice.database.db_engines import create_recipes_db
from recipeservice.datamodel import RecipeEntry

from data import recipes_data_suite


class AbstractRecipeDBTest(unittest.TestCase):
    def read_config(self, txt: str) -> Dict:
        with StringIO(txt) as f:
            cfg = yaml.load(f.read(), Loader=yaml.SafeLoader)
        return cfg

    def test_in_memory_db_config(self):
        cfg = self.read_config('''
recipe-db:
  memory: null
        ''')

        self.assertIn('memory', cfg['recipe-db'])
        db = create_recipes_db(cfg['recipe-db'])
        self.assertEqual(type(db), InMemoryRecipeDB)

    def test_file_system_db_config(self):
        cfg = self.read_config('''
recipe-db:
  fs: /tmp
        ''')

        self.assertIn('fs', cfg['recipe-db'])
        db = create_recipes_db(cfg['recipe-db'])
        self.assertEqual(type(db), FileSystemRecipeDB)
        self.assertEqual(db.store, '/tmp')

    def test_sql_db_config(self):
        cfg = self.read_config('''
recipe-db:
  sql: /tmp/recipe.db
        ''')

        self.assertIn('sql', cfg['recipe-db'])
        db = create_recipes_db(cfg['recipe-db'])
        self.assertEqual(type(db), SQLRecipeDB)
        self.assertEqual(db.store, '/tmp/recipe.db')


class AbstractRecipeDBTestCase(metaclass=ABCMeta):
    def setUp(self) -> None:
        self.recipe_data = {
            k: RecipeEntry.from_api_dm(v)
            for k, v in recipes_data_suite().items()
        }
        self.recipe_db = self.make_recipe_db()

    @abstractmethod
    def make_recipe_db(self) -> AbstractRecipeDB:
        raise NotImplementedError()

    @abstractmethod
    async def recipe_count(self) -> int:
        raise NotImplementedError()

    @asynctest.fail_on(active_handles=True)
    async def test_crud_lifecycle(self) -> None:
        # Nothing in the database
        for key in self.recipe_data:
            with self.assertRaises(KeyError):  # type: ignore
                await self.recipe_db.read_recipe(key)

        # Create then Read, again Create(fail)
        for key, recipe in self.recipe_data.items():
            await self.recipe_db.create_recipe(recipe, key)
            await self.recipe_db.read_recipe(key)
            with self.assertRaises(KeyError):  # type: ignore
                await self.recipe_db.create_recipe(recipe, key)

        self.assertEqual(await self.recipe_count(), 2)  # type: ignore

        # First data in test set
        first_key = list(self.recipe_data.keys())[0]
        first_recipe = self.recipe_data[first_key]

        # Update
        await self.recipe_db.update_recipe(first_key, first_recipe)
        with self.assertRaises(KeyError):  # type: ignore
            await self.recipe_db.update_recipe('does not exist', first_recipe)

        # Create without giving key
        new_key = await self.recipe_db.create_recipe(recipe)
        self.assertIsNotNone(new_key)  # type: ignore
        self.assertEqual(await self.recipe_count(), 3)  # type: ignore

        # Get All Recipes
        recipes = {}
        async for key, recipe in self.recipe_db.read_all_recipes():
            recipes[key] = recipe

        self.assertEqual(len(recipes), 3)  # type: ignore

        # Delete then Read, and the again Delete
        for key in self.recipe_data:
            await self.recipe_db.delete_recipe(key)
            with self.assertRaises(KeyError):  # type: ignore
                await self.recipe_db.read_recipe(key)
            with self.assertRaises(KeyError):  # type: ignore
                await self.recipe_db.delete_recipe(key)

        self.assertEqual(await self.recipe_count(), 1)  # type: ignore

        await self.recipe_db.delete_recipe(new_key)
        self.assertEqual(await self.recipe_count(), 0)  # type: ignore


class InMemoryRecipeDBTest(
    AbstractRecipeDBTestCase,
    asynctest.TestCase
):
    def make_recipe_db(self) -> AbstractRecipeDB:
        self.mem_db = InMemoryRecipeDB()
        _run_coroutine(self.mem_db.start())
        _run_coroutine(self.mem_db.clear_all_recipes())
        return self.mem_db

    async def recipe_count(self) -> int:
        return len(self.mem_db.db)


class FilesystemRecipeDBTest(
    AbstractRecipeDBTestCase,
    asynctest.TestCase
):
    def make_recipe_db(self) -> AbstractRecipeDB:
        self.tmp_dir = tempfile.TemporaryDirectory(prefix='recipe-fsdb')
        self.store_dir = self.tmp_dir.name
        self.fs_db = FileSystemRecipeDB(self.store_dir)
        _run_coroutine(self.fs_db.start())
        _run_coroutine(self.fs_db.clear_all_recipes())
        return self.fs_db

    async def recipe_count(self) -> int:
        return len([
            name for name in os.listdir(self.store_dir)
            if os.path.isfile(os.path.join(self.store_dir, name))
        ])
        # return len(self.addr_db.db)

    def tearDown(self):
        # self.tmp_dir.cleanup()
        _run_coroutine(self.fs_db.clear_all_recipes())
        super().tearDown()

    def test_db_creation(self):
        with tempfile.TemporaryDirectory(prefix='recipe-fsdb') as tempdir:
            store_dir = os.path.join(tempdir, 'abc')
            FileSystemRecipeDB(store_dir)
            tmpfilename = os.path.join(tempdir, 'xyz.txt')
            with open(tmpfilename, 'w') as f:
                f.write('this is a file and not a dir')
            with self.assertRaises(ValueError):
                FileSystemRecipeDB(tmpfilename)


class SQLRecipeDBTest(
    AbstractRecipeDBTestCase,
    asynctest.TestCase
):
    def make_recipe_db(self) -> AbstractRecipeDB:
        self.tmp_dir = tempfile.TemporaryDirectory(prefix='recipe-fsdb')
        self.store_dir = self.tmp_dir.name
        self.test_db_path = os.path.join(self.store_dir, 'test_db.db')
        self.sql_db = SQLRecipeDB(self.test_db_path)
        _run_coroutine(self.sql_db.start())
        _run_coroutine(self.sql_db.clear_all_recipes())
        return self.sql_db

    async def recipe_count(self) -> int:
        recipes = self.sql_db.read_all_recipes()
        count = 0
        async for key, recipe in recipes:
            count = count + 1
        return count

    def tearDown(self):
        _run_coroutine(self.sql_db.clear_all_recipes())
        _run_coroutine(self.recipe_db.stop())
        super().tearDown()

    def test_db_creation(self):
        self.sql_db = SQLRecipeDB('/tmp/test_db.db')
        _run_coroutine(self.sql_db.start())
        assert os.path.isfile('/tmp/test_db.db')


if __name__ == '__main__':
    unittest.main()
