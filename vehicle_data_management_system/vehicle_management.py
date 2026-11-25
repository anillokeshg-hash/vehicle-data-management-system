"""
Vehicle Data Management System
------------------------------
A simple command-line application to add, view, search, update,
delete and export vehicle records. Uses SQLite (built into Python).

Run:  python vehicle_management.py
"""

import csv
import sqlite3
from datetime import datetime

DB_NAME = "vehicles.db"
FUEL_TYPES = ["Petrol", "Diesel", "Electric", "CNG", "Hybrid"]


# ---------------------------------------------------------------
# Database layer
# ---------------------------------------------------------------
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vehicles (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                reg_number    TEXT NOT NULL UNIQUE,
                make          TEXT NOT NULL,
                model         TEXT NOT NULL,
                year          INTEGER NOT NULL,
                fuel_type     TEXT NOT NULL,
                owner_name    TEXT NOT NULL,
                mileage_km    INTEGER DEFAULT 0,
                created_at    TEXT NOT NULL
            )
            """
        )


def add_vehicle(reg, make, model, year, fuel, owner, mileage):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO vehicles
               (reg_number, make, model, year, fuel_type, owner_name, mileage_km, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (reg.upper(), make, model, year, fuel, owner, mileage,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )


def get_all_vehicles():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM vehicles ORDER BY id").fetchall()


def search_vehicles(keyword):
    like = f"%{keyword}%"
    with get_connection() as conn:
        return conn.execute(
            """SELECT * FROM vehicles
               WHERE reg_number LIKE ? OR make LIKE ? OR model LIKE ?
                  OR owner_name LIKE ? OR fuel_type LIKE ?
               ORDER BY id""",
            (like, like, like, like, like),
        ).fetchall()


def get_vehicle(vehicle_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)
        ).fetchone()


def update_vehicle(vehicle_id, field, value):
    allowed = {"make", "model", "year", "fuel_type", "owner_name", "mileage_km"}
    if field not in allowed:
        raise ValueError("Invalid field")
    with get_connection() as conn:
        conn.execute(f"UPDATE vehicles SET {field} = ? WHERE id = ?",
                     (value, vehicle_id))


def delete_vehicle(vehicle_id):
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
        return cur.rowcount > 0


# ---------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------
def ask_text(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("  Value cannot be empty.")


def ask_int(prompt, minimum, maximum):
    while True:
        try:
            value = int(input(prompt).strip())
            if minimum <= value <= maximum:
                return value
            print(f"  Enter a number between {minimum} and {maximum}.")
        except ValueError:
            print("  Please enter a valid number.")


def ask_fuel():
    print("  Fuel types:", ", ".join(f"{i}. {f}" for i, f in enumerate(FUEL_TYPES, 1)))
    choice = ask_int("  Choose fuel type number: ", 1, len(FUEL_TYPES))
    return FUEL_TYPES[choice - 1]


# ---------------------------------------------------------------
# Display
# ---------------------------------------------------------------
def print_table(rows):
    if not rows:
        print("\nNo records found.")
        return
    header = (f"{'ID':<4}{'Reg. No.':<14}{'Make':<12}{'Model':<14}"
              f"{'Year':<6}{'Fuel':<10}{'Owner':<16}{'Mileage(km)':<12}")
    print("\n" + header)
    print("-" * len(header))
    for r in rows:
        print(f"{r['id']:<4}{r['reg_number']:<14}{r['make']:<12}{r['model']:<14}"
              f"{r['year']:<6}{r['fuel_type']:<10}{r['owner_name']:<16}{r['mileage_km']:<12}")
    print(f"\nTotal: {len(rows)} record(s)")


# ---------------------------------------------------------------
# Menu actions
# ---------------------------------------------------------------
def action_add():
    print("\n--- Add New Vehicle ---")
    reg = ask_text("Registration number: ")
    make = ask_text("Make (e.g. Toyota): ")
    model = ask_text("Model (e.g. Innova): ")
    year = ask_int("Year of manufacture: ", 1950, datetime.now().year + 1)
    fuel = ask_fuel()
    owner = ask_text("Owner name: ")
    mileage = ask_int("Mileage (km): ", 0, 5_000_000)
    try:
        add_vehicle(reg, make, model, year, fuel, owner, mileage)
        print("\n✔ Vehicle added successfully.")
    except sqlite3.IntegrityError:
        print("\n✘ A vehicle with this registration number already exists.")


def action_view():
    print("\n--- All Vehicles ---")
    print_table(get_all_vehicles())


def action_search():
    keyword = ask_text("\nEnter search keyword: ")
    print_table(search_vehicles(keyword))


def action_update():
    print("\n--- Update Vehicle ---")
    vid = ask_int("Enter vehicle ID: ", 1, 10**9)
    if not get_vehicle(vid):
        print("✘ Vehicle not found.")
        return
    options = {
        "1": ("make", "New make: ", str),
        "2": ("model", "New model: ", str),
        "3": ("year", "New year: ", int),
        "4": ("fuel_type", None, None),
        "5": ("owner_name", "New owner name: ", str),
        "6": ("mileage_km", "New mileage (km): ", int),
    }
    print("1. Make  2. Model  3. Year  4. Fuel type  5. Owner  6. Mileage")
    choice = input("Field to update: ").strip()
    if choice not in options:
        print("✘ Invalid choice.")
        return
    field, prompt, kind = options[choice]
    if field == "fuel_type":
        value = ask_fuel()
    elif kind is int:
        value = ask_int(prompt, 0, 5_000_000)
    else:
        value = ask_text(prompt)
    update_vehicle(vid, field, value)
    print("✔ Vehicle updated.")


def action_delete():
    print("\n--- Delete Vehicle ---")
    vid = ask_int("Enter vehicle ID: ", 1, 10**9)
    vehicle = get_vehicle(vid)
    if not vehicle:
        print("✘ Vehicle not found.")
        return
    confirm = input(f"Delete {vehicle['reg_number']} ({vehicle['make']} "
                    f"{vehicle['model']})? (y/n): ").strip().lower()
    if confirm == "y":
        delete_vehicle(vid)
        print("✔ Vehicle deleted.")
    else:
        print("Cancelled.")


def action_export():
    rows = get_all_vehicles()
    if not rows:
        print("\nNothing to export.")
        return
    filename = f"vehicles_export_{datetime.now():%Y%m%d_%H%M%S}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(rows[0].keys())
        writer.writerows([tuple(r) for r in rows])
    print(f"\n✔ Exported {len(rows)} record(s) to {filename}")


def action_stats():
    rows = get_all_vehicles()
    if not rows:
        print("\nNo data available.")
        return
    total = len(rows)
    avg_mileage = sum(r["mileage_km"] for r in rows) / total
    by_fuel = {}
    for r in rows:
        by_fuel[r["fuel_type"]] = by_fuel.get(r["fuel_type"], 0) + 1
    print("\n--- Statistics ---")
    print(f"Total vehicles : {total}")
    print(f"Average mileage: {avg_mileage:,.0f} km")
    for fuel, count in sorted(by_fuel.items()):
        print(f"  {fuel:<10}: {count}")


# ---------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------
MENU = """
==============================================
        VEHICLE DATA MANAGEMENT SYSTEM
==============================================
 1. Add vehicle
 2. View all vehicles
 3. Search vehicles
 4. Update vehicle
 5. Delete vehicle
 6. Statistics
 7. Export to CSV
 0. Exit
----------------------------------------------"""

ACTIONS = {
    "1": action_add,
    "2": action_view,
    "3": action_search,
    "4": action_update,
    "5": action_delete,
    "6": action_stats,
    "7": action_export,
}


def main():
    init_db()
    while True:
        print(MENU)
        choice = input("Enter your choice: ").strip()
        if choice == "0":
            print("Goodbye!")
            break
        action = ACTIONS.get(choice)
        if action:
            action()
        else:
            print("Invalid choice, try again.")


if __name__ == "__main__":
    main()
