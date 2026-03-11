from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import OutputPacket, Policy, Quote, Trip, Vendor


def initialize_database(
    db_path: Path,
    trips: list[Trip],
    policy: Policy,
    vendors: list[Vendor],
    quotes: list[Quote],
) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trips (
                trip_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS policies (
                policy_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS vendors (
                vendor_id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS quotes (
                vendor_id TEXT NOT NULL,
                trip_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY (vendor_id, trip_id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scenario_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS output_packets (
                generated_at TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )

        cursor.executemany(
            "INSERT OR REPLACE INTO trips (trip_id, payload) VALUES (?, ?)",
            [(trip.trip_id, json.dumps(trip.to_dict())) for trip in trips],
        )
        cursor.execute(
            "INSERT OR REPLACE INTO policies (policy_id, payload) VALUES (?, ?)",
            (policy.policy_id, json.dumps(policy.to_dict())),
        )
        cursor.executemany(
            "INSERT OR REPLACE INTO vendors (vendor_id, category, payload) VALUES (?, ?, ?)",
            [
                (vendor.vendor_id, vendor.category, json.dumps(vendor.to_dict()))
                for vendor in vendors
            ],
        )
        cursor.executemany(
            "INSERT OR REPLACE INTO quotes (vendor_id, trip_id, payload) VALUES (?, ?, ?)",
            [
                (quote.vendor_id, quote.trip_id, json.dumps(quote.to_dict()))
                for quote in quotes
            ],
        )
        connection.commit()


def save_settings(db_path: Path, settings: dict[str, str]) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.executemany(
            "INSERT OR REPLACE INTO scenario_settings (key, value) VALUES (?, ?)",
            [(key, json.dumps(value)) for key, value in settings.items()],
        )
        connection.commit()


def load_settings(db_path: Path) -> dict[str, str]:
    if not db_path.exists():
        return {}
    with sqlite3.connect(db_path) as connection:
        rows = connection.execute("SELECT key, value FROM scenario_settings").fetchall()
    return {key: json.loads(value) for key, value in rows}


def save_output_packet(db_path: Path, packet: OutputPacket) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO output_packets (generated_at, payload) VALUES (?, ?)",
            (packet.generated_at, json.dumps(packet.to_dict())),
        )
        connection.commit()
