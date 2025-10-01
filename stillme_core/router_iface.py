from typing import Protocol, runtime_checkable


@runtime_checkable
class Router(Protocol):
    """Interface for model routing implementations.
    
    Both Pro and Stub implementations must conform to this protocol.
    """
    def choose_model(self, prompt: str) -> str:
        """Choose the most appropriate model for the given prompt.
        
        Args:
            prompt: The input prompt to analyze
            
        Returns:
            Model identifier string
        """
        ...
