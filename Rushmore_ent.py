import os
import random
from decimal import Decimal

import psycopg2
from faker import Faker
from dotenv import load_dotenv


# ----------------------------
#  LOAD ENV & DB CONNECTION
# ----------------------------

load_dotenv()  # Loads variables from .env in the current folder

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")

fake = Faker()


def get_connection():
    """
    Create a PostgreSQL connection using environment variables.
    Azure PostgreSQL requires SSL, so we use sslmode='require'.
    Also set the search_path so we use the 'rushmore' schema by default.
    """
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        sslmode="require",
    )
    with conn.cursor() as cur:
        cur.execute("SET search_path TO rushmore, public;")
    conn.commit()
    return conn


# ----------------------------
#  INSERT HELPERS
# ----------------------------

def insert_stores(conn, n_stores=4):
    store_ids = []
    with conn.cursor() as cur:
        for _ in range(n_stores):
            address = fake.street_address()
            city = fake.city()
            phone = fake.phone_number()
            phone = phone.replace(" ", "")[:20]  #  ensuring <= 20 chars

            cur.execute(
                """
                INSERT INTO stores (address, city, phone_number, opened_at)
                VALUES (%s, %s, %s, NOW() - (INTERVAL '1 year' * RANDOM()))
                RETURNING store_id;
                """,
                (address, city, phone),
            )
            store_id = cur.fetchone()[0]
            store_ids.append(store_id)
    conn.commit()
    print(f"Inserted {len(store_ids)} stores")
    return store_ids



def insert_ingredients(conn, n_ingredients=45):
    """
    Insert 40–50 ingredients and return list of ingredient_ids.
    """
    ingredient_ids = []

    base_names = [
        "Mozzarella", "Cheddar", "Parmesan", "Tomato Sauce", "BBQ Sauce",
        "Pepperoni", "Ham", "Bacon", "Chicken", "Beef",
        "Onions", "Mushrooms", "Green Peppers", "Olives", "Pineapple",
        "Jalapeños", "Spinach", "Garlic", "Basil", "Oregano",
    ]

    units = ["kg", "g", "liters", "ml", "units"]

    with conn.cursor() as cur:
        for i in range(n_ingredients):
            if i < len(base_names):
                name = base_names[i]
            else:
                name = fake.word().title() + " " + random.choice(
                    ["Topping", "Cheese", "Sauce", "Mix"]
                )
            stock_qty = round(random.uniform(5, 200), 2)
            unit = random.choice(units)
            cur.execute(
                """
                INSERT INTO ingredients (name, stock_quantity, unit)
                VALUES (%s, %s, %s)
                ON CONFLICT (name) DO NOTHING
                RETURNING ingredient_id;
                """,
                (name, Decimal(str(stock_qty)), unit),
            )
            row = cur.fetchone()
            if row:
                ingredient_ids.append(row[0])
    conn.commit()
    print(f"Inserted {len(ingredient_ids)} ingredients")
    return ingredient_ids


def insert_menu_items(conn, n_items=25):
    """
    Insert 20–30 menu items and return list of (item_id, price).
    """
    item_ids = []
    categories = ["Pizza", "Drink", "Side"]
    pizza_sizes = ["Small", "Medium", "Large"]
    drink_sizes = ["330ml", "500ml", "1L"]
    side_sizes = ["Regular", "Large"]

    with conn.cursor() as cur:
        for _ in range(n_items):
            category = random.choice(categories)
            if category == "Pizza":
                size = random.choice(pizza_sizes)
                name = f"{fake.word().title()} {random.choice(['Classic', 'Special', 'Deluxe'])} Pizza"
                price = round(random.uniform(7, 18), 2)
            elif category == "Drink":
                size = random.choice(drink_sizes)
                name = f"{fake.word().title()} Drink"
                price = round(random.uniform(1.5, 4), 2)
            else:  # Side
                size = random.choice(side_sizes)
                name = f"{fake.word().title()} {random.choice(['Fries', 'Wedges', 'Side'])}"
                price = round(random.uniform(3, 7), 2)

            cur.execute(
                """
                INSERT INTO menu_items (name, category, size, price)
                VALUES (%s, %s, %s, %s)
                RETURNING item_id, price;
                """,
                (name, category, size, Decimal(str(price))),
            )
            item_id, price_val = cur.fetchone()
            item_ids.append((item_id, price_val))
    conn.commit()
    print(f"Inserted {len(item_ids)} menu items")
    return item_ids


def insert_item_ingredients(conn, item_ids, ingredient_ids):
    """
    Create recipe mapping: each menu item uses 2–6 random ingredients.
    """
    with conn.cursor() as cur:
        for item_id, _ in item_ids:
            n_ing = random.randint(2, 6)
            chosen_ings = random.sample(ingredient_ids, n_ing)
            for ing_id in chosen_ings:
                qty = round(random.uniform(0.05, 0.5), 2)
                cur.execute(
                    """
                    INSERT INTO item_ingredients (item_id, ingredient_id, quantity_required)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (item_id, ingredient_id) DO NOTHING;
                    """,
                    (item_id, ing_id, Decimal(str(qty))),
                )
    conn.commit()
    print("Linked menu_items to ingredients via item_ingredients")


def insert_customers(conn, n_customers=1200):
    customer_ids = []
    with conn.cursor() as cur:
        for _ in range(n_customers):
            full_name = fake.name()
            parts = full_name.split()
            first_name = parts[0]
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

            email = fake.unique.email()
            phone = fake.unique.phone_number()
            phone = phone.replace(" ", "")[:20]  #  limit length

            cur.execute(
                """
                INSERT INTO customers (first_name, last_name, email, phone_number, created_at)
                VALUES (%s, %s, %s, %s, NOW() - (INTERVAL '90 days' * RANDOM()))
                RETURNING customer_id;
                """,
                (first_name, last_name, email, phone),
            )
            customer_id = cur.fetchone()[0]
            customer_ids.append(customer_id)
    conn.commit()
    print(f"Inserted {len(customer_ids)} customers")
    return customer_ids



def insert_orders_and_order_items(
    conn,
    customer_ids,
    store_ids,
    item_ids_with_price,
    n_orders=5000,
):
    """
    Insert 5000+ orders and ~15,000+ order_items.
    """
    statuses = ["Pending", "In Progress", "Delivered", "Cancelled"]
    total_order_items = 0

    with conn.cursor() as cur:
        for _ in range(n_orders):
            customer_id = random.choice(customer_ids)
            store_id = random.choice(store_ids)
            order_ts = fake.date_time_this_year()
            status = random.choices(
                statuses, weights=[0.1, 0.2, 0.6, 0.1], k=1
            )[0]

            # Create order with temporary zero total
            cur.execute(
                """
                INSERT INTO orders (customer_id, store_id, order_timestamp, total_amount, status)
                VALUES (%s, %s, %s, 0, %s)
                RETURNING order_id;
                """,
                (customer_id, store_id, order_ts, status),
            )
            order_id = cur.fetchone()[0]

            # 1–5 items per order
            n_items_in_order = random.randint(1, 5)
            order_total = Decimal("0.00")

            for _ in range(n_items_in_order):
                item_id, current_price = random.choice(item_ids_with_price)
                quantity = random.randint(1, 4)
                price_at_time = current_price
                line_total = price_at_time * quantity

                cur.execute(
                    """
                    INSERT INTO order_items (order_id, item_id, quantity, price_at_time_of_order)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (order_id, item_id, quantity, price_at_time),
                )
                order_total += line_total
                total_order_items += 1

            # Update order total
            cur.execute(
                """
                UPDATE orders
                SET total_amount = %s
                WHERE order_id = %s;
                """,
                (order_total, order_id),
            )

    conn.commit()
    print(f"Inserted {n_orders} orders and {total_order_items} order_items")


# ----------------------------
#  MAIN DRIVER
# ----------------------------

def main():
    print("Connecting to database...")
    conn = get_connection()
    print("Connected successfully.")

    try:
        # OPTIONAL: truncate tables for a clean load during development
        # with conn.cursor() as cur:
        #     cur.execute("""
        #         TRUNCATE order_items, orders,
        #                  item_ingredients, menu_items,
        #                  ingredients, customers, stores
        #         RESTART IDENTITY CASCADE;
        #     """)
        # conn.commit()
        # print("Truncated existing data (dev reset).")

        # 1. Stores
        store_ids = insert_stores(conn, n_stores=random.randint(3, 5))

        # 2. Ingredients
        ingredient_ids = insert_ingredients(conn, n_ingredients=random.randint(40, 50))

        # 3. Menu items
        item_ids_with_price = insert_menu_items(conn, n_items=random.randint(20, 30))

        # 4. Link recipes
        insert_item_ingredients(conn, item_ids_with_price, ingredient_ids)

        # 5. Customers
        customer_ids = insert_customers(conn, n_customers=1200)

        # 6. Orders + Order items
        insert_orders_and_order_items(
            conn,
            customer_ids=customer_ids,
            store_ids=store_ids,
            item_ids_with_price=item_ids_with_price,
            n_orders=5000,
        )

        print("\n Fake data generation complete.")
    finally:
        conn.close()
        print("Connection closed.")


if __name__ == "__main__":
    main()
