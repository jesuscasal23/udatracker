# This module contains the OrderTracker class, which encapsulates the core
# business logic for managing orders.


class OrderError(ValueError):
    """Base class for order errors. It inherits from ValueError so that tests
    written against ValueError still pass."""


class ValidationError(OrderError):
    """Raised when the data passed in is invalid, such as a bad field or status."""


class DuplicateOrderError(OrderError):
    """Raised when an order ID is already taken."""


class OrderNotFoundError(OrderError):
    """Raised when the order we are looking for does not exist."""


class OrderTracker:
    """
    Manages customer orders, providing functionalities to add, update,
    and retrieve order information.
    """

    # Every status the app allows, listed once so the checks and the error
    # messages always agree.
    VALID_STATUSES = ("pending", "processing", "shipped", "delivered", "cancelled")

    def __init__(self, storage):
        required_methods = ['save_order', 'get_order', 'get_all_orders']
        for method in required_methods:
            if not hasattr(storage, method) or not callable(getattr(storage, method)):
                raise TypeError(f"Storage object must implement a callable '{method}' method.")
        self.storage = storage

    # --- Validation helpers ---

    @staticmethod
    def _require_non_empty_string(value, field_label):
        """Check a text field is filled in and return it without extra spaces."""
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{field_label} must be a non-empty string.")
        return value.strip()

    @classmethod
    def _require_valid_status(cls, status):
        """Check the status is one we allow and return it."""
        cls._require_non_empty_string(status, "Status")
        if status not in cls.VALID_STATUSES:
            raise ValidationError(
                f"Invalid status '{status}'. Valid statuses are: "
                f"{', '.join(cls.VALID_STATUSES)}."
            )
        return status

    # --- Public methods ---

    def add_order(self, order_id: str, item_name: str, quantity: int,
                  customer_id: str, status: str = "pending"):
        """Create a new order, save it, and return it."""
        # Check the input first, before we go near storage.
        order_id = self._require_non_empty_string(order_id, "Order ID")
        item_name = self._require_non_empty_string(item_name, "Item name")
        customer_id = self._require_non_empty_string(customer_id, "Customer ID")

        # In Python a bool is also an int, so True would otherwise count as 1.
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise ValidationError("Quantity must be a positive integer.")

        status = self._require_valid_status(status)

        # Now make sure the ID is not already taken.
        if self.storage.get_order(order_id) is not None:
            raise DuplicateOrderError(f"Order with ID '{order_id}' already exists.")

        # Build the record, save it, and return it.
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
        """Return the order with this ID, or None if there is no such order."""
        order_id = self._require_non_empty_string(order_id, "Order ID")
        return self.storage.get_order(order_id)

    def update_order_status(self, order_id: str, new_status: str):
        """Change the status of an order and return the updated order."""
        order_id = self._require_non_empty_string(order_id, "Order ID")
        # Check the status before reading storage, so bad input stops here.
        new_status = self._require_valid_status(new_status)

        existing_order = self.storage.get_order(order_id)
        if existing_order is None:
            raise OrderNotFoundError(f"Order with ID '{order_id}' not found.")

        # Work on a copy so we do not change the dict that storage gave us.
        updated_order = dict(existing_order)
        updated_order["status"] = new_status
        self.storage.save_order(order_id, updated_order)
        return updated_order

    def list_all_orders(self):
        """Return all orders as a list."""
        return list(self.storage.get_all_orders().values())

    def list_orders_by_status(self, status: str):
        """Return only the orders that have this status."""
        status = self._require_valid_status(status)
        return [
            order
            for order in self.storage.get_all_orders().values()
            if order.get("status") == status
        ]
