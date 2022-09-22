# Copyright (c) 2020. All rights reserved.

from typing import Dict

from recipeservice.database.recipe_db import (
    AbstractRecipeDB, InMemoryRecipeDB, FileSystemRecipeDB, SQLRecipeDB
)


def create_recipes_db(recipes_db_config: Dict) -> AbstractRecipeDB:
    db_type = list(recipes_db_config.keys())[0]
    db_config = recipes_db_config[db_type]

    return {
        'memory': lambda cfg: InMemoryRecipeDB(),
        'fs': lambda cfg: FileSystemRecipeDB(cfg),
        'sql': lambda cfg: SQLRecipeDB(cfg)
    }[db_type](db_config)
