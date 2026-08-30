from flask import Flask, request, jsonify, send_from_directory
from backend.order_tracker import (
    OrderTracker,
    DuplicateOrderError,
    OrderNotFoundError,
    ValidationError,
)
from backend.in_memory_storage import InMemoryStorage

app = Flask(__name__, static_folder='../frontend')
in_memory_storage = InMemoryStorage()
order_tracker = OrderTracker(in_memory_storage)


# --- Error handling ---
# These turn the errors raised by OrderTracker into JSON responses, so every
# failure comes back in the same shape.


@app.errorhandler(ValidationError)
def handle_validation_error(error):
    return jsonify({"error": str(error)}), 400


@app.errorhandler(DuplicateOrderError)
def handle_duplicate_order_error(error):
    return jsonify({"error": str(error)}), 409


@app.errorhandler(OrderNotFoundError)
def handle_order_not_found_error(error):
    return jsonify({"error": str(error)}), 404


# --- Frontend ---


@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

# --- API ---


@app.route('/api/orders', methods=['POST'])
def add_order_api():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    new_order = order_tracker.add_order(
        order_id=data.get("order_id"),
        item_name=data.get("item_name"),
        quantity=data.get("quantity"),
        customer_id=data.get("customer_id"),
        status=data.get("status", "pending"),
    )
    return jsonify(new_order), 201


@app.route('/api/orders/<string:order_id>', methods=['GET'])
def get_order_api(order_id):
    order = order_tracker.get_order_by_id(order_id)
    if order is None:
        return jsonify({"error": f"Order with ID '{order_id}' not found."}), 404
    return jsonify(order), 200


# The status can be updated at either path, so both are handled here.
@app.route('/api/orders/<string:order_id>/status', methods=['PUT'])
@app.route('/api/orders/<string:order_id>', methods=['PUT'])
def update_order_status_api(order_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "new_status" not in data:
        return jsonify({"error": "Request body must include 'new_status'."}), 400

    updated_order = order_tracker.update_order_status(order_id, data["new_status"])
    return jsonify(updated_order), 200


@app.route('/api/orders', methods=['GET'])
def list_orders_api():
    status = request.args.get("status")
    if status is None:
        return jsonify(order_tracker.list_all_orders()), 200
    return jsonify(order_tracker.list_orders_by_status(status)), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
