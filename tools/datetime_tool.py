"""
DateTime Tool - Work with dates, times, and timezones
"""

import time
from datetime import datetime, timedelta


class DateTimeTool:
    """Work with dates, times, conversions, and calculations."""

    @staticmethod
    def get_name():
        """Return the tool's name."""
        return "datetime_tool"

    @staticmethod
    def get_description():
        """Return description of what the tool does."""
        return "Get current date/time, convert timestamps, calculate date differences, and format dates"

    @staticmethod
    def get_parameters():
        """Return the parameters this tool accepts."""
        return {
            "operation": "string (optional) - Operation: 'now', 'timestamp', 'format', 'parse', 'diff', 'add' (default: 'now')",
            "value": "string (optional) - Value for operation (timestamp, date string, or number of days)",
            "format": "string (optional) - Date format string (default: ISO 8601)",
        }

    def execute(self, operation: str = "now", value: str = None, format: str = None):
        """
        Execute the datetime operation.

        Args:
            operation: Operation to perform
            value: Input value for operation
            format: Date format string

        Returns:
            Dictionary with datetime results
        """
        try:
            operation = operation.lower()

            # Current datetime
            if operation == "now":
                now = datetime.now()
                return {
                    "success": True,
                    "operation": "now",
                    "datetime": {
                        "iso": now.isoformat(),
                        "formatted": now.strftime("%Y-%m-%d %H:%M:%S"),
                        "date": now.strftime("%Y-%m-%d"),
                        "time": now.strftime("%H:%M:%S"),
                        "timestamp": int(now.timestamp()),
                        "year": now.year,
                        "month": now.month,
                        "day": now.day,
                        "hour": now.hour,
                        "minute": now.minute,
                        "second": now.second,
                        "weekday": now.strftime("%A"),
                    },
                }

            # Convert timestamp to datetime
            elif operation == "timestamp":
                if not value:
                    return {
                        "success": False,
                        "error": "Value (timestamp) is required for 'timestamp' operation",
                    }

                timestamp = int(value)
                dt = datetime.fromtimestamp(timestamp)

                return {
                    "success": True,
                    "operation": "timestamp",
                    "input_timestamp": timestamp,
                    "datetime": {
                        "iso": dt.isoformat(),
                        "formatted": dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "date": dt.strftime("%Y-%m-%d"),
                        "time": dt.strftime("%H:%M:%S"),
                        "weekday": dt.strftime("%A"),
                    },
                }

            # Format datetime
            elif operation == "format":
                if not format:
                    format = "%Y-%m-%d %H:%M:%S"

                now = datetime.now()
                formatted = now.strftime(format)

                return {
                    "success": True,
                    "operation": "format",
                    "format": format,
                    "result": formatted,
                    "examples": {
                        "ISO 8601": now.strftime("%Y-%m-%dT%H:%M:%S"),
                        "US format": now.strftime("%m/%d/%Y %I:%M %p"),
                        "EU format": now.strftime("%d/%m/%Y %H:%M"),
                        "Long format": now.strftime("%A, %B %d, %Y at %I:%M %p"),
                    },
                }

            # Add days to current date
            elif operation == "add":
                if not value:
                    return {
                        "success": False,
                        "error": "Value (number of days) is required for 'add' operation",
                    }

                days = int(value)
                now = datetime.now()
                future = now + timedelta(days=days)

                return {
                    "success": True,
                    "operation": "add",
                    "days_added": days,
                    "from_date": now.strftime("%Y-%m-%d"),
                    "to_date": future.strftime("%Y-%m-%d"),
                    "result": {
                        "iso": future.isoformat(),
                        "formatted": future.strftime("%Y-%m-%d %H:%M:%S"),
                        "weekday": future.strftime("%A"),
                    },
                }

            # Calculate difference
            elif operation == "diff":
                # For simplicity, calculate days from now to a future timestamp
                if not value:
                    return {
                        "success": False,
                        "error": "Value (timestamp or date) is required for 'diff' operation",
                    }

                now = datetime.now()
                try:
                    # Try as timestamp
                    target = datetime.fromtimestamp(int(value))
                except ValueError:
                    # Try as date string
                    target = datetime.fromisoformat(value)

                diff = target - now

                return {
                    "success": True,
                    "operation": "diff",
                    "from": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "to": target.strftime("%Y-%m-%d %H:%M:%S"),
                    "difference": {
                        "days": diff.days,
                        "seconds": diff.seconds,
                        "total_seconds": int(diff.total_seconds()),
                        "total_hours": round(diff.total_seconds() / 3600, 2),
                        "total_minutes": round(diff.total_seconds() / 60, 2),
                        "formatted": self._format_timedelta(diff),
                    },
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown operation: {operation}. Use: now, timestamp, format, add, diff",
                }

        except ValueError as e:
            return {"success": False, "error": f"Invalid value: {str(e)}"}
        except Exception as e:
            return {
                "success": False,
                "error": f"DateTime error: {str(e)}",
            }

    @staticmethod
    def _format_timedelta(td: timedelta) -> str:
        """Format timedelta in human-readable format."""
        days = td.days
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if days:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds and not days:  # Only show seconds if less than a day
            parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

        return ", ".join(parts) if parts else "0 seconds"
