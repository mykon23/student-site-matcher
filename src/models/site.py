from dataclasses import dataclass

@dataclass
class Site:
    id: str
    name: str
    type: str
    distance: float
    capacity: int