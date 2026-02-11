from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from crafters_toolkit.db import get_db
from crafters_toolkit.models import Item, Recipe, RecipeIngredient
from crafters_toolkit.schemas import (
    RecipeCreate,
    RecipeUpdate,
    RecipeRead,
    CalculateRequest,
    CalculateResponse,
    BaseMaterial,
)

router = APIRouter(prefix="/recipes", tags=["Recipes"])


@router.post("/", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
def create_recipe(payload: RecipeCreate, db: Session = Depends(get_db)):
    output_item = db.get(Item, payload.output_item_id)
    if output_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Output item {payload.output_item_id} not found",
        )

    ingredient_item_ids = [ingredient.item_id for ingredient in payload.ingredients]
    unique_item_ids: set[int] = set()
    duplicate_item_ids: set[int] = set()
    for item_id in ingredient_item_ids:
        if item_id in unique_item_ids:
            duplicate_item_ids.add(item_id)
        else:
            unique_item_ids.add(item_id)

    if duplicate_item_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Duplicate ingredient item_ids are not allowed: {sorted(duplicate_item_ids)}",
        )

    existing_ingredient_ids = set(
        db.scalars(select(Item.id).where(Item.id.in_(unique_item_ids)))
    )
    missing_ingredients = unique_item_ids - existing_ingredient_ids

    if missing_ingredients:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Missing ingredients: {sorted(missing_ingredients)}",
        )
    if payload.output_item_id in unique_item_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A recipe cannot use its own output as an ingredient",
        )

    recipe = Recipe(
        output_item_id=payload.output_item_id, output_quantity=payload.output_quantity
    )
    for ingredient in payload.ingredients:
        recipe.ingredients.append(
            RecipeIngredient(item_id=ingredient.item_id, quantity=ingredient.quantity)
        )

    db.add(recipe)
    db.commit()
    db.refresh(recipe)

    stmt = (
        select(Recipe)
        .where(Recipe.id == recipe.id)
        .options(
            joinedload(Recipe.output_item),
            selectinload(Recipe.ingredients).joinedload(RecipeIngredient.item),
        )
    )

    recipe_response = db.execute(stmt).scalar_one()
    return recipe_response


@router.get("/", response_model=list[RecipeRead])
def list_recipes(db: Session = Depends(get_db)):
    stmt = (
        select(Recipe)
        .options(
            joinedload(Recipe.output_item),
            selectinload(Recipe.ingredients).joinedload(RecipeIngredient.item),
        )
        .order_by(Recipe.id)
    )
    recipes_response = db.scalars(stmt).all()
    return recipes_response


@router.get("/{recipe_id}", response_model=RecipeRead)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    stmt = (
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(
            joinedload(Recipe.output_item),
            selectinload(Recipe.ingredients).joinedload(RecipeIngredient.item),
        )
    )
    recipe = db.execute(stmt).scalar_one_or_none()
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Recipe not found"
        )
    return recipe


@router.patch("/{recipe_id}", response_model=RecipeRead)
def update_recipe(recipe_id: int, payload: RecipeUpdate, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Recipe not found"
        )
    if payload.output_quantity is not None:
        recipe.output_quantity = payload.output_quantity

    if payload.ingredients is not None:
        recipe.ingredients.clear()
        for ingredient in payload.ingredients:
            recipe.ingredients.append(
                RecipeIngredient(
                    item_id=ingredient.item_id, quantity=ingredient.quantity
                )
            )

    db.commit()

    stmt = (
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(
            joinedload(Recipe.output_item),
            selectinload(Recipe.ingredients).joinedload(RecipeIngredient.item),
        )
    )
    recipe_response = db.execute(stmt).scalar_one_or_none()
    if recipe_response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )
    return recipe_response


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    db.delete(recipe)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/calculate", response_model=CalculateResponse)
def calculate_base_materials(payload: CalculateRequest, db: Session = Depends(get_db)):
    stmt = select(Recipe).options(selectinload(Recipe.ingredients))
    recipes = db.scalars(stmt).all()

    recipe_by_id = {recipe.id: recipe for recipe in recipes}
    recipes_by_output_item_id = {recipe.output_item_id: recipe for recipe in recipes}

    total_ingredients = defaultdict(float)

    def nested_resolve(item_id: int, quantity_needed: int, visited: set[int]):
        if item_id in visited:
            raise HTTPException(
                status_code=400,
                detail=f"Circular dependency detected involving item {item_id}",
            )
        visited.add(item_id)
        if item_id not in recipes_by_output_item_id:
            total_ingredients[item_id] += quantity_needed
        else:
            recipe = recipes_by_output_item_id[item_id]
            batches = quantity_needed / recipe.output_quantity
            for ingredient in recipe.ingredients:
                nested_resolve(
                    ingredient.item_id, ingredient.quantity * batches, visited.copy()
                )

    for craft_order in payload.recipes:
        recipe = recipe_by_id.get(craft_order.recipe_id)
        if recipe is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe {craft_order.recipe_id} not found",
            )
        nested_resolve(recipe.output_item_id, craft_order.quantity, set())

    item_ids = list(total_ingredients.keys())
    items = db.scalars(select(Item).where(Item.id.in_(item_ids))).all()
    item_name_by_id = {item.id: item.name for item in items}

    return CalculateResponse(
        base_materials=[
            BaseMaterial(
                item_id=item_id, item_name=item_name_by_id[item_id], quantity_needed=qty
            )
            for item_id, qty in sorted(total_ingredients.items())
        ]
    )
