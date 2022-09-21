# Copyright (c) 2020. All rights reserved.

import glob
import json
import os
from typing import Dict, Sequence

RECIPE_SERVICE_TEST_DATA_DIR = os.path.abspath(os.path.dirname(__file__))


RECIPE_DATA_DIR = os.path.abspath(os.path.join(
    RECIPE_SERVICE_TEST_DATA_DIR,
    'recipes'
))

RECIPE_FILES = glob.glob(RECIPE_DATA_DIR + '/*.json')


def recipes_data_suite(
    json_files: Sequence[str] = RECIPE_FILES
) -> Dict[str, Dict]:
    recipes_data_suite = {}

    for fname in json_files:
        nickname = os.path.splitext(os.path.basename(fname))[0]
        with open(fname, mode='r', encoding='utf-8') as f:
            recipe_json = json.load(f)
            recipes_data_suite[nickname] = recipe_json

    return recipes_data_suite
