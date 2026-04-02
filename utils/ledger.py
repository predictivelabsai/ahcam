"""
Immutable transaction ledger with SHA-256 hash chain.

Every transaction is hash-chained: hash = SHA-256(transaction_id + amount + timestamp + previous_hash).
Reversals create new offsetting transactions — no updates or deletes.
"""

import hashlib
import logging
from datetime import datetime, timezone

from sqlalchemy import text

from utils.db import get_pool

logger = logging.getLogger(__name__)


def compute_hash(transaction_id: str, amount: float, timestamp: str, previous_hash: str) -> str:
    """Compute SHA-256 hash for a transaction in the chain."""
    data = f"{transaction_id}|{amount}|{timestamp}|{previous_hash}"
    return hashlib.sha256(data.encode()).hexdigest()


def get_latest_hash(account_id: str) -> str:
    """Get the hash of the most recent transaction for an account."""
    pool = get_pool()
    with pool.get_session() as session:
        row = session.execute(text("""
            SELECT hash FROM ahcam.transactions
            WHERE account_id = :aid
            ORDER BY created_at DESC LIMIT 1
        """), {"aid": account_id}).fetchone()
    return row[0] if row else "GENESIS"


def record_transaction(
    account_id: str,
    transaction_type: str,
    amount: float,
    description: str,
    source_stakeholder_id: str = None,
    destination_stakeholder_id: str = None,
    reference: str = None,
    metadata: dict = None,
    created_by: str = None,
) -> dict:
    """Record an immutable, hash-chained transaction."""
    import uuid

    pool = get_pool()
    txn_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    previous_hash = get_latest_hash(account_id)
    txn_hash = compute_hash(txn_id, amount, now, previous_hash)

    with pool.get_session() as session:
        session.execute(text("""
            INSERT INTO ahcam.transactions
                (transaction_id, account_id, transaction_type, amount, currency,
                 source_stakeholder_id, destination_stakeholder_id,
                 reference, description, status, previous_hash, hash, metadata, created_by)
            VALUES
                (:tid, :aid, :ttype, :amount, 'USD',
                 :src, :dst, :ref, :desc, 'confirmed',
                 :prev_hash, :hash, :meta::jsonb, :created_by)
        """), {
            "tid": txn_id, "aid": account_id, "ttype": transaction_type,
            "amount": amount, "src": source_stakeholder_id,
            "dst": destination_stakeholder_id, "ref": reference,
            "desc": description, "prev_hash": previous_hash,
            "hash": txn_hash, "meta": str(metadata) if metadata else None,
            "created_by": created_by,
        })

        # Update account balance
        if transaction_type == "inflow":
            session.execute(text("""
                UPDATE ahcam.collection_accounts
                SET balance = balance + :amount WHERE account_id = :aid
            """), {"amount": amount, "aid": account_id})
        elif transaction_type == "outflow":
            session.execute(text("""
                UPDATE ahcam.collection_accounts
                SET balance = balance - :amount WHERE account_id = :aid
            """), {"amount": amount, "aid": account_id})

    return {"transaction_id": txn_id, "hash": txn_hash, "amount": amount}


def verify_chain(account_id: str) -> dict:
    """Verify the hash chain integrity for an account's transactions."""
    pool = get_pool()
    with pool.get_session() as session:
        rows = session.execute(text("""
            SELECT transaction_id, amount, created_at, previous_hash, hash
            FROM ahcam.transactions
            WHERE account_id = :aid
            ORDER BY created_at ASC
        """), {"aid": account_id}).fetchall()

    if not rows:
        return {"valid": True, "count": 0}

    expected_prev = "GENESIS"
    for i, row in enumerate(rows):
        if row[3] != expected_prev:
            return {"valid": False, "broken_at": i, "transaction_id": str(row[0])}
        expected_hash = compute_hash(str(row[0]), float(row[1]), str(row[2]), row[3])
        if row[4] != expected_hash:
            return {"valid": False, "broken_at": i, "transaction_id": str(row[0]), "reason": "hash_mismatch"}
        expected_prev = row[4]

    return {"valid": True, "count": len(rows)}
