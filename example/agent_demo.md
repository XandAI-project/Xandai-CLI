# Agent Command Demonstration

The `/agent` command is a multi-step LLM orchestrator that executes multiple calls to the language model to process complex instructions through reasoning stages.

## How It Works

The `/agent` executes a 4+ step pipeline:

1. **Intent Analysis**: Classifies the user's intent (fix, explain, analyze, create, refactor)
2. **Context Gathering**: Identifies necessary information based on intent
3. **Task Execution**: Performs the main task
4. **Validation**: Checks and validates the output
5. **Refinement** (optional): If needed, refines the output based on validation

## Usage Examples

### Example 1: Fix Code
```bash
/agent fix the bug in main.py where the loop never terminates
```

**Expected output:**
```
🤖 Agent Mode - Multi-Step Processing
Max calls: 20

Agent Execution Steps:

✅ [Step 1] Analyze Intent
✅ [Step 2] Gather Context
✅ [Step 3] Execute Task
✅ [Step 4] Validate Output

✓ Agent Task Complete
Reason: completed
Total calls: 4/20
Total tokens: 2450

┌─ Agent Output ────────────────────────────┐
│ [Fixed code and explanation]              │
└───────────────────────────────────────────┘
```

### Example 2: Explain Code
```bash
/agent explain how the authentication system works in this project
```

### Example 3: Create New Feature
```bash
/agent create a REST API endpoint for user registration with validation
```

### Example 4: Analyze Code
```bash
/agent analyze the performance bottlenecks in the data processing pipeline
```

## Limit Configuration

By default, the agent can make up to 20 LLM calls. You can adjust this:

```bash
# View current limit
/set-agent-limit

# Set new limit
/set-agent-limit 30

# Limits:
# - Minimum: 1
# - Maximum: 100
# - Default: 20
```

## Difference between /agent and Normal Chat

| Aspect | Normal Chat | /agent |
|--------|-------------|---------|
| LLM Calls | 1 | 4-20 (configurable) |
| Reasoning | Direct | Multi-step |
| Context | Simple | Structured |
| Validation | None | Automatic |
| Use | Simple questions | Complex tasks |
| Tokens | Low | High |

## When to Use /agent

**Use /agent when:**
- Task requires multiple reasoning steps
- You need structured analysis
- Response needs validation
- Task is complex and may need refinement

**Use normal chat when:**
- Simple and direct questions
- Casual conversation
- Quick explanations
- Token economy is priority

## Verbose Mode

To see details of each step:

```bash
xandai -v
```

Then use the `/agent` command normally. You will see:
```
✅ [Step 1] Analyze Intent
  → INTENT: code_fix, COMPLEXITY: moderate...
✅ [Step 2] Gather Context
  → CONTEXT_NEEDED: current file, error logs...
```

## Stop Status

The agent stops when:

1. **completed**: Task completed successfully
2. **limit_reached**: Reached call limit
3. **error**: Error during execution

## History Integration

All agent interactions are saved in the conversation history:

```bash
/history
```

You will see "agent" mode entries with metadata:
- Total calls made
- Total tokens used
- Stop reason

## Complete Example

```bash
# Start XandAI
xandai

# Check current limit
/set-agent-limit
# Current agent limit: 20 calls

# Adjust limit if necessary
/set-agent-limit 15
# ✓ Agent limit set to 15 calls

# Execute complex task
/agent refactor the authentication code to use JWT tokens instead of sessions

# Agent executes multiple steps...
# [Step 1] Analyze Intent - ✅
# [Step 2] Gather Context - ✅
# [Step 3] Execute Task - ✅
# [Step 4] Validate Output - ✅

# Final result is presented
```

## Tips

1. **Be specific**: The clearer the instruction, the better the result
2. **Use context**: Mention specific files, functions or components
3. **Adjust the limit**: For very complex tasks, increase the limit
4. **Verbose mode**: Use `-v` for debugging and understanding the process
5. **Compare results**: Try the same task in normal chat vs /agent

## Limitations

- Each LLM call consumes tokens (can be costly)
- Response time is longer than normal chat
- Better for well-defined tasks
- Does not replace human analysis for critical decisions

## Advanced Examples

### Complex Refactoring
```bash
/agent refactor the monolithic app.py into a modular structure with separate files for routes, models, and services
```

### Systematic Debugging
```bash
/agent debug why the user registration fails intermittently under high load
```

### Automatic Documentation
```bash
/agent generate comprehensive API documentation for all endpoints in the server.js file
```
