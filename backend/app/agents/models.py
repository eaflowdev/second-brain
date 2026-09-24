from dataclasses import dataclass
from typing import Callable


@dataclass
class Tool:
    """A capability the agent can invoke: name + JSON-schema params + handler."""

    name: str
    description: str
    parameters: dict
    handler: Callable[..., str]

    def to_schema(self) -> dict:
        """OpenAI-compatible function schema, as expected by the tools= param."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
