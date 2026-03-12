from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Log:
    """Input data for a single exercise session."""
    reps: List[float]
    mass: List[float]

@dataclass
class Exercise:
    """Registry for exercise identity."""
    id: str
    display_name: Optional[str] = None

    def __post_init__(self):
        if self.display_name is None:
            self.display_name = self.id
