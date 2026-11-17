DROP TABLE IF EXISTS deliveries, inventory_hourly, sales_daily, products, stores, suppliers CASCADE;

CREATE TABLE suppliers (
    supplier_id    INT PRIMARY KEY,
    supplier_name  TEXT,
    reliability    NUMERIC(3,2),
    avg_lead_days  INT
);

CREATE TABLE stores (
    store_id  INT PRIMARY KEY,
    city      TEXT
);

CREATE TABLE products (
    product_id         INT PRIMARY KEY,
    product_name       TEXT,
    unit_price         INT,
    base_daily_demand  INT,
    supplier_id        INT REFERENCES suppliers(supplier_id),
    reorder_level      INT
);

CREATE TABLE sales_daily (
    sale_date   DATE,
    store_id    INT REFERENCES stores(store_id),
    product_id  INT REFERENCES products(product_id),
    units_sold  INT
);

CREATE TABLE inventory_hourly (
    snapshot_time  TIMESTAMP,
    store_id       INT REFERENCES stores(store_id),
    product_id     INT REFERENCES products(product_id),
    stock_on_hand  INT
);

CREATE TABLE deliveries (
    delivery_id    INT PRIMARY KEY,
    supplier_id    INT REFERENCES suppliers(supplier_id),
    store_id       INT REFERENCES stores(store_id),
    product_id     INT REFERENCES products(product_id),
    quantity       INT,
    order_date     DATE,
    promised_date  DATE,
    actual_date    DATE,
    delay_days     INT);