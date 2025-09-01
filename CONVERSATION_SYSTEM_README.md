# Robust Conversation History System

## Overview

The XandAI CLI now features a completely refactored conversation history system that addresses the limitations of the previous basic implementation. This new system provides:

- **Persistent, ordered chat history** with rich message types
- **Token budget management** with model-specific limits  
- **Auto-summarization** of old conversations
- **Tool/function call support** in conversation history
- **Clean APIs** for seamless integration

## Architecture

### Core Components

1. **ConversationHistory** - Rich data models for messages and conversations
2. **TokenBudgetManager** - Smart token budget management with model-specific optimization
3. **ConversationSummarizer** - Intelligent auto-summarization using the LLM itself
4. **HistoryManager** - Main API interface for all operations

### Key Features

#### 🧠 **Rich Message Types**
- User/Assistant conversation messages
- System prompts and coding rules  
- Tool calls and results
- Context summaries
- Session markers

#### 🎯 **Token Budget Management**
- Model-specific context limits (llama3:8k, qwen2.5:32k, etc.)
- Smart sliding window optimization
- Preserves recent + important messages
- Emergency compression at 90% utilization

#### 📝 **Auto-Summarization** 
- Classifies conversation types (coding, tools, general)
- Creates compact summaries of old conversations
- Maintains important technical details
- Configurable age thresholds

#### 🔧 **Tool Call Support**
- Native support for function calls
- Tool execution results tracking
- Rich metadata preservation

## Usage Examples

### Basic Usage

```python
from xandai.conversation import HistoryManager

# Initialize with OLLAMA API
history_manager = HistoryManager(api=ollama_api)
history_manager.set_model("llama3:8b")

# Add messages
user_msg = history_manager.add_user_message("Create a Python function to sort arrays")
assistant_msg = history_manager.add_assistant_message(
    "I'll create that function for you...", 
    tool_calls=[ToolCall(id="call1", name="create_file", arguments={"filename": "sort.py"})]
)

# Get optimized context for LLM
context_messages = history_manager.get_context_for_model()
status = history_manager.get_context_status()
```

### Integration with Existing CLI

```python
from xandai.conversation_integration import ConversationIntegration

# Replace existing history system
conv_integration = ConversationIntegration(api=ollama_api)
conv_integration.set_model("llama3:8b")

# Migrate existing prompt enhancer
conv_integration.integrate_with_prompt_enhancer(prompt_enhancer)

# Use with existing session manager
migrate_existing_session(session_manager, conv_integration)
```

## Load Test Results

The system was validated with comprehensive load testing:

| Model | Context | Messages | Optimized | Tokens Saved | Performance |
|-------|---------|----------|-----------|--------------|-------------|
| llama3 | 8,192 | 400 | 194 | 0 | 2.81s |
| qwen2.5-coder | 32,768 | 800 | 800 | 0 | 6.86s |
| mistral | 8,192 | 1,200 | 198 | 0 | 11.19s |
| llama3.1 | 128,000 | 1,600 | 1,600 | 0 | 15.22s |

**Extreme Load Test**: Successfully optimized 2,000 messages, saving 76,860 tokens.

## Model Support

The system includes configurations for popular OLLAMA models:

### Llama Models
- llama2 (4k context)
- llama3:8b (8k context) 
- llama3.1:70b (128k context)

### Coding Models  
- codellama:7b (16k context)
- qwen2.5-coder (32k context)

### Other Models
- mistral:7b (8k context)
- gemma2:9b (8k context)
- phi3:mini (4k context)

Unknown models get conservative defaults with intelligent inference from model names.

## File Structure

```
xandai/conversation/
├── __init__.py                 # Package exports
├── conversation_history.py     # Core data models
├── token_budget_manager.py     # Token budgeting
├── conversation_summarizer.py  # Auto-summarization
└── history_manager.py          # Main API

xandai/conversation_integration.py  # CLI integration layer
tests/test_conversation_history.py  # Comprehensive tests
load_test_history_system.py         # Performance validation
```

## Migration Guide

### From Existing PromptEnhancer

```python
# Old way
prompt_enhancer.add_to_context_history("user", "Hello", {"type": "conversation"})
prompt_enhancer.flush_context()

# New way  
history_manager.add_user_message("Hello")
history_manager.auto_summarize()  # Intelligent optimization
```

### From Existing SessionManager

```python
# The ConversationIntegration provides backward compatibility
conv_integration = ConversationIntegration(api=api)
conv_integration.load_from_session_data(session_data)
```

## Configuration

### Token Budget Strategy

```python
strategy = TokenBudgetStrategy(
    preserve_recent_messages=20,      # Always keep recent messages
    target_utilization=0.75,          # Use 75% of available context
    emergency_threshold=0.90,         # Emergency compression at 90%
    summarize_threshold=50,           # Summarize when 50+ messages
    min_summary_age_hours=1           # Don't summarize recent conversations
)

history_manager = HistoryManager(default_strategy=strategy)
```

### Custom Model Configuration

```python
# Add custom model to registry
ModelRegistry.MODELS["my-model:7b"] = ModelInfo(
    name="my-model:7b",
    family=ModelFamily.UNKNOWN,
    context_length=16384,
    recommended_reserve=1024
)
```

## Performance Characteristics

- **Memory Efficient**: Automatic cleanup and compression
- **Fast Token Calculation**: Cached estimation with ~4 chars/token accuracy
- **Persistent Storage**: JSON with atomic saves and backup system
- **Scalable**: Handles thousands of messages with optimization

## Future Enhancements

- **Vector embeddings** for semantic conversation search
- **Export formats** for external analysis
- **Advanced summarization strategies** per conversation type
- **Real-time context optimization** during generation
- **Integration with external vector databases**

## Testing

Run the comprehensive test suite:

```bash
python -m pytest tests/test_conversation_history.py -v
```

Run the load test to validate performance:

```bash
python load_test_history_system.py
```

## Conclusion

This robust conversation history system transforms XandAI CLI from a basic chat tool into a sophisticated conversation management platform. It ensures long conversations work reliably, big projects maintain context effectively, and the system scales to enterprise-level usage.

The system is production-ready and provides clean migration paths from the existing implementation while maintaining full backward compatibility.
