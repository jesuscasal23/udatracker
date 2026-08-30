# UdaTracker — Order Tracking Service (TDD)

A minimal order-tracking service built test-first with **pytest** and **Flask**, following the
Red → Green → Refactor cycle. Business logic lives in a framework-agnostic `OrderTracker` class;
a thin Flask layer exposes it as a REST API that the provided frontend consumes.

Udacity project starter: [udacity/cd14599-project-starter](https://github.com/udacity/cd14599-project-starter)

## Layout

```
.
└── starter/                        # ← project root: run all commands from here
    ├── pytest.ini
    ├── README.md                   # reflection + API reference
    ├── backend/
    │   ├── app.py                  # Flask routes (HTTP layer)
    │   ├── order_tracker.py        # business logic (no Flask)
    │   ├── in_memory_storage.py    # dict-backed store
    │   ├── requirements.txt
    │   └── tests/
    │       ├── test_order_tracker.py   # unit tests (mocked storage)
    │       └── test_api.py             # integration tests (Flask test client)
    └── frontend/                   # provided UI — index.html, css/, js/
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate            # Windows: .\venv\Scripts\Activate.ps1
pip install -r starter/backend/requirements.txt
```

## Run the tests

Always from the `starter/` directory — `pytest.ini` sets `pythonpath = .` there, which is what
makes `from backend.app import app` resolve.

```bash
cd starter
pytest
```

## Run the app

```bash
cd starter
python -m backend.app
```

Then open <http://127.0.0.1:5000/>. Data is in-memory only and resets on restart.

## API

| Endpoint | Method | Body | Success | Errors |
| --- | --- | --- | --- | --- |
| `/api/orders` | POST | `{order_id, item_name, quantity, customer_id, status?}` | `201` + order | `400` invalid, `409` duplicate ID |
| `/api/orders/<order_id>` | GET | – | `200` + order | `404` not found |
| `/api/orders/<order_id>/status` | PUT | `{new_status}` | `200` + updated order | `400` invalid status, `404` not found |
| `/api/orders` | GET | – | `200` + list of orders | – |
| `/api/orders?status=<status>` | GET | – | `200` + filtered list | `400` empty/invalid status |

Valid statuses: `pending`, `processing`, `shipped`, `delivered`, `cancelled`.

## License

See [LICENSE.txt](LICENSE.txt). Starter code © Udacity.
