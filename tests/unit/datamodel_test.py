# Copyright (c) 2020. All rights reserved.

import unittest

from recipeservice.datamodel import (
    RecipeEntry
)


class DataModelTest(unittest.TestCase):
    def test_data_model(self) -> None:
        recipe_entry = RecipeEntry(
            name="any recipe",
            datePublished="2022-05-01",
            description="any description",
            rating=4,
            prepTime="02:01",
            cookTime="01:02",
            ingredients=['Ingredient 1', 'Ingredient 2'],
            instructions=['Instruction 1', 'Instruction 2'],
            nutrition={
                'calories': 200,
                'servingSize': "2 cups"
            }
        )
        self.assertEqual(recipe_entry.name, "any recipe")
        self.assertEqual(recipe_entry.datePublished, "2022-05-01")
        self.assertEqual(recipe_entry.description, "any description")
        self.assertEqual(recipe_entry.rating, 4)
        self.assertEqual(recipe_entry.prepTime, "02:01")
        self.assertEqual(recipe_entry.cookTime, "01:02")
        self.assertEqual(recipe_entry.ingredients, ['Ingredient 1', 'Ingredient 2']) # noqa
        self.assertEqual(recipe_entry.instructions, ['Instruction 1', 'Instruction 2']) # noqa
        self.assertEqual(recipe_entry.nutrition, {
            'calories': 200,
            'servingSize': "2 cups"
        })

        recipe_dict_1 = recipe_entry.to_api_dm()
        recipe_dict_2 = recipe_entry.from_api_dm(recipe_dict_1).to_api_dm()
        self.assertEqual(recipe_dict_1, recipe_dict_2)

        # Setters
        recipe_entry.name = "new recipe"
        recipe_entry.datePublished = "2022-06-02"
        recipe_entry.description = "new description"
        recipe_entry.rating = 5
        recipe_entry.prepTime = "03:01"
        recipe_entry.cookTime = "02:02"
        recipe_entry.ingredients = ['Ingredient 4', 'Ingredient 5'] # noqa
        recipe_entry.instructions = ['Instruction 4', 'Instruction 5'] # noqa
        recipe_entry.nutrition = {
            'calories': 200,
            'servingSize': "2 cups"
        }

        # Exceptions
        with self.assertRaises(ValueError):
            RecipeEntry(name=None, instructions=None, ingredients=None)  # type: ignore # noqa

        a = RecipeEntry(name='name', instructions=['instructions1'], ingredients=['ingredients1']) # noqa

        with self.assertRaises(ValueError):
            a.name = None  # type: ignore

        with self.assertRaises(ValueError):
            a.datePublished = None  # type: ignore


if __name__ == '__main__':
    unittest.main()
