from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Student:
    id: str
    name: str
    workplace: Optional[str]
    max_distance: int
    preferred_type: Optional[str]
    other_constraints: Optional[str]
