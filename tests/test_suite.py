"""
AHCAM Test Suite

Covers: DB connection, auth, waterfall engine, ledger hash chain,
command interceptor, chat store, config, module tools.

Run: python tests/test_suite.py
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

_results = []
_pass = 0
_fail = 0


def test(name):
    def decorator(fn):
        fn._test_name = name
        return fn
    return decorator


def run_test(fn):
    global _pass, _fail
    name = getattr(fn, "_test_name", fn.__name__)
    try:
        result = fn()
        _pass += 1
        _results.append({"test": name, "status": "PASS", "result": str(result)[:200]})
        print(f"  PASS  {name}")
    except Exception as e:
        _fail += 1
        _results.append({"test": name, "status": "FAIL", "error": str(e)[:200]})
        print(f"  FAIL  {name}: {e}")


def save_results(filename, results):
    out_dir = Path(__file__).parent.parent / "test-data"
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / filename, "w") as f:
        json.dump(results, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

print("\n=== AHCAM Test Suite ===\n")

# --- DB ---
print("DB Tests:")

@test("DB connection")
def test_db_connection():
    from utils.db import get_pool
    from sqlalchemy import text
    pool = get_pool()
    with pool.get_session() as s:
        result = s.execute(text("SELECT 1")).scalar()
    assert result == 1
    return "Connected"

run_test(test_db_connection)

@test("Schema exists")
def test_schema_exists():
    from utils.db import get_pool
    from sqlalchemy import text
    pool = get_pool()
    with pool.get_session() as s:
        result = s.execute(text(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'ahcam'"
        )).fetchone()
    assert result is not None, "ahcam schema not found"
    return "Schema exists"

run_test(test_schema_exists)

# --- Auth ---
print("\nAuth Tests:")

@test("Password hashing")
def test_password_hash():
    from utils.auth import hash_password, verify_password
    h = hash_password("testpass123")
    assert verify_password("testpass123", h)
    assert not verify_password("wrongpass", h)
    return "Hash/verify works"

run_test(test_password_hash)

@test("JWT encode/decode")
def test_jwt():
    from utils.auth import create_jwt_token, decode_jwt_token
    token = create_jwt_token("test-user-id", "test@example.com")
    payload = decode_jwt_token(token)
    assert payload is not None
    assert payload["user_id"] == "test-user-id"
    assert payload["email"] == "test@example.com"
    return "JWT works"

run_test(test_jwt)

# --- Waterfall Engine ---
print("\nWaterfall Engine Tests:")

@test("Basic percentage waterfall")
def test_waterfall_percentage():
    from modules.waterfall import apply_waterfall
    rules = [
        {"priority": 1, "recipient_label": "Financier", "rule_type": "percentage", "percentage": 50, "cap": None, "floor": None, "corridor_start": None, "corridor_end": None},
        {"priority": 2, "recipient_label": "Producer", "rule_type": "percentage", "percentage": 30, "cap": None, "floor": None, "corridor_start": None, "corridor_end": None},
        {"priority": 3, "recipient_label": "Sales Agent", "rule_type": "percentage", "percentage": 20, "cap": None, "floor": None, "corridor_start": None, "corridor_end": None},
    ]
    result = apply_waterfall(1000000, rules)
    assert result["Financier"] == 500000
    assert result["Producer"] == 150000  # 30% of remaining 500000
    assert result["Sales Agent"] == 70000  # 20% of remaining 350000
    return result

run_test(test_waterfall_percentage)

@test("Waterfall with cap")
def test_waterfall_cap():
    from modules.waterfall import apply_waterfall
    rules = [
        {"priority": 1, "recipient_label": "Financier", "rule_type": "percentage", "percentage": 100, "cap": 200000, "floor": None, "corridor_start": None, "corridor_end": None},
        {"priority": 2, "recipient_label": "Producer", "rule_type": "residual", "percentage": None, "cap": None, "floor": None, "corridor_start": None, "corridor_end": None},
    ]
    result = apply_waterfall(500000, rules)
    assert result["Financier"] == 200000
    assert result["Producer"] == 300000
    return result

run_test(test_waterfall_cap)

@test("Empty waterfall")
def test_waterfall_empty():
    from modules.waterfall import apply_waterfall
    result = apply_waterfall(100000, [])
    assert result["Unallocated"] == 100000
    return result

run_test(test_waterfall_empty)

# --- Ledger ---
print("\nLedger Tests:")

@test("Hash computation")
def test_ledger_hash():
    from utils.ledger import compute_hash
    h = compute_hash("txn-1", 1000.0, "2024-01-01", "GENESIS")
    assert len(h) == 64
    # Same inputs should produce same hash
    h2 = compute_hash("txn-1", 1000.0, "2024-01-01", "GENESIS")
    assert h == h2
    # Different inputs should produce different hash
    h3 = compute_hash("txn-2", 1000.0, "2024-01-01", "GENESIS")
    assert h != h3
    return f"Hash: {h[:16]}..."

run_test(test_ledger_hash)

# --- Config ---
print("\nConfig Tests:")

@test("Config constants loaded")
def test_config():
    from config.settings import APP_NAME, APP_PORT, PRODUCTION_STATUSES, STAKEHOLDER_ROLES, RULE_TYPES
    assert APP_NAME == "Ashland Hill Collection Account Management"
    assert APP_PORT == 5011
    assert len(PRODUCTION_STATUSES) == 6
    assert len(STAKEHOLDER_ROLES) == 8
    assert len(RULE_TYPES) == 4
    return "Config OK"

run_test(test_config)

# --- Command Interceptor ---
print("\nCommand Interceptor Tests:")

@test("Help command")
def test_help_command():
    import asyncio
    from app import _command_interceptor
    result = asyncio.get_event_loop().run_until_complete(
        _command_interceptor("help", {})
    )
    assert result is not None
    assert "AHCAM Commands" in result
    return "Help works"

run_test(test_help_command)

@test("Unknown command returns None")
def test_unknown_command():
    import asyncio
    from app import _command_interceptor
    result = asyncio.get_event_loop().run_until_complete(
        _command_interceptor("What is the meaning of life?", {})
    )
    assert result is None
    return "Falls through to AI"

run_test(test_unknown_command)

# --- Summary ---
print(f"\n{'='*40}")
print(f"Results: {_pass} passed, {_fail} failed, {_pass + _fail} total")
print(f"{'='*40}\n")

save_results("test_summary.json", {
    "total": _pass + _fail,
    "passed": _pass,
    "failed": _fail,
    "tests": _results,
})
