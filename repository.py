import sqlite3
from typing import List, Optional
from models import Product, UserProfile, FoodEntry


INITIAL_PRODUCTS = [
    ("Куряче філе відварне", "М'ясо та птиця", 165.0, 31.0, 3.6, 0.0),
    ("Гречана каша варена", "Крупи та гарніри", 110.0, 4.2, 1.1, 21.3),
    ("Рис білий відварний", "Крупи та гарніри", 130.0, 2.7, 0.3, 28.2),
    ("Вівсянка на воді", "Крупи та гарніри", 88.0, 3.0, 1.7, 15.0),
    ("Яйце куряче варене", "Яйця та молочне", 155.0, 12.6, 10.6, 1.1),
    ("Сир кисломолочний 5%", "Яйця та молочне", 121.0, 17.2, 5.0, 1.8),
    ("Йогурт грецький 2%", "Яйця та молочне", 66.0, 8.0, 2.0, 4.0),
    ("Лосось запечений", "Риба та морепродукти", 208.0, 20.4, 13.4, 0.0),
    ("Тунець у власному соку", "Риба та морепродукти", 116.0, 25.5, 1.0, 0.0),
    ("Банан свіжий", "Фрукти та ягоди", 89.0, 1.1, 0.3, 22.8),
    ("Яблуко свіже", "Фрукти та ягоди", 52.0, 0.3, 0.2, 13.8),
    ("Огірок свіжий", "Овочі", 15.0, 0.8, 0.1, 2.8),
    ("Помідор свіжий", "Овочі", 18.0, 0.9, 0.2, 3.9),
    ("Броколі відварна", "Овочі", 35.0, 2.4, 0.4, 7.2),
    ("Хліб цільнозерновий", "Випічка", 247.0, 13.0, 3.4, 41.0),
    ("Горіхи волоські", "Горіхи та насіння", 654.0, 15.2, 65.2, 7.0),
    ("Олія оливкова", "Олії та соуси", 884.0, 0.0, 100.0, 0.0),
]


class ProductRepository:
    """Репозиторій для роботи з локальною базою даних SQLite."""

    def __init__(self, db_path: str = "nutricalc.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.create_function("PY_LOWER", 1, lambda s: s.lower() if s else "")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS user_profile (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    name TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    weight_kg REAL NOT NULL,
                    height_cm REAL NOT NULL,
                    activity_level REAL NOT NULL,
                    goal TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    calories_per_100g REAL NOT NULL,
                    protein_per_100g REAL NOT NULL,
                    fat_per_100g REAL NOT NULL,
                    carbs_per_100g REAL NOT NULL,
                    is_custom INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS food_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_date TEXT NOT NULL,
                    product_id INTEGER NOT NULL,
                    weight_grams REAL NOT NULL,
                    meal_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                );
                """
            )
            cursor = conn.execute("SELECT COUNT(*) FROM products")
            if cursor.fetchone()[0] == 0:
                conn.executemany(
                    """
                    INSERT INTO products (name, category, calories_per_100g, protein_per_100g, fat_per_100g, carbs_per_100g, is_custom)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                    """,
                    INITIAL_PRODUCTS,
                )

    def save_profile(self, profile: UserProfile) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO user_profile
                (id, name, gender, age, weight_kg, height_cm, activity_level, goal)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile.name,
                    profile.gender,
                    profile.age,
                    profile.weight_kg,
                    profile.height_cm,
                    profile.activity_level,
                    profile.goal,
                ),
            )

    def load_profile(self) -> Optional[UserProfile]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM user_profile WHERE id = 1").fetchone()
            if not row:
                return None
            return UserProfile(
                id=row["id"],
                name=row["name"],
                gender=row["gender"],
                age=row["age"],
                weight_kg=row["weight_kg"],
                height_cm=row["height_cm"],
                activity_level=row["activity_level"],
                goal=row["goal"],
            )

    def search_products(self, query: str = "", category: str = "") -> List[Product]:
        sql = "SELECT * FROM products WHERE 1=1"
        params = []
        if query:
            sql += " AND PY_LOWER(name) LIKE ?"
            params.append(f"%{query.strip().lower()}%")
        if category:
            sql += " AND PY_LOWER(category) = ?"
            params.append(category.strip().lower())
        sql += " ORDER BY name ASC"

        with self._get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [
                Product(
                    id=r["id"],
                    name=r["name"],
                    category=r["category"],
                    calories_per_100g=r["calories_per_100g"],
                    protein_per_100g=r["protein_per_100g"],
                    fat_per_100g=r["fat_per_100g"],
                    carbs_per_100g=r["carbs_per_100g"],
                    is_custom=bool(r["is_custom"]),
                )
                for r in rows
            ]

    def get_categories(self) -> List[str]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT category FROM products ORDER BY category ASC"
            ).fetchall()
            return [r["category"] for r in rows]

    def add_custom_product(self, product: Product) -> Product:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO products
                (name, category, calories_per_100g, protein_per_100g, fat_per_100g, carbs_per_100g, is_custom)
                VALUES (?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    product.name,
                    product.category,
                    product.calories_per_100g,
                    product.protein_per_100g,
                    product.fat_per_100g,
                    product.carbs_per_100g,
                ),
            )
            product.id = cursor.lastrowid
            product.is_custom = True
            return product

    def save_food_entry(self, log_date: str, entry: FoodEntry) -> FoodEntry:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO food_entries (log_date, product_id, weight_grams, meal_type, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (log_date, entry.product.id, entry.weight_grams, entry.meal_type, entry.timestamp),
            )
            entry.id = cursor.lastrowid
            return entry

    def delete_food_entry(self, entry_id: int) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM food_entries WHERE id = ?", (entry_id,))

    def load_daily_entries(self, log_date: str) -> List[FoodEntry]:
        sql = """
            SELECT fe.id AS entry_id, fe.weight_grams, fe.meal_type, fe.timestamp,
                   p.id AS prod_id, p.name, p.category, p.calories_per_100g,
                   p.protein_per_100g, p.fat_per_100g, p.carbs_per_100g, p.is_custom
            FROM food_entries fe
            JOIN products p ON fe.product_id = p.id
            WHERE fe.log_date = ?
            ORDER BY fe.id ASC
        """
        with self._get_connection() as conn:
            rows = conn.execute(sql, (log_date,)).fetchall()
            entries = []
            for r in rows:
                product = Product(
                    id=r["prod_id"],
                    name=r["name"],
                    category=r["category"],
                    calories_per_100g=r["calories_per_100g"],
                    protein_per_100g=r["protein_per_100g"],
                    fat_per_100g=r["fat_per_100g"],
                    carbs_per_100g=r["carbs_per_100g"],
                    is_custom=bool(r["is_custom"]),
                )
                entries.append(
                    FoodEntry(
                        id=r["entry_id"],
                        product=product,
                        weight_grams=r["weight_grams"],
                        meal_type=r["meal_type"],
                        timestamp=r["timestamp"],
                    )
                )
            return entries
