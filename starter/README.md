# Udatracker

An order-tracking service built test-first with pytest and Flask, following the
Red → Green → Refactor cycle. Business rules live in `backend/order_tracker.py`
(no Flask imports); `backend/app.py` is a thin HTTP layer over it.

**Final state:** 42 tests passing — 36 unit tests over mocked storage, 6 provided
integration tests over the Flask test client.

```bash
cd starter
pytest                    # 42 passed
python -m backend.app     # http://127.0.0.1:5000/
```

## Reflection

- **Design trade-off.** I first raised a plain `ValueError` for every failure, which forced the
  API layer to match on message text to choose between 400, 404 and 409 — a mapping that breaks
  silently the moment anyone rewords a message. I refactored to `ValidationError`,
  `DuplicateOrderError` and `OrderNotFoundError`, all subclassing `ValueError` so my existing
  tests kept passing, and mapped type to status code in three `@app.errorhandler`s.

- **Testing insight.** `assert_not_called()` caught `update_order_status` reading from storage
  *before* validating the new status. Both orderings return an identical error, so no
  output-based test could have seen it — only a mock recording the collaboration.

- **A test that lied.** Two of my tests passed against methods that still said `pass`; "returns
  None when missing" is vacuously true of a no-op. Good reason to watch a test fail first.

- **Next step.** Add `DELETE /api/orders/<id>` and swap `InMemoryStorage` for SQLite. Since
  `OrderTracker` depends on three storage methods rather than a dict, the unit tests should keep
  passing untouched.

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

## API reference

Valid statuses: `pending`, `processing`, `shipped`, `delivered`, `cancelled`.

| Endpoint | Method | Body | Success | Errors |
| --- | --- | --- | --- | --- |
| `/api/orders` | POST | `{order_id, item_name, quantity, customer_id, status?}` | `201` + order | `400` invalid input, `409` duplicate ID |
| `/api/orders/<order_id>` | GET | – | `200` + order | `404` not found |
| `/api/orders/<order_id>/status` | PUT | `{new_status}` | `200` + updated order | `400` invalid status, `404` not found |
| `/api/orders` | GET | – | `200` + list of all orders | – |
| `/api/orders?status=<status>` | GET | – | `200` + filtered list | `400` empty or invalid status |

Errors are returned as `{"error": "message"}` by three centralised
`@app.errorhandler`s, so every failure has the same shape.

```bash
# Create → 201
curl -X POST http://127.0.0.1:5000/api/orders \
     -H "Content-Type: application/json" \
     -d '{"order_id":"CURL001","item_name":"Headphones","quantity":1,"customer_id":"CUST123"}'

# Read → 200
curl http://127.0.0.1:5000/api/orders/CURL001

# Update → 200
curl -X PUT http://127.0.0.1:5000/api/orders/CURL001/status \
     -H "Content-Type: application/json" -d '{"new_status":"shipped"}'

# Filter → 200
curl "http://127.0.0.1:5000/api/orders?status=shipped"
```

Data is stored in memory only and resets whenever the server restarts.
