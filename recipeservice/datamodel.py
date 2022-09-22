# Copyright (c) 2020. All rights reserved.
from datetime import date, time
from typing import (
    Any,
    Dict,
    Mapping,
    Optional,
    Sequence,
    Union
)

VALUE_ERR_MSG = '{} has invalid value {}'


class RecipeEntry:
    def __init__(
        self,
        name: str,
        ingredients: Sequence[str],
        instructions: Sequence[str],
        datePublished: date = None,
        description: str = None,
        rating: float = None,
        prepTime: time = None,
        cookTime: time = None,
        nutrition: Dict[str, Optional[Union[int, str]]] = None
    ):
        if not name:
            raise ValueError(
                VALUE_ERR_MSG.format('name', name)
            )
        if not ingredients:
            raise ValueError(
                VALUE_ERR_MSG.format('ingredients', ingredients)
            )
        if not instructions:
            raise ValueError(
                VALUE_ERR_MSG.format('instructions', instructions)
            )

        self._name = name
        self._datePublished = datePublished
        self._description = description
        self._rating = rating
        self._prepTime = prepTime
        self._cookTime = cookTime
        self._ingredients = ingredients
        self._instructions = instructions
        self._nutrition = nutrition

    @classmethod
    def from_api_dm(cls, vars: Mapping[str, Any]) -> 'RecipeEntry':
        return RecipeEntry(
            name=vars['name'],
            datePublished=vars['datePublished'],
            description=vars['description'],
            rating=vars['rating'],
            prepTime=vars['prepTime'],
            cookTime=vars['cookTime'],
            ingredients=vars['ingredients'],
            instructions=vars['instructions'],
            nutrition=vars['nutrition']
        )

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if value is None:
            raise ValueError(VALUE_ERR_MSG.format('value', value))

        self._name = value

    @property
    def datePublished(self) -> date:
        return self._datePublished

    @datePublished.setter
    def datePublished(self, value: date) -> None:
        if value is None:
            raise ValueError(VALUE_ERR_MSG.format('value', value))

        self._datePublished = value

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        if value is None:
            raise ValueError(VALUE_ERR_MSG.format('value', value))

        self._description = value

    @property
    def rating(self) -> float:
        return self._rating

    @rating.setter
    def rating(self, value: float) -> None:
        if value is None:
            raise ValueError(VALUE_ERR_MSG.format('value', value))

        self._rating = value

    @property
    def prepTime(self) -> time:
        return self._prepTime

    @prepTime.setter
    def prepTime(self, value: time) -> None:
        if value is None:
            raise ValueError(VALUE_ERR_MSG.format('value', value))

        self._prepTime = value

    @property
    def cookTime(self) -> time:
        return self._cookTime

    @cookTime.setter
    def cookTime(self, value: time) -> None:
        if value is None:
            raise ValueError(VALUE_ERR_MSG.format('value', value))

        self._cookTime = value

    @property
    def ingredients(self) -> Sequence[str]:
        return self._ingredients

    @ingredients.setter
    def ingredients(self, value: Sequence[str]) -> None:
        if value is None:
            raise ValueError(VALUE_ERR_MSG.format('value', value))

        self._ingredients = list(value)

    @property
    def instructions(self) -> Sequence[str]:
        return self._instructions

    @instructions.setter
    def instructions(self, value: Sequence[str]) -> None:
        if value is None:
            raise ValueError(VALUE_ERR_MSG.format('value', value))

        self._instructions = list(value)

    @property
    def nutrition(self) -> Dict[str, Optional[Union[int, str]]]:
        return self._nutrition

    @nutrition.setter
    def nutrition(self, value: Dict[str, Optional[Union[int, str]]]) -> None:
        if value is None:
            raise ValueError(VALUE_ERR_MSG.format('value', value))

        self._nutrition = value

    def to_api_dm(self) -> Mapping[str, Any]:
        d = {
            'name': self.name,
            'datePublished': self.datePublished,
            'description': self.description,
            'rating': self.rating,
            'prepTime': self.prepTime,
            'cookTime': self.cookTime,
            'ingredients': self.ingredients,
            'instructions': self.instructions,
            'nutrition': self.nutrition
        }

        return {k: v for k, v in d.items() if v is not None}
