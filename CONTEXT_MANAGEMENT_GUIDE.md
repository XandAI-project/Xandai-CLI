# Context Management System Guide

## Overview

The XandAI CLI features an intelligent context management system that tracks token usage and automatically manages LLM context to prevent hitting token limits while preserving important conversation history.

## Features

### 🔢 **Token Tracking**
- Real-time token counting using tiktoken (GPT-4 tokenizer)
- Fallback estimation when tiktoken is unavailable (~4 characters per token)
- Percentage display of current context usage
- Color-coded status indicators

### 🔄 **Automatic Context Flushing**
- Automatically triggers at 90% token capacity
- Preserves recent messages and system context
- Creates summary of flushed content
- Intelligent preservation of coding rules and important context

### 📊 **Context Status Display**
- Shows in the CLI banner: `🧠 Context: 15.2% (8 msgs, 1,234 tokens)`
- Color coding:
  - 🟢 Green: < 50% usage
  - 🟡 Yellow: 50-80% usage  
  - 🔴 Red: > 80% usage

### 🗂️ **Smart Context Preservation**
- **System Messages**: Always preserved (coding rules, instructions)
- **Recent Messages**: Last 5 user-assistant interactions kept
- **Important Metadata**: Technology-specific rules and context
- **Flush Summaries**: Brief summaries of removed content

## Commands

### `/context` - Show Context Status
```
📊 Context Status: 23.4% (12 msgs, 2,998 tokens)
Messages breakdown:
  user: 6 messages
  assistant: 5 messages
  system: 1 messages
```

### `/flush` - Manual Context Flush
```
🔄 Context manually flushed: 87.3% → 23.1%
```

## Configuration

### Token Limits
```python
max_context_tokens = 128000        # Total context limit
token_flush_threshold = 0.90       # Auto-flush at 90%
preserve_recent_messages = 5       # Keep last 5 interactions
```

### Context Preservation
```python
preserve_system_context = True     # Keep system messages
preserve_recent_messages = 5       # Number of recent messages to keep
```

## How It Works

### 1. **Message Tracking**
Every interaction is tracked with metadata:
```python
{
    'role': 'user|assistant|system',
    'content': 'message content',
    'tokens': 42,
    'timestamp': 1234567890,
    'metadata': {'type': 'coding_rules', 'technologies': ['react']}
}
```

### 2. **Automatic Flush Process**
When context reaches 90% capacity:

1. **Identify Preserved Content**:
   - System messages (coding rules, instructions)
   - Recent messages (last 5 interactions)
   - Important metadata

2. **Create Summary**:
   - Count of flushed messages
   - Brief description of removed content

3. **Update Context**:
   - Remove old messages
   - Keep preserved content
   - Add flush summary

### 3. **Token Counting**
Uses tiktoken for accurate GPT-4 token counting:
```python
def count_tokens(self, text: str) -> int:
    if self.tokenizer:
        return len(self.tokenizer.encode(text))
    # Fallback: estimate 4 chars per token
    return len(text) // 4
```

## Benefits

### 🚀 **Performance**
- Prevents context overflow errors
- Maintains conversation flow
- Optimizes LLM response quality

### 🧠 **Intelligence**
- Preserves important context
- Maintains coding rules and preferences
- Keeps recent conversation relevant

### 📈 **Transparency**
- Real-time usage display
- Clear flush notifications
- Detailed status information

## Usage Examples

### Normal Operation
```
[XandAI] > create a react app
🧠 Context: 12.3% (4 msgs, 1,576 tokens)

Creating React application...
```

### Auto-Flush Triggered
```
[XandAI] > add more features to the app
🔄 Context at 91.2% - Auto-flushing...
✓ Context flushed: 115,234 → 15,678 tokens (12.2%)

Adding features to your app...
```

### Manual Status Check
```
[XandAI] > /context
📊 Context Status: 34.7% (18 msgs, 44,421 tokens)
Messages breakdown:
  user: 9 messages
  assistant: 8 messages  
  system: 1 messages
```

### Manual Flush
```
[XandAI] > /flush
🔄 Context manually flushed: 78.9% → 23.4%
```

## Context History Structure

### Message Types
- **User**: Direct user input and commands
- **Assistant**: LLM responses and generated content
- **System**: Coding rules, instructions, flush summaries

### Metadata Types
- `coding_rules`: Technology-specific development guidelines
- `flush_summary`: Summary of previously flushed content
- `file_context`: Information about mentioned files
- `system_context`: OS and directory information

## Best Practices

### 🎯 **Optimal Usage**
1. Monitor context percentage in banner
2. Use `/flush` before starting new major topics
3. Check `/context` for detailed breakdown
4. Let auto-flush handle routine management

### ⚠️ **Considerations**
- Flushing removes conversation history
- Important context is preserved automatically
- Manual flush gives immediate control
- Recent messages are always kept

### 🔧 **Troubleshooting**
- If responses seem disconnected, check context status
- Use `/flush` to clear confusing historical context
- Verify coding rules are being preserved
- Check that recent messages are maintained

## Technical Implementation

### Dependencies
```
tiktoken>=0.5.0    # Accurate token counting
```

### Key Components
- `PromptEnhancer.count_tokens()`: Token counting
- `PromptEnhancer.flush_context()`: Context management
- `PromptEnhancer.add_to_context_history()`: Message tracking
- `XandAICLI.show_context_status()`: Status display

### Integration Points
- CLI banner displays current usage
- Auto-flush triggers during prompt enhancement
- Manual commands available via `/flush` and `/context`
- Context tracking integrated with all LLM interactions

---

**Note**: This system ensures optimal LLM performance while maintaining conversation continuity and preserving important development context.
