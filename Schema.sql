-- =========================================================
-- RushMore Pizzeria - Core OLTP Schema
-- Normalized to 3NF, with FK constraints and helpful indexes
-- =========================================================

-- A dedicated schema(since i want to add other schemas)
CREATE SCHEMA IF NOT EXISTS rushmore;
SET search_path = rushmore, public;

-- Safety: drop tables in dependency order (for dev resets)
DO $$
BEGIN
  IF to_regclass('rushmore.order_items') IS NOT NULL THEN DROP TABLE rushmore.order_items CASCADE; END IF;
  IF to_regclass('rushmore.orders') IS NOT NULL THEN DROP TABLE rushmore.orders CASCADE; END IF;
  IF to_regclass('rushmore.item_ingredients') IS NOT NULL THEN DROP TABLE rushmore.item_ingredients CASCADE; END IF;
  IF to_regclass('rushmore.menu_items') IS NOT NULL THEN DROP TABLE rushmore.menu_items CASCADE; END IF;
  IF to_regclass('rushmore.ingredients') IS NOT NULL THEN DROP TABLE rushmore.ingredients CASCADE; END IF;
  IF to_regclass('rushmore.customers') IS NOT NULL THEN DROP TABLE rushmore.customers CASCADE; END IF;
  IF to_regclass('rushmore.stores') IS NOT NULL THEN DROP TABLE rushmore.stores CASCADE; END IF;
END$$;

-- ======================
-- STORES
-- ======================
CREATE TABLE stores (
  store_id      SERIAL PRIMARY KEY,
  address       VARCHAR(255) NOT NULL,
  city          VARCHAR(100) NOT NULL,
  phone_number  VARCHAR(20)  NOT NULL UNIQUE,
  opened_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ======================
-- CUSTOMERS
-- ======================
CREATE TABLE customers (
  customer_id   SERIAL PRIMARY KEY,
  first_name    VARCHAR(100) NOT NULL,
  last_name     VARCHAR(100) NOT NULL,
  email         VARCHAR(255) NOT NULL UNIQUE,
  phone_number  VARCHAR(20)  NOT NULL UNIQUE,
  created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  -- light sanity checks (check constraint that ensures every email stored has an @ symbol after the first character)
  CONSTRAINT chk_email_has_at CHECK (POSITION('@' IN email) > 1)
);
-- ======================
-- INGREDIENTS (Inventory master,no negative stock levels, no nonsense data.)
-- ======================
CREATE TABLE ingredients (
  ingredient_id   SERIAL PRIMARY KEY,
  name            VARCHAR(100) NOT NULL UNIQUE,
  stock_quantity  NUMERIC(10,2) NOT NULL DEFAULT 0,
  unit            VARCHAR(20)  NOT NULL,
  CONSTRAINT chk_stock_nonnegative CHECK (stock_quantity >= 0)
);

-- ======================
-- MENU_ITEMS (Product catalog)
-- ======================
CREATE TABLE menu_items (
  item_id   SERIAL PRIMARY KEY,
  name      VARCHAR(150) NOT NULL,
  category  VARCHAR(50)  NOT NULL,         -- e.g., 'Pizza','Drink','Side'
  size      VARCHAR(20),                   -- e.g., 'Small','Medium','Large','500ml','N/A'
  price     NUMERIC(10,2) NOT NULL,
  CONSTRAINT chk_price_nonnegative CHECK (price >= 0),
  -- prevent accidental dupes across name/size/category
  CONSTRAINT uq_menuitem UNIQUE (name, category, size)
);

-- ======================
-- ITEM_INGREDIENTS (Recipe: Menu_Items -> Ingredients) M:N
-- ======================
CREATE TABLE item_ingredients (
  item_id            INTEGER NOT NULL REFERENCES menu_items(item_id) ON DELETE CASCADE,
  ingredient_id      INTEGER NOT NULL REFERENCES ingredients(ingredient_id) ON DELETE RESTRICT,
  quantity_required  NUMERIC(10,2) NOT NULL,
  CONSTRAINT pk_item_ingredients PRIMARY KEY (item_id, ingredient_id),
  CONSTRAINT chk_qty_required_positive CHECK (quantity_required > 0)
);

-- Helpful index for reverse lookups (ingredient -> items)performance optimazation
CREATE INDEX idx_item_ingredients_ingredient ON item_ingredients (ingredient_id);

-- ======================
-- ORDERS (Master transaction)
-- ======================
CREATE TABLE orders (
  order_id        SERIAL PRIMARY KEY,
  customer_id     INTEGER REFERENCES customers(customer_id) ON DELETE SET NULL,
  store_id        INTEGER NOT NULL REFERENCES stores(store_id) ON DELETE RESTRICT,
  order_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  total_amount    NUMERIC(10,2) NOT NULL,
  status          VARCHAR(50) NOT NULL DEFAULT 'Pending',
  CONSTRAINT chk_total_nonnegative CHECK (total_amount >= 0),
  CONSTRAINT chk_status_valid CHECK (status IN ('Pending','In Progress','Delivered','Cancelled'))
);

-- FK helper indexes (common best practice)
CREATE INDEX idx_orders_customer  ON orders (customer_id);
CREATE INDEX idx_orders_store     ON orders (store_id);
CREATE INDEX idx_orders_timestamp ON orders (order_timestamp);

-- ======================
-- ORDER_ITEMS (Order lines: Orders -> Menu_Items)
-- ======================
CREATE TABLE order_items (
  order_item_id            SERIAL PRIMARY KEY,
  order_id                 INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
  item_id                  INTEGER NOT NULL REFERENCES menu_items(item_id) ON DELETE RESTRICT,
  quantity                 INTEGER NOT NULL,
  price_at_time_of_order   NUMERIC(10,2) NOT NULL,
  CONSTRAINT chk_quantity_positive CHECK (quantity > 0),
  CONSTRAINT chk_price_at_time_nonnegative CHECK (price_at_time_of_order >= 0)
);

-- FK helper indexes
CREATE INDEX idx_order_items_order ON order_items (order_id);
CREATE INDEX idx_order_items_item  ON order_items (item_id);

-- Optional: computed helper view (nice for analytics quick start)
CREATE OR REPLACE VIEW v_order_items_expanded AS
SELECT
  oi.order_item_id,
  o.order_id,
  o.order_timestamp,
  o.status,
  o.store_id,
  o.customer_id,
  oi.item_id,
  mi.name        AS item_name,
  mi.category    AS item_category,
  mi.size        AS item_size,
  oi.quantity,
  oi.price_at_time_of_order,
  (oi.quantity * oi.price_at_time_of_order) AS line_total
FROM order_items oi
JOIN orders o      ON o.order_id = oi.order_id
JOIN menu_items mi ON mi.item_id = oi.item_id;