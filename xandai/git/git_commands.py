"""
Git Commands Module

AI-powered Git operations:
- Generate commit messages from staged changes
- Summarize pull requests
- Explain diffs in plain English
- Explain why lines exist (blame)
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from xandai.integrations.base_provider import LLMProvider


class GitCommands:
    """AI-powered Git command implementations"""

    def __init__(self, llm_provider: LLMProvider, verbose: bool = False):
        """
        Initialize Git Commands

        Args:
            llm_provider: LLM provider for AI operations
            verbose: Enable verbose logging
        """
        self.llm_provider = llm_provider
        self.verbose = verbose

    def generate_commit_message(self, repo_path: str = ".") -> str:
        """
        Generate commit message from staged changes

        Args:
            repo_path: Path to Git repository

        Returns:
            Generated commit message
        """
        # Check if in a Git repository
        if not self._is_git_repo(repo_path):
            raise ValueError("Not a Git repository")

        # Get staged changes
        diff = self._get_staged_diff(repo_path)

        if not diff:
            raise ValueError("No staged changes found. Use 'git add' first.")

        # Get status for context
        status = self._get_git_status(repo_path)

        # Generate commit message using AI
        prompt = self._build_commit_prompt(diff, status)
        response = self.llm_provider.generate(prompt, temperature=0.3, max_tokens=500)

        return response.content.strip()

    def summarize_pr(
        self, repo_path: str = ".", base_branch: str = "main", head_branch: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Summarize a pull request

        Args:
            repo_path: Path to Git repository
            base_branch: Base branch (default: main)
            head_branch: Head branch (default: current branch)

        Returns:
            Dictionary with summary, changes, risks
        """
        if not self._is_git_repo(repo_path):
            raise ValueError("Not a Git repository")

        # Get current branch if not specified
        if not head_branch:
            head_branch = self._get_current_branch(repo_path)

        # Get diff between branches
        diff = self._get_branch_diff(repo_path, base_branch, head_branch)

        if not diff:
            raise ValueError(f"No differences between {base_branch} and {head_branch}")

        # Get commit log
        commits = self._get_commit_log(repo_path, base_branch, head_branch)

        # Generate PR summary using AI
        prompt = self._build_pr_prompt(diff, commits, base_branch, head_branch)
        response = self.llm_provider.generate(prompt, temperature=0.3, max_tokens=1000)

        # Parse response into sections
        return self._parse_pr_summary(response.content)

    def explain_diff(
        self, repo_path: str = ".", file_path: Optional[str] = None, commit: Optional[str] = None
    ) -> str:
        """
        Explain a diff in plain English

        Args:
            repo_path: Path to Git repository
            file_path: Specific file to diff (optional)
            commit: Commit to compare against (default: working directory vs HEAD)

        Returns:
            Plain English explanation of changes
        """
        if not self._is_git_repo(repo_path):
            raise ValueError("Not a Git repository")

        # Get diff
        if commit:
            diff = self._get_commit_diff(repo_path, commit, file_path)
        else:
            diff = self._get_working_diff(repo_path, file_path)

        if not diff:
            raise ValueError("No changes found")

        # Generate explanation using AI
        prompt = self._build_diff_prompt(diff, file_path)
        response = self.llm_provider.generate(prompt, temperature=0.3, max_tokens=800)

        return response.content.strip()

    def explain_blame(
        self, repo_path: str = ".", file_path: str = None, line_number: Optional[int] = None
    ) -> str:
        """
        Explain why a line exists using git blame

        Args:
            repo_path: Path to Git repository
            file_path: File to blame
            line_number: Specific line number (optional)

        Returns:
            Explanation of why the line exists
        """
        if not file_path:
            raise ValueError("file_path is required")

        if not self._is_git_repo(repo_path):
            raise ValueError("Not a Git repository")

        # Get blame information
        blame_info = self._get_blame_info(repo_path, file_path, line_number)

        if not blame_info:
            raise ValueError("Could not get blame information")

        # Get the commit details
        commit_hash = blame_info["commit"]
        commit_details = self._get_commit_details(repo_path, commit_hash)

        # Generate explanation using AI
        prompt = self._build_blame_prompt(blame_info, commit_details, file_path, line_number)
        response = self.llm_provider.generate(prompt, temperature=0.3, max_tokens=600)

        return response.content.strip()

    # Helper methods

    def _is_git_repo(self, repo_path: str) -> bool:
        """Check if directory is a Git repository"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"], cwd=repo_path, capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def _get_staged_diff(self, repo_path: str) -> str:
        """Get diff of staged changes"""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached"], cwd=repo_path, capture_output=True, text=True
            )
            return result.stdout
        except Exception as e:
            if self.verbose:
                print(f"Error getting staged diff: {e}")
            return ""

    def _get_git_status(self, repo_path: str) -> str:
        """Get Git status"""
        try:
            result = subprocess.run(
                ["git", "status", "--short"], cwd=repo_path, capture_output=True, text=True
            )
            return result.stdout
        except Exception:
            return ""

    def _get_current_branch(self, repo_path: str) -> str:
        """Get current branch name"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except Exception:
            return "HEAD"

    def _get_branch_diff(self, repo_path: str, base: str, head: str) -> str:
        """Get diff between two branches"""
        try:
            result = subprocess.run(
                ["git", "diff", f"{base}...{head}"], cwd=repo_path, capture_output=True, text=True
            )
            return result.stdout
        except Exception as e:
            if self.verbose:
                print(f"Error getting branch diff: {e}")
            return ""

    def _get_commit_log(self, repo_path: str, base: str, head: str) -> str:
        """Get commit log between branches"""
        try:
            result = subprocess.run(
                ["git", "log", f"{base}..{head}", "--oneline"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            return result.stdout
        except Exception:
            return ""

    def _get_commit_diff(self, repo_path: str, commit: str, file_path: Optional[str]) -> str:
        """Get diff for a specific commit"""
        try:
            cmd = ["git", "show", commit]
            if file_path:
                cmd.append("--")
                cmd.append(file_path)

            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            if self.verbose:
                print(f"Error getting commit diff: {e}")
            return ""

    def _get_working_diff(self, repo_path: str, file_path: Optional[str]) -> str:
        """Get diff of working directory"""
        try:
            cmd = ["git", "diff"]
            if file_path:
                cmd.append("--")
                cmd.append(file_path)

            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            if self.verbose:
                print(f"Error getting working diff: {e}")
            return ""

    def _get_blame_info(
        self, repo_path: str, file_path: str, line_number: Optional[int]
    ) -> Optional[Dict]:
        """Get git blame information"""
        try:
            cmd = ["git", "blame", "-L"]

            if line_number:
                cmd.append(f"{line_number},{line_number}")
            else:
                cmd.append("1,1")

            cmd.extend(["--porcelain", file_path])

            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)

            if result.returncode != 0:
                return None

            # Parse porcelain output
            lines = result.stdout.split("\n")
            commit = lines[0].split()[0]

            # Get the actual line content
            line_content = ""
            for line in lines:
                if line.startswith("\t"):
                    line_content = line[1:]
                    break

            return {"commit": commit, "line_content": line_content, "line_number": line_number or 1}
        except Exception as e:
            if self.verbose:
                print(f"Error getting blame info: {e}")
            return None

    def _get_commit_details(self, repo_path: str, commit: str) -> Dict:
        """Get detailed information about a commit"""
        try:
            result = subprocess.run(
                ["git", "show", "--format=%H%n%an%n%ae%n%at%n%s%n%b", "-s", commit],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )

            lines = result.stdout.strip().split("\n")

            return {
                "hash": lines[0] if len(lines) > 0 else "",
                "author": lines[1] if len(lines) > 1 else "",
                "email": lines[2] if len(lines) > 2 else "",
                "timestamp": lines[3] if len(lines) > 3 else "",
                "subject": lines[4] if len(lines) > 4 else "",
                "body": "\n".join(lines[5:]) if len(lines) > 5 else "",
            }
        except Exception:
            return {}

    # Prompt builders

    def _build_commit_prompt(self, diff: str, status: str) -> str:
        """Build prompt for commit message generation"""
        return f"""Generate a concise, informative Git commit message for the following staged changes.

Follow these guidelines:
- Use conventional commit format (feat:, fix:, docs:, refactor:, etc.)
- First line: short summary (50 chars max)
- Add blank line, then detailed explanation if needed
- Be specific about what changed and why
- Focus on the user impact

STAGED CHANGES:
{diff[:3000]}

STATUS:
{status}

Generate the commit message:"""

    def _build_pr_prompt(self, diff: str, commits: str, base: str, head: str) -> str:
        """Build prompt for PR summary"""
        return f"""Summarize this pull request from branch '{head}' to '{base}'.

COMMITS:
{commits}

DIFF (truncated):
{diff[:4000]}

Provide a structured summary with these sections:
1. SUMMARY: What this PR does (2-3 sentences)
2. CHANGES: Key changes made (bullet points)
3. RISKS: Potential risks or breaking changes (bullet points)

Format as:
SUMMARY:
[summary text]

CHANGES:
- [change 1]
- [change 2]

RISKS:
- [risk 1]
- [risk 2]"""

    def _build_diff_prompt(self, diff: str, file_path: Optional[str]) -> str:
        """Build prompt for diff explanation"""
        file_context = f" in {file_path}" if file_path else ""

        return f"""Explain the following Git diff{file_context} in plain English.

DIFF:
{diff[:3000]}

Provide a clear explanation that:
- Describes what changed
- Explains why these changes matter
- Highlights any important details
- Uses simple, non-technical language where possible

Explanation:"""

    def _build_blame_prompt(
        self, blame_info: Dict, commit_details: Dict, file_path: str, line_number: Optional[int]
    ) -> str:
        """Build prompt for blame explanation"""
        line_ref = f"line {line_number}" if line_number else "this line"

        return f"""Explain why {line_ref} exists in {file_path}.

LINE CONTENT:
{blame_info.get('line_content', '')}

COMMIT INFORMATION:
- Author: {commit_details.get('author', 'Unknown')}
- Date: {commit_details.get('timestamp', 'Unknown')}
- Message: {commit_details.get('subject', '')}
- Details: {commit_details.get('body', '')}

Provide a clear explanation that:
- Explains the purpose of this line
- Describes the context from the commit message
- Mentions when and why it was added
- Keeps it concise (2-3 sentences)

Explanation:"""

    def _parse_pr_summary(self, content: str) -> Dict[str, str]:
        """Parse PR summary response into sections"""
        sections = {"summary": "", "changes": "", "risks": ""}

        current_section = None
        lines = content.split("\n")

        for line in lines:
            line_upper = line.upper().strip()

            if line_upper.startswith("SUMMARY:"):
                current_section = "summary"
                # Get any text after "SUMMARY:"
                rest = line[8:].strip()
                if rest:
                    sections["summary"] = rest + "\n"
            elif line_upper.startswith("CHANGES:"):
                current_section = "changes"
            elif line_upper.startswith("RISKS:"):
                current_section = "risks"
            elif current_section and line.strip():
                sections[current_section] += line + "\n"

        # Clean up sections
        for key in sections:
            sections[key] = sections[key].strip()

        return sections
