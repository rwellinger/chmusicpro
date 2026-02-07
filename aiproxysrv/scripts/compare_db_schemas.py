#!/usr/bin/env python3
"""
Database Schema Comparison Script

Compares two PostgreSQL database schemas (Dev vs Prod) and reports differences.

Usage:
    # Set connection strings in .env files or environment variables
    # Dev: Uses default .env
    # Prod: Set PROD_DATABASE_URL environment variable

    python scripts/compare_db_schemas.py

Requirements:
    - psycopg2
    - python-dotenv
"""

import os
import sys
from typing import Any

import psycopg2
from dotenv import load_dotenv


def get_db_connection(connection_string: str):
    """Create database connection"""
    return psycopg2.connect(connection_string)


def get_tables(conn) -> set[str]:
    """Get all table names"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        return {row[0] for row in cur.fetchall()}


def get_table_columns(conn, table_name: str) -> dict[str, dict[str, Any]]:
    """Get column definitions for a table"""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
                AND table_name = %s
            ORDER BY ordinal_position
        """,
            (table_name,),
        )
        columns = {}
        for row in cur.fetchall():
            col_name, data_type, max_length, nullable, default = row
            columns[col_name] = {
                "type": data_type,
                "max_length": max_length,
                "nullable": nullable,
                "default": default,
            }
        return columns


def get_constraints(conn, table_name: str) -> dict[str, dict[str, Any]]:
    """Get constraints for a table"""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                tc.constraint_name,
                tc.constraint_type,
                string_agg(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) as columns
            FROM information_schema.table_constraints tc
            LEFT JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema = 'public'
                AND tc.table_name = %s
            GROUP BY tc.constraint_name, tc.constraint_type
            ORDER BY tc.constraint_type, tc.constraint_name
        """,
            (table_name,),
        )
        constraints = {}
        for row in cur.fetchall():
            constraint_name, constraint_type, columns = row
            constraints[constraint_name] = {"type": constraint_type, "columns": columns}
        return constraints


def get_indexes(conn, table_name: str) -> dict[str, str]:
    """Get indexes for a table"""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
                AND tablename = %s
            ORDER BY indexname
        """,
            (table_name,),
        )
        return {row[0]: row[1] for row in cur.fetchall()}


def get_alembic_version(conn) -> str | None:
    """Get current Alembic migration version"""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT version_num FROM alembic_version")
            result = cur.fetchone()
            return result[0] if result else None
    except Exception:
        return None


def compare_schemas(dev_conn_str: str, prod_conn_str: str):
    """Compare Dev and Prod database schemas"""
    print("=" * 80)
    print("DATABASE SCHEMA COMPARISON: DEV vs PROD")
    print("=" * 80)
    print()

    # Connect to both databases
    print("Connecting to databases...")
    dev_conn = get_db_connection(dev_conn_str)
    prod_conn = get_db_connection(prod_conn_str)
    print("✓ Connected to Dev")
    print("✓ Connected to Prod")
    print()

    # Compare Alembic versions
    print("=" * 80)
    print("1. ALEMBIC MIGRATION VERSIONS")
    print("=" * 80)
    dev_version = get_alembic_version(dev_conn)
    prod_version = get_alembic_version(prod_conn)
    print(f"Dev:  {dev_version}")
    print(f"Prod: {prod_version}")
    if dev_version == prod_version:
        print("✓ Versions match")
    else:
        print("✗ VERSIONS DIFFER!")
    print()

    # Compare tables
    print("=" * 80)
    print("2. TABLES")
    print("=" * 80)
    dev_tables = get_tables(dev_conn)
    prod_tables = get_tables(prod_conn)

    only_in_dev = dev_tables - prod_tables
    only_in_prod = prod_tables - dev_tables
    common_tables = dev_tables & prod_tables

    print(f"Common tables: {len(common_tables)}")
    print(f"Only in Dev:   {len(only_in_dev)}")
    print(f"Only in Prod:  {len(only_in_prod)}")

    if only_in_dev:
        print("\nTables only in Dev:")
        for table in sorted(only_in_dev):
            print(f"  - {table}")

    if only_in_prod:
        print("\nTables only in Prod:")
        for table in sorted(only_in_prod):
            print(f"  - {table}")

    if not only_in_dev and not only_in_prod:
        print("✓ All tables exist in both databases")
    print()

    # Compare table structures
    differences_found = False

    for table in sorted(common_tables):
        print("=" * 80)
        print(f"3. TABLE: {table}")
        print("=" * 80)

        # Compare columns
        dev_cols = get_table_columns(dev_conn, table)
        prod_cols = get_table_columns(prod_conn, table)

        only_in_dev_cols = set(dev_cols.keys()) - set(prod_cols.keys())
        only_in_prod_cols = set(prod_cols.keys()) - set(dev_cols.keys())
        common_cols = set(dev_cols.keys()) & set(prod_cols.keys())

        # Column differences
        if only_in_dev_cols or only_in_prod_cols:
            differences_found = True
            print("\n⚠️  COLUMN DIFFERENCES:")
            if only_in_dev_cols:
                print(f"  Only in Dev: {', '.join(sorted(only_in_dev_cols))}")
            if only_in_prod_cols:
                print(f"  Only in Prod: {', '.join(sorted(only_in_prod_cols))}")

        # Check column definition differences
        col_def_diffs = []
        for col in common_cols:
            if dev_cols[col] != prod_cols[col]:
                col_def_diffs.append(col)
                differences_found = True

        if col_def_diffs:
            print("\n⚠️  COLUMN DEFINITION DIFFERENCES:")
            for col in col_def_diffs:
                print(f"\n  Column: {col}")
                print(f"    Dev:  {dev_cols[col]}")
                print(f"    Prod: {prod_cols[col]}")

        # Compare constraints
        dev_constraints = get_constraints(dev_conn, table)
        prod_constraints = get_constraints(prod_conn, table)

        only_in_dev_cons = set(dev_constraints.keys()) - set(prod_constraints.keys())
        only_in_prod_cons = set(prod_constraints.keys()) - set(dev_constraints.keys())

        if only_in_dev_cons or only_in_prod_cons:
            differences_found = True
            print("\n⚠️  CONSTRAINT DIFFERENCES:")
            if only_in_dev_cons:
                print("  Only in Dev:")
                for cons in sorted(only_in_dev_cons):
                    print(f"    - {cons} ({dev_constraints[cons]['type']}): {dev_constraints[cons]['columns']}")
            if only_in_prod_cons:
                print("  Only in Prod:")
                for cons in sorted(only_in_prod_cons):
                    print(f"    - {cons} ({prod_constraints[cons]['type']}): {prod_constraints[cons]['columns']}")

        # Compare indexes
        dev_indexes = get_indexes(dev_conn, table)
        prod_indexes = get_indexes(prod_conn, table)

        only_in_dev_idx = set(dev_indexes.keys()) - set(prod_indexes.keys())
        only_in_prod_idx = set(prod_indexes.keys()) - set(dev_indexes.keys())

        if only_in_dev_idx or only_in_prod_idx:
            differences_found = True
            print("\n⚠️  INDEX DIFFERENCES:")
            if only_in_dev_idx:
                print("  Only in Dev:")
                for idx in sorted(only_in_dev_idx):
                    print(f"    - {idx}")
            if only_in_prod_idx:
                print("  Only in Prod:")
                for idx in sorted(only_in_prod_idx):
                    print(f"    - {idx}")

        if not (
            only_in_dev_cols
            or only_in_prod_cols
            or col_def_diffs
            or only_in_dev_cons
            or only_in_prod_cons
            or only_in_dev_idx
            or only_in_prod_idx
        ):
            print("✓ Structure identical")

        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    if differences_found:
        print("✗ SCHEMA DIFFERENCES FOUND!")
        print("\nRecommendation:")
        print("1. Check Alembic migration versions")
        print("2. Run missing migrations on Prod: cd aiproxysrv/src && alembic upgrade head")
        print("3. Re-run this script to verify")
    else:
        print("✓ Schemas are identical (tables, columns, constraints, indexes)")

    # Close connections
    dev_conn.close()
    prod_conn.close()


if __name__ == "__main__":
    # Load Dev environment
    load_dotenv()
    dev_db_url = os.getenv("DATABASE_URL")

    # Get Prod connection string from environment
    prod_db_url = os.getenv("PROD_DATABASE_URL")

    if not dev_db_url:
        print("ERROR: DATABASE_URL not found in .env")
        sys.exit(1)

    if not prod_db_url:
        print("ERROR: PROD_DATABASE_URL environment variable not set")
        print("\nUsage:")
        print('  export PROD_DATABASE_URL="postgresql://user:pass@prodhost:5432/dbname"')
        print("  python scripts/compare_db_schemas.py")
        sys.exit(1)

    try:
        compare_schemas(dev_db_url, prod_db_url)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
