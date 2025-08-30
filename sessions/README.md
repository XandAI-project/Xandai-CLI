# XandAI Sessions

This directory stores XandAI-CLI sessions to maintain context between executions.

## Files

- **session.store** - Current active session
- **session.backup.*.store** - Backups of previous sessions

## Features

### Automatic Loading
When you run `xandai`, the system:
1. Detects if a previous session exists
2. Shows a summary of the found session  
3. Asks if you want to continue the previous session
4. If yes, restores:
   - Selected model
   - Conversation context
   - Settings (shell, prompts, etc.)
   - Working directory

### Automatic Saving
The system automatically saves:
- Each interaction with the AI
- Complete conversation context
- Current settings
- Current working directory
- Last 10 detailed interactions

### Session Commands

```bash
# Current session information
/session info

# Clear current session (archives automatically)
/session clear

# List available backups
/session backups

# Restore a specific backup
/session restore session.backup.20250108_203045.store

# Manually save current session
/session save
```

## Session File Structure

```json
{
  "version": "1.0",
  "created_at": "ISO timestamp",
  "last_updated": "ISO timestamp", 
  "model_name": "selected model",
  "context_history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "interaction_count": 0,
  "working_directory": "current directory",
  "shell_settings": {
    "auto_execute_shell": true,
    "enhance_prompts": true,
    "better_prompting": true
  },
  "last_interactions": [
    {
      "prompt": "user prompt",
      "enhanced_prompt": "enhanced prompt (optional)", 
      "response": "AI response",
      "model": "model used",
      "directory": "directory at time",
      "had_special_processing": true,
      "timestamp": "ISO timestamp"
    }
  ]
}
```

## Benefits

- **Continuity**: Maintain context between sessions
- **Automatic Backup**: Never lose your work
- **Portability**: Sessions can be shared/restored
- **History**: Easy access to previous interactions
- **Complete State**: Restores settings and directory
