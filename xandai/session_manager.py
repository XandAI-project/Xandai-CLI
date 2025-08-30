"""
XandAI Session Manager
Stores and retrieves context and interactions from the last session
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from rich.console import Console

console = Console()

class SessionManager:
    """Manages storage and retrieval of XandAI sessions"""
    
    def __init__(self, session_dir: str = None):
        """
        Initializes the session manager
        
        Args:
            session_dir: Directory where sessions will be stored (defaults to XandAI-CLI/sessions)
        """
        if session_dir is None:
            # Get the XandAI-CLI project directory (parent of the xandai package)
            xandai_package_dir = Path(__file__).parent
            xandai_project_dir = xandai_package_dir.parent
            self.session_dir = xandai_project_dir / "sessions"
        else:
            self.session_dir = Path(session_dir)
            
        # Ensure the directory exists, create if it doesn't
        try:
            self.session_dir.mkdir(exist_ok=True, parents=True)
            console.print(f"[dim]Sessions directory: {self.session_dir}[/dim]")
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not create sessions directory: {e}[/yellow]")
            console.print(f"[yellow]Sessions will be disabled for this run[/yellow]")
            self.session_dir = None
        
        # Current session file
        self.session_file = self.session_dir / "session.store" if self.session_dir else None
        
        # Current session data
        self.session_data = {
            "version": "1.0",
            "created_at": None,
            "last_updated": None,
            "model_name": None,
            "context_history": [],
            "interaction_count": 0,
            "working_directory": None,
            "shell_settings": {
                "auto_execute_shell": True,
                "enhance_prompts": True,
                "better_prompting": True
            },
            "last_interactions": []  # Last 10 interactions
        }
        
    def save_session(self, 
                    model_name: str,
                    context_history: List[Dict],
                    working_directory: str,
                    shell_settings: Dict[str, bool],
                    last_interaction: Optional[Dict] = None) -> bool:
        """
        Saves the current session state
        
        Args:
            model_name: Name of the selected model
            context_history: Conversation context history
            working_directory: Current working directory
            shell_settings: Shell settings (auto_execute, enhance_prompts, etc.)
            last_interaction: Last interaction (prompt + response)
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Check if sessions are available
            if not self.session_file:
                return False
                
            # Ensure directory exists before saving
            if not self.session_dir.exists():
                try:
                    self.session_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    console.print(f"[red]Error creating sessions directory: {e}[/red]")
                    return False
            
            now = datetime.now().isoformat()
            
            # Load existing data if available
            if self.session_file.exists():
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    self.session_data = json.load(f)
            else:
                # First time saving
                self.session_data["created_at"] = now
            
            # Update data
            self.session_data.update({
                "last_updated": now,
                "model_name": model_name,
                "context_history": context_history[-50:] if context_history else [],  # Last 50 messages
                "working_directory": working_directory,
                "shell_settings": shell_settings,
                "interaction_count": self.session_data.get("interaction_count", 0) + 1
            })
            
            # Add last interaction if provided
            if last_interaction:
                interactions = self.session_data.get("last_interactions", [])
                interactions.append({
                    **last_interaction,
                    "timestamp": now
                })
                # Keep only the last 10 interactions
                self.session_data["last_interactions"] = interactions[-10:]
            
            # Save to file
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            console.print(f"[red]Error saving session: {e}[/red]")
            return False
    
    def load_session(self) -> Optional[Dict]:
        """
        Loads the previous session if it exists
        
        Returns:
            Session data or None if no saved session exists
        """
        try:
            if not self.session_file or not self.session_file.exists():
                return None
            
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Check if it's a valid session
            required_fields = ["model_name", "context_history", "working_directory"]
            if not all(field in session_data for field in required_fields):
                console.print("[yellow]⚠️  Invalid session found, ignoring...[/yellow]")
                return None
            
            return session_data
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Error loading previous session: {e}[/yellow]")
            return None
    
    def get_session_summary(self) -> Optional[str]:
        """
        Returns a summary of the previous session
        
        Returns:
            String with session summary or None
        """
        session_data = self.load_session()
        if not session_data:
            return None
        
        try:
            last_updated = datetime.fromisoformat(session_data["last_updated"])
            time_ago = self._time_since(last_updated)
            
            summary = f"""
[bold blue]📊 Last Session Found:[/bold blue]
[dim]• Model: {session_data['model_name']}
• Directory: {session_data['working_directory']}
• Interactions: {session_data.get('interaction_count', 0)}
• Context: {len(session_data.get('context_history', []))} messages
• Last activity: {time_ago}[/dim]"""
            
            return summary
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Error generating session summary: {e}[/yellow]")
            return None
    
    def _time_since(self, past_time: datetime) -> str:
        """
        Calculates elapsed time in a human-friendly way
        
        Args:
            past_time: Past time
            
        Returns:
            String describing elapsed time
        """
        now = datetime.now()
        diff = now - past_time
        
        if diff.days > 0:
            return f"{diff.days} day(s) ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour(s) ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute(s) ago"
        else:
            return "just now"
    
    def clear_session(self) -> bool:
        """
        Clears the current session
        
        Returns:
            True if cleared successfully
        """
        try:
            if self.session_file and self.session_file.exists():
                # Rename to backup instead of deleting
                backup_name = f"session.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.store"
                backup_path = self.session_dir / backup_name
                self.session_file.rename(backup_path)
                console.print(f"[green]✓ Previous session archived as: {backup_name}[/green]")
            
            return True
            
        except Exception as e:
            console.print(f"[red]Error clearing session: {e}[/red]")
            return False
    
    def list_backup_sessions(self) -> List[Path]:
        """
        Lists available backup sessions
        
        Returns:
            List of backup files
        """
        try:
            if not self.session_dir:
                return []
            backups = list(self.session_dir.glob("session.backup.*.store"))
            return sorted(backups, key=lambda x: x.stat().st_mtime, reverse=True)
        except Exception:
            return []
    
    def restore_backup_session(self, backup_file: Path) -> bool:
        """
        Restores a backup session
        
        Args:
            backup_file: Backup file to restore
            
        Returns:
            True if restored successfully
        """
        try:
            if not self.session_file:
                return False
            if backup_file.exists():
                # Backup current session if it exists
                if self.session_file.exists():
                    current_backup = self.session_dir / f"session.backup.current.{datetime.now().strftime('%Y%m%d_%H%M%S')}.store"
                    self.session_file.rename(current_backup)
                
                # Restore the backup
                backup_file.rename(self.session_file)
                console.print(f"[green]✓ Session restored from: {backup_file.name}[/green]")
                return True
            
        except Exception as e:
            console.print(f"[red]Error restoring session: {e}[/red]")
        
        return False
    
    def get_interaction_stats(self) -> Dict[str, Any]:
        """
        Returns interaction statistics
        
        Returns:
            Dictionary with statistics
        """
        session_data = self.load_session()
        if not session_data:
            return {}
        
        interactions = session_data.get("last_interactions", [])
        context_history = session_data.get("context_history", [])
        
        stats = {
            "total_interactions": session_data.get("interaction_count", 0),
            "recent_interactions": len(interactions),
            "context_messages": len(context_history),
            "user_messages": len([msg for msg in context_history if isinstance(msg, dict) and msg.get("role") == "user"]),
            "assistant_messages": len([msg for msg in context_history if isinstance(msg, dict) and msg.get("role") == "assistant"]),
            "session_duration": None
        }
        
        # Calculate session duration
        if session_data.get("created_at") and session_data.get("last_updated"):
            try:
                created = datetime.fromisoformat(session_data["created_at"])
                updated = datetime.fromisoformat(session_data["last_updated"])
                duration = updated - created
                stats["session_duration"] = str(duration).split('.')[0]  # Remove microseconds
            except Exception:
                pass
        
        return stats
