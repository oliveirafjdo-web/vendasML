import sqlite3
from pathlib import Path

DB_PATH = Path("vendas.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT,
            variable_cost REAL NOT NULL,
            default_price REAL NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            marketplace_fee REAL DEFAULT 0,
            shipping_cost REAL DEFAULT 0,
            other_variable_cost REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # tenta adicionar colunas novas se a tabela já existir sem elas
    cols_to_add = [
        ("marketplace_fee", "REAL DEFAULT 0"),
        ("shipping_cost", "REAL DEFAULT 0"),
        ("other_variable_cost", "REAL DEFAULT 0"),
        ("discount", "REAL DEFAULT 0"),
    ]
    for col, col_def in cols_to_add:
        try:
            cur.execute(f"ALTER TABLE sales ADD COLUMN {col} {col_def}")
        except Exception:
            pass

    conn.commit()
    conn.close()
