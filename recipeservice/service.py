import asyncio
import logging
from typing import AsyncIterator, Mapping, Tuple
import jsonschema

from recipeservice import RECIPE_SCHEMA
from recipeservice.database.db_engines import create_recipes_db
from recipeservice.datamodel import RecipeEntry


class RecipeService:
    def __init__(self, config: Mapping, logger: logging.Logger) -> None:
        self.recipes_db = create_recipes_db(config['recipes-db'])
        self.logger = logger
        self.loop = asyncio.get_event_loop()

    def start(self):
        self.loop.run_until_complete(self.recipes_db.start())

    def stop(self):
        self.loop.run_until_complete(self.recipes_db.stop())

    def validate_address(self, recipe: Mapping) -> None:
        try:
            jsonschema.validate(recipe, RECIPE_SCHEMA)
        except jsonschema.exceptions.ValidationError:
            raise ValueError('JSON Schema validation failed')

    async def create_recipe(self, value: Mapping) -> str:
        self.validate_address(value)
        recipe = RecipeEntry.from_api_dm(value)
        key = await self.recipes_db.create_recipe(recipe=recipe)
        return key

    async def get_recipe(self, key: str) -> Mapping:
        recipe = await self.recipes_db.read_recipe(key)
        return recipe.to_api_dm()

    async def get_all_recipes(self) -> AsyncIterator[Tuple[str, Mapping]]:
        async for key, recipe in self.recipes_db.read_all_recipes():
            yield key, recipe.to_api_dm()

    async def update_recipe(self, key: str, value: Mapping) -> None:
        self.validate_address(value)
        recipe = RecipeEntry.from_api_dm(value)
        await self.recipes_db.update_recipe(key, recipe)

    async def delete_recipe(self, key: str) -> None:
        await self.recipes_db.delete_recipe(key)

    def clear_all_recipes(self) -> None:
        self.loop.run_until_complete(self.recipes_db.clear_all_recipes())
