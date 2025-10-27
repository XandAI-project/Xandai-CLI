"""
Text Analyzer Tool - Analyze text and provide statistics
"""

import re
from collections import Counter


class TextAnalyzerTool:
    """Analyze text and provide detailed statistics."""

    @staticmethod
    def get_name():
        """Return the tool's name."""
        return "text_analyzer_tool"

    @staticmethod
    def get_description():
        """Return description of what the tool does."""
        return "Analyze text to get word count, character count, reading time, and other statistics"

    @staticmethod
    def get_parameters():
        """Return the parameters this tool accepts."""
        return {
            "text": "string (required) - Text to analyze",
        }

    def execute(self, text: str):
        """
        Execute the text analysis.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with analysis results
        """
        try:
            # Basic counts
            char_count = len(text)
            char_count_no_spaces = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))

            # Word analysis
            words = re.findall(r"\b\w+\b", text.lower())
            word_count = len(words)
            unique_words = len(set(words))

            # Sentence analysis
            sentences = re.split(r"[.!?]+", text)
            sentences = [s.strip() for s in sentences if s.strip()]
            sentence_count = len(sentences)

            # Paragraph analysis
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            paragraph_count = len(paragraphs)

            # Line analysis
            lines = text.split("\n")
            line_count = len(lines)

            # Most common words (excluding very short words)
            meaningful_words = [w for w in words if len(w) > 3]
            word_freq = Counter(meaningful_words)
            most_common = word_freq.most_common(10)

            # Reading time (average 200 words per minute)
            reading_time_minutes = word_count / 200

            # Average lengths
            avg_word_length = char_count_no_spaces / word_count if word_count > 0 else 0
            avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

            return {
                "success": True,
                "statistics": {
                    "characters": {
                        "total": char_count,
                        "without_spaces": char_count_no_spaces,
                    },
                    "words": {
                        "total": word_count,
                        "unique": unique_words,
                        "average_length": round(avg_word_length, 2),
                    },
                    "sentences": {
                        "total": sentence_count,
                        "average_words_per_sentence": round(avg_sentence_length, 2),
                    },
                    "paragraphs": paragraph_count,
                    "lines": line_count,
                },
                "reading_time": {
                    "minutes": round(reading_time_minutes, 1),
                    "formatted": self._format_reading_time(reading_time_minutes),
                },
                "most_common_words": [
                    {"word": word, "count": count} for word, count in most_common
                ],
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Analysis error: {str(e)}",
            }

    @staticmethod
    def _format_reading_time(minutes: float) -> str:
        """Format reading time in human-readable format."""
        if minutes < 1:
            seconds = int(minutes * 60)
            return f"{seconds} seconds"
        elif minutes < 60:
            return f"{int(minutes)} minute{'s' if minutes >= 2 else ''}"
        else:
            hours = int(minutes / 60)
            remaining_minutes = int(minutes % 60)
            return f"{hours}h {remaining_minutes}m"
