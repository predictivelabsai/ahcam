"""
Seed data loader — populate AHCAM tables from CSV files.

Creates a test user, then loads productions, stakeholders, accounts,
waterfall rules, transactions, and production-stakeholder links.

Run: python data/load_seed_data.py
"""

import os
import sys
import csv
import hashlib
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

engine = create_engine(os.getenv("DB_URL"))
DATA_DIR = Path(__file__).parent

TEST_EMAIL = "demo@ashlandhill.com"
TEST_PASSWORD = "demo1234"
TEST_NAME = "Demo User"


def read_csv(filename):
    with open(DATA_DIR / filename, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    print("=== AHCAM Seed Data Loader ===\n")

    with engine.connect() as conn:
        # ---------------------------------------------------------------
        # 1. Create test user
        # ---------------------------------------------------------------
        from utils.auth import hash_password
        pw_hash = hash_password(TEST_PASSWORD)

        row = conn.execute(text("""
            INSERT INTO ahcam.users (email, password_hash, display_name, role)
            VALUES (:email, :pw, :name, 'admin')
            ON CONFLICT (email) DO UPDATE SET display_name = :name
            RETURNING user_id
        """), {"email": TEST_EMAIL, "pw": pw_hash, "name": TEST_NAME}).fetchone()
        user_id = str(row[0])
        conn.commit()
        print(f"1. Test user: {TEST_EMAIL} / {TEST_PASSWORD}  (id: {user_id[:8]}...)")

        # ---------------------------------------------------------------
        # 2. Load productions
        # ---------------------------------------------------------------
        productions = read_csv("productions.csv")
        prod_map = {}  # title -> production_id
        for p in productions:
            budget = float(p["budget"]) if p["budget"] else None
            row = conn.execute(text("""
                INSERT INTO ahcam.productions
                    (title, project_type, genre, status, budget, currency,
                     producer, director, cast_summary, synopsis, territory, created_by)
                VALUES (:title, :ptype, :genre, :status, :budget, :currency,
                        :producer, :director, :cast, :synopsis, :territory, :uid)
                ON CONFLICT DO NOTHING
                RETURNING production_id
            """), {
                "title": p["title"], "ptype": p["project_type"], "genre": p["genre"],
                "status": p["status"], "budget": budget, "currency": p["currency"],
                "producer": p["producer"] or None, "director": p["director"] or None,
                "cast": p["cast_summary"] or None, "synopsis": p["synopsis"] or None,
                "territory": p["territory"] or None, "uid": user_id,
            }).fetchone()
            if row:
                prod_map[p["title"]] = str(row[0])
        conn.commit()

        # If productions already existed, fetch their IDs
        if len(prod_map) < len(productions):
            existing = conn.execute(text("SELECT production_id, title FROM ahcam.productions")).fetchall()
            for r in existing:
                prod_map[r[1]] = str(r[0])

        print(f"2. Productions: {len(prod_map)} loaded")

        # ---------------------------------------------------------------
        # 3. Load stakeholders
        # ---------------------------------------------------------------
        stakeholders = read_csv("stakeholders.csv")
        stake_map = {}  # name -> stakeholder_id
        for s in stakeholders:
            row = conn.execute(text("""
                INSERT INTO ahcam.stakeholders
                    (name, role, company, email, phone, created_by)
                VALUES (:name, :role, :company, :email, :phone, :uid)
                ON CONFLICT DO NOTHING
                RETURNING stakeholder_id
            """), {
                "name": s["name"], "role": s["role"],
                "company": s["company"] or None, "email": s["email"] or None,
                "phone": s["phone"] or None, "uid": user_id,
            }).fetchone()
            if row:
                stake_map[s["name"]] = str(row[0])
        conn.commit()

        if len(stake_map) < len(stakeholders):
            existing = conn.execute(text("SELECT stakeholder_id, name FROM ahcam.stakeholders")).fetchall()
            for r in existing:
                stake_map[r[1]] = str(r[0])

        print(f"3. Stakeholders: {len(stake_map)} loaded")

        # ---------------------------------------------------------------
        # 4. Load collection accounts
        # ---------------------------------------------------------------
        accounts = read_csv("collection_accounts.csv")
        acct_map = {}  # production_title -> account_id
        for a in accounts:
            pid = prod_map.get(a["production_title"])
            if not pid:
                continue
            balance = float(a["balance"]) if a["balance"] else 0
            row = conn.execute(text("""
                INSERT INTO ahcam.collection_accounts
                    (production_id, account_name, bank_name, balance, currency, status, created_by)
                VALUES (:pid, :name, :bank, :bal, :currency, :status, :uid)
                ON CONFLICT DO NOTHING
                RETURNING account_id
            """), {
                "pid": pid, "name": a["account_name"], "bank": a["bank_name"],
                "bal": balance, "currency": a["currency"], "status": a["status"],
                "uid": user_id,
            }).fetchone()
            if row:
                acct_map[a["production_title"]] = str(row[0])
        conn.commit()

        if len(acct_map) < len(accounts):
            existing = conn.execute(text("""
                SELECT a.account_id, p.title
                FROM ahcam.collection_accounts a
                JOIN ahcam.productions p ON p.production_id = a.production_id
            """)).fetchall()
            for r in existing:
                acct_map[r[1]] = str(r[0])

        print(f"4. Collection accounts: {len(acct_map)} loaded")

        # ---------------------------------------------------------------
        # 5. Load waterfall rules
        # ---------------------------------------------------------------
        rules = read_csv("waterfall_rules.csv")
        rule_count = 0
        for r in rules:
            pid = prod_map.get(r["production_title"])
            sid = stake_map.get(r["recipient_name"]) if r["recipient_name"] else None
            if not pid:
                continue
            pct = float(r["percentage"]) if r["percentage"] else None
            cap = float(r["cap"]) if r["cap"] else None
            conn.execute(text("""
                INSERT INTO ahcam.waterfall_rules
                    (production_id, priority, recipient_stakeholder_id, recipient_label,
                     rule_type, percentage, cap, description)
                VALUES (:pid, :pri, :sid, :label, :rtype, :pct, :cap, :desc)
            """), {
                "pid": pid, "pri": int(r["priority"]),
                "sid": sid, "label": r["recipient_label"],
                "rtype": r["rule_type"], "pct": pct, "cap": cap,
                "desc": r["description"] or None,
            })
            rule_count += 1
        conn.commit()
        print(f"5. Waterfall rules: {rule_count} loaded")

        # ---------------------------------------------------------------
        # 6. Load transactions (with hash chain)
        # ---------------------------------------------------------------
        txns = read_csv("transactions.csv")
        txn_count = 0
        # Track last hash per account for chaining
        last_hash = {}  # account_id -> hash

        for t in txns:
            acct_id = acct_map.get(t["production_title"])
            src_id = stake_map.get(t["source_name"]) if t["source_name"] else None
            if not acct_id:
                continue

            import uuid
            txn_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            prev_hash = last_hash.get(acct_id, "GENESIS")
            amount = float(t["amount"])
            txn_hash = hashlib.sha256(f"{txn_id}|{amount}|{now}|{prev_hash}".encode()).hexdigest()

            conn.execute(text("""
                INSERT INTO ahcam.transactions
                    (transaction_id, account_id, transaction_type, amount, currency,
                     source_stakeholder_id, description, reference,
                     status, previous_hash, hash, created_by)
                VALUES (:tid, :aid, :ttype, :amount, 'USD',
                        :src, :desc, :ref,
                        'confirmed', :prev, :hash, :uid)
            """), {
                "tid": txn_id, "aid": acct_id, "ttype": t["transaction_type"],
                "amount": amount, "src": src_id,
                "desc": t["description"], "ref": t["reference"],
                "prev": prev_hash, "hash": txn_hash, "uid": user_id,
            })
            last_hash[acct_id] = txn_hash
            txn_count += 1
        conn.commit()
        print(f"6. Transactions: {txn_count} loaded")

        # ---------------------------------------------------------------
        # 7. Load production-stakeholder links
        # ---------------------------------------------------------------
        links = read_csv("production_stakeholders.csv")
        link_count = 0
        for l in links:
            pid = prod_map.get(l["production_title"])
            sid = stake_map.get(l["stakeholder_name"])
            if not pid or not sid:
                continue
            pct = float(l["participation_percentage"]) if l["participation_percentage"] else 0
            conn.execute(text("""
                INSERT INTO ahcam.production_stakeholders
                    (production_id, stakeholder_id, role_in_production, participation_percentage)
                VALUES (:pid, :sid, :role, :pct)
                ON CONFLICT (production_id, stakeholder_id) DO NOTHING
            """), {"pid": pid, "sid": sid, "role": l["role_in_production"], "pct": pct})
            link_count += 1
        conn.commit()
        print(f"7. Production-stakeholder links: {link_count} loaded")

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------
    print(f"\n{'='*45}")
    print(f"Seed data loaded successfully!")
    print(f"Login: {TEST_EMAIL} / {TEST_PASSWORD}")
    print(f"{'='*45}")


if __name__ == "__main__":
    main()
