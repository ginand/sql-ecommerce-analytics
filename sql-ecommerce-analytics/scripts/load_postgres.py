# scripts/load_postgres.py
import os
from pathlib import Path
import psycopg

DATA_DIR = Path("data")
SCHEMA_FILE = Path("sql/00_schema.sql")

TABLE_FILES = [
    ("customers", "customers.csv"),
    ("categories", "categories.csv"),
    ("products", "products.csv"),
    ("orders", "orders.csv"),
    ("order_items", "order_items.csv"),
    ("payments", "payments.csv"),
    ("returns", "returns.csv"),
    ("return_items", "return_items.csv"),
]

def copy_csv(conn, table: str, csv_path: Path) -> None:
    """
    COPY FROM STDIN is fast and avoids server-side file permission issues.
    """
    with conn.cursor() as cur:
        sql = f"COPY {table} FROM STDIN WITH (FORMAT csv, HEADER true)"
        with csv_path.open("r", encoding="utf-8") as f:
            with cur.copy(sql) as copy:
                for line in f:
                    copy.write(line)

def reset_sequences(conn):
    """
    Because we import explicit IDs into IDENTITY BY DEFAULT columns,
    we must move the sequence forward to max(id)+1.
    Otherwise, future inserts may collide.
    """
    pairs = [
        ("customers","customer_id"),
        ("categories","category_id"),
        ("products","product_id"),
        ("orders","order_id"),
        ("order_items","order_item_id"),
        ("payments","payment_id"),
        ("returns","return_id"),
        ("return_items","return_item_id"),
    ]
    with conn.cursor() as cur:
        for table, col in pairs:
            cur.execute(f"""
                SELECT setval(
                    pg_get_serial_sequence(%s, %s),
                    COALESCE((SELECT MAX({col}) FROM {table}), 1)
                );
            """, (table, col))
    conn.commit()

def main():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise SystemExit(
            "Missing DATABASE_URL. Example:\n"
            '  postgresql://postgres:1@localhost:5432/da_portfolio'
        )

    if not SCHEMA_FILE.exists():
        raise SystemExit("Missing sql/00_schema.sql")

    for table, fname in TABLE_FILES:
        if not (DATA_DIR / fname).exists():
            raise SystemExit(f"Missing data file: {DATA_DIR/fname}")

    with psycopg.connect(dsn) as conn:
        # Apply schema (drops & recreates tables)
        conn.execute(SCHEMA_FILE.read_text(encoding="utf-8"))
        conn.commit()
        print("✅ Schema applied")

        # Load data in FK-safe order
        for table, fname in TABLE_FILES:
            path = DATA_DIR / fname
            copy_csv(conn, table, path)
            conn.commit()
            print(f"✅ Loaded {table}")

        reset_sequences(conn)
        print("✅ Sequences reset")
        print("🎉 Import complete")

if __name__ == "__main__":
    main()