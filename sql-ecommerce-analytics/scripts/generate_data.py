# scripts/generate_data.py
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# =========================
# CONFIG (tùy chỉnh tại đây)
# =========================
RANDOM_SEED = 42

START_DATE = datetime(2024, 1, 1, tzinfo=timezone.utc)
END_DATE   = datetime(2026, 1, 1, tzinfo=timezone.utc)

N_CUSTOMERS  = 8000
N_CATEGORIES = 12
N_PRODUCTS   = 600
N_ORDERS     = 120000

MAX_ITEMS_PER_ORDER = 6

CANCEL_RATE = 0.07               # % orders cancelled
RETURN_RATE_COMPLETED = 0.06     # % completed orders have return

CHANNEL_WEIGHTS = {"web": 0.45, "app": 0.55}

PAYMENT_METHOD_WEIGHTS = {"cod": 0.38, "card": 0.37, "wallet": 0.25}
PAYMENT_STATUS_WEIGHTS = {"captured": 0.93, "authorized": 0.05, "failed": 0.02}  # only for completed payments

CITIES = [
    "Ho Chi Minh City", "Ha Noi", "Da Nang", "Hai Phong", "Can Tho",
    "Nha Trang", "Hue", "Binh Duong", "Dong Nai", "Vung Tau"
]

CATEGORY_NAMES = [
    "Electronics", "Home", "Beauty", "Fashion", "Sports", "Books",
    "Toys", "Grocery", "Office", "Pet", "Health", "Automotive"
]

RETURN_REASONS = [
    "Damaged item", "Wrong size", "Not as described", "Late delivery",
    "Changed mind", "Missing parts"
]

OUT_DIR = Path("data")


# =========================
# Helpers
# =========================
def weighted_choice(weights: dict[str, float], size: int) -> np.ndarray:
    keys = np.array(list(weights.keys()))
    w = np.array(list(weights.values()), dtype=float)
    w = w / w.sum()
    idx = np.random.choice(len(keys), size=size, p=w)
    return keys[idx]

def random_datetimes(n: int, start: datetime, end: datetime) -> pd.Series:
    start_ts = start.timestamp()
    end_ts = end.timestamp()
    r = np.random.uniform(start_ts, end_ts, size=n)
    return pd.Series(pd.to_datetime(r, unit="s", utc=True))

def seasonality_multiplier(dt: pd.Series) -> np.ndarray:
    # Peak Q4 (Nov-Dec) and mild peak Sep-Oct; dip Jan-Feb
    month = dt.dt.month.to_numpy()
    mult = np.ones_like(month, dtype=float)
    mult += np.where(np.isin(month, [11, 12]), 0.25, 0.0)
    mult += np.where(np.isin(month, [9, 10]), 0.10, 0.0)
    mult += np.where(np.isin(month, [1, 2]), -0.05, 0.0)
    return mult

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# =========================
# Generators
# =========================
def make_customers() -> pd.DataFrame:
    customer_id = np.arange(1, N_CUSTOMERS + 1, dtype=np.int64)
    created_at = random_datetimes(N_CUSTOMERS, START_DATE, END_DATE - timedelta(days=60))

    first_names = ["An","Binh","Chi","Dung","Giang","Huy","Khanh","Linh","Minh","Nam","Phuc","Quang","Trang","Tuan","Vy"]
    last_names  = ["Nguyen","Tran","Le","Pham","Hoang","Phan","Vu","Vo","Dang","Bui","Do","Ngo"]
    full_name = [f"{random.choice(last_names)} {random.choice(first_names)}" for _ in range(N_CUSTOMERS)]

    email = [f"user{cid}@example.com" for cid in customer_id]
    city = np.random.choice(CITIES, size=N_CUSTOMERS, replace=True)

    # updated_at >= created_at
    updated_at = created_at + pd.to_timedelta(np.random.randint(0, 60*60*24*30, size=N_CUSTOMERS), unit="s")

    return pd.DataFrame({
        "customer_id": customer_id,
        "full_name": full_name,
        "email": email,
        "city": city,
        "created_at": created_at,
        "updated_at": updated_at
    })

def make_categories() -> pd.DataFrame:
    names = CATEGORY_NAMES[:N_CATEGORIES]
    category_id = np.arange(1, len(names) + 1, dtype=np.int64)
    created_at = pd.Timestamp(datetime(2024, 1, 1, tzinfo=timezone.utc))
    return pd.DataFrame({
        "category_id": category_id,
        "category_name": names,
        "created_at": [created_at] * len(names)
    })

def make_products(categories: pd.DataFrame) -> pd.DataFrame:
    product_id = np.arange(1, N_PRODUCTS + 1, dtype=np.int64)
    category_ids = categories["category_id"].to_numpy()
    category_id = np.random.choice(category_ids, size=N_PRODUCTS, replace=True)

    # Pricing realism: electronics more expensive
    cat_name_map = categories.set_index("category_id")["category_name"].to_dict()
    is_elec = np.array([cat_name_map[cid] == "Electronics" for cid in category_id], dtype=bool)

    base_cost = np.random.lognormal(mean=3.2, sigma=0.5, size=N_PRODUCTS)  # ~ 20-80
    unit_cost = base_cost * np.where(is_elec, 2.4, 1.0)

    margin = np.random.uniform(1.15, 1.6, size=N_PRODUCTS)
    list_price = unit_cost * margin

    sku = [f"SKU-{pid:06d}" for pid in product_id]
    product_name = [f"Product {pid:04d}" for pid in product_id]

    is_active = np.random.choice([True, True, True, False], size=N_PRODUCTS)  # ~25% inactive

    created_at = random_datetimes(N_PRODUCTS, START_DATE, START_DATE + timedelta(days=120))
    updated_at = created_at + pd.to_timedelta(np.random.randint(0, 60*60*24*180, size=N_PRODUCTS), unit="s")

    return pd.DataFrame({
        "product_id": product_id,
        "category_id": category_id.astype(np.int64),
        "sku": sku,
        "product_name": product_name,
        "unit_cost": np.round(unit_cost, 2),
        "list_price": np.round(list_price, 2),
        "is_active": is_active,
        "created_at": created_at,
        "updated_at": updated_at
    })

def make_orders(customers: pd.DataFrame) -> pd.DataFrame:
    order_id = np.arange(1, N_ORDERS + 1, dtype=np.int64)

    chosen_customers = np.random.choice(customers["customer_id"].to_numpy(), size=N_ORDERS, replace=True)
    order_date = random_datetimes(N_ORDERS, START_DATE, END_DATE)

    # seasonality affects cancel probability slightly
    mult = seasonality_multiplier(order_date)
    cancel_prob = np.clip(CANCEL_RATE / mult, 0.02, 0.15)
    status = np.where(np.random.rand(N_ORDERS) < cancel_prob, "cancelled", "completed")

    channel = weighted_choice(CHANNEL_WEIGHTS, N_ORDERS)

    shipping_fee = np.random.lognormal(mean=2.2, sigma=0.25, size=N_ORDERS)  # ~ 8-12
    shipping_fee = np.round(shipping_fee, 2)

    created_at = order_date + pd.to_timedelta(np.random.randint(0, 600, size=N_ORDERS), unit="s")
    updated_at = created_at + pd.to_timedelta(np.random.randint(0, 60*60*24*10, size=N_ORDERS), unit="s")

    # placeholder totals; will be filled after generating items
    df = pd.DataFrame({
        "order_id": order_id,
        "customer_id": chosen_customers.astype(np.int64),
        "order_date": order_date,
        "status": status,
        "channel": channel,
        "shipping_fee": shipping_fee,
        "items_subtotal": np.zeros(N_ORDERS, dtype=float),
        "discount_total": np.zeros(N_ORDERS, dtype=float),
        "order_total": np.zeros(N_ORDERS, dtype=float),
        "created_at": created_at,
        "updated_at": updated_at
    })
    return df

def make_order_items(orders: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    product_ids = products["product_id"].to_numpy()
    list_price_map = products.set_index("product_id")["list_price"].to_dict()

    order_ids = orders["order_id"].to_numpy()

    items_per_order = np.random.choice(
        np.arange(1, MAX_ITEMS_PER_ORDER + 1),
        size=len(order_ids),
        p=np.array([0.28, 0.26, 0.20, 0.14, 0.08, 0.04])
    )

    rows = []
    order_item_id = 1

    for oid, k in zip(order_ids, items_per_order):
        chosen = np.random.choice(product_ids, size=k, replace=False)

        for pid in chosen:
            qty = int(np.random.choice([1, 1, 1, 2, 2, 3], p=[0.38, 0.22, 0.12, 0.18, 0.07, 0.03]))

            base_price = float(list_price_map[pid])
            # snapshot unit price with small fluctuation
            unit_price = round(base_price * float(np.random.uniform(0.95, 1.05)), 2)

            line_gross = unit_price * qty
            # discount sometimes
            if np.random.rand() < 0.62:
                discount = 0.0
            else:
                discount = line_gross * float(np.random.uniform(0.03, 0.20))
            discount = round(discount, 2)

            # ensure discount <= line_gross (schema constraint)
            if discount > line_gross:
                discount = round(line_gross, 2)

            created_at = orders.loc[orders["order_id"] == oid, "created_at"].iloc[0]

            rows.append([
                order_item_id, int(oid), int(pid), qty,
                unit_price, discount, created_at
            ])
            order_item_id += 1

    return pd.DataFrame(rows, columns=[
        "order_item_id", "order_id", "product_id", "quantity",
        "unit_price", "discount_amount", "created_at"
    ])

def fill_order_totals(orders: pd.DataFrame, order_items: pd.DataFrame) -> pd.DataFrame:
    oi = order_items.copy()
    oi["line_subtotal"] = oi["quantity"] * oi["unit_price"]
    oi["line_net"] = oi["line_subtotal"] - oi["discount_amount"]

    agg = oi.groupby("order_id").agg(
        items_subtotal=("line_subtotal", "sum"),
        discount_total=("discount_amount", "sum"),
        items_net=("line_net", "sum")
    ).reset_index()

    merged = orders.merge(agg, on="order_id", how="left")
    merged["items_subtotal"] = merged["items_subtotal_y"].fillna(0.0)
    merged["discount_total"] = merged["discount_total_y"].fillna(0.0)

    # order_total = items_subtotal - discount_total + shipping_fee
    merged["order_total"] = (merged["items_subtotal"] - merged["discount_total"] + merged["shipping_fee"]).clip(lower=0.0)

    merged = merged.drop(columns=["items_subtotal_x", "discount_total_x", "items_subtotal_y", "discount_total_y", "items_net"])
    # keep numeric with 2 decimals
    merged["items_subtotal"] = np.round(merged["items_subtotal"].to_numpy(), 2)
    merged["discount_total"] = np.round(merged["discount_total"].to_numpy(), 2)
    merged["order_total"] = np.round(merged["order_total"].to_numpy(), 2)

    return merged

def make_payments(orders: pd.DataFrame) -> pd.DataFrame:
    completed = orders[orders["status"] == "completed"].copy()

    method = weighted_choice(PAYMENT_METHOD_WEIGHTS, len(completed))
    status = weighted_choice(PAYMENT_STATUS_WEIGHTS, len(completed))

    # For "failed", paid_amount should be 0 (realistic)
    paid_amount = completed["order_total"].to_numpy()
    paid_amount = np.where(status == "failed", 0.0, paid_amount)

    # paid_at within 5 min to 24h after order_date
    paid_at = completed["order_date"] + pd.to_timedelta(np.random.randint(300, 3600 * 24, size=len(completed)), unit="s")

    provider_txn_id = [f"TXN-{oid:010d}" if st != "failed" else None
                       for oid, st in zip(completed["order_id"].to_numpy(), status)]

    created_at = paid_at + pd.to_timedelta(np.random.randint(0, 120, size=len(completed)), unit="s")

    df = pd.DataFrame({
        "payment_id": np.arange(1, len(completed) + 1, dtype=np.int64),
        "order_id": completed["order_id"].to_numpy(dtype=np.int64),
        "method": method,
        "status": status,
        "paid_amount": np.round(paid_amount.astype(float), 2),
        "paid_at": paid_at,
        "provider_txn_id": provider_txn_id,
        "created_at": created_at
    })
    return df

def make_returns_and_items(
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
    payments: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:

    completed_orders = orders[orders["status"] == "completed"][["order_id", "order_date"]].copy()

    # only orders that are not failed payments (paid_amount > 0)
    paid_map = payments.set_index("order_id")["paid_amount"].to_dict()
    completed_orders["paid_amount"] = completed_orders["order_id"].map(paid_map).fillna(0.0)
    eligible = completed_orders[completed_orders["paid_amount"] > 0.0].copy()

    n_ret = int(len(eligible) * RETURN_RATE_COMPLETED)
    if n_ret <= 0:
        returns = pd.DataFrame(columns=[
            "return_id","order_id","status","return_date","reason","refund_amount","created_at"
        ])
        return_items = pd.DataFrame(columns=[
            "return_item_id","return_id","order_item_id","quantity","refund_amount"
        ])
        return returns, return_items

    ret_order_ids = np.random.choice(eligible["order_id"].to_numpy(), size=n_ret, replace=False)
    ret_base = eligible.set_index("order_id").loc[ret_order_ids].reset_index()

    # return date after 3-20 days
    return_date = ret_base["order_date"] + pd.to_timedelta(np.random.randint(3, 21, size=n_ret), unit="D")
    reason = np.random.choice(RETURN_REASONS, size=n_ret, replace=True)

    # For each returned order, choose some order_items to return (partial return)
    oi = order_items.set_index("order_id")
    return_rows = []
    return_item_rows = []
    return_id = 1
    return_item_id = 1

    for oid, rdate, rsn in zip(ret_order_ids, return_date, reason):
        paid_amt = float(paid_map.get(int(oid), 0.0))
        if paid_amt <= 0:
            continue

        order_oi = oi.loc[int(oid)]
        # if only one item returns as Series, normalize
        if isinstance(order_oi, pd.Series):
            order_oi = order_oi.to_frame().T

        # pick 1..min(3, n_items) lines to return
        n_lines = len(order_oi)
        k = int(np.random.randint(1, min(3, n_lines) + 1))
        chosen_lines = order_oi.sample(n=k, replace=False, random_state=np.random.randint(0, 10**9))

        # compute each line net value (qty*price - discount) for pro-rating refunds
        chosen_lines = chosen_lines.copy()
        chosen_lines["line_net"] = chosen_lines["quantity"] * chosen_lines["unit_price"] - chosen_lines["discount_amount"]
        chosen_lines["line_net"] = chosen_lines["line_net"].clip(lower=0.0)

        # decide total refund: between 30% and 100% of paid amount, but also <= sum(selected line net)
        selected_net = float(chosen_lines["line_net"].sum())
        target_refund = paid_amt * float(np.random.uniform(0.30, 1.00))
        target_refund = min(target_refund, selected_net if selected_net > 0 else paid_amt)
        target_refund = round(clamp(target_refund, 0.0, paid_amt), 2)

        # pro-rate line refunds
        if selected_net <= 0:
            # fallback: split evenly
            per_line = round(target_refund / k, 2)
            line_refunds = [per_line] * k
            # fix rounding remainder
            line_refunds[-1] = round(target_refund - per_line * (k - 1), 2)
        else:
            ratios = (chosen_lines["line_net"].astype(float).to_numpy(dtype=float) / float(selected_net))
            vals = (ratios * float(target_refund)).astype(float)

            line_refunds = np.around(vals, 2).tolist()

            diff = round(float(target_refund) - float(sum(line_refunds)), 2)
            line_refunds[-1] = round(float(line_refunds[-1]) + diff, 2)

        # build return header
        created_at = rdate + pd.to_timedelta(np.random.randint(0, 600), unit="s")
        return_rows.append([
            return_id,
            int(oid),
            "refunded",   # realistic final state
            rdate,
            rsn,
            target_refund,
            created_at
        ])

        # build return items
        for (idx, row), rf in zip(chosen_lines.iterrows(), line_refunds):
            oi_id = int(row["order_item_id"])
            max_qty = int(row["quantity"])
            # return quantity 1..max_qty
            ret_qty = int(np.random.randint(1, max_qty + 1))
            # refund line amount can't exceed proportional of rf (keep simple)
            refund_amt = round(clamp(float(rf), 0.0, float(rf)), 2)

            return_item_rows.append([
                return_item_id,
                return_id,
                oi_id,
                ret_qty,
                refund_amt
            ])
            return_item_id += 1

        return_id += 1

    returns = pd.DataFrame(return_rows, columns=[
        "return_id","order_id","status","return_date","reason","refund_amount","created_at"
    ])

    return_items = pd.DataFrame(return_item_rows, columns=[
        "return_item_id","return_id","order_item_id","quantity","refund_amount"
    ])

    return returns, return_items


# =========================
# Main
# =========================
def main() -> None:
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    customers = make_customers()
    categories = make_categories()
    products = make_products(categories)

    orders = make_orders(customers)
    order_items = make_order_items(orders, products)
    orders = fill_order_totals(orders, order_items)

    payments = make_payments(orders)
    returns, return_items = make_returns_and_items(orders, order_items, payments)

    # =========================
    # Write CSVs (match schema columns)
    # =========================
    customers.to_csv(OUT_DIR / "customers.csv", index=False)

    categories.to_csv(OUT_DIR / "categories.csv", index=False)

    products = products[[
        "product_id","category_id","sku","product_name","unit_cost","list_price",
        "is_active","created_at","updated_at"
    ]]
    products.to_csv(OUT_DIR / "products.csv", index=False)

    orders = orders[[
        "order_id","customer_id","order_date","status","channel",
        "shipping_fee","items_subtotal","discount_total","order_total",
        "created_at","updated_at"
    ]]
    orders.to_csv(OUT_DIR / "orders.csv", index=False)

    order_items = order_items[[
        "order_item_id","order_id","product_id","quantity","unit_price","discount_amount","created_at"
    ]]
    order_items.to_csv(OUT_DIR / "order_items.csv", index=False)

    payments = payments[[
        "payment_id","order_id","method","status","paid_amount","paid_at","provider_txn_id","created_at"
    ]]
    payments.to_csv(OUT_DIR / "payments.csv", index=False)

    returns = returns[[
        "return_id","order_id","status","return_date","reason","refund_amount","created_at"
    ]]
    returns.to_csv(OUT_DIR / "returns.csv", index=False)

    return_items = return_items[[
        "return_item_id","return_id","order_item_id","quantity","refund_amount"
    ]]
    return_items.to_csv(OUT_DIR / "return_items.csv", index=False)

    print("✅ Generated CSV files in ./data")
    print(f"customers:     {len(customers):,}")
    print(f"categories:    {len(categories):,}")
    print(f"products:      {len(products):,}")
    print(f"orders:        {len(orders):,}")
    print(f"order_items:   {len(order_items):,}")
    print(f"payments:      {len(payments):,}")
    print(f"returns:       {len(returns):,}")
    print(f"return_items:  {len(return_items):,}")

    # quick sanity hints
    completed = (orders["status"] == "completed").sum()
    cancelled = (orders["status"] == "cancelled").sum()
    print(f"completed orders: {completed:,} | cancelled orders: {cancelled:,}")

if __name__ == "__main__":
    main()