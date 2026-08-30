# Udatracker

An order tracking service built with Flask, using a test first approach. The
business rules live in `backend/order_tracker.py` and do not import Flask.
`backend/app.py` is a thin layer on top that handles the HTTP side.

All 42 tests pass: 36 unit tests that I wrote for `OrderTracker`, plus the 6
integration tests that came with the starter code.

```bash
cd starter
pytest                    # 42 passed
python -m backend.app     # http://127.0.0.1:5000/
```

## Reflection

* At first I raised a plain `ValueError` for every problem. That made the API
  layer messy, because it had to read the error message text to decide between
  400, 404 and 409. I replaced it with three small error classes that all
  inherit from `ValueError`, so none of my tests had to change, and `app.py`
  now maps each class to a status code in one place.

* Mocks were more useful than I expected. `assert_not_called()` showed me that
  `update_order_status` was reading from storage before it checked the new
  status was valid. Both versions return the same error, so a normal test would
  never have caught it.

* Two of my tests passed before I had written any code. "Returns None when the
  order is missing" is also true of an empty method. After that I ran every
  test and watched it fail first.

* Next I would add a DELETE endpoint and swap the in memory storage for SQLite.
  `OrderTracker` only depends on three storage methods, so the business logic
  should not need to change.

## Project structure

```
.
├── backend
│   ├── __init__.py
│   ├── app.py
│   ├── in_memory_storage.py
│   ├── order_tracker.py
│   ├── requirements.txt
│   └── tests
│       ├── __init__.py
│       ├── test_api.py
│       └── test_order_tracker.py
├── frontend
│   ├── css
│   │   └── style.css
│   ├── index.html
│   └── js
│       └── script.js
├── pytest.ini
└── README.md
```

## API

The allowed statuses are `pending`, `processing`, `shipped`, `delivered` and
`cancelled`.

| Endpoint | Method | Body | Success | Errors |
| --- | --- | --- | --- | --- |
| `/api/orders` | POST | `{order_id, item_name, quantity, customer_id, status}` (status optional) | `201` and the order | `400` bad input, `409` ID already used |
| `/api/orders/<order_id>` | GET | none | `200` and the order | `404` no such order |
| `/api/orders/<order_id>/status` | PUT | `{new_status}` | `200` and the updated order | `400` bad status, `404` no such order |
| `/api/orders` | GET | none | `200` and a list of all orders | none |
| `/api/orders?status=<status>` | GET | none | `200` and a filtered list | `400` empty or unknown status |

Errors always come back in the same shape, `{"error": "message"}`, because
`app.py` registers one handler per error class.

```bash
# Create an order
curl -X POST http://127.0.0.1:5000/api/orders \
     -H "Content-Type: application/json" \
     -d '{"order_id":"CURL001","item_name":"Headphones","quantity":1,"customer_id":"CUST123"}'

# Read it back
curl http://127.0.0.1:5000/api/orders/CURL001

# Change its status
curl -X PUT http://127.0.0.1:5000/api/orders/CURL001/status \
     -H "Content-Type: application/json" -d '{"new_status":"shipped"}'

# Only the shipped orders
curl "http://127.0.0.1:5000/api/orders?status=shipped"
```

Orders are only held in memory, so they are cleared whenever the server
restarts.
