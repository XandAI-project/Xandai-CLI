from flask import Flask, jsonify, request

# Initialize the Flask application
app = Flask(__name__)

# In-memory storage for messages
messages = []


# Message model (simulated)
class Message:
    def __init__(self, id, content, timestamp=None):
        self.id = id
        self.content = content
        self.timestamp = timestamp or "2023-01-01T00:00:00Z"

    def to_dict(self):
        return {"id": self.id, "content": self.content, "timestamp": self.timestamp}


# Helper function to find message by ID
def find_message_by_id(message_id):
    for msg in messages:
        if msg.id == message_id:
            return msg
    return None


# HEALTH endpoint
@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint to verify API is running
    Returns:
        JSON response with status and timestamp
    """
    return jsonify({"status": "healthy", "timestamp": "2023-01-01T00:00:00Z"}), 200


# GET all messages endpoint
@app.route("/messages", methods=["GET"])
def get_messages():
    """
    Retrieve all messages from memory
    Returns:
        JSON list of all messages
    """
    return jsonify([msg.to_dict() for msg in messages]), 200


# POST new message endpoint
@app.route("/messages", methods=["POST"])
def create_message():
    """
    Create a new message in memory
    Request body should contain:
        - content (string): the message content
    Returns:
        JSON response with created message and 201 status
    """
    data = request.get_json()

    if not data or "content" not in data:
        return jsonify({"error": "Content is required"}), 400

    # Generate new ID (simple increment)
    new_id = len(messages) + 1

    # Create new message object
    new_message = Message(new_id, data["content"])

    # Store in memory
    messages.append(new_message)

    return jsonify(new_message.to_dict()), 201


# GET single message endpoint
@app.route("/messages/<int:message_id>", methods=["GET"])
def get_message(message_id):
    """
    Retrieve a specific message by ID
    Args:
        message_id (int): The ID of the message to retrieve
    Returns:
        JSON response with message if found, 404 if not found
    """
    message = find_message_by_id(message_id)

    if not message:
        return jsonify({"error": "Message not found"}), 404

    return jsonify(message.to_dict()), 200


# PUT update message endpoint
@app.route("/messages/<int:message_id>", methods=["PUT"])
def update_message(message_id):
    """
    Update an existing message by ID
    Args:
        message_id (int): The ID of the message to update
    Request body should contain:
        - content (string): updated message content
    Returns:
        JSON response with updated message if found, 404 if not found
    """
    message = find_message_by_id(message_id)

    if not message:
        return jsonify({"error": "Message not found"}), 404

    data = request.get_json()

    if not data or "content" not in data:
        return jsonify({"error": "Content is required"}), 400

    # Update content
    message.content = data["content"]

    return jsonify(message.to_dict()), 200


# DELETE message endpoint
@app.route("/messages/<int:message_id>", methods=["DELETE"])
def delete_message(message_id):
    """
    Delete a message by ID
    Args:
        message_id (int): The ID of the message to delete
    Returns:
        JSON response with success message if deleted, 404 if not found
    """
    message = find_message_by_id(message_id)

    if not message:
        return jsonify({"error": "Message not found"}), 404

    # Remove from memory
    messages.remove(message)

    return jsonify({"message": "Message deleted successfully"}), 200


# Run the application
if __name__ == "__main__":
    app.run(debug=True)
