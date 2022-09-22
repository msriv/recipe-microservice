from abc import ABCMeta, abstractmethod
import json
import os
import sqlite3
import aiosqlite
from typing import AsyncIterator, Dict, Mapping, Tuple
import uuid
import aiofiles  # type: ignore

from recipeservice.datamodel import RecipeEntry


# Facade to handle all types of storage implementations
class AbstractRecipeDB(metaclass=ABCMeta):
    def start(self):
        pass

    def stop(self):
        pass

    @abstractmethod
    async def create_recipe(
        self,
        recipe: RecipeEntry,
        key: str = None
    ) -> str:
        raise NotImplementedError()

    @abstractmethod
    async def read_recipe(
        self,
        key: str
    ) -> RecipeEntry:
        raise NotImplementedError()

    @abstractmethod
    async def read_all_recipes(
        self
    ) -> AsyncIterator[Tuple[str, RecipeEntry]]:
        raise NotImplementedError()

    @abstractmethod
    async def update_recipe(
        self,
        key: str,
        recipe: RecipeEntry
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def delete_recipe(
        self,
        key: str
    ) -> None:
        raise NotImplementedError()


class InMemoryRecipeDB(AbstractRecipeDB):
    def __init__(self):
        self.db: Dict[str, RecipeEntry] = {}

    async def create_recipe(self, recipe: RecipeEntry, key: str = None) -> str:
        if key is None:
            key = uuid.uuid4().hex

        if key in self.db:
            raise KeyError('{} already exists'.format(key))

        self.db[key] = recipe
        return key

    async def read_recipe(self, key: str) -> RecipeEntry:
        return self.db[key]

    async def read_all_recipes(self) -> AsyncIterator[Tuple[str, RecipeEntry]]:
        for key, recipe in self.db.items():
            yield key, recipe

    async def update_recipe(self, key: str, recipe: RecipeEntry) -> None:
        if key is None or key not in self.db:
            raise KeyError('{} does not exist'.format(key))

        self.db[key] = recipe

    async def delete_recipe(self, key: str) -> None:
        if key is None or key not in self.db:
            raise KeyError('{} does not exist'.format(key))

        del self.db[key]


class FileSystemRecipeDB(AbstractRecipeDB):
    def __init__(self, cfg: Dict):
        store_dir = os.path.abspath(cfg.get('store_dir_path'))
        print(store_dir)
        if not os.path.exists(store_dir):
            os.makedirs(store_dir)
        if not (os.path.isdir(store_dir) and os.access(store_dir, os.W_OK)):
            raise ValueError(
                'String store "{}" is not a writable directory'.format(
                    store_dir
                )
            )
        self._store = store_dir

    @property
    def store(self) -> str:
        return self._store

    def _file_name(self, key: str) -> str:
        return os.path.join(
            self.store,
            key + '.json'
        )

    def _file_exists(self, key: str) -> bool:
        return os.path.exists(self._file_name(key))

    async def _file_read(self, key: str) -> Dict:
        try:
            async with aiofiles.open(
                self._file_name(key),
                encoding='utf-8',
                mode='r'
            ) as f:
                contents = await f.read()
                return json.loads(contents)
        except FileNotFoundError:
            raise KeyError(key)

    async def _file_write(self, key: str, recipe: Mapping) -> None:
        print(key, recipe)
        async with aiofiles.open(
            self._file_name(key),
            mode='w',
            encoding='utf-8'
        ) as f:
            await f.write(json.dumps(recipe))
            await f.flush()

    async def _file_delete(self, key: str) -> None:
        os.remove(self._file_name(key))

    async def _file_read_all(self) -> AsyncIterator[Tuple[str, Dict]]:
        all_files = os.listdir(self.store)
        extn_end = '.json'
        extn_len = len(extn_end)
        for f in all_files:
            if f.endswith(extn_end):
                key = f[:-extn_len]
                addr = await self._file_read(key)
                yield key, addr

    async def create_recipe(self, recipe: RecipeEntry, key: str = None) -> str:
        if key is None:
            key = uuid.uuid4().hex

        if self._file_exists(key):
            raise KeyError('{} already exists'.format(key))

        await self._file_write(key, recipe=recipe.to_api_dm())
        return key

    async def read_recipe(self, key: str) -> RecipeEntry:
        recipe = await self._file_read(key)
        return RecipeEntry.from_api_dm(recipe)

    async def read_all_recipes(self) -> AsyncIterator[Tuple[str, RecipeEntry]]:
        async for key, recipe in self._file_read_all():
            yield key, RecipeEntry.from_api_dm(recipe)

    async def update_recipe(self, key: str, recipe: RecipeEntry) -> None:
        if self._file_exists(key):
            await self._file_write(key, recipe.to_api_dm())
        else:
            raise KeyError(key)

    async def delete_recipe(self, key: str) -> None:
        if self._file_exists(key):
            await self._file_delete(key)
        else:
            raise KeyError(key)


class SQLRecipeDB(AbstractRecipeDB):
    def __init__(self, cfg: Dict) -> None:
        self.cfg = cfg
        self.conn = sqlite3.connect(self.cfg.get('sql_db_path'))
        self.cursor = self.conn.cursor()
        recipe_entry_table = self.cursor.execute(
            """
                SELECT name FROM sqlite_master
                WHERE type=\'table\' AND name=(?);
            """, ("recipe_entries",)).fetchall()
        if recipe_entry_table == []:
            self.cursor.execute(
                """
                    CREATE TABLE recipe_entries(
                        id VARCHAR(255),
                        name VARCHAR(255),
                        datePublished VARCHAR(255),
                        description VARCHAR(500),
                        rating DECIMAL(1,2),
                        prepTime VARCHAR(5),
                        cookTime VARCHAR(5),
                        ingredients VARCHAR(1000),
                        instructions VARCHAR(1000),
                        calories INTEGER,
                        servingSize VARCHAR(10)
                    );
                """
            )
            self.conn.commit()

    def _row_exists(self, key: str) -> bool:
        rows = self.cursor.execute(
            """
                SELECT * FROM recipe_entries WHERE id = (?)
            """, (key,)
        ).fetchall()

        if rows == []:
            return False
        else:
            return True

    async def create_recipe(self, recipe: RecipeEntry, key: str = None) -> str:
        if key is None:
            key = uuid.uuid4().hex

        if self._row_exists(key):
            raise KeyError('{} already exists'.format(key))

        self.cursor.execute(
            """
                INSERT INTO recipe_entries (
                    id,
                    name,
                    datePublished,
                    description,
                    rating,
                    prepTime,
                    cookTime,
                    ingredients,
                    instructions,
                    calories,
                    servingSize
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                key,
                recipe.to_api_dm().get('name'),
                recipe.to_api_dm().get('datePublished'),
                recipe.to_api_dm().get('description'),
                recipe.to_api_dm().get('rating'),
                recipe.to_api_dm().get('prepTime'),
                recipe.to_api_dm().get('cookTime'),
                ", ".join(recipe.to_api_dm().get('ingredients')),
                ", ".join(recipe.to_api_dm().get('instructions')),
                recipe.to_api_dm().get('nutrition').get('calories'),
                recipe.to_api_dm().get('nutrition').get('servingSize') # noqa
            )
        )
        self.conn.commit()
        return key

    async def delete_recipe(self, key: str) -> None:
        if self._row_exists(key):
            self.cursor.execute(
                """
                    DELETE FROM recipe_entries WHERE id = (?)
                """, (key, )
            )
            self.conn.commit()
        else:
            raise KeyError(key)

    async def update_recipe(self, key: str, recipe: RecipeEntry) -> None:
        if self._row_exists(key):
            self.cursor.execute(
                """
                    UPDATE recipe_entries SET
                        name=(?),
                        datePublished=(?),
                        description=(?),
                        rating=(?),
                        prepTime=(?),
                        cookTime=(?),
                        ingredients=(?),
                        instructions=(?),
                        calories=(?),
                        servingSize=(?)
                    WHERE
                        id=(?)
                """, (
                    recipe.to_api_dm().get('name'),
                    recipe.to_api_dm().get('datePublished'),
                    recipe.to_api_dm().get('description'),
                    recipe.to_api_dm().get('rating'),
                    recipe.to_api_dm().get('prepTime'),
                    recipe.to_api_dm().get('cookTime'),
                    ', '.join(recipe.to_api_dm().get('ingredients')), # noqa
                    ', '.join(recipe.to_api_dm().get('instructions')), # noqa
                    recipe.to_api_dm().get('nutrition').get('calories'), # noqa
                    recipe.to_api_dm().get('nutrition').get('servingSize'), # noqa
                    key
                )
            )
            self.conn.commit()
        else:
            raise KeyError(key)

    async def read_recipe(self, key: str) -> RecipeEntry:
        if self._row_exists(key):
            async with aiosqlite.connect(self.cfg.get('sql_db_path')) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM recipe_entries WHERE id=(?)", (key, )) as cursor: # noqa
                    async for row in cursor:
                        return RecipeEntry(
                            name=row['name'],
                            datePublished=row['datePublished'],
                            description=row['description'],
                            rating=row['rating'],
                            prepTime=row['prepTime'],
                            cookTime=row['cookTime'],
                            ingredients=row['ingredients'].split(", "), # noqa
                            instructions=row['instructions'].split(", "), # noqa
                            nutrition={
                                'calories': row['calories'],
                                'servingSize': row['servingSize']
                            }
                        )
        else:
            raise KeyError(key)

    async def read_all_recipes(self) -> AsyncIterator[Tuple[str, Dict]]:
        async with aiosqlite.connect(self.cfg.get('sql_db_path')) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM recipe_entries") as cursor:
                async for row in cursor:
                    yield row['id'], RecipeEntry(
                        name=row['name'],
                        datePublished=row['datePublished'],
                        description=row['description'],
                        rating=row['rating'],
                        prepTime=row['prepTime'],
                        cookTime=row['cookTime'],
                        ingredients=row['ingredients'].split(", "), # noqa
                        instructions=row['instructions'].split(", "), # noqa
                        nutrition={
                            'calories': row['calories'],
                            'servingSize': row['servingSize']
                        }
                    )
