# Copyright (c) 2020. All rights reserved.

import json
import os

RECIPE_SERVICE_ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

RECIPE_SCHEMA_FILE = os.path.abspath(os.path.join(
    RECIPE_SERVICE_ROOT_DIR,
    '../schema/recipe-v1.0.json'
))

with open(RECIPE_SCHEMA_FILE, mode='r', encoding='utf-8') as f:
    RECIPE_SCHEMA = json.load(f)

LOGGER_NAME = 'recipeservice'
