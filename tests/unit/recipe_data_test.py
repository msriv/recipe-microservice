# Copyright (c) 2020. All rights reserved.

import jsonschema  # type: ignore
import unittest

from recipeservice import RECIPE_SCHEMA
from data import recipes_data_suite
import recipeservice.datamodel as datamodel


class RecipeDataTest(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.recipe_data = recipes_data_suite()

    def test_json_schema(self) -> None:
        # Validate Recipe Schema
        jsonschema.Draft7Validator.check_schema(RECIPE_SCHEMA)

    def test_recipe_data_json(self) -> None:
        # Validate Recipe Test Data
        for key, recipe in self.recipe_data.items():
            # validate using application subschema
            jsonschema.validate(recipe, RECIPE_SCHEMA)

            # Roundrtrip Test
            recipe_obj = datamodel.RecipeEntry.from_api_dm(recipe)
            recipe_dict = recipe_obj.to_api_dm()
            self.assertEqual(recipe, recipe_dict)


if __name__ == '__main__':
    unittest.main()
