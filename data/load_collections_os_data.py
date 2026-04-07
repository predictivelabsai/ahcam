"""
Collections OS seed data loader — populates new tables for Phases 1-5.

Loads: distribution_agreements, beneficiary_bank_accounts, territory_avails,
       collection_statements, title_groups, shared_documents, production_comments,
       user_favorites, user_recent_views.

Also updates existing transactions with territory/distributor data.

Run: python data/load_collections_os_data.py
"""

import os
import sys
import uuid
import random
from pathlib import Path
from datetime import datetime, date, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

engine = create_engine(os.getenv("DB_URL"))


def main():
    print("=== Collections OS Seed Data Loader ===\n")

    with engine.connect() as conn:
        # ---------------------------------------------------------------
        # Get existing data references
        # ---------------------------------------------------------------
        productions = conn.execute(text(
            "SELECT production_id, title, budget, currency FROM ahcam.productions ORDER BY title"
        )).fetchall()
        prod_map = {str(r[0]): r[1] for r in productions}
        prod_ids = [str(r[0]) for r in productions]

        stakeholders = conn.execute(text(
            "SELECT stakeholder_id, name, role FROM ahcam.stakeholders ORDER BY name"
        )).fetchall()
        stake_map = {str(r[0]): (r[1], r[2]) for r in stakeholders}
        distributors = [str(r[0]) for r in stakeholders if r[2] in ('distributor', 'sales_agent')]
        financiers = [str(r[0]) for r in stakeholders if r[2] == 'financier']

        users = conn.execute(text("SELECT user_id FROM ahcam.users LIMIT 1")).fetchone()
        user_id = str(users[0]) if users else None

        accounts = conn.execute(text(
            "SELECT account_id, production_id FROM ahcam.collection_accounts"
        )).fetchall()
        acct_map = {str(r[1]): str(r[0]) for r in accounts}

        print(f"  Found {len(prod_ids)} productions, {len(distributors)} distributors, {len(financiers)} financiers")

        # ---------------------------------------------------------------
        # 1. Distribution Agreements (80+ agreements across productions)
        # ---------------------------------------------------------------
        territories = [
            "Domestic (US/Canada)", "UK", "Germany", "France", "Italy", "Spain",
            "Scandinavia", "Benelux", "Australia/NZ", "Japan", "South Korea",
            "China", "Latin America", "Middle East", "Eastern Europe",
            "India", "Southeast Asia",
        ]
        distributor_names = [
            "StudioCanal", "Wild Bunch", "TF1 Studio", "Pathé International",
            "Toho International", "CJ Entertainment", "Huanxi Media", "Zee Studios",
            "Lionsgate International", "eOne Films", "FilmNation", "A24 International",
            "Neon Films", "Magnolia Pictures", "IFC Films", "Mubi Distribution",
            "Altitude Film Distribution", "Vertigo Films", "Protagonist Pictures",
            "MK2 Films", "Beta Cinema", "The Match Factory", "Memento Films",
            "Plaion Pictures", "Koch Films", "Weltkino", "Leonine Distribution",
        ]

        agreement_count = 0
        agreement_ids = []
        for pid in prod_ids:
            # Each production gets 4-10 territory agreements
            n_agreements = random.randint(4, 10)
            chosen_territories = random.sample(territories, min(n_agreements, len(territories)))
            for territory in chosen_territories:
                dist_name = random.choice(distributor_names)
                dist_sid = random.choice(distributors) if distributors else None
                mg = random.choice([50000, 100000, 150000, 250000, 500000, 750000, 1000000, 1500000, 2000000, 3000000])
                mg_paid = round(mg * random.choice([0, 0.25, 0.5, 0.75, 1.0]), 2)
                sig_date = date(2024, random.randint(1, 12), random.randint(1, 28))
                term = random.choice([3, 5, 7, 10, 15])
                start_date = sig_date + timedelta(days=random.randint(30, 180))
                expiry_date = start_date + timedelta(days=365 * term)
                expired = expiry_date < date.today()
                status = "paid" if mg_paid >= mg else "partial" if mg_paid > 0 else "pending"

                row = conn.execute(text("""
                    INSERT INTO ahcam.distribution_agreements
                        (production_id, distributor_stakeholder_id, territory, distributor_name,
                         agreement_type, signature_date, term_years, start_date, expiry_date,
                         expired, mg_amount, mg_currency, mg_paid, contract_available,
                         financial_status, notes, created_by)
                    VALUES (:pid, :dsid, :territory, :dname,
                            'distribution', :sig, :term, :start, :expiry,
                            :expired, :mg, 'USD', :mg_paid, :contract,
                            :status, :notes, :uid)
                    RETURNING agreement_id
                """), {
                    "pid": pid, "dsid": dist_sid, "territory": territory, "dname": dist_name,
                    "sig": sig_date, "term": term, "start": start_date, "expiry": expiry_date,
                    "expired": expired, "mg": mg, "mg_paid": mg_paid,
                    "contract": random.choice([True, True, True, False]),
                    "status": status,
                    "notes": f"{dist_name} distribution deal for {territory}" if random.random() > 0.5 else None,
                    "uid": user_id,
                }).fetchone()
                if row:
                    agreement_ids.append(str(row[0]))
                agreement_count += 1

        conn.commit()
        print(f"1. Distribution agreements: {agreement_count} loaded")

        # ---------------------------------------------------------------
        # 2. Beneficiary Bank Accounts (2-4 per production)
        # ---------------------------------------------------------------
        banks = [
            ("JPMorgan Chase", "270 Park Avenue, New York, NY 10017", "CHASUS33"),
            ("Barclays Bank", "1 Churchill Place, London E14 5HP", "BARCGB22"),
            ("Deutsche Bank", "Taunusanlage 12, 60325 Frankfurt", "DEUTDEFF"),
            ("BNP Paribas", "16 Boulevard des Italiens, 75009 Paris", "BNPAFRPP"),
            ("HSBC Holdings", "8 Canada Square, London E14 5HQ", "MIDLGB22"),
            ("Credit Suisse", "Paradeplatz 8, 8001 Zurich", "CRESCHZZ"),
            ("Mizuho Bank", "1-5-5 Otemachi, Chiyoda, Tokyo", "MHCBJPJT"),
            ("Standard Chartered", "1 Basinghall Avenue, London EC2V 5DD", "SCBLGB2L"),
        ]
        currencies = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY"]

        bank_count = 0
        for pid in prod_ids:
            n_banks = random.randint(2, 4)
            used_banks = random.sample(banks, min(n_banks, len(banks)))
            for bank_name, bank_addr, swift in used_banks:
                sid = random.choice(list(stake_map.keys()))
                beneficiary = stake_map[sid][0]
                acct_num = f"{random.randint(10000000, 99999999)}{random.randint(1000, 9999)}"
                iban = f"GB{random.randint(10, 99)}MIDL{random.randint(10000000, 99999999)}{random.randint(10000000, 99999999)}"
                aba = f"0{random.randint(10000000, 99999999)}"

                conn.execute(text("""
                    INSERT INTO ahcam.beneficiary_bank_accounts
                        (production_id, stakeholder_id, beneficiary_name, bank_name, bank_address,
                         aba_routing_encrypted, account_number_encrypted, iban_encrypted,
                         swift_bic, currency, status, created_by)
                    VALUES (:pid, :sid, :name, :bank, :addr,
                            :aba, :acct, :iban, :swift, :currency, :status, :uid)
                """), {
                    "pid": pid, "sid": sid, "name": beneficiary,
                    "bank": bank_name, "addr": bank_addr,
                    "aba": aba, "acct": acct_num, "iban": iban,
                    "swift": swift, "currency": random.choice(currencies),
                    "status": random.choice(["active", "active", "active", "pending_verification", "verified"]),
                    "uid": user_id,
                })
                bank_count += 1

        conn.commit()
        print(f"2. Bank accounts: {bank_count} loaded")

        # ---------------------------------------------------------------
        # 3. Territory Avails (mark territories as sold or available)
        # ---------------------------------------------------------------
        all_territories = [
            "Domestic (US/Canada)", "UK", "Ireland", "Germany", "France", "Italy",
            "Spain", "Scandinavia", "Benelux", "Australia/NZ", "Japan",
            "South Korea", "China", "India", "Southeast Asia", "Latin America",
            "Brazil", "Mexico", "Middle East", "Africa", "Eastern Europe",
            "Greece", "Turkey",
        ]
        rights_types = ["all_rights", "theatrical", "streaming", "tv", "home_video"]

        avail_count = 0
        for pid in prod_ids:
            # Get which territories have agreements for this production
            sold = conn.execute(text("""
                SELECT DISTINCT territory FROM ahcam.distribution_agreements WHERE production_id = :pid
            """), {"pid": pid}).fetchall()
            sold_territories = {r[0] for r in sold}

            for territory in all_territories:
                available = territory not in sold_territories
                # Find agreement_id if sold
                aid = None
                if not available:
                    aid_row = conn.execute(text("""
                        SELECT agreement_id FROM ahcam.distribution_agreements
                        WHERE production_id = :pid AND territory = :t LIMIT 1
                    """), {"pid": pid, "t": territory}).fetchone()
                    aid = str(aid_row[0]) if aid_row else None

                conn.execute(text("""
                    INSERT INTO ahcam.territory_avails
                        (production_id, territory, rights_type, available, agreement_id)
                    VALUES (:pid, :territory, 'all_rights', :available, :aid)
                    ON CONFLICT (production_id, territory, rights_type) DO NOTHING
                """), {
                    "pid": pid, "territory": territory,
                    "available": available, "aid": aid,
                })
                avail_count += 1

        conn.commit()
        print(f"3. Territory avails: {avail_count} loaded")

        # ---------------------------------------------------------------
        # 4. Update existing transactions with territory + distributor
        # ---------------------------------------------------------------
        txns = conn.execute(text("""
            SELECT t.transaction_id, t.account_id, ca.production_id
            FROM ahcam.transactions t
            JOIN ahcam.collection_accounts ca ON ca.account_id = t.account_id
            WHERE t.territory IS NULL
        """)).fetchall()

        txn_update_count = 0
        for txn in txns:
            pid = str(txn[2])
            # Get a random territory from this production's agreements
            da = conn.execute(text("""
                SELECT territory, distributor_name FROM ahcam.distribution_agreements
                WHERE production_id = :pid ORDER BY RANDOM() LIMIT 1
            """), {"pid": pid}).fetchone()

            if da:
                territory, dist_name = da[0], da[1]
            else:
                territory = random.choice(territories)
                dist_name = random.choice(distributor_names)

            pdate = date(2025, random.randint(1, 12), random.randint(1, 28))
            conn.execute(text("""
                UPDATE ahcam.transactions
                SET territory = :territory, distributor_name = :dname,
                    payment_date = :pdate, reported = :reported
                WHERE transaction_id = :tid
            """), {
                "territory": territory, "dname": dist_name,
                "pdate": pdate, "reported": random.choice([True, True, False]),
                "tid": str(txn[0]),
            })
            txn_update_count += 1

        conn.commit()
        print(f"4. Transactions updated with territory data: {txn_update_count}")

        # ---------------------------------------------------------------
        # 5. Collection Statements (2-5 per production)
        # ---------------------------------------------------------------
        account_managers = [
            "David Tompa", "Sarah Mitchell", "James Blackwood",
            "Elena Kowalski", "Marcus Chen", "Isabelle Rousseau",
        ]
        statement_count = 0
        for pid in prod_ids:
            title = prod_map[pid]
            n_stmts = random.randint(2, 5)
            for i in range(n_stmts):
                period_start = date(2024 + (i // 4), ((i * 3) % 12) + 1, 1)
                period_end = period_start + timedelta(days=89)
                issued = period_end + timedelta(days=random.randint(5, 30))
                payment = issued + timedelta(days=random.randint(15, 45))
                next_due = payment + timedelta(days=90)
                status = "paid" if payment < date.today() else "issued" if issued < date.today() else "draft"

                conn.execute(text("""
                    INSERT INTO ahcam.collection_statements
                        (production_id, statement_name, period_start, period_end,
                         issued_date, payment_date, next_due_date, status,
                         account_manager, content, created_by)
                    VALUES (:pid, :name, :pstart, :pend,
                            :issued, :payment, :next_due, :status,
                            :mgr, :content, :uid)
                """), {
                    "pid": pid,
                    "name": f"{title} — Q{(i % 4) + 1} {2024 + (i // 4)} Collection Statement",
                    "pstart": period_start, "pend": period_end,
                    "issued": issued, "payment": payment,
                    "next_due": next_due, "status": status,
                    "mgr": random.choice(account_managers),
                    "content": f'{{"total_collected": {random.randint(50000, 5000000)}, "total_disbursed": {random.randint(20000, 3000000)}, "net_balance": {random.randint(10000, 2000000)}, "territories_reported": {random.randint(3, 12)}}}',
                    "uid": user_id,
                })
                statement_count += 1

        conn.commit()
        print(f"5. Collection statements: {statement_count} loaded")

        # ---------------------------------------------------------------
        # 6. Title Groups (5 groups)
        # ---------------------------------------------------------------
        groups = [
            ("Slate A — 2024 Theatrical", "High-budget theatrical releases for 2024 distribution window", 4),
            ("European Co-Productions", "EU-funded co-productions with European distribution", 3),
            ("Streaming Originals", "Titles with primary streaming distribution deals", 3),
            ("Horror & Genre Package", "Genre titles bundled for territory sales", 2),
            ("Award Season Contenders", "Titles targeting festival/awards circuit", 4),
        ]
        group_count = 0
        for gname, comment, n_titles in groups:
            row = conn.execute(text("""
                INSERT INTO ahcam.title_groups (group_name, comment, created_by)
                VALUES (:name, :comment, :uid) RETURNING group_id
            """), {"name": gname, "comment": comment, "uid": user_id}).fetchone()

            if row:
                gid = str(row[0])
                chosen = random.sample(prod_ids, min(n_titles, len(prod_ids)))
                for pid in chosen:
                    conn.execute(text("""
                        INSERT INTO ahcam.title_group_members (group_id, production_id)
                        VALUES (:gid, :pid) ON CONFLICT DO NOTHING
                    """), {"gid": gid, "pid": pid})
                group_count += 1

        conn.commit()
        print(f"6. Title groups: {group_count} groups with members loaded")

        # ---------------------------------------------------------------
        # 7. Shared Documents (8 documents)
        # ---------------------------------------------------------------
        docs = [
            ("CAMA — Slate A Master Agreement", "Master CAMA covering all Slate A titles", 3),
            ("Interparty Agreement — European Co-Pro", "IP agreement between EU co-production partners", 2),
            ("Bank Verification Letter — JPMorgan", "Bank confirmation for primary collection account", 1),
            ("Completion Bond — Northstar", "Completion guarantee certificate", 2),
            ("Audit Report Q4 2025", "External audit of collection accounts for Q4 2025", 4),
            ("Tax Certificate — UK Production", "HMRC tax relief qualification certificate", 1),
            ("Insurance Certificate — Fireman's Fund", "E&O and production insurance confirmation", 2),
            ("Chain of Title — The Last Horizon", "Complete chain of title documentation", 1),
        ]
        doc_count = 0
        for dname, comment, n_titles in docs:
            row = conn.execute(text("""
                INSERT INTO ahcam.shared_documents (document_name, comment, uploaded_by)
                VALUES (:name, :comment, :uid) RETURNING doc_id
            """), {"name": dname, "comment": comment, "uid": user_id}).fetchone()

            if row:
                did = str(row[0])
                chosen = random.sample(prod_ids, min(n_titles, len(prod_ids)))
                for pid in chosen:
                    conn.execute(text("""
                        INSERT INTO ahcam.shared_document_titles (doc_id, production_id)
                        VALUES (:did, :pid) ON CONFLICT DO NOTHING
                    """), {"did": did, "pid": pid})

                # Add permissions for some stakeholders
                for sid in random.sample(list(stake_map.keys()), min(3, len(stake_map))):
                    conn.execute(text("""
                        INSERT INTO ahcam.shared_document_permissions (doc_id, stakeholder_id, permission)
                        VALUES (:did, :sid, :perm) ON CONFLICT DO NOTHING
                    """), {"did": did, "sid": sid, "perm": random.choice(["view", "download"])})

                doc_count += 1

        conn.commit()
        print(f"7. Shared documents: {doc_count} with permissions loaded")

        # ---------------------------------------------------------------
        # 8. Production Comments (3-8 per production)
        # ---------------------------------------------------------------
        comment_templates = [
            "Distributor payment received for {territory}. Processing through waterfall.",
            "MG advance from {distributor} confirmed. Updating recoupment tracker.",
            "Statement for Q{q} {year} has been issued to all stakeholders.",
            "Anomaly flagged: duplicate payment entry for {territory}. Under review.",
            "Contract amendment signed — new MG terms for {territory}.",
            "Sales agent reporting delay for {territory}. Follow up scheduled.",
            "Revenue forecast updated based on latest box office data.",
            "Bank details verified for {beneficiary}. Ready for disbursement.",
            "Waterfall rules updated per amendment #3 to CAMA.",
            "Collection account reconciliation completed. All balances confirmed.",
            "New distribution agreement executed for {territory} with {distributor}.",
            "Residual payments calculated and queued for approval.",
            "Audit committee review scheduled for next month.",
            "Tax withholding certificate received from {territory} distributor.",
            "Cross-collateralization adjustment applied across slate titles.",
        ]
        comment_count = 0
        for pid in prod_ids:
            n_comments = random.randint(3, 8)
            for i in range(n_comments):
                template = random.choice(comment_templates)
                content = template.format(
                    territory=random.choice(territories),
                    distributor=random.choice(distributor_names),
                    q=random.randint(1, 4),
                    year=random.choice([2024, 2025, 2026]),
                    beneficiary=random.choice(list(stake_map.values()))[0],
                )
                days_ago = random.randint(0, 365)
                conn.execute(text("""
                    INSERT INTO ahcam.production_comments (production_id, user_id, content, created_at)
                    VALUES (:pid, :uid, :content, NOW() - INTERVAL ':days days')
                """.replace(":days days", f"{days_ago} days")), {
                    "pid": pid, "uid": user_id, "content": content,
                })
                comment_count += 1

        conn.commit()
        print(f"8. Production comments: {comment_count} loaded")

        # ---------------------------------------------------------------
        # 9. User Favorites + Recent Views
        # ---------------------------------------------------------------
        if user_id:
            # Favorite 5 random productions
            fav_prods = random.sample(prod_ids, min(5, len(prod_ids)))
            for pid in fav_prods:
                conn.execute(text("""
                    INSERT INTO ahcam.user_favorites (user_id, entity_type, entity_id)
                    VALUES (:uid, 'production', :eid) ON CONFLICT DO NOTHING
                """), {"uid": user_id, "eid": pid})

            # Favorite 3 random stakeholders
            fav_stakes = random.sample(list(stake_map.keys()), min(3, len(stake_map)))
            for sid in fav_stakes:
                conn.execute(text("""
                    INSERT INTO ahcam.user_favorites (user_id, entity_type, entity_id)
                    VALUES (:uid, 'stakeholder', :eid) ON CONFLICT DO NOTHING
                """), {"uid": user_id, "eid": sid})

            # Recent views (15 entries)
            for _ in range(15):
                etype = random.choice(["production", "stakeholder", "agreement"])
                if etype == "production":
                    eid = random.choice(prod_ids)
                    etitle = prod_map[eid]
                elif etype == "stakeholder":
                    eid = random.choice(list(stake_map.keys()))
                    etitle = stake_map[eid][0]
                else:
                    if agreement_ids:
                        eid = random.choice(agreement_ids)
                        etitle = f"Distribution Agreement"
                    else:
                        continue
                days_ago = random.randint(0, 30)
                conn.execute(text("""
                    INSERT INTO ahcam.user_recent_views (user_id, entity_type, entity_id, entity_title, viewed_at)
                    VALUES (:uid, :etype, :eid, :etitle, NOW() - INTERVAL ':days days')
                """.replace(":days days", f"{days_ago} days")), {
                    "uid": user_id, "etype": etype, "eid": eid, "etitle": etitle,
                })

            conn.commit()
            print(f"9. Favorites: {len(fav_prods) + len(fav_stakes)}, Recent views: 15 loaded")

        # ---------------------------------------------------------------
        # 10. Recoupment Positions (update based on waterfall rules)
        # ---------------------------------------------------------------
        recoup_count = 0
        for pid in prod_ids:
            rules = conn.execute(text("""
                SELECT r.rule_id, r.recipient_stakeholder_id, r.percentage, r.cap, r.recipient_label
                FROM ahcam.waterfall_rules r
                WHERE r.production_id = :pid AND r.active = TRUE
            """), {"pid": pid}).fetchall()

            # Get total inflows for this production
            inflow_row = conn.execute(text("""
                SELECT COALESCE(SUM(t.amount), 0)
                FROM ahcam.transactions t
                JOIN ahcam.collection_accounts ca ON ca.account_id = t.account_id
                WHERE ca.production_id = :pid AND t.transaction_type = 'inflow'
            """), {"pid": pid}).fetchone()
            total_inflows = float(inflow_row[0]) if inflow_row else 0

            for rule in rules:
                sid = rule[1]
                if not sid:
                    continue
                pct = float(rule[2]) if rule[2] else 0
                cap = float(rule[3]) if rule[3] else None
                total_owed = total_inflows * (pct / 100)
                if cap:
                    total_owed = min(total_owed, cap)
                received = round(total_owed * random.choice([0.3, 0.5, 0.7, 0.85, 1.0]), 2)
                outstanding = round(total_owed - received, 2)

                conn.execute(text("""
                    INSERT INTO ahcam.recoupment_positions
                        (production_id, stakeholder_id, total_owed, total_received, outstanding, last_calculated)
                    VALUES (:pid, :sid, :owed, :received, :outstanding, NOW())
                    ON CONFLICT DO NOTHING
                """), {
                    "pid": pid, "sid": str(sid),
                    "owed": round(total_owed, 2), "received": received, "outstanding": outstanding,
                })
                recoup_count += 1

        conn.commit()
        print(f"10. Recoupment positions: {recoup_count} loaded")

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------
    print(f"\n{'='*50}")
    print(f"Collections OS seed data loaded successfully!")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
