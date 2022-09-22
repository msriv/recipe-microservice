from abc import ABCMeta, abstractmethod
import json
import os
import aiosqlite
from typing import AsyncIterator, Dict, Mapping, Tuple
import uuid
import aiofiles  # type: ignore

from recipeservice.datamodel import RecipeEntry


# Facade to handle all types of storage implementations
class AbstractRecipeDB(metaclass=ABCMeta):
    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def stop(self):
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

    @abstractmethod
    async def clear_all_recipes(
        self
    ) -> None:
        raise NotImplementedError()


class InMemoryRecipeDB(AbstractRecipeDB):
    def __init__(self):
        self.db: Dict[str, RecipeEntry] = {}

    async def start(self):
        await super().start()

    async def stop(self):
        await super().stop()

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

    async def clear_all_recipes(self) -> None:
        self.db = {}


class FileSystemRecipeDB(AbstractRecipeDB):
    def __init__(self, store_dir_path: str):
        if not os.path.exists(store_dir_path):
            os.makedirs(store_dir_path)
        if not (os.path.isdir(store_dir_path) and os.access(store_dir_path, os.W_OK)): # noqa
            raise ValueError(
                'String store "{}" is not a writable directory'.format(
                    store_dir_path
                )
            )
        self._store = store_dir_path

    async def start(self):
        await super().start()

    async def stop(self):
        await super().stop()

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
                recipe = await self._file_read(key)
                yield key, recipe

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

    async def clear_all_recipes(self) -> None:
        all_files = os.listdir(self.store)
        for f in all_files:
            os.remove(os.path.join(self.store, f))


class SQLRecipeDB(AbstractRecipeDB):
    def __init__(self, sql_db_path: str) -> None:
        self._store = sql_db_path

    @property
    def store(self) -> str:
        return self._store

    async def start(self):
        self.conn = await aiosqlite.connect(self._store)
        recipe_entry_table = await self.conn.execute(
            """
                SELECT name FROM sqlite_master
                WHERE type=\'table\' AND name=(?);
            """, ("recipe_entries",))

        if await recipe_entry_table.fetchall() == []:
            await self.conn.execute(
                """
                    CREATE TABLE recipe_entries(
                        id VARCHAR(255) PRIMARY KEY,
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
            await self.conn.commit()

    async def stop(self):
        await self.conn.close()

    async def _row_exists(self, key: str) -> bool:
        rows = await self.conn.execute(
            """
                SELECT * FROM recipe_entries WHERE id = (?)
            """, (key,)
        )
        if await rows.fetchall() == []:
            return False
        else:
            return True

    async def create_recipe(self, recipe: RecipeEntry, key: str = None) -> str:
        if key is None:
            key = uuid.uuid4().hex

        if await self._row_exists(key):
            raise KeyError('{} already exists'.format(key))

        await self.conn.execute(
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
                recipe.name,
                recipe.datePublished,
                recipe.description,
                recipe.rating,
                recipe.prepTime,
                recipe.cookTime,
                "||".join(recipe.ingredients),
                "||".join(recipe.instructions),
                recipe.nutrition.get('calories'),
                recipe.nutrition.get('servingSize') # noqa
            )
        )
        await self.conn.commit()
        return key

    async def delete_recipe(self, key: str) -> None:
        if await self._row_exists(key):
            await self.conn.execute(
                """
                    DELETE FROM recipe_entries WHERE id = (?)
                """, (key, )
            )
            await self.conn.commit()
        else:
            raise KeyError(key)

    async def update_recipe(self, key: str, recipe: RecipeEntry) -> None:
        if await self._row_exists(key):
            await self.conn.execute(
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
                    recipe.name,
                    recipe.datePublished,
                    recipe.description,
                    recipe.rating,
                    recipe.prepTime,
                    recipe.cookTime,
                    '||'.join(recipe.ingredients), # noqa
                    '||'.join(recipe.instructions), # noqa
                    recipe.nutrition.get('calories'), # noqa
                    recipe.nutrition.get('servingSize'), # noqa
                    key
                )
            )
            await self.conn.commit()
        else:
            raise KeyError(key)

    async def read_recipe(self, key: str) -> RecipeEntry:
        if await self._row_exists(key):
            async with aiosqlite.connect(self._store) as db:
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
                            ingredients=row['ingredients'].split("||"), # noqa
                            instructions=row['instructions'].split("||"), # noqa
                            nutrition={
                                'calories': row['calories'],
                                'servingSize': row['servingSize']
                            }
                        )
        else:
            raise KeyError(key)

    async def read_all_recipes(self) -> AsyncIterator[Tuple[str, Dict]]:
        async with aiosqlite.connect(self._store) as db:
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

    async def clear_all_recipes(self) -> None:
        await self.conn.execute(
                """
                    DELETE FROM recipe_entries
                """
            )
        await self.conn.commit()
