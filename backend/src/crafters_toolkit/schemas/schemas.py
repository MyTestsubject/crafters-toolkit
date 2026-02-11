from pydantic import BaseModel, ConfigDict, PositiveInt, Field


# ---Item Schemas---


class ItemCreate(BaseModel):
    name: str


class ItemUpdate(BaseModel):
    name: str | None = None


class ItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


# ---Recipe Ingredient Schemas---


class RecipeIngredientCreate(BaseModel):
    item_id: int
    quantity: PositiveInt


class RecipeIngredientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quantity: PositiveInt
    item: ItemRead


# ---Recipe Schemas---
class RecipeCreate(BaseModel):
    output_item_id: int
    output_quantity: PositiveInt
    ingredients: list[RecipeIngredientCreate] = Field(min_length=1)


class RecipeUpdate(BaseModel):
    output_quantity: PositiveInt | None = None
    ingredients: list[RecipeIngredientCreate] | None = Field(default=None, min_length=1)


class RecipeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    output_item: ItemRead
    output_quantity: PositiveInt
    ingredients: list[RecipeIngredientRead]


# ---Calculation Schemas---


class CraftOrder(BaseModel):
    recipe_id: int
    quantity: PositiveInt


class CalculateRequest(BaseModel):
    recipes: list[CraftOrder] = Field(min_length=1)


class BaseMaterial(BaseModel):
    item_id: int
    item_name: str
    quantity_needed: float


class CalculateResponse(BaseModel):
    base_materials: list[BaseMaterial]
