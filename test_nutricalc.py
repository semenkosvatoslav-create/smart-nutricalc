import os
import tempfile
import unittest
from models import UserProfile, Product, FoodEntry, DailyLog
from calculator import NutritionCalculator
from repository import ProductRepository


class TestSmartNutriCalc(unittest.TestCase):
    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.tmp_db.close()
        self.repo = ProductRepository(self.tmp_db.name)

    def tearDown(self):
        if os.path.exists(self.tmp_db.name):
            os.remove(self.tmp_db.name)

    def test_bmr_and_tdee_male(self):
        profile = UserProfile(
            name="Тест",
            gender="M",
            age=25,
            weight_kg=80.0,
            height_cm=180.0,
            activity_level=1.55,
            goal="maintain",
        )
        self.assertEqual(NutritionCalculator.calculate_bmr(profile), 1805.0)
        self.assertEqual(NutritionCalculator.calculate_tdee(profile), round(1805.0 * 1.55, 1))

    def test_daily_log_calculations(self):
        chicken = Product("Курка", "М'ясо", 165.0, 31.0, 3.6, 0.0)
        rice = Product("Рис", "Крупи", 130.0, 2.7, 0.3, 28.2)
        log = DailyLog(target_calories=2000.0, target_protein=150.0, target_fat=65.0, target_carbs=200.0)
        log.add_entry(FoodEntry(product=chicken, weight_grams=200.0, meal_type="Обід"))
        log.add_entry(FoodEntry(product=rice, weight_grams=150.0, meal_type="Обід"))

        totals = log.get_totals()
        self.assertEqual(totals["calories"], 525.0)
        self.assertEqual(totals["protein"], 66.0)
        self.assertEqual(totals["fat"], 7.7)
        self.assertEqual(totals["carbs"], 42.3)

    def test_repository_search_and_custom_product(self):
        results = self.repo.search_products(query="філе")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Куряче філе відварне")

        custom = Product("Протеїновий батончик", "Снеки", 360.0, 30.0, 10.0, 35.0)
        saved = self.repo.add_custom_product(custom)
        self.assertIsNotNone(saved.id)
        found = self.repo.search_products(query="батончик")
        self.assertEqual(len(found), 1)


if __name__ == "__main__":
    unittest.main()
