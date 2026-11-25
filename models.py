from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional


@dataclass
class UserProfile:
    """Модель профілю користувача для розрахунку добової норми."""
    name: str
    gender: str            # 'M' (чоловіча) або 'F' (жіноча)
    age: int               # років
    weight_kg: float       # кг
    height_cm: float       # см
    activity_level: float  # коефіцієнт активності (1.2 - 1.9)
    goal: str              # 'lose' (схуднення), 'maintain' (підтримання), 'gain' (набір маси)
    id: Optional[int] = None


@dataclass
class Product:
    """Модель продукту харчування (показники на 100 г)."""
    name: str
    category: str
    calories_per_100g: float
    protein_per_100g: float
    fat_per_100g: float
    carbs_per_100g: float
    is_custom: bool = False
    id: Optional[int] = None


@dataclass
class FoodEntry:
    """Запис про спожитий продукт із зазначенням маси порції."""
    product: Product
    weight_grams: float
    meal_type: str       # 'Сніданок', 'Обід', 'Вечеря', 'Перекус'
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M"))
    id: Optional[int] = None

    @property
    def calories(self) -> float:
        return round(self.product.calories_per_100g * self.weight_grams / 100.0, 1)

    @property
    def protein(self) -> float:
        return round(self.product.protein_per_100g * self.weight_grams / 100.0, 1)

    @property
    def fat(self) -> float:
        return round(self.product.fat_per_100g * self.weight_grams / 100.0, 1)

    @property
    def carbs(self) -> float:
        return round(self.product.carbs_per_100g * self.weight_grams / 100.0, 1)


@dataclass
class DailyLog:
    """Щоденний журнал харчування та підсумковий баланс БЖУ."""
    log_date: str = field(default_factory=lambda: date.today().isoformat())
    target_calories: float = 2000.0
    target_protein: float = 150.0
    target_fat: float = 65.0
    target_carbs: float = 200.0
    entries: List[FoodEntry] = field(default_factory=list)

    def add_entry(self, entry: FoodEntry) -> None:
        self.entries.append(entry)

    def remove_entry(self, index: int) -> Optional[FoodEntry]:
        if 0 <= index < len(self.entries):
            return self.entries.pop(index)
        return None

    def get_totals(self) -> dict:
        return {
            "calories": round(sum(e.calories for e in self.entries), 1),
            "protein": round(sum(e.protein for e in self.entries), 1),
            "fat": round(sum(e.fat for e in self.entries), 1),
            "carbs": round(sum(e.carbs for e in self.entries), 1),
        }

    def get_remaining(self) -> dict:
        totals = self.get_totals()
        return {
            "calories": round(self.target_calories - totals["calories"], 1),
            "protein": round(self.target_protein - totals["protein"], 1),
            "fat": round(self.target_fat - totals["fat"], 1),
            "carbs": round(self.target_carbs - totals["carbs"], 1),
        }
