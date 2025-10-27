"""
Hash Tool - Generate cryptographic hashes for text
"""

import base64
import hashlib


class HashTool:
    """Generate cryptographic hashes and encodings."""

    @staticmethod
    def get_name():
        """Return the tool's name."""
        return "hash_tool"

    @staticmethod
    def get_description():
        """Return description of what the tool does."""
        return "Generate cryptographic hashes (MD5, SHA256, SHA512) and encodings (Base64) for text"

    @staticmethod
    def get_parameters():
        """Return the parameters this tool accepts."""
        return {
            "text": "string (required) - Text to hash or encode",
            "algorithm": "string (optional) - Hash algorithm: 'md5', 'sha1', 'sha256', 'sha512', 'base64', 'all' (default: 'all')",
        }

    def execute(self, text: str, algorithm: str = "all"):
        """
        Execute the hash/encoding operation.

        Args:
            text: Text to hash or encode
            algorithm: Hash algorithm to use

        Returns:
            Dictionary with hash results
        """
        try:
            text_bytes = text.encode("utf-8")
            algorithm = algorithm.lower()

            results = {}

            # Generate requested hashes
            if algorithm in ["md5", "all"]:
                results["md5"] = hashlib.md5(text_bytes).hexdigest()

            if algorithm in ["sha1", "all"]:
                results["sha1"] = hashlib.sha1(text_bytes).hexdigest()

            if algorithm in ["sha256", "all"]:
                results["sha256"] = hashlib.sha256(text_bytes).hexdigest()

            if algorithm in ["sha512", "all"]:
                results["sha512"] = hashlib.sha512(text_bytes).hexdigest()

            if algorithm in ["base64", "all"]:
                results["base64"] = base64.b64encode(text_bytes).decode("utf-8")

            # Add Base64 decode capability
            if algorithm == "base64_decode":
                try:
                    decoded = base64.b64decode(text).decode("utf-8")
                    results["base64_decoded"] = decoded
                except Exception as e:
                    results["base64_decode_error"] = f"Invalid Base64: {str(e)}"

            if not results:
                return {
                    "success": False,
                    "error": f"Unknown algorithm: {algorithm}. Use: md5, sha1, sha256, sha512, base64, base64_decode, or all",
                }

            return {
                "success": True,
                "input": text[:100] + ("..." if len(text) > 100 else ""),
                "input_length": len(text),
                "algorithm": algorithm,
                "results": results,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Hash error: {str(e)}",
            }
