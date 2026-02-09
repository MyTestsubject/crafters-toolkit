from pydantic import BaseModel, ConfigDict


# ---Item Schemas---


class ItemCreate(BaseModel):
    name: str
    description: str | None = None


class ItemUpdate(BaseModel):
    name: str
    description: str | None = None


class ItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None


# ---Recipe Ingredient Schemas---


class RecipeIngredientCreate(BaseModel):
    item_id: int
    quantity: int


class RecipeIngredientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quantity: int
    item: ItemRead


# ---Recipe Schemas---
class RecipeCreate(BaseModel):
    name: str
    output_quantity: int = 1
    description: str | None = None
    ingredients: list[RecipeIngredientCreate]


class RecipeUpdate(BaseModel):
    output_quantity: int | None = None
    ingredients: list[RecipeIngredientRead] | None = None


class RecipeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    output_quantity: int
    output_item: ItemRead
    ingredients: list[RecipeIngredientRead]


# ---Calculation Schemas---


class CraftOrder(BaseModel):
    recipe_id: int
    quantity: int = 1


class CalculateRequest(BaseModel):
    recipes: list[CraftOrder]


class BaseMaterial(BaseModel):
    item_id: int
    item_name: str
    quantity_needed: float


class CalculateResponse(BaseModel):
    base_materials: list[BaseMaterial]
