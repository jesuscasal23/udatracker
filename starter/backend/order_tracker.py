# This module contains the OrderTracker class, which encapsulates the core
# business logic for managing orders.


class OrderError(ValueError):
    """Base class for order-related errors. Subclasses ValueError so that
    existing tests written against ValueError continue to pass."""


class ValidationError(OrderError):
    """Raised when the caller supplies invalid data (bad field, bad status)."""


class DuplicateOrderError(OrderError):
    """Raised when creating an order whose ID is already in use."""


class OrderNotFoundError(OrderError):
    """Raised when an operation targets an order that does not exist."""


class OrderTracker:
    """
    Manages customer orders, providing functionalities to add, update,
    and retrieve order information.
    """

    # The single source of truth for what a status may be. Defined once,
    # on the class, so validation and error messages can never drift apart.
    VALID_STATUSES = ("pending", "processing", "shipped", "delivered", "cancelled")

    def __init__(self, storage):
        required_methods = ['save_order', 'get_order', 'get_all_orders']
        for method in required_methods:
            if not hasattr(storage, method) or not callable(getattr(storage, method)):
                raise TypeError(f"Storage object must implement a callable '{method}' method.")
        self.storage = storage

    # --- Internal validation helpers -------------------------------------

    @staticmethod
    def _require_non_empty_string(value, field_label):
        """Guard for the string fields. Returns the trimmed value."""
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{field_label} must be a non-empty string.")
        return value.strip()

    @classmethod
    def _require_valid_status(cls, status):
        """Guard for status values. Returns the validated status."""
        cls._require_non_empty_string(status, "Status")
        if status not in cls.VALID_STATUSES:
            raise ValidationError(
                f"Invalid status '{status}'. Valid statuses are: "
                f"{', '.join(cls.VALID_STATUSES)}."
            )
        return status

    # --- Public API -------------------------------------------------------

    def add_order(self, order_id: str, item_name: str, quantity: int,
                  customer_id: str, status: str = "pending"):
        """Create a new order and persist it. Returns the stored order dict."""
        # --- 1. Validate the caller's data before anything else happens ---
        order_id = self._require_non_empty_string(order_id, "Order ID")
        item_name = self._require_non_empty_string(item_name, "Item name")
        customer_id = self._require_non_empty_string(customer_id, "Customer ID")

        # bool is a subclass of int in Python, so True would otherwise pass as 1.
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise ValidationError("Quantity must be a positive integer.")

        status = self._require_valid_status(status)

        # --- 2. Only now touch storage, to enforce uniqueness ---
        if self.storage.get_order(order_id) is not None:
            raise DuplicateOrderError(f"Order with ID '{order_id}' already exists.")

        # --- 3. Build, save, and hand the record back to the caller ---
        order = {
            "order_id": order_id,
            "item_name": item_name,
            "quantity": quantity,
            "customer_id": customer_id,
            "status": status,
        }
        self.storage.save_order(order_id, order)
        return order

    def get_order_by_id(self, order_id: str):
        """Return the order dict for `order_id`, or None if it does not exist."""
        order_id = self._require_non_empty_string(order_id, "Order ID")
        return self.storage.get_order(order_id)

    def update_order_status(self, order_id: str, new_status: str):
        """Change an order's status. Returns the updated order dict."""
        order_id = self._require_non_empty_string(order_id, "Order ID")
        # Validate the status before touching storage: fail fast on bad input.
        new_status = self._require_valid_status(new_status)

        existing_order = self.storage.get_order(order_id)
        if existing_order is None:
            raise OrderNotFoundError(f"Order with ID '{order_id}' not found.")

        # Copy-update-save rather than mutating the dict storage handed us.
        updated_order = dict(existing_order)
        updated_order["status"] = new_status
        self.storage.save_order(order_id, updated_order)
        return updated_order

    def list_all_orders(self):
        """Return every order as a list of dicts."""
        return list(self.storage.get_all_orders().values())

    def list_orders_by_status(self, status: str):
        """Return only the orders whose status matches `status`."""
        status = self._require_valid_status(status)
        return [
            order
            for order in self.storage.get_all_orders().values()
            if order.get("status") == status
        ]
