"""
UUID Generator Tool - Generate UUIDs and random IDs
"""

import random
import string
import uuid


class UuidGeneratorTool:
    """Generate UUIDs and various random identifiers."""

    @staticmethod
    def get_name():
        """Return the tool's name."""
        return "uuid_generator_tool"

    @staticmethod
    def get_description():
        """Return description of what the tool does."""
        return "Generate UUIDs (v1, v4) and random identifiers"

    @staticmethod
    def get_parameters():
        """Return the parameters this tool accepts."""
        return {
            "type": "string (optional) - Type of ID: 'uuid4', 'uuid1', 'random_string', 'random_hex', 'random_number' (default: 'uuid4')",
            "count": "integer (optional) - Number of IDs to generate (default: 1, max: 20)",
            "length": "integer (optional) - Length for random strings/hex (default: 16)",
        }

    def execute(self, type: str = "uuid4", count: int = 1, length: int = 16):
        """
        Execute the UUID/ID generation.

        Args:
            type: Type of ID to generate
            count: Number of IDs to generate
            length: Length for random strings/hex

        Returns:
            Dictionary with generated IDs
        """
        try:
            # Validate count
            count = max(1, min(count, 20))  # Limit between 1 and 20
            length = max(4, min(length, 128))  # Limit between 4 and 128

            type = type.lower()
            ids = []

            for _ in range(count):
                if type == "uuid4":
                    ids.append(str(uuid.uuid4()))

                elif type == "uuid1":
                    ids.append(str(uuid.uuid1()))

                elif type == "random_string":
                    # Random alphanumeric string
                    chars = string.ascii_letters + string.digits
                    random_id = "".join(random.choices(chars, k=length))
                    ids.append(random_id)

                elif type == "random_hex":
                    # Random hexadecimal string
                    random_id = "".join(random.choices(string.hexdigits.lower(), k=length))
                    ids.append(random_id)

                elif type == "random_number":
                    # Random number string
                    random_id = "".join(random.choices(string.digits, k=length))
                    ids.append(random_id)

                else:
                    return {
                        "success": False,
                        "error": f"Unknown type: {type}. Use: uuid4, uuid1, random_string, random_hex, random_number",
                    }

            result = {
                "success": True,
                "type": type,
                "count": len(ids),
                "ids": ids,
            }

            # Add single ID field for convenience when count is 1
            if len(ids) == 1:
                result["id"] = ids[0]

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Generation error: {str(e)}",
            }
