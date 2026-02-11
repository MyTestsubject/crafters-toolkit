from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)

    recipes_as_output: Mapped[list["Recipe"]] = relationship(
        back_populates="output_item", cascade="all,delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Item id={self.id} name={self.name!r}>"


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    output_item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    output_quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    output_item: Mapped["Item"] = relationship(back_populates="recipes_as_output")
    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="recipe", cascade="all,delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Recipe id={self.id} produces={self.output_item_id} qty={self.output_quantity}>"


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    __table_args__ = (
        UniqueConstraint(
            "recipe_id",
            "item_id",
            name="unique_recipe_ingredient",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")
    item: Mapped["Item"] = relationship()

    def __repr__(self) -> str:
        return f"<RecipeIngredient recipe={self.recipe_id} item={self.item_id} qty={self.quantity}>"
