import json

import tornado.testing

from recipeservice.tornado.app import (
    RECIPE_ENTRY_URI_FORMAT_STR
)

from tests.unit.tornado_app_handlers_test import (
    RecipeServiceTornadoAppTestSetup
)


class TestRecipeServiceApp(RecipeServiceTornadoAppTestSetup):
    def test_recipe_endpoints(self):
        # Get all Recipes in the recipe list, must be ZERO
        r = self.fetch(
            RECIPE_ENTRY_URI_FORMAT_STR.format(id=''),
            method='GET',
            headers=None,
        )
        print("DEBUG", r)
        all_recipes = json.loads(r.body.decode('utf-8'))
        self.assertEqual(r.code, 200, all_recipes)
        self.assertEqual(len(all_recipes), 0, all_recipes)
        # Add a Recipe
        r = self.fetch(
            RECIPE_ENTRY_URI_FORMAT_STR.format(id=''),
            method='POST',
            headers=self.headers,
            body=json.dumps(self.recipe0),
        )
        self.assertEqual(r.code, 201)
        recipe_uri = r.headers['Location']
        # POST: error cases
        r = self.fetch(
            RECIPE_ENTRY_URI_FORMAT_STR.format(id=''),
            method='POST',
            headers=self.headers,
            body='it is not json',
        )
        self.assertEqual(r.code, 400)
        self.assertEqual(r.reason, 'Invalid JSON body')
        # Get the added Recipe
        r = self.fetch(
            recipe_uri,
            method='GET',
            headers=None,
        )
        self.assertEqual(r.code, 200)
        self.assertEqual(
            self.recipe0,
            json.loads(r.body.decode('utf-8'))
        )
        # GET: error cases
        r = self.fetch(
            RECIPE_ENTRY_URI_FORMAT_STR.format(id='no-such-id'),
            method='GET',
            headers=None,
        )
        self.assertEqual(r.code, 404)
        # Update that Recipe
        r = self.fetch(
            recipe_uri,
            method='PUT',
            headers=self.headers,
            body=json.dumps(self.recipe1),
        )
        self.assertEqual(r.code, 204)
        r = self.fetch(
            recipe_uri,
            method='GET',
            headers=None,
        )
        self.assertEqual(r.code, 200)
        self.assertEqual(
            self.recipe1,
            json.loads(r.body.decode('utf-8'))
        )
        # PUT: error cases
        r = self.fetch(
            recipe_uri,
            method='PUT',
            headers=self.headers,
            body='it is not json',
        )
        self.assertEqual(r.code, 400)
        self.assertEqual(r.reason, 'Invalid JSON body')
        r = self.fetch(
            RECIPE_ENTRY_URI_FORMAT_STR.format(id='1234'),
            method='PUT',
            headers=self.headers,
            body=json.dumps(self.recipe1),
        )
        self.assertEqual(r.code, 404)
        # Delete that Recipe
        r = self.fetch(
            recipe_uri,
            method='DELETE',
            headers=None,
        )
        self.assertEqual(r.code, 204)
        r = self.fetch(
            recipe_uri,
            method='GET',
            headers=None,
        )
        self.assertEqual(r.code, 404)
        # DELETE: error cases
        r = self.fetch(
            recipe_uri,
            method='DELETE',
            headers=None,
        )
        self.assertEqual(r.code, 404)
        # Get all recipes in the recipes list, must be ZERO
        r = self.fetch(
            RECIPE_ENTRY_URI_FORMAT_STR.format(id=''),
            method='GET',
            headers=None,
        )
        all_recipes = json.loads(r.body.decode('utf-8'))
        self.assertEqual(r.code, 200, all_recipes)
        self.assertEqual(len(all_recipes), 0, all_recipes)


if __name__ == '__main__':
    tornado.testing.main()
