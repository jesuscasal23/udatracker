import pytest
from unittest.mock import Mock
from ..order_tracker import OrderTracker

# --- Fixtures for Unit Tests ---


@pytest.fixture
def mock_storage():
    """
    Provides a mock storage object for tests.
    This mock will be configured to simulate various storage behaviors.
    """
    mock = Mock()
    # By default, mock get_order to return None (no order found)
    mock.get_order.return_value = None
    # By default, mock get_all_orders to return an empty dict
    mock.get_all_orders.return_value = {}
    return mock


@pytest.fixture
def order_tracker(mock_storage):
    """
    Provides an OrderTracker instance initialized with the mock_storage.
    """
    return OrderTracker(mock_storage)

#
# --- TODO: add test functions below this line ---
#

# =====================================================================
# add_order
# =====================================================================


def test_add_order_successfully(order_tracker, mock_storage):
    """Tests adding a new order with default 'pending' status."""
    order_tracker.add_order("ORD001", "Laptop", 1, "CUST001")

    # We expect save_order to be called once
    mock_storage.save_order.assert_called_once()


def test_add_order_raises_error_if_exists(order_tracker, mock_storage):
    """Tests that adding an order with a duplicate ID raises a ValueError."""
    # Simulate that the storage finds an existing order
    mock_storage.get_order.return_value = {"order_id": "ORD_EXISTING"}

    with pytest.raises(ValueError, match="Order with ID 'ORD_EXISTING' already exists."):
        order_tracker.add_order("ORD_EXISTING", "New Item", 1, "CUST001")


def test_add_order_stores_all_fields_with_default_status(order_tracker, mock_storage):
    """The saved order has every field and the status defaults to pending."""
    order_tracker.add_order("ORD002", "Keyboard", 3, "CUST002")

    mock_storage.save_order.assert_called_once_with(
        "ORD002",
        {
            "order_id": "ORD002",
            "item_name": "Keyboard",
            "quantity": 3,
            "customer_id": "CUST002",
            "status": "pending",
        },
    )


def test_add_order_returns_the_created_order(order_tracker):
    """add_order returns the new order so app.py can send it back as JSON."""
    created = order_tracker.add_order("ORD003", "Mouse", 2, "CUST003")

    assert created == {
        "order_id": "ORD003",
        "item_name": "Mouse",
        "quantity": 2,
        "customer_id": "CUST003",
        "status": "pending",
    }


def test_add_order_accepts_explicit_status(order_tracker, mock_storage):
    """Passing a status uses that instead of the pending default."""
    created = order_tracker.add_order("ORD004", "Monitor", 1, "CUST004", status="shipped")

    assert created["status"] == "shipped"
    assert mock_storage.save_order.call_args[0][1]["status"] == "shipped"


@pytest.mark.parametrize("bad_quantity", [0, -1, 1.5, "2", None])
def test_add_order_rejects_invalid_quantity(order_tracker, mock_storage, bad_quantity):
    """Quantity must be a positive whole number, and nothing is saved."""
    with pytest.raises(ValueError, match="Quantity must be a positive integer."):
        order_tracker.add_order("ORD005", "Cable", bad_quantity, "CUST005")

    mock_storage.save_order.assert_not_called()


@pytest.mark.parametrize(
    "order_id, item_name, customer_id, expected_message",
    [
        ("", "Laptop", "CUST001", "Order ID must be a non-empty string."),
        ("ORD006", "", "CUST001", "Item name must be a non-empty string."),
        ("ORD006", "Laptop", "", "Customer ID must be a non-empty string."),
        ("   ", "Laptop", "CUST001", "Order ID must be a non-empty string."),
    ],
)
def test_add_order_rejects_missing_required_fields(
    order_tracker, mock_storage, order_id, item_name, customer_id, expected_message
):
    """Required fields that are empty or only spaces are rejected."""
    with pytest.raises(ValueError, match=expected_message):
        order_tracker.add_order(order_id, item_name, 1, customer_id)

    mock_storage.save_order.assert_not_called()


def test_add_order_rejects_invalid_initial_status(order_tracker, mock_storage):
    """A status we do not allow is rejected and nothing is saved."""
    with pytest.raises(ValueError, match="Invalid status 'teleported'"):
        order_tracker.add_order("ORD007", "Desk", 1, "CUST007", status="teleported")

    mock_storage.save_order.assert_not_called()


# =====================================================================
# get_order_by_id
# =====================================================================


def test_get_order_by_id_returns_existing_order(order_tracker, mock_storage):
    """An existing ID returns the stored order."""
    stored_order = {
        "order_id": "ORD010", "item_name": "Laptop", "quantity": 1,
        "customer_id": "CUST010", "status": "pending",
    }
    mock_storage.get_order.return_value = stored_order

    assert order_tracker.get_order_by_id("ORD010") == stored_order
    mock_storage.get_order.assert_called_once_with("ORD010")


def test_get_order_by_id_returns_none_when_missing(order_tracker, mock_storage):
    """A missing order is not an error. It just returns None."""
    mock_storage.get_order.return_value = None

    assert order_tracker.get_order_by_id("NOPE") is None


@pytest.mark.parametrize("bad_id", ["", "   ", None, 42])
def test_get_order_by_id_rejects_invalid_id(order_tracker, mock_storage, bad_id):
    """An empty or non text ID raises an error instead of returning None."""
    with pytest.raises(ValueError, match="Order ID must be a non-empty string."):
        order_tracker.get_order_by_id(bad_id)

    mock_storage.get_order.assert_not_called()


# =====================================================================
# update_order_status
# =====================================================================


def test_update_order_status_successfully(order_tracker, mock_storage):
    """Changing pending to shipped saves the order and returns it."""
    mock_storage.get_order.return_value = {
        "order_id": "ORD020", "item_name": "Laptop", "quantity": 1,
        "customer_id": "CUST020", "status": "pending",
    }

    updated = order_tracker.update_order_status("ORD020", "shipped")

    assert updated["status"] == "shipped"
    mock_storage.save_order.assert_called_once_with(
        "ORD020",
        {
            "order_id": "ORD020", "item_name": "Laptop", "quantity": 1,
            "customer_id": "CUST020", "status": "shipped",
        },
    )


def test_update_order_status_does_not_mutate_stored_dict(order_tracker, mock_storage):
    """The dict we got back from storage is not changed."""
    original = {
        "order_id": "ORD021", "item_name": "Laptop", "quantity": 1,
        "customer_id": "CUST021", "status": "pending",
    }
    mock_storage.get_order.return_value = original

    order_tracker.update_order_status("ORD021", "delivered")

    assert original["status"] == "pending"


def test_update_order_status_rejects_invalid_status_without_reading_storage(
    order_tracker, mock_storage
):
    """An invalid status is rejected before storage is read at all."""
    with pytest.raises(ValueError, match="Invalid status 'lost_in_space'"):
        order_tracker.update_order_status("ORD022", "lost_in_space")

    mock_storage.get_order.assert_not_called()
    mock_storage.save_order.assert_not_called()


def test_update_order_status_raises_when_order_missing(order_tracker, mock_storage):
    """Updating an order that does not exist raises an error."""
    mock_storage.get_order.return_value = None

    with pytest.raises(ValueError, match="Order with ID 'GHOST' not found."):
        order_tracker.update_order_status("GHOST", "shipped")

    mock_storage.save_order.assert_not_called()


@pytest.mark.parametrize("bad_id", ["", "   ", None])
def test_update_order_status_rejects_invalid_id(order_tracker, mock_storage, bad_id):
    """An empty order ID raises an error."""
    with pytest.raises(ValueError, match="Order ID must be a non-empty string."):
        order_tracker.update_order_status(bad_id, "shipped")

    mock_storage.save_order.assert_not_called()


# =====================================================================
# list_all_orders
# =====================================================================


def test_list_all_orders_returns_empty_list_when_storage_empty(order_tracker, mock_storage):
    """Empty storage gives back an empty list."""
    mock_storage.get_all_orders.return_value = {}

    assert order_tracker.list_all_orders() == []


def test_list_all_orders_returns_every_order(order_tracker, mock_storage):
    """All stored orders come back in a list. The order does not matter."""
    order_a = {"order_id": "A", "item_name": "A", "quantity": 1,
               "customer_id": "C1", "status": "pending"}
    order_b = {"order_id": "B", "item_name": "B", "quantity": 2,
               "customer_id": "C2", "status": "shipped"}
    mock_storage.get_all_orders.return_value = {"A": order_a, "B": order_b}

    result = order_tracker.list_all_orders()

    assert isinstance(result, list)
    assert len(result) == 2
    assert order_a in result and order_b in result


# =====================================================================
# list_orders_by_status
# =====================================================================


def test_list_orders_by_status_returns_only_matching_orders(order_tracker, mock_storage):
    """Only the orders with a matching status are returned."""
    pending = {"order_id": "A", "item_name": "A", "quantity": 1,
               "customer_id": "C1", "status": "pending"}
    shipped = {"order_id": "B", "item_name": "B", "quantity": 2,
               "customer_id": "C2", "status": "shipped"}
    mock_storage.get_all_orders.return_value = {"A": pending, "B": shipped}

    assert order_tracker.list_orders_by_status("shipped") == [shipped]


def test_list_orders_by_status_returns_empty_list_when_nothing_matches(order_tracker, mock_storage):
    """A valid status with no matches returns an empty list."""
    pending = {"order_id": "A", "item_name": "A", "quantity": 1,
               "customer_id": "C1", "status": "pending"}
    mock_storage.get_all_orders.return_value = {"A": pending}

    assert order_tracker.list_orders_by_status("delivered") == []


def test_list_orders_by_status_returns_empty_list_when_storage_empty(order_tracker, mock_storage):
    """Empty storage gives back an empty list."""
    mock_storage.get_all_orders.return_value = {}

    assert order_tracker.list_orders_by_status("pending") == []


@pytest.mark.parametrize("bad_status", ["", "   ", "banana"])
def test_list_orders_by_status_rejects_invalid_status(order_tracker, mock_storage, bad_status):
    """An empty or unknown status raises an error."""
    with pytest.raises(ValueError):
        order_tracker.list_orders_by_status(bad_status)

    mock_storage.get_all_orders.assert_not_called()
