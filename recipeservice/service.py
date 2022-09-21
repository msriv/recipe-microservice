import logging
from typing import Dict
import uuid


class RecipeService:
    def __init__(self, config: Dict, logger: logging.Logger) -> None:
        self.recipes: Dict[str, Dict] = {}
        self.logger = logger

    def start(self):
        self.recipes = {}

    def stop(self):
        pass

    async def create_recipe(self, value: Dict) -> str:
        recipe_id = uuid.uuid4().hex
        self.recipes[recipe_id] = value
        return recipe_id

    async def get_recipe(self, key: str) -> Dict:
        return self.recipes[key]

    async def get_all_recipes(self) -> Dict[str, Dict]:
        return self.recipes

    async def update_recipe(self, key: str, value: Dict) -> None:
        self.recipes[key]
        self.recipes[key] = value

    async def delete_recipe(self, key: str) -> None:
        self.recipes[key]
        del self.recipes[key]
