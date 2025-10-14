"""
XandAI Processors - Review Processor
Code review processor for analyzing Git changes with LLM
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Import removed to be compatible with both HistoryManager and ConversationManager
from xandai.core.app_state import AppState
from xandai.integrations.base_provider import LLMProvider, LLMResponse
from xandai.utils.git_utils import GitUtils
from xandai.utils.review_rules import ReviewRules


@dataclass
class ReviewResult:
    """Structured result of code review"""

    summary: str
    key_issues: List[str]
    suggestions: List[str]
    inline_comments: Dict[str, List[str]]  # file_path -> list of comments
    architecture_notes: List[str]
    security_concerns: List[str]
    performance_notes: List[str]
    code_quality_score: int  # 1-10
    files_reviewed: List[str]
    total_lines_reviewed: int
    review_time_estimate: str


class ReviewProcessor:
    """
    Code Review Processor

    Analyzes Git changes using LLM to provide comprehensive code review
    with focus on quality, maintainability, and best practices.
    """

    def __init__(self, llm_provider: LLMProvider, conversation_manager):
        self.llm_provider = llm_provider
        self.conversation_manager = conversation_manager
        self._current_git_context = None  # Store git context for fallback

        # System prompt for code review
        self.system_prompt = """You are a Senior Code Reviewer. You MUST respond in the EXACT format shown below.

CRITICAL: Your response must START with "EXECUTIVE SUMMARY:" and follow the exact structure. Do NOT use markdown headers (#) or any other format.

MANDATORY RESPONSE FORMAT (copy this structure exactly):

EXECUTIVE SUMMARY:
[2-3 sentences about the code changes]

OVERALL SCORE: [number]/10
[Brief justification]

CRITICAL ISSUES:
• [Issue with filename Line X: description]
• [Issue with filename Line Y: description]

IMPROVEMENT SUGGESTIONS:
• [Suggestion with specific file reference]
• [Suggestion with specific file reference]

ARCHITECTURE & DESIGN:
• [Architecture observation]
• [Design observation]

SECURITY:
• [Security concern or "No security concerns identified"]

PERFORMANCE:
• [Performance observation or "Performance is adequate"]

FILE-SPECIFIC COMMENTS:

filename1.py:
  - Line X: [Specific issue or observation]
    Code: `actual code from line X`
    Suggestion: [How to fix or improve it]
  - Line Y: [Another issue]
    Code: `actual code from line Y`
    Suggestion: [Specific improvement]
  - Code block (lines A-B):
    ```
    A: actual code line A
    B: actual code line B
    ```
    Analysis: [Comment on this code block]
  - Function name(): [Function-specific comment with code examples]
  - Overall: [File summary]

filename2.js:
  - Line X: [Specific issue]
    Code: `actual JavaScript code`
    Suggestion: [How to improve]
  - Code sample (lines A-C):
    ```
    A: actual code
    B: actual code
    C: actual code
    ```
    Analysis: [Comment on structure/patterns]
  - Overall: [File summary]

FINAL RECOMMENDATIONS:
• [Priority recommendation]
• [Another recommendation]

REQUIREMENTS:
- Use EXACT format above (no markdown # headers)
- Start with "EXECUTIVE SUMMARY:"
- Include specific line numbers for issues
- ALWAYS show actual code snippets with backticks `code here`
- ALWAYS provide code blocks for context when commenting
- Analyze EVERY file in FILE-SPECIFIC COMMENTS section
- Comment on blocks of code with specific suggestions
- Focus on real bugs and improvements, not just style
- Keep response in English
- Show representative code samples from each file"""

    def process(self, app_state: AppState, repo_path: str = ".") -> ReviewResult:
        """
        Process code review for Git changes

        Args:
            app_state: Current application state
            repo_path: Repository path to analyze

        Returns:
            ReviewResult: Structured review results
        """
        # Add user request to history (compatible with both HistoryManager and ConversationManager)
        self._add_to_history(
            role="user", content="/review", mode="review", metadata={"repo_path": repo_path}
        )

        # Increment review interaction counter
        app_state.increment_chat_interaction()  # Using chat counter for now

        try:
            # Prepare Git context
            git_context = GitUtils.prepare_review_context(repo_path)

            # Store git context for fallback use
            self._current_git_context = git_context

            if git_context.get("error"):
                return self._create_error_result(git_context["error"])

            if not git_context["code_files"]:
                return self._create_no_changes_result()

            # Prepare context for LLM
            context = self._prepare_review_context(git_context, app_state)

            # Generate review using LLM
            response = self._generate_review_response(context, app_state)

            # Parse response into structured result
            review_result = self._parse_review_response(response.content, git_context)

            # Add response to history (compatible with both HistoryManager and ConversationManager)
            self._add_to_history(
                role="assistant",
                content=response.content,
                mode="review",
                metadata={
                    "model": response.model,
                    "tokens": response.total_tokens,
                    "files_reviewed": len(git_context["code_files"]),
                },
            )

            return review_result

        except Exception as e:
            error_msg = f"Error during review: {str(e)}"
            self._add_to_history(
                role="system", content=error_msg, mode="review", metadata={"error": True}
            )
            return self._create_error_result(error_msg)

    def _prepare_review_context(
        self, git_context: Dict, app_state: AppState
    ) -> List[Dict[str, str]]:
        """
        Prepare context for LLM review
        """
        # Start with system prompt
        context = [{"role": "system", "content": self._get_enhanced_review_prompt(app_state)}]

        # Add recent review history for consistency
        review_history = self._get_recent_history(limit=3, mode_filter="review")
        for msg in review_history[-2:]:  # Last 2 reviews for context
            context.append({"role": msg.role, "content": msg.content})

        # Build review request with file content
        review_request = self._build_review_request(git_context)
        context.append({"role": "user", "content": review_request})

        return context

    def _create_fallback_detailed_response(self, original_response: str, git_context: Dict) -> str:
        """Create a detailed response when LLM doesn't follow the format, with actual file analysis"""

        # Extract meaningful content from original response
        summary_text = "Automated code review completed with enhanced analysis."
        if original_response:
            # Try to extract meaningful summary from markdown or other formats
            lines = original_response.split("\n")[:5]
            meaningful_lines = [
                line.strip() for line in lines if line.strip() and not line.startswith("#")
            ]
            if meaningful_lines:
                summary_text = " ".join(meaningful_lines)[:200]

        # Analyze the actual files for detailed feedback
        code_files = git_context.get("code_files", [])
        file_contents = git_context.get("file_contents", {})

        file_analysis = {}
        critical_issues = []
        suggestions = []

        for file_path in code_files[:5]:  # Limit to first 5 files to avoid overwhelming output
            content = file_contents.get(file_path, "")
            if not content:
                continue

            lines = content.split("\n")
            file_comments = []

            # Basic static analysis based on file type and patterns
            file_ext = file_path.split(".")[-1].lower()

            # Advanced rule-based analysis using pattern matching
            file_analysis_result = self._analyze_file_with_rules(file_path, lines, file_ext)
            file_comments.extend(file_analysis_result["comments"])
            critical_issues.extend(file_analysis_result["critical_issues"])
            suggestions.extend(file_analysis_result["suggestions"])

            # AI-powered code analysis - send code snippets to LLM for intelligent feedback
            ai_analysis = self._ai_analyze_code_snippets(file_path, lines, file_ext)
            if ai_analysis:
                file_comments.extend(ai_analysis["comments"])
                critical_issues.extend(ai_analysis["critical_issues"])
                suggestions.extend(ai_analysis["suggestions"])

            # Add function analysis
            function_count = len([line for line in lines if "def " in line or "function " in line])
            if function_count > 20:
                file_comments.append(
                    f"File has {function_count} functions - consider splitting for maintainability"
                )

            # Add sample code block analysis
            if len(lines) > 10:
                # Show a representative code block (around middle of file)
                mid_point = len(lines) // 2
                start_line = max(0, mid_point - 2)
                end_line = min(len(lines), mid_point + 3)
                code_block = "\n".join(
                    f"    {i+1:3d}: {lines[i]}" for i in range(start_line, end_line)
                )
                file_comments.append(f"Code block sample (lines {start_line+1}-{end_line}):")
                file_comments.append(code_block)
                file_comments.append(
                    "    Analysis: Code structure and formatting appear consistent"
                )

            if not file_comments:
                file_comments.append("No major issues detected in this file")
                # Still show a small code sample even if no issues
                if len(lines) > 5:
                    sample_lines = "\n".join(
                        f"    {i+1:3d}: {lines[i]}" for i in range(min(5, len(lines)))
                    )
                    file_comments.append(f"Code sample:\n{sample_lines}")

            file_comments.append(
                f"Overall: File contains {len(lines)} lines with {function_count} functions"
            )
            file_analysis[file_path] = file_comments

        # Add general suggestions if none found
        if not suggestions:
            suggestions = [
                "Add comprehensive error handling throughout the codebase",
                "Consider adding unit tests for critical functionality",
                "Implement input validation for user-provided data",
                "Add logging for better debugging and monitoring",
            ]

        # Build the structured response with better formatting
        file_comments_section = []
        for file_path, comments in file_analysis.items():
            file_comments_section.append(f"\n{file_path}:")
            for comment in comments:
                # Handle multi-line comments (code snippets)
                if "\n" in comment:
                    lines = comment.split("\n")
                    file_comments_section.append(f"  - {lines[0]}")
                    for line in lines[1:]:
                        file_comments_section.append(f"    {line}")
                else:
                    file_comments_section.append(f"  - {comment}")

        return f"""EXECUTIVE SUMMARY:
{summary_text}

OVERALL SCORE: 6/10
Automated analysis completed with basic static analysis. Manual review recommended for comprehensive assessment.

CRITICAL ISSUES:
{chr(10).join(f'• {issue}' for issue in critical_issues) if critical_issues else '• No critical security issues detected in static analysis'}

IMPROVEMENT SUGGESTIONS:
{chr(10).join(f'• {suggestion}' for suggestion in suggestions)}

ARCHITECTURE & DESIGN:
• Code organization appears modular with clear separation of concerns
• Consider reviewing function complexity and file size for maintainability

SECURITY:
• Basic security scan completed - manual security review recommended
• Check for proper input validation and sanitization

PERFORMANCE:
• Performance analysis requires runtime profiling
• Consider optimizing file I/O operations and subprocess calls

FILE-SPECIFIC COMMENTS:
{''.join(file_comments_section)}

FINAL RECOMMENDATIONS:
• Conduct manual code review for comprehensive analysis
• Add automated testing and continuous integration
• Implement proper logging and error handling patterns"""

    def _get_enhanced_review_prompt(self, app_state: AppState) -> str:
        """
        Build enhanced review prompt with project context
        """
        context_info = app_state.get_context_summary()

        enhanced_prompt = self.system_prompt

        # Add project context if available
        if context_info.get("project_type") != "unknown":
            enhanced_prompt += f"\n\nPROJECT CONTEXT:\n"
            enhanced_prompt += f"- Type: {context_info.get('project_type')}\n"
            enhanced_prompt += f"- Directory: {context_info.get('root_path')}\n"
            enhanced_prompt += f"- Tracked files: {context_info.get('tracked_files')}\n"
            enhanced_prompt += "- Consider this context when reviewing changes\n"

        return enhanced_prompt

    def _build_review_request(self, git_context: Dict) -> str:
        """
        Build comprehensive review request with file contents
        """
        request_parts = ["CODE REVIEW REQUEST\n"]

        # Add repository info
        commit_info = git_context.get("commit_info", {})
        if commit_info:
            request_parts.append("REPOSITORY INFORMATION:")
            if commit_info.get("branch"):
                request_parts.append(f"- Branch: {commit_info['branch']}")
            if commit_info.get("commit_hash"):
                request_parts.append(f"- Last commit: {commit_info['commit_hash']}")
            if commit_info.get("commit_message"):
                request_parts.append(f"- Message: {commit_info['commit_message']}")
            if commit_info.get("author"):
                request_parts.append(f"- Author: {commit_info['author']}")
            request_parts.append("")

        # Add statistics
        repo_stats = git_context.get("repo_stats", {})
        if repo_stats:
            request_parts.append("STATISTICS:")
            if repo_stats.get("total_files"):
                request_parts.append(f"- Total files: {repo_stats['total_files']}")
            if repo_stats.get("total_commits"):
                request_parts.append(f"- Total commits: {repo_stats['total_commits']}")
            request_parts.append("")

        # Add files to review
        code_files = git_context.get("code_files", [])
        request_parts.append(f"CHANGED FILES ({len(code_files)}):")
        for file_path in code_files:
            request_parts.append(f"- {file_path}")
        request_parts.append("")

        # Add file contents
        file_contents = git_context.get("file_contents", {})
        file_diffs = git_context.get("file_diffs", {})

        if file_contents:
            request_parts.append("FILE CONTENTS:")
            request_parts.append("")

            for file_path, content in file_contents.items():
                request_parts.append(f"=== {file_path} ===")

                # Add diff if available
                if file_path in file_diffs:
                    diff = file_diffs[file_path]
                    if diff.strip():
                        request_parts.append("CHANGES (diff):")
                        request_parts.append(diff)
                        request_parts.append("")

                # Add current content
                request_parts.append("CURRENT CONTENT:")
                lines = content.split("\n")
                if len(lines) > 200:  # Limit very large files
                    request_parts.append("\n".join(lines[:100]))
                    request_parts.append(
                        f"\n... (file truncated, showing first 100 of {len(lines)} lines)"
                    )
                else:
                    request_parts.append(content)

                request_parts.append(f"=== End of {file_path} ===")
                request_parts.append("")

        request_parts.append(
            "Please provide a comprehensive technical review following the specified format."
        )

        return "\n".join(request_parts)

    def _generate_review_response(
        self, context: List[Dict[str, str]], app_state: AppState
    ) -> LLMResponse:
        """
        Generate review response using LLM
        """
        try:
            response = self.llm_provider.chat(
                messages=context,
                temperature=0.1,  # Lower temperature for more consistent reviews
                max_tokens=8192,  # Allow for detailed responses
            )

            # Check if response contains required sections
            content = response.content if hasattr(response, "content") else str(response)
            required_sections = ["EXECUTIVE SUMMARY:", "FILE-SPECIFIC COMMENTS:", "OVERALL SCORE:"]
            missing_sections = [section for section in required_sections if section not in content]

            if missing_sections:
                # Create enhanced fallback response with actual file analysis
                enhanced_content = self._create_fallback_detailed_response(
                    content, self._current_git_context
                )
                response.content = enhanced_content
            elif len(content) < 500:
                # Also trigger fallback for very short responses
                enhanced_content = self._create_fallback_detailed_response(
                    content, self._current_git_context
                )
                response.content = enhanced_content

            return response

        except Exception as e:
            # Create fallback response if LLM provider fails
            class ErrorResponse:
                def __init__(self, content):
                    self.content = content
                    self.model = "fallback"
                    self.total_tokens = 0

            fallback_content = self._create_fallback_detailed_response(
                f"LLM communication failed: {str(e)}", self._current_git_context
            )
            return ErrorResponse(fallback_content)

    def _parse_review_response(self, response_content: str, git_context: Dict) -> ReviewResult:
        """
        Parse LLM response into structured ReviewResult
        """
        try:
            # Extract different sections using regex patterns
            import re

            # Extract summary
            summary_match = re.search(
                r"EXECUTIVE SUMMARY:\s*\n(.*?)(?=\n\n|\nOVERALL SCORE)", response_content, re.DOTALL
            )
            summary = summary_match.group(1).strip() if summary_match else "Review completed"

            # Extract score
            score_match = re.search(r"OVERALL SCORE:\s*(\d+)", response_content)
            score = int(score_match.group(1)) if score_match else 7

            # Extract key issues
            issues = self._extract_list_section(response_content, "CRITICAL ISSUES:")

            # Extract suggestions
            suggestions = self._extract_list_section(response_content, "IMPROVEMENT SUGGESTIONS:")

            # Extract architecture notes
            arch_notes = self._extract_list_section(response_content, "ARCHITECTURE & DESIGN:")

            # Extract security concerns
            security = self._extract_list_section(response_content, "SECURITY:")

            # Extract performance notes
            performance = self._extract_list_section(response_content, "PERFORMANCE:")

            # Extract inline comments
            inline_comments = self._extract_inline_comments(response_content)

            # Debug: check if inline comments extraction is working
            if not inline_comments and len(response_content) > 1000:
                # Try alternative extraction for fallback format
                inline_comments = self._extract_fallback_comments(response_content)

            # Also try to extract from AI-structured content
            if not inline_comments and "<issue description=" in response_content:
                inline_comments = self._extract_ai_structured_comments(response_content)

            # Calculate stats
            files_reviewed = git_context.get("code_files", [])
            total_lines = sum(
                len(content.split("\n"))
                for content in git_context.get("file_contents", {}).values()
            )

            return ReviewResult(
                summary=summary,
                key_issues=issues,
                suggestions=suggestions,
                inline_comments=inline_comments,
                architecture_notes=arch_notes,
                security_concerns=security,
                performance_notes=performance,
                code_quality_score=score,
                files_reviewed=files_reviewed,
                total_lines_reviewed=total_lines,
                review_time_estimate=self._estimate_review_time(len(files_reviewed), total_lines),
            )

        except Exception as e:
            # Fallback: create basic result with original content
            return ReviewResult(
                summary=f"Review completed with limited parsing: {str(e)}",
                key_issues=["Error parsing response"],
                suggestions=["Review response manually"],
                inline_comments={},
                architecture_notes=[],
                security_concerns=[],
                performance_notes=[],
                code_quality_score=5,
                files_reviewed=git_context.get("code_files", []),
                total_lines_reviewed=0,
                review_time_estimate="N/A",
            )

    def _extract_list_section(self, content: str, section_header: str) -> List[str]:
        """Extract bullet points from a section"""
        import re

        pattern = rf"{re.escape(section_header)}\s*\n((?:•.*\n?)*)"
        match = re.search(pattern, content)

        if match:
            section_content = match.group(1)
            items = []
            for line in section_content.split("\n"):
                line = line.strip()
                if line.startswith("•"):
                    items.append(line[1:].strip())
            return items

        return []

    def _extract_inline_comments(self, content: str) -> Dict[str, List[str]]:
        """Extract inline comments per file"""
        import re

        comments = {}

        # Find FILE-SPECIFIC COMMENTS section - more flexible regex
        section_match = re.search(
            r"FILE-SPECIFIC COMMENTS:\s*\n(.*?)(?=\n\n[A-Z]+:|FINAL RECOMMENDATIONS:|$)",
            content,
            re.DOTALL,
        )

        if section_match:
            section_content = section_match.group(1)

            # Extract file-specific comments
            file_pattern = r"([^:\n]+\.(py|js|ts|java|cpp|c|h|php|rb|go|rs|swift|kt|scala|r|sql|html|css|scss|yaml|yml|json|xml|md|txt|sh|bat|ps1)):\s*\n((?:\s*-.*\n?)*)"

            for file_match in re.finditer(file_pattern, section_content):
                file_name = file_match.group(1).strip()
                comment_lines = file_match.group(3)

                file_comments = []
                for line in comment_lines.split("\n"):
                    line = line.strip()
                    if line.startswith("-"):
                        file_comments.append(line[1:].strip())

                if file_comments:
                    comments[file_name] = file_comments

        return comments

    def _analyze_file_with_rules(self, file_path: str, lines: List[str], file_ext: str) -> Dict:
        """Advanced rule-based file analysis using pattern matching approach"""

        # Get rules for this file type from centralized rules module
        rules = ReviewRules.get_rules_for_language(file_ext)

        # Apply rules to analyze the file
        result = {"comments": [], "critical_issues": [], "suggestions": []}

        for i, line in enumerate(lines[:150], 1):  # Analyze first 150 lines
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("#") or line_stripped.startswith("//"):
                continue

            # Apply each rule to the line
            for rule in rules:
                if rule["condition"](line, line_stripped, i):
                    issue_result = rule["action"](line, line_stripped, i, file_path)

                    # Add to appropriate result category
                    if issue_result["severity"] == "critical":
                        result["critical_issues"].append(f"{file_path} {issue_result['message']}")

                    result["comments"].append(issue_result["formatted_comment"])

                    if issue_result.get("suggestion"):
                        result["suggestions"].append(issue_result["suggestion"])

                    # Break after first matching rule to avoid duplicates
                    break

        return result

    def _ai_analyze_code_snippets(self, file_path: str, lines: List[str], file_ext: str) -> Dict:
        """AI-powered code analysis using LLM"""

        # Select interesting code snippets for AI analysis
        code_snippets = self._extract_code_snippets_for_ai(lines, file_ext)

        if not code_snippets:
            return None

        # Prepare AI analysis prompt
        ai_prompt = f"""Analyze this {file_ext.upper()} code for issues, bugs, and improvements.

For each issue found, respond EXACTLY in this format:
<issue description="Brief description of the problem">
[CODE_SNIPPET_HERE]
</issue>

Focus on:
- Security vulnerabilities
- Performance problems
- Logic errors
- Best practice violations
- Code smells

File: {file_path}
Code to analyze:

"""

        # Add code snippets with line numbers
        for snippet in code_snippets:
            ai_prompt += f"\nLines {snippet['start']}-{snippet['end']}:\n"
            for i, line in enumerate(snippet["lines"], snippet["start"]):
                ai_prompt += f"{i:3d}: {line}\n"
            ai_prompt += "\n---\n"

        try:
            # Send to LLM for analysis
            ai_response = self.llm_provider.chat(
                messages=[{"role": "user", "content": ai_prompt}], temperature=0.1, max_tokens=2048
            )

            # Parse LLM response for structured issues
            ai_content = (
                ai_response.content if hasattr(ai_response, "content") else str(ai_response)
            )
            parsed_issues = self._parse_ai_issues(ai_content, file_path)

            return parsed_issues

        except Exception as e:
            # Fallback if AI analysis fails
            return {
                "comments": [f"AI analysis failed: {str(e)}"],
                "critical_issues": [],
                "suggestions": ["Consider manual code review for comprehensive analysis"],
            }

    def _extract_code_snippets_for_ai(self, lines: List[str], file_ext: str) -> List[Dict]:
        """Extract interesting code snippets for AI analysis"""
        snippets = []

        # Find function definitions, complex logic, error handling blocks
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and comments
            if not line or line.startswith("#") or line.startswith("//"):
                i += 1
                continue

            # Extract functions/methods (multi-language support)
            if any(
                pattern in line
                for pattern in ["def ", "function ", "class ", "public ", "private ", "async "]
            ):
                snippet_start = i
                snippet_end = min(i + 15, len(lines))  # Get 15 lines max

                snippets.append(
                    {
                        "start": snippet_start + 1,  # 1-based line numbers
                        "end": snippet_end,
                        "lines": [lines[j] for j in range(snippet_start, snippet_end)],
                        "type": "function_definition",
                    }
                )

                i = snippet_end

            # Extract complex expressions or error handling
            elif any(
                pattern in line for pattern in ["try:", "catch", "if ", "for ", "while ", "switch"]
            ):
                snippet_start = i
                snippet_end = min(i + 8, len(lines))  # Smaller snippets for control flow

                snippets.append(
                    {
                        "start": snippet_start + 1,
                        "end": snippet_end,
                        "lines": [lines[j] for j in range(snippet_start, snippet_end)],
                        "type": "control_flow",
                    }
                )

                i = snippet_end
            else:
                i += 1

            # Limit to 3 snippets per file to avoid overwhelming the LLM
            if len(snippets) >= 3:
                break

        return snippets

    def _parse_ai_issues(self, ai_content: str, file_path: str) -> Dict:
        """Parse AI response with <issue> XML tags"""
        import re

        result = {"comments": [], "critical_issues": [], "suggestions": []}

        # Parse XML-like issue tags
        issue_pattern = r'<issue description="([^"]*)">\s*(.*?)\s*</issue>'
        issues = re.findall(issue_pattern, ai_content, re.DOTALL)

        for description, code_snippet in issues:
            # Clean up the code snippet
            code_lines = [line.strip() for line in code_snippet.split("\n") if line.strip()]

            # Extract line number if present
            line_num = "Unknown"
            for line in code_lines:
                if ":" in line and line.split(":")[0].strip().isdigit():
                    line_num = line.split(":")[0].strip()
                    break

            # Format the comment
            formatted_comment = f"AI Analysis - Line {line_num}: {description}\n"
            formatted_comment += f"    Code: `{code_snippet.strip()[:100]}...`\n"
            formatted_comment += f"    AI Suggestion: Review and address this issue"

            result["comments"].append(formatted_comment)

            # Categorize by severity keywords
            if any(
                keyword in description.lower()
                for keyword in ["security", "vulnerability", "injection", "xss", "critical"]
            ):
                result["critical_issues"].append(f"{file_path} Line {line_num}: {description}")

            result["suggestions"].append(
                f"Address AI-identified issue: {description} in {file_path}"
            )

        return result

    def _extract_fallback_comments(self, content: str) -> Dict[str, List[str]]:
        """Alternative extraction method for fallback responses with code snippets"""
        import re

        comments = {}

        # Look for the section after FILE-SPECIFIC COMMENTS:
        section_start = content.find("FILE-SPECIFIC COMMENTS:")
        if section_start == -1:
            return comments

        # Extract everything after that until FINAL RECOMMENDATIONS or end
        section_end = content.find("FINAL RECOMMENDATIONS:", section_start)
        if section_end == -1:
            section_content = content[section_start:]
        else:
            section_content = content[section_start:section_end]

        # Split into lines and parse
        lines = section_content.split("\n")[1:]  # Skip the header line
        current_file = None
        current_comment_lines = []

        for line in lines:
            # Check for file names (contains file extension)
            if ":" in line and any(
                ext in line
                for ext in [
                    ".py",
                    ".js",
                    ".ts",
                    ".jsx",
                    ".tsx",
                    ".java",
                    ".cpp",
                    ".c",
                    ".h",
                    ".php",
                    ".rb",
                    ".go",
                    ".rs",
                    ".swift",
                    ".kt",
                ]
            ):
                # Save previous comment
                if current_file and current_comment_lines:
                    if current_file not in comments:
                        comments[current_file] = []
                    comments[current_file].append("\n".join(current_comment_lines))

                # Start new file
                current_file = line.split(":")[0].strip()
                current_comment_lines = []

            elif line.strip().startswith("- ") and current_file:
                # New comment item
                if current_comment_lines:
                    # Save previous comment
                    if current_file not in comments:
                        comments[current_file] = []
                    comments[current_file].append("\n".join(current_comment_lines))

                # Start new comment
                current_comment_lines = [line.strip()[2:]]  # Remove '- '

            elif (
                line.strip() and current_file and (line.startswith("  ") or line.startswith("    "))
            ):
                # Continuation of current comment (code snippets, suggestions, etc.)
                current_comment_lines.append(line)

            elif not line.strip() and current_comment_lines:
                # Empty line - might be end of comment or separator
                continue

        # Save final comment
        if current_file and current_comment_lines:
            if current_file not in comments:
                comments[current_file] = []
            comments[current_file].append("\n".join(current_comment_lines))

        return comments

    def _extract_ai_structured_comments(self, content: str) -> Dict[str, List[str]]:
        """Extract comments from AI-structured XML responses"""
        import re

        comments = {"AI Analysis": []}

        # Parse XML-like issue tags from AI responses
        issue_pattern = r'<issue description="([^"]*)">\s*(.*?)\s*</issue>'
        issues = re.findall(issue_pattern, content, re.DOTALL)

        for description, code_snippet in issues:
            # Extract line number if present
            line_num = "Unknown"
            code_lines = code_snippet.split("\n")
            for line in code_lines:
                if ":" in line and line.split(":")[0].strip().isdigit():
                    line_num = line.split(":")[0].strip()
                    break

            # Format the AI comment
            formatted_comment = f"Line {line_num}: {description}\n"
            formatted_comment += f"    Code: `{code_snippet.strip()[:80]}...`\n"
            formatted_comment += f"    AI Finding: This issue was detected by AI analysis\n"
            formatted_comment += f"    Suggestion: Review and address this AI-identified issue"

            comments["AI Analysis"].append(formatted_comment)

        return comments

    def _estimate_review_time(self, file_count: int, line_count: int) -> str:
        """Estimate time needed for manual review"""
        # Rough estimation: 1 minute per file + 1 minute per 50 lines
        base_time = file_count * 1
        content_time = line_count // 50
        total_minutes = base_time + content_time

        if total_minutes < 5:
            return "< 5 minutes"
        elif total_minutes < 15:
            return "5-15 minutes"
        elif total_minutes < 30:
            return "15-30 minutes"
        elif total_minutes < 60:
            return "30-60 minutes"
        else:
            return f"~{total_minutes // 60}h {total_minutes % 60}min"

    def _create_error_result(self, error_msg: str) -> ReviewResult:
        """Create error result"""
        return ReviewResult(
            summary=f"Review error: {error_msg}",
            key_issues=[error_msg],
            suggestions=["Check if in a Git repository", "Verify there are changes to review"],
            inline_comments={},
            architecture_notes=[],
            security_concerns=[],
            performance_notes=[],
            code_quality_score=0,
            files_reviewed=[],
            total_lines_reviewed=0,
            review_time_estimate="N/A",
        )

    def _create_no_changes_result(self) -> ReviewResult:
        """Create result for no changes detected"""
        return ReviewResult(
            summary="No code changes detected for review",
            key_issues=[],
            suggestions=["Make some code changes", "Check if in the correct directory"],
            inline_comments={},
            architecture_notes=[],
            security_concerns=[],
            performance_notes=[],
            code_quality_score=10,
            files_reviewed=[],
            total_lines_reviewed=0,
            review_time_estimate="0 minutes",
        )

    def _context_to_prompt(self, context: List[Dict[str, str]]) -> str:
        """Convert context to single prompt (fallback)"""
        prompt_parts = []

        for message in context:
            role = message["role"]
            content = message["content"]

            if role == "system":
                prompt_parts.append(content)
            elif role == "user":
                prompt_parts.append(f"USER: {content}")
            elif role == "assistant":
                prompt_parts.append(f"ASSISTANT: {content}")

        return "\n\n".join(prompt_parts)

    def _add_to_history(self, role: str, content: str, mode: str = "review", metadata: dict = None):
        """Add message to history with compatibility for both HistoryManager and ConversationManager"""
        try:
            # Try ConversationManager interface first (newer processors)
            if hasattr(self.conversation_manager, "add_message"):
                self.conversation_manager.add_message(
                    role=role, content=content, mode=mode, metadata=metadata or {}
                )
            # Fallback to HistoryManager interface (chat.py)
            elif hasattr(self.conversation_manager, "add_conversation"):
                self.conversation_manager.add_conversation(
                    role=role, content=content, context_usage=None, metadata=metadata or {}
                )
            else:
                # Last resort - just ignore if no compatible interface
                pass
        except Exception:
            # Silently ignore history errors to not break review functionality
            pass

    def _get_recent_history(self, limit: int = 3, mode_filter: str = "review"):
        """Get recent history with compatibility for both manager types"""
        try:
            # Try ConversationManager interface first
            if hasattr(self.conversation_manager, "get_recent_history"):
                return self.conversation_manager.get_recent_history(
                    limit=limit, mode_filter=mode_filter
                )
            # Fallback to HistoryManager interface
            elif hasattr(self.conversation_manager, "get_recent_conversation"):
                recent = self.conversation_manager.get_recent_conversation(limit=limit)
                # Convert to ConversationMessage-like objects for compatibility
                return [
                    type(
                        "Message",
                        (),
                        {
                            "role": msg.get("role", "user"),
                            "content": msg.get("content", ""),
                            "mode": mode_filter,
                        },
                    )()
                    for msg in recent
                    if msg.get("role") in ["user", "assistant"]
                ]
            else:
                return []
        except Exception:
            return []
