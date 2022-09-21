import json

import tornado.testing

from recipeservice.tornado.app import (
    RECIPE_ENTRY_URI_FORMAT_STR
)

from tests.unit.tornado_app_handlers_test import (
    RecipeServiceTornadoAppTestSetup
)

class TestRecipeServiceApp(RecipeServiceTornadoAppTestSetup):
  def test_address_book_endpoints(self):
    # Get all addresses in the address book, must be ZERO
    r = self.fetch(
        RECIPE_ENTRY_URI_FORMAT_STR.format(id=''),
        method='GET',
        headers=None,
    )
    all_addrs = json.loads(r.body.decode('utf-8'))
    self.assertEqual(r.code, 200, all_addrs)
    self.assertEqual(len(all_addrs), 0, all_addrs)
    # Add an address
    r = self.fetch(
        RECIPE_ENTRY_URI_FORMAT_STR.format(id=''),
        method='POST',
        headers=self.headers,
        body=json.dumps(self.addr0),
    )
    self.assertEqual(r.code, 201)
    addr_uri = r.headers['Location']
    # POST: error cases
    r = self.fetch(
        RECIPE_ENTRY_URI_FORMAT_STR.format(id=''),
        method='POST',
        headers=self.headers,
        body='it is not json',
    )
    self.assertEqual(r.code, 400)
    self.assertEqual(r.reason, 'Invalid JSON body')
    # Get the added address
    r = self.fetch(
        addr_uri,
        method='GET',
        headers=None,
    )
    self.assertEqual(r.code, 200)
    self.assertEqual(
        self.addr0,
        json.loads(r.body.decode('utf-8'))
    )
    # GET: error cases
    r = self.fetch(
        RECIPE_ENTRY_URI_FORMAT_STR.format(id='no-such-id'),
        method='GET',
        headers=None,
    )
    self.assertEqual(r.code, 404)
    # Update that address
    r = self.fetch(
        addr_uri,
        method='PUT',
        headers=self.headers,
        body=json.dumps(self.addr1),
    )
    self.assertEqual(r.code, 204)
    r = self.fetch(
        addr_uri,
        method='GET',
        headers=None,
    )
    self.assertEqual(r.code, 200)
    self.assertEqual(
        self.addr1,
        json.loads(r.body.decode('utf-8'))
    )
    # PUT: error cases
    r = self.fetch(
        addr_uri,
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
        body=json.dumps(self.addr1),
    )
    self.assertEqual(r.code, 404)
    # Delete that address
    r = self.fetch(
        addr_uri,
        method='DELETE',
        headers=None,
    )
    self.assertEqual(r.code, 204)
    r = self.fetch(
        addr_uri,
        method='GET',
        headers=None,
    )
    self.assertEqual(r.code, 404)
    # DELETE: error cases
    r = self.fetch(
        addr_uri,
        method='DELETE',
        headers=None,
    )
    self.assertEqual(r.code, 404)
    # Get all addresses in the address book, must be ZERO
    r = self.fetch(
        RECIPE_ENTRY_URI_FORMAT_STR.format(id=''),
        method='GET',
        headers=None,
    )
    all_addrs = json.loads(r.body.decode('utf-8'))
    self.assertEqual(r.code, 200, all_addrs)
    self.assertEqual(len(all_addrs), 0, all_addrs)

if __name__ == '__main__':
    tornado.testing.main()