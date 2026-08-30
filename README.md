# UdaTracker

An order tracking service built with Flask and pytest, using a test first
approach. The business rules live in a plain Python class called
`OrderTracker`, which does not import Flask. A small Flask layer sits on top
and exposes those rules as a REST API, which the frontend then calls.

Starter code: [udacity/cd14599-project-starter](https://github.com/udacity/cd14599-project-starter)

## Layout

```
.
└── starter/                        run all commands from here
    ├── pytest.ini
    ├── README.md                   reflection and API notes
    ├── backend/
    │   ├── app.py                  Flask routes
    │   ├── order_tracker.py        business rules, no Flask
    │   ├── in_memory_storage.py    storage backed by a dictionary
    │   ├── requirements.txt
    │   └── tests/
    │       ├── test_order_tracker.py   unit tests using a mock store
    │       └── test_api.py             integration tests using Flask's test client
    └── frontend/                   provided web page
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate            # on Windows: .\venv\Scripts\Activate.ps1
pip install -r starter/backend/requirements.txt
```

## Running the tests

Run them from the `starter/` folder. The `pytest.ini` file there sets
`pythonpath = .`, which is what lets `from backend.app import app` work.

```bash
cd starter
pytest
```

## Running the app

```bash
cd starter
python -m backend.app
```

Then open http://127.0.0.1:5000/ in a browser. Orders are only held in memory,
so they are cleared when the server restarts.

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

## License

See [LICENSE.txt](LICENSE.txt). Starter code belongs to Udacity.
