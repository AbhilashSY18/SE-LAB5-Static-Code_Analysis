"""
inventory_system.py

A small, safe inventory manager suitable for static-analysis exercises.

Changes from original:
- Converted functions to snake_case.
- Removed mutable default arguments.
- Removed bare except and eval().
- Added type checks and validation.
- Used context managers with explicit encoding for file I/O.
- Replaced global usage with module-level state but safer access patterns.
- Added docstrings and logging.
"""

from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure module-level logger (main config happens in __main__)
logger = logging.getLogger(__name__)

Stock = Dict[str, int]
stock_data: Stock = {}


def add_item(item: str = "default", qty: int = 0, logs: Optional[List[str]] = None) -> None:
    """
    Add quantity of an item to stock.

    :param item: Item name (must be a non-empty string).
    :param qty: Quantity to add (integer, must be >= 0).
    :param logs: Optional list to append log entries to (if provided).
    :raises ValueError: If input types/values are invalid.
    """
    if logs is None:
        logs = []

    if not isinstance(item, str) or not item:
        raise ValueError("item must be a non-empty string")
    if not isinstance(qty, int):
        raise ValueError("qty must be an integer")
    if qty < 0:
        raise ValueError("qty must be non-negative")

    previous = stock_data.get(item, 0)
    stock_data[item] = previous + qty

    entry = f"{datetime.now().isoformat()}: Added {qty} of {item} (was {previous}, now {stock_data[item]})"
    logs.append(entry)
    logger.info(entry)


def remove_item(item: str, qty: int) -> None:
    """
    Remove quantity of an item from stock. If resulting qty <= 0, the item is deleted.

    :param item: Item name (string).
    :param qty: Quantity to remove (integer, must be > 0).
    :raises ValueError: If qty is invalid or item not found.
    """
    if not isinstance(item, str) or not item:
        raise ValueError("item must be a non-empty string")
    if not isinstance(qty, int) or qty <= 0:
        raise ValueError("qty must be a positive integer")

    try:
        current = stock_data[item]
    except KeyError as exc:
        logger.warning("Attempted to remove non-existent item: %s", item)
        raise ValueError(f"Item '{item}' not found") from exc

    if qty >= current:
        del stock_data[item]
        logger.info("Removed item '%s' from stock (removed all %d).", item, current)
    else:
        stock_data[item] = current - qty
        logger.info("Decreased '%s' by %d (new qty=%d).", item, qty, stock_data[item])


def get_qty(item: str) -> int:
    """
    Return quantity of an item; returns 0 if item is not present.

    :param item: Item name.
    :return: Quantity as integer (0 if missing).
    """
    if not isinstance(item, str) or not item:
        raise ValueError("item must be a non-empty string")
    return int(stock_data.get(item, 0))


def load_data(file: str = "inventory.json") -> None:
    """
    Load inventory data from a JSON file. If file doesn't exist, keep current stock.

    :param file: Path to JSON file.
    """
    try:
        with open(file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            # Validate values are integers
            validated: Stock = {}
            for k, v in data.items():
                if not isinstance(k, str):
                    logger.warning("Skipping non-string key in JSON: %r", k)
                    continue
                try:
                    validated[k] = int(v)
                except (TypeError, ValueError):
                    logger.warning("Skipping key with non-integer value: %s -> %r", k, v)
            stock_data.clear()
            stock_data.update(validated)
            logger.info("Loaded inventory from %s", file)
        else:
            logger.error("Inventory file %s does not contain a JSON object; ignoring.", file)
    except FileNotFoundError:
        logger.info("Inventory file %s not found; starting with current stock.", file)
    except json.JSONDecodeError as exc:
        logger.error("Failed to decode JSON from %s: %s", file, exc)


def save_data(file: str = "inventory.json") -> None:
    """
    Save current inventory to a JSON file.

    :param file: Path to JSON file.
    """
    try:
        with open(file, "w", encoding="utf-8") as fh:
            json.dump(stock_data, fh, ensure_ascii=False, indent=2)
        logger.info("Saved inventory to %s", file)
    except OSError as exc:
        logger.error("Failed to save inventory to %s: %s", file, exc)


def print_data() -> None:
    """
    Print a human-readable report of current inventory.
    """
    print("Items Report")
    if not stock_data:
        print("(no items)")
        return

    for name, qty in sorted(stock_data.items()):
        print(f"{name} -> {qty}")


def check_low_items(threshold: int = 5) -> List[str]:
    """
    Return a list of item names whose quantities are below the given threshold.

    :param threshold: Threshold integer (must be >= 0).
    :return: List of item names below threshold.
    """
    if not isinstance(threshold, int) or threshold < 0:
        raise ValueError("threshold must be a non-negative integer")

    return [name for name, qty in stock_data.items() if qty < threshold]


def main() -> None:
    """
    Demo main function. Shows usage and exercises functions safely.
    """
    # Example logs collector
    logs: List[str] = []

    # Populate safely (type/value-checked)
    add_item("apple", 10, logs)
    try:
        add_item("banana", -2, logs)  # will raise ValueError — intentional to show validation
    except ValueError as exc:
        logger.warning("Ignored invalid add_item call: %s", exc)

    try:
        # invalid types
        add_item(str(123), 10, logs)  # convert 123 to string if intent was numeric label
        # avoid silently allowing wrong types - previous code added '123' as int key with 'ten' qty
    except ValueError as exc:
        logger.warning("Ignored invalid add_item call: %s", exc)

    try:
        remove_item("apple", 3)
    except ValueError as exc:
        logger.warning("remove_item error: %s", exc)

    try:
        remove_item("orange", 1)
    except ValueError:
        # already logged in remove_item
        pass

    try:
        print("Apple stock:", get_qty("apple"))
    except ValueError as exc:
        logger.warning("get_qty error: %s", exc)

    print("Low items:", check_low_items())
    save_data()
    load_data()
    print_data()

    # NOTE: removed eval() for security reasons


if __name__ == "__main__":
    # Configure root logger for script runs
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
