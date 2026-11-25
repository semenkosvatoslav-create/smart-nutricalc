from models import UserProfile


class NutritionCalculator:
    """Математичне ядро для обчислення норм калорійності та БЖУ."""

    ACTIVITY_LEVELS = {
        "1": (1.2, "Мінімальна активність (сидячий спосіб життя)"),
        "2": (1.375, "Легка активність (тренування 1-3 рази на тиждень)"),
        "3": (1.55, "Середня активність (тренування 3-5 разів на тиждень)"),
        "4": (1.725, "Висока активність (інтенсивні тренування 6-7 разів)"),
        "5": (1.9, "Екстремальна активність (фізична праця / двічі на день)"),
    }

    GOALS = {
        "lose": ("Схуднення (-15% ккал)", 0.85, (0.30, 0.30, 0.40)),
        "maintain": ("Підтримання ваги (100% ккал)", 1.00, (0.25, 0.30, 0.45)),
        "gain": ("Набір м'язової маси (+15% ккал)", 1.15, (0.30, 0.25, 0.45)),
    }

    @staticmethod
    def calculate_bmr(profile: UserProfile) -> float:
        """Розрахунок базового обміну речовин (BMR) за формулою Міффліна — Сан Жеора."""
        base = 10.0 * profile.weight_kg + 6.25 * profile.height_cm - 5.0 * profile.age
        if profile.gender.upper() == "M":
            return round(base + 5.0, 1)
        return round(base - 161.0, 1)

    @classmethod
    def calculate_tdee(cls, profile: UserProfile) -> float:
        """Розрахунок добової витрати енергії (TDEE)."""
        bmr = cls.calculate_bmr(profile)
        return round(bmr * profile.activity_level, 1)

    @classmethod
    def calculate_daily_targets(cls, profile: UserProfile) -> dict:
        """Розрахунок цільової калорійності та норми БЖУ у грамах."""
        tdee = cls.calculate_tdee(profile)
        _, multiplier, (p_ratio, f_ratio, c_ratio) = cls.GOALS.get(
            profile.goal, cls.GOALS["maintain"]
        )
        target_calories = round(tdee * multiplier, 1)

        # 1 г білка = 4 ккал, 1 г жиру = 9 ккал, 1 г вуглеводів = 4 ккал
        target_protein = round((target_calories * p_ratio) / 4.0, 1)
        target_fat = round((target_calories * f_ratio) / 9.0, 1)
        target_carbs = round((target_calories * c_ratio) / 4.0, 1)

        return {
            "bmr": cls.calculate_bmr(profile),
            "tdee": tdee,
            "calories": target_calories,
            "protein": target_protein,
            "fat": target_fat,
            "carbs": target_carbs,
        }
