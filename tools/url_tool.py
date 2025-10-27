"""
URL Tool - Parse, encode, decode, and analyze URLs
"""

import re
from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse


class UrlTool:
    """Parse, encode, decode, and analyze URLs."""

    @staticmethod
    def get_name():
        """Return the tool's name."""
        return "url_tool"

    @staticmethod
    def get_description():
        """Return description of what the tool does."""
        return (
            "Parse URLs, encode/decode URL components, extract query parameters, and validate URLs"
        )

    @staticmethod
    def get_parameters():
        """Return the parameters this tool accepts."""
        return {
            "url": "string (required) - URL to process",
            "operation": "string (optional) - Operation: 'parse', 'encode', 'decode', 'validate' (default: 'parse')",
        }

    def execute(self, url: str, operation: str = "parse"):
        """
        Execute the URL operation.

        Args:
            url: URL to process
            operation: Operation to perform

        Returns:
            Dictionary with URL operation results
        """
        try:
            operation = operation.lower()

            # Parse URL
            if operation == "parse":
                parsed = urlparse(url)
                query_params = parse_qs(parsed.query)

                # Extract path segments
                path_segments = [s for s in parsed.path.split("/") if s]

                # Detect URL type
                url_type = self._detect_url_type(url)

                return {
                    "success": True,
                    "operation": "parse",
                    "original_url": url,
                    "components": {
                        "scheme": parsed.scheme or None,
                        "domain": parsed.netloc or None,
                        "hostname": parsed.hostname or None,
                        "port": parsed.port or None,
                        "path": parsed.path or None,
                        "query": parsed.query or None,
                        "fragment": parsed.fragment or None,
                    },
                    "path_segments": path_segments,
                    "query_parameters": {
                        key: values[0] if len(values) == 1 else values
                        for key, values in query_params.items()
                    },
                    "url_type": url_type,
                    "is_valid": bool(parsed.scheme and parsed.netloc),
                }

            # Encode URL
            elif operation == "encode":
                encoded = quote(url, safe="")

                return {
                    "success": True,
                    "operation": "encode",
                    "original": url,
                    "encoded": encoded,
                    "length_change": len(encoded) - len(url),
                }

            # Decode URL
            elif operation == "decode":
                decoded = unquote(url)

                return {
                    "success": True,
                    "operation": "decode",
                    "original": url,
                    "decoded": decoded,
                    "was_encoded": decoded != url,
                }

            # Validate URL
            elif operation == "validate":
                parsed = urlparse(url)
                is_valid = bool(parsed.scheme and parsed.netloc)

                validation = {
                    "has_scheme": bool(parsed.scheme),
                    "has_domain": bool(parsed.netloc),
                    "has_path": bool(parsed.path),
                    "has_query": bool(parsed.query),
                    "has_fragment": bool(parsed.fragment),
                }

                # Additional checks
                issues = []
                if not parsed.scheme:
                    issues.append("Missing protocol/scheme (http, https, etc.)")
                if not parsed.netloc:
                    issues.append("Missing domain name")
                if parsed.scheme and parsed.scheme not in [
                    "http",
                    "https",
                    "ftp",
                    "ftps",
                    "ws",
                    "wss",
                ]:
                    issues.append(f"Uncommon scheme: {parsed.scheme}")

                return {
                    "success": True,
                    "operation": "validate",
                    "url": url,
                    "is_valid": is_valid,
                    "validation": validation,
                    "issues": issues if issues else None,
                    "suggestion": self._get_url_suggestion(url, parsed) if issues else None,
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown operation: {operation}. Use: parse, encode, decode, validate",
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"URL error: {str(e)}",
            }

    @staticmethod
    def _detect_url_type(url: str) -> str:
        """Detect the type of URL."""
        if re.match(r"^https?://(?:www\.)?github\.com/", url):
            return "GitHub repository"
        elif re.match(r"^https?://(?:www\.)?youtube\.com/", url):
            return "YouTube video"
        elif re.match(r"^https?://(?:www\.)?twitter\.com/", url):
            return "Twitter/X post"
        elif re.match(r"^https?://(?:www\.)?linkedin\.com/", url):
            return "LinkedIn page"
        elif re.match(r"^https?://[^/]+\.(?:com|org|net|edu|gov)/?$", url):
            return "Homepage/Root URL"
        elif re.match(r"^https?://api\.", url):
            return "API endpoint"
        elif "/api/" in url.lower():
            return "API endpoint"
        elif re.search(r"\.(jpg|jpeg|png|gif|webp|svg)$", url, re.I):
            return "Image URL"
        elif re.search(r"\.(mp4|avi|mov|webm|mkv)$", url, re.I):
            return "Video URL"
        elif re.search(r"\.(pdf|doc|docx|xls|xlsx)$", url, re.I):
            return "Document URL"
        else:
            return "Web page"

    @staticmethod
    def _get_url_suggestion(url: str, parsed) -> str:
        """Get suggestion for fixing URL."""
        if not parsed.scheme and not parsed.netloc:
            # Might be a domain without protocol
            if "." in url and not url.startswith("."):
                return f"Try: https://{url}"
        elif not parsed.scheme:
            return f"Try: https://{url}"
        return None
