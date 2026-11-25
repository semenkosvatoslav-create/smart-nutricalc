from datetime import date
from models import UserProfile, Product, FoodEntry, DailyLog
from calculator import NutritionCalculator
from repository import ProductRepository


def render_progress_bar(label: str, current: float, target: float, unit: str, width: int = 22) -> str:
    ratio = min(current / target, 1.0) if target > 0 else 0.0
    filled = int(width * ratio)
    bar = "#" * filled + "-" * (width - filled)
    pct = round((current / target) * 100, 1) if target > 0 else 0.0
    return f"{label:<10} [{bar}] {current:>6.1f} / {target:<6.1f} {unit} ({pct:>5.1f}%)"


class NutriCalcApp:
    """Головний контролер застосунку Smart NutriCalc."""

    def __init__(self, db_path: str = "nutricalc.db"):
        self.repo = ProductRepository(db_path)
        self.profile = self.repo.load_profile()
        if not self.profile:
            self.profile = UserProfile(
                name="Користувач",
                gender="M",
                age=20,
                weight_kg=75.0,
                height_cm=178.0,
                activity_level=1.55,
                goal="maintain",
            )
            self.repo.save_profile(self.profile)
        self.daily_log = self._build_daily_log()

    def _build_daily_log(self) -> DailyLog:
        targets = NutritionCalculator.calculate_daily_targets(self.profile)
        today_str = date.today().isoformat()
        log = DailyLog(
            log_date=today_str,
            target_calories=targets["calories"],
            target_protein=targets["protein"],
            target_fat=targets["fat"],
            target_carbs=targets["carbs"],
        )
        for entry in self.repo.load_daily_entries(today_str):
            log.add_entry(entry)
        return log

    def show_dashboard(self) -> None:
        targets = NutritionCalculator.calculate_daily_targets(self.profile)
        totals = self.daily_log.get_totals()
        remaining = self.daily_log.get_remaining()

        print("\n" + "=" * 66)
        print(f"  SMART NUTRICALC | Дата: {self.daily_log.log_date} | Профіль: {self.profile.name}")
        print(f"  BMR: {targets['bmr']} ккал | TDEE: {targets['tdee']} ккал | Ціль: {self.daily_log.target_calories} ккал")
        print("=" * 66)
        print(render_progress_bar("Калорії", totals["calories"], self.daily_log.target_calories, "ккал"))
        print(render_progress_bar("Білки", totals["protein"], self.daily_log.target_protein, "г"))
        print(render_progress_bar("Жири", totals["fat"], self.daily_log.target_fat, "г"))
        print(render_progress_bar("Вуглеводи", totals["carbs"], self.daily_log.target_carbs, "г"))
        print("-" * 66)
        print(
            f"  Залишок на день: {remaining['calories']} ккал | "
            f"Б: {remaining['protein']} г | Ж: {remaining['fat']} г | В: {remaining['carbs']} г"
        )
        print("=" * 66)

    def configure_profile(self) -> None:
        print("\n--- Налаштування профілю та розрахунок норми ---")
        name = input(f"Ім'я [{self.profile.name}]: ").strip() or self.profile.name
        gender = input(f"Стать (M/F) [{self.profile.gender}]: ").strip().upper() or self.profile.gender
        if gender not in ("M", "F"):
            gender = "M"

        try:
            age = int(input(f"Вік (років) [{self.profile.age}]: ").strip() or self.profile.age)
            weight = float(input(f"Вага (кг) [{self.profile.weight_kg}]: ").strip() or self.profile.weight_kg)
            height = float(input(f"Зріст (см) [{self.profile.height_cm}]: ").strip() or self.profile.height_cm)
        except ValueError:
            print("Помилка введення числових параметрів. Зміни скасовано.")
            return

        print("Рівень активності:")
        for key, (coef, desc) in NutritionCalculator.ACTIVITY_LEVELS.items():
            print(f"  {key}. {desc} (x{coef})")
        act_choice = input("Оберіть рівень (1-5) [3]: ").strip() or "3"
        activity_level = NutritionCalculator.ACTIVITY_LEVELS.get(act_choice, (1.55, ""))[0]

        print("Мета: 1 - Схуднення, 2 - Підтримання ваги, 3 - Набір маси")
        goal_map = {"1": "lose", "2": "maintain", "3": "gain"}
        goal_choice = input("Оберіть мету (1-3) [2]: ").strip() or "2"
        goal = goal_map.get(goal_choice, "maintain")

        self.profile = UserProfile(
            name=name,
            gender=gender,
            age=age,
            weight_kg=weight,
            height_cm=height,
            activity_level=activity_level,
            goal=goal,
        )
        self.repo.save_profile(self.profile)
        self.daily_log = self._build_daily_log()
        print("Профіль оновлено, добову норму перераховано!")

    def add_meal_entry(self) -> None:
        print("\n--- Пошук та додавання продукту до раціону ---")
        query = input("Введіть назву продукту для пошуку (або Enter для списку всіх): ").strip()
        products = self.repo.search_products(query=query)
        if not products:
            print("Продуктів за вашим запитом не знайдено.")
            return

        for idx, p in enumerate(products, start=1):
            print(
                f"  {idx:>2}. {p.name:<26} ({p.category}) — "
                f"{p.calories_per_100g} ккал | Б:{p.protein_per_100g} Ж:{p.fat_per_100g} В:{p.carbs_per_100g}"
            )

        try:
            choice = int(input("Оберіть номер продукту: ").strip())
            if not (1 <= choice <= len(products)):
                print("Некоректний номер.")
                return
            weight = float(input("Введіть масу порції у грамах (наприклад, 150): ").strip())
            if weight <= 0:
                print("Маса має бути додатною.")
                return
        except ValueError:
            print("Некоректне числове значення.")
            return

        meals = {"1": "Сніданок", "2": "Обід", "3": "Вечеря", "4": "Перекус"}
        meal_key = input("Прийом їжі (1-Сніданок, 2-Обід, 3-Вечеря, 4-Перекус) [2]: ").strip() or "2"
        meal_type = meals.get(meal_key, "Обід")

        entry = FoodEntry(product=products[choice - 1], weight_grams=weight, meal_type=meal_type)
        self.repo.save_food_entry(self.daily_log.log_date, entry)
        self.daily_log.add_entry(entry)
        print(f"Додано: {entry.product.name} ({entry.weight_grams} г) — {entry.calories} ккал.")

    def view_diary(self) -> None:
        print(f"\n--- Щоденник харчування за {self.daily_log.log_date} ---")
        if not self.daily_log.entries:
            print("Записів за сьогодні ще немає.")
            return

        for idx, e in enumerate(self.daily_log.entries, start=1):
            print(
                f"  {idx}. [{e.timestamp}] {e.meal_type:<9} | {e.product.name:<24} "
                f"{e.weight_grams:>5.0f} г -> {e.calories:>6.1f} ккал (Б:{e.protein} Ж:{e.fat} В:{e.carbs})"
            )

        action = input("\nВведіть номер запису для видалення або Enter для повернення: ").strip()
        if action.isdigit():
            removed = self.daily_log.remove_entry(int(action) - 1)
            if removed and removed.id is not None:
                self.repo.delete_food_entry(removed.id)
                print(f"Видалено запис: {removed.product.name}")

    def create_custom_product(self) -> None:
        print("\n--- Додавання власного продукту в базу даних ---")
        name = input("Назва продукту: ").strip()
        if not name:
            print("Назва не може бути порожньою.")
            return
        category = input("Категорія [Власні продукти]: ").strip() or "Власні продукти"
        try:
            kcal = float(input("Калорійність на 100 г (ккал): ").strip())
            prot = float(input("Білки на 100 г (г): ").strip())
            fat = float(input("Жири на 100 г (г): ").strip())
            carbs = float(input("Вуглеводи на 100 г (г): ").strip())
        except ValueError:
            print("Помилка: введіть коректні числові значення.")
            return

        product = Product(
            name=name,
            category=category,
            calories_per_100g=kcal,
            protein_per_100g=prot,
            fat_per_100g=fat,
            carbs_per_100g=carbs,
        )
        try:
            self.repo.add_custom_product(product)
            print(f"Продукт '{product.name}' успішно збережено в БД!")
        except Exception as exc:
            print(f"Не вдалося додати продукт: {exc}")

    def run(self) -> None:
        while True:
            self.show_dashboard()
            print("Меню дій:")
            print("  1. Додати продукт до раціону (пошук та розрахунок)")
            print("  2. Переглянути / редагувати щоденник за день")
            print("  3. Налаштувати профіль та перерахувати норму БЖУ")
            print("  4. Додати новий продукт до бази даних")
            print("  0. Вихід")

            choice = input("Ваш вибір: ").strip()
            if choice == "1":
                self.add_meal_entry()
            elif choice == "2":
                self.view_diary()
            elif choice == "3":
                self.configure_profile()
            elif choice == "4":
                self.create_custom_product()
            elif choice == "0":
                print("Роботу завершено. До зустрічі!")
                break
            else:
                print("Невідома команда, спробуйте ще раз.")


if __name__ == "__main__":
    app = NutriCalcApp()
    app.run()
