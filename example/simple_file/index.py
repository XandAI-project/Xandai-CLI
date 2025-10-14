import tokens
from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory storage for objects
stored_objects = []


@app.route("/")
def hello():
    return "Hello, World!"


@app.route("/health", methods=["GET"])
def health():
    return {"status": "healthy"}


@app.route("/objects", methods=["POST"])
def store_object():
    # Get API key from headers
    api_key = request.headers.get("X-API-Key")

    if not api_key:
        return jsonify({"error": "API key is required"}), 401

    # Validate API key
    is_valid, user_id = tokens.validate_api_key(api_key)
    if not is_valid:
        return jsonify({"error": "Invalid or expired API key"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    # Store the object in memory with user info
    stored_objects.append({"data": data, "user_id": user_id})

    return jsonify({"message": "Object stored successfully", "data": data}), 201


@app.route("/objects", methods=["GET"])
def get_objects():
    # Get API key from headers
    api_key = request.headers.get("X-API-Key")

    if not api_key:
        return jsonify({"error": "API key is required"}), 401

    # Validate API key
    is_valid, user_id = tokens.validate_api_key(api_key)
    if not is_valid:
        return jsonify({"error": "Invalid or expired API key"}), 401

    # Return objects with user info
    return jsonify({"objects": stored_objects})


@app.route("/api-keys", methods=["POST"])
def create_api_key():
    # Get user ID from request body
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    # Generate API key with default 30-day expiry
    api_key = tokens.create_api_key(user_id, expiry_days=30)

    return jsonify({"api_key": api_key}), 201


@app.route("/api-keys/<string:api_key>", methods=["DELETE"])
def revoke_api_key(api_key):
    # Validate API key first
    is_valid, user_id = tokens.validate_api_key(api_key)
    if not is_valid:
        return jsonify({"error": "Invalid or expired API key"}), 401

    # Revoke the key
    success = tokens.revoke_api_key(api_key)

    if success:
        return jsonify({"message": "API key revoked successfully"}), 200
    else:
        return jsonify({"error": "API key not found"}), 404


if __name__ == "__main__":
    app.run(debug=True)
