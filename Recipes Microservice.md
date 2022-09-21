# Recipes Microservice

## API Model

`[POST]` `/v1/recipes`
Create a recipe item

`[GET]` `/v1/recipes/{id}`
Get a specific recipe

`[GET]` `/v1/recipes`
Get a list of all the recipes

`[PUT]` `/v1/recipes/{id}`
Update a recipe

`[DELETE]` `/v1/recipes/{id}`
Delete a recipe

## Data Model

Schema of the recipe

```
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Schema of an Recipe listings site",
    "definitions": {
        "nutrition": {
            "$id": "#nutrition",
            "type": "object",
            "properties": {
                "servingSize": {
                    "type": "string"
                },
                "calories": {
                    "type": "number"
                }
            },
            "required": [
                "servingSize",
                "calories"
            ],
            "additionalProperties": false
        }
        "recipeEntry": {
            "$id": "#recipeEntry",
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                },
                "datePublished": {
                    "type": "date"
                }
                "description": {
                    "type": "string",
                    "minLength": 10,
                    "maxLength": 500
                },
                "rating": {
                    "type": "number"
                    "minimum": 0,
                    "maximum": 5
                },
                "prepTime": {
                    "type": "time"
                }
                "cookTime": {
                    "type": "time"
                },
                "ingredients": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "minLength": 1
                    }
                },
                "instructions": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "minLength": 1
                    }
                },
                "nutrition": {
                    "$ref": "#/definitions/nutrition"
                }
            },
            "required": [
                "name",
                "datePublished",
                "description",
                "prepTime",
                "cookTime",
                "ingredients",
                "instructions",
                "nutrition"
            ],
            "additionalProperties": false
        }
    }
    "$ref": "#/defintions/recipeEntry"
}
```
