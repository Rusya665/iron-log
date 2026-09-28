from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Log:
    """
    Exercise execution log representing performed sets.

    :param reps: Repetitions completed per set.
    :param mass: Working mass in kilograms lifted per set.
    """

    reps: List[float]
    mass: List[float]


@dataclass
class Exercise:
    """
    Exercise registry entry defining canonical ID and display name.

    :param id: Unique canonical identifier slug.
    :param display_name: Optional human-readable exercise name.
    """

    id: str
    display_name: Optional[str] = None

    def __post_init__(self) -> None:
        """
        Default display name to ID when unset.

        :return: None
        """
        if self.display_name is None:
            self.display_name = self.id
