"""
Token budget management system for XandAI CLI.
Handles model-specific token limits and smart context window management.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import re
from .conversation_history import Message, MessageRole, MessageType, ConversationHistory


class ModelFamily(Enum):
    """Known model families with different characteristics."""
    LLAMA = "llama"
    QWEN = "qwen"
    MISTRAL = "mistral"
    GEMMA = "gemma"
    PHI = "phi"
    CODELLAMA = "codellama"
    UNKNOWN = "unknown"


@dataclass
class ModelInfo:
    """Information about a specific model."""
    name: str
    family: ModelFamily
    context_length: int
    recommended_reserve: int  # Tokens to reserve for response
    supports_tool_calls: bool = False
    priority_preservation: List[MessageType] = field(default_factory=lambda: [
        MessageType.SYSTEM_PROMPT,
        MessageType.CODING_RULE,
        MessageType.CONTEXT_SUMMARY
    ])
    
    def get_available_context(self) -> int:
        """Get available context tokens after reserving for response."""
        return max(self.context_length - self.recommended_reserve, 512)


class ModelRegistry:
    """Registry of known model configurations."""
    
    # Model configurations based on known OLLAMA models
    MODELS = {
        # Llama models
        "llama2": ModelInfo("llama2", ModelFamily.LLAMA, 4096, 512),
        "llama2:7b": ModelInfo("llama2:7b", ModelFamily.LLAMA, 4096, 512),
        "llama2:13b": ModelInfo("llama2:13b", ModelFamily.LLAMA, 4096, 512),
        "llama2:70b": ModelInfo("llama2:70b", ModelFamily.LLAMA, 4096, 1024),
        "llama3": ModelInfo("llama3", ModelFamily.LLAMA, 8192, 1024),
        "llama3:8b": ModelInfo("llama3:8b", ModelFamily.LLAMA, 8192, 1024),
        "llama3:70b": ModelInfo("llama3:70b", ModelFamily.LLAMA, 8192, 2048),
        "llama3.1": ModelInfo("llama3.1", ModelFamily.LLAMA, 128000, 4096),
        "llama3.1:8b": ModelInfo("llama3.1:8b", ModelFamily.LLAMA, 128000, 4096),
        "llama3.1:70b": ModelInfo("llama3.1:70b", ModelFamily.LLAMA, 128000, 8192),
        "llama3.2": ModelInfo("llama3.2", ModelFamily.LLAMA, 128000, 4096),
        
        # Code Llama models
        "codellama": ModelInfo("codellama", ModelFamily.CODELLAMA, 16384, 2048),
        "codellama:7b": ModelInfo("codellama:7b", ModelFamily.CODELLAMA, 16384, 2048),
        "codellama:13b": ModelInfo("codellama:13b", ModelFamily.CODELLAMA, 16384, 2048),
        "codellama:34b": ModelInfo("codellama:34b", ModelFamily.CODELLAMA, 16384, 4096),
        
        # Qwen models (these are often used for coding)
        "qwen": ModelInfo("qwen", ModelFamily.QWEN, 8192, 1024),
        "qwen2": ModelInfo("qwen2", ModelFamily.QWEN, 32768, 2048),
        "qwen2.5": ModelInfo("qwen2.5", ModelFamily.QWEN, 32768, 2048),
        "qwen2.5-coder": ModelInfo("qwen2.5-coder", ModelFamily.QWEN, 32768, 2048),
        
        # Mistral models
        "mistral": ModelInfo("mistral", ModelFamily.MISTRAL, 8192, 1024),
        "mistral:7b": ModelInfo("mistral:7b", ModelFamily.MISTRAL, 8192, 1024),
        "mixtral": ModelInfo("mixtral", ModelFamily.MISTRAL, 32768, 2048),
        "mixtral:8x7b": ModelInfo("mixtral:8x7b", ModelFamily.MISTRAL, 32768, 2048),
        
        # Gemma models
        "gemma": ModelInfo("gemma", ModelFamily.GEMMA, 8192, 1024),
        "gemma:7b": ModelInfo("gemma:7b", ModelFamily.GEMMA, 8192, 1024),
        "gemma2": ModelInfo("gemma2", ModelFamily.GEMMA, 8192, 1024),
        "gemma2:9b": ModelInfo("gemma2:9b", ModelFamily.GEMMA, 8192, 1024),
        
        # Phi models
        "phi3": ModelInfo("phi3", ModelFamily.PHI, 4096, 512),
        "phi3:mini": ModelInfo("phi3:mini", ModelFamily.PHI, 4096, 512),
        "phi3:medium": ModelInfo("phi3:medium", ModelFamily.PHI, 4096, 512),
    }
    
    @classmethod
    def get_model_info(cls, model_name: str) -> ModelInfo:
        """Get model information, with fuzzy matching and defaults."""
        # Direct match
        if model_name in cls.MODELS:
            return cls.MODELS[model_name]
        
        # Try fuzzy matching
        model_lower = model_name.lower()
        for known_name, info in cls.MODELS.items():
            if (known_name in model_lower or 
                model_lower.startswith(known_name.split(':')[0]) or
                any(family_name in model_lower for family_name in [
                    'llama', 'qwen', 'mistral', 'gemma', 'phi', 'codellama'
                ])):
                # Create a copy with the actual model name
                return ModelInfo(
                    name=model_name,
                    family=info.family,
                    context_length=info.context_length,
                    recommended_reserve=info.recommended_reserve,
                    supports_tool_calls=info.supports_tool_calls,
                    priority_preservation=info.priority_preservation.copy()
                )
        
        # Default for unknown models - conservative settings
        return cls._get_default_model_info(model_name)
    
    @classmethod
    def _get_default_model_info(cls, model_name: str) -> ModelInfo:
        """Get default model info for unknown models."""
        # Try to infer from the name
        context_length = 4096  # Conservative default
        reserve = 512
        
        # Look for clues in the model name
        if any(x in model_name.lower() for x in ['32k', '32768']):
            context_length = 32768
            reserve = 2048
        elif any(x in model_name.lower() for x in ['16k', '16384']):
            context_length = 16384
            reserve = 1024
        elif any(x in model_name.lower() for x in ['128k', '128000']):
            context_length = 128000
            reserve = 4096
        elif any(x in model_name.lower() for x in ['8k', '8192']):
            context_length = 8192
            reserve = 1024
        
        # Larger models typically need more reserve
        if any(x in model_name.lower() for x in ['70b', '72b', '65b']):
            reserve = max(reserve * 2, 2048)
        elif any(x in model_name.lower() for x in ['34b', '30b']):
            reserve = max(reserve * 1.5, 1024)
        
        return ModelInfo(
            name=model_name,
            family=ModelFamily.UNKNOWN,
            context_length=context_length,
            recommended_reserve=reserve
        )


@dataclass
class TokenBudgetStrategy:
    """Configuration for token budget management."""
    # Sliding window configuration
    preserve_recent_messages: int = 20  # Always keep recent messages
    preserve_system_messages: bool = True  # Always keep system messages
    
    # Context management
    target_utilization: float = 0.75  # Try to use 75% of available context
    emergency_threshold: float = 0.90  # Emergency compression at 90%
    
    # Summarization settings
    summarize_threshold: int = 50  # Start summarizing when we have 50+ messages
    messages_per_summary: int = 20  # Summarize in chunks of 20 messages
    min_summary_age_hours: int = 1  # Don't summarize very recent conversations


class TokenBudgetManager:
    """
    Smart token budget management with model-specific optimization.
    """
    
    def __init__(self, model_name: str, strategy: Optional[TokenBudgetStrategy] = None):
        self.model_info = ModelRegistry.get_model_info(model_name)
        self.strategy = strategy or TokenBudgetStrategy()
        
        # Cache for token calculations
        self._token_cache: Dict[str, int] = {}
    
    def calculate_tokens(self, text: str) -> int:
        """
        Calculate tokens for text with caching.
        Uses a simple but effective estimation method.
        """
        if text in self._token_cache:
            return self._token_cache[text]
        
        # Simple but effective tokenization estimation
        # More accurate than just character count / 4
        token_count = self._estimate_tokens(text)
        
        # Cache result
        if len(self._token_cache) < 10000:  # Prevent memory bloat
            self._token_cache[text] = token_count
        
        return token_count
    
    def _estimate_tokens(self, text: str) -> int:
        """Improved token estimation method."""
        if not text:
            return 0
        
        # Base calculation: words + punctuation + special tokens
        words = len(text.split())
        
        # Count special characters that often become separate tokens
        special_chars = len(re.findall(r'[^\w\s]', text))
        
        # Code-like content tends to have more tokens per character
        if self.model_info.family == ModelFamily.CODELLAMA:
            code_indicators = text.count('{') + text.count('}') + text.count('(') + text.count(')')
            special_chars += code_indicators * 0.5
        
        # Estimate tokens (roughly 1.3 tokens per word + special characters)
        estimated = int(words * 1.3 + special_chars * 0.7)
        
        # Add some buffer for model-specific tokenization differences
        return max(int(estimated * 1.1), 1)
    
    def assess_context_fit(self, messages: List[Message]) -> Dict[str, Any]:
        """
        Assess whether messages fit within the context budget.
        Returns detailed analysis and recommendations.
        """
        total_tokens = sum(self.calculate_tokens(msg.content) + 
                          sum(self.calculate_tokens(str(tc.arguments)) for tc in msg.tool_calls) +
                          sum(self.calculate_tokens(tr.content) for tr in msg.tool_results)
                          for msg in messages)
        
        available_context = self.model_info.get_available_context()
        utilization = total_tokens / available_context
        
        analysis = {
            "total_tokens": total_tokens,
            "available_context": available_context,
            "utilization": utilization,
            "fits": total_tokens <= available_context,
            "emergency": utilization >= self.strategy.emergency_threshold,
            "needs_optimization": utilization >= self.strategy.target_utilization,
            "messages_analyzed": len(messages),
            "model_info": {
                "name": self.model_info.name,
                "family": self.model_info.family.value,
                "context_length": self.model_info.context_length,
                "reserved": self.model_info.recommended_reserve
            }
        }
        
        # Add recommendations
        recommendations = []
        if analysis["emergency"]:
            recommendations.append("URGENT: Context usage is critical - immediate compression needed")
        elif analysis["needs_optimization"]:
            recommendations.append("Consider summarizing older messages")
        
        if len(messages) > self.strategy.summarize_threshold:
            recommendations.append(f"Consider summarizing - {len(messages)} messages exceeds threshold of {self.strategy.summarize_threshold}")
        
        analysis["recommendations"] = recommendations
        
        return analysis
    
    def optimize_message_list(self, messages: List[Message]) -> Tuple[List[Message], Dict[str, Any]]:
        """
        Optimize message list to fit within token budget.
        Returns optimized messages and optimization report.
        """
        if not messages:
            return [], {"action": "no_messages", "tokens_saved": 0}
        
        # Analyze current state
        analysis = self.assess_context_fit(messages)
        
        if analysis["fits"] and not analysis["needs_optimization"]:
            return messages, {"action": "no_optimization_needed", "tokens_saved": 0}
        
        # Separate messages by priority
        priority_messages = []
        regular_messages = []
        
        for msg in messages:
            if (msg.message_type in self.model_info.priority_preservation or
                msg.role == MessageRole.SYSTEM):
                priority_messages.append(msg)
            else:
                regular_messages.append(msg)
        
        # Always preserve recent messages
        recent_cutoff = max(0, len(regular_messages) - self.strategy.preserve_recent_messages)
        recent_messages = regular_messages[recent_cutoff:]
        older_messages = regular_messages[:recent_cutoff]
        
        # Start with priority messages and recent messages
        optimized_messages = priority_messages + recent_messages
        
        # Add older messages if they fit
        target_tokens = int(self.model_info.get_available_context() * self.strategy.target_utilization)
        current_tokens = sum(self.calculate_tokens(msg.content) for msg in optimized_messages)
        
        for msg in reversed(older_messages):  # Add most recent first
            msg_tokens = self.calculate_tokens(msg.content)
            if current_tokens + msg_tokens <= target_tokens:
                optimized_messages.insert(-len(recent_messages), msg)
                current_tokens += msg_tokens
            else:
                break
        
        # Sort by timestamp to maintain order
        optimized_messages.sort(key=lambda m: m.timestamp)
        
        # Calculate savings
        original_tokens = analysis["total_tokens"]
        new_tokens = sum(self.calculate_tokens(msg.content) for msg in optimized_messages)
        tokens_saved = original_tokens - new_tokens
        
        optimization_report = {
            "action": "optimized",
            "original_messages": len(messages),
            "optimized_messages": len(optimized_messages),
            "original_tokens": original_tokens,
            "optimized_tokens": new_tokens,
            "tokens_saved": tokens_saved,
            "utilization_before": analysis["utilization"],
            "utilization_after": new_tokens / self.model_info.get_available_context(),
            "priority_preserved": len(priority_messages),
            "recent_preserved": len(recent_messages),
            "older_included": len(optimized_messages) - len(priority_messages) - len(recent_messages)
        }
        
        return optimized_messages, optimization_report
    
    def suggest_summarization_candidates(self, conversation: ConversationHistory) -> List[Tuple[int, int]]:
        """
        Suggest ranges of messages that should be summarized.
        Returns list of (start_index, end_index) tuples.
        """
        messages = conversation.get_conversation_messages()
        
        if len(messages) < self.strategy.summarize_threshold:
            return []
        
        candidates = []
        
        # Find ranges of older messages that aren't already summarized
        preserve_recent = self.strategy.preserve_recent_messages
        available_for_summary = messages[:-preserve_recent] if preserve_recent < len(messages) else []
        
        # Group into chunks for summarization
        chunk_size = self.strategy.messages_per_summary
        for i in range(0, len(available_for_summary), chunk_size):
            end_idx = min(i + chunk_size, len(available_for_summary))
            if end_idx - i >= chunk_size // 2:  # Only suggest if chunk is reasonably sized
                candidates.append((i, end_idx))
        
        return candidates
    
    def get_context_status(self, messages: List[Message]) -> str:
        """Get human-readable context status."""
        analysis = self.assess_context_fit(messages)
        
        utilization = analysis["utilization"]
        tokens = analysis["total_tokens"]
        available = analysis["available_context"]
        
        if utilization >= 0.9:
            color = "red"
            status = "CRITICAL"
        elif utilization >= 0.75:
            color = "yellow" 
            status = "HIGH"
        elif utilization >= 0.5:
            color = "cyan"
            status = "MODERATE"
        else:
            color = "green"
            status = "LOW"
        
        return f"[{color}]{status}[/{color}]: {tokens:,}/{available:,} tokens ({utilization:.1%})"
