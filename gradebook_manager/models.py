
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from datetime import date

@dataclass(eq=True, frozen=True)
class Student:
    student_id: str
    first_name: str
    last_name: str
    email: str = ""
    def __str__(self) -> str:
        return f"{self.last_name}, {self.first_name} ({self.student_id})"

@dataclass
class Assignment:
    assignment_id: str
    name: str
    max_points: float = 100.0
    weight: float = 0.0
    due: Optional[date] = None
    type: str = "generic"
    description: str = ""
    def __post_init__(self):
        if self.max_points <= 0: raise ValueError("max_points must be > 0")
        if not (0.0 <= self.weight <= 1.0): raise ValueError("weight must be between 0.0 and 1.0")
    def __str__(self) -> str:
        w = f"{self.weight * 100:.0f}%"
        return f"{self.name} [{self.type}] (max {self.max_points}, weight {w})"

class Quiz(Assignment):
    def __init__(self, **kwargs): super().__init__(type="quiz", **kwargs)
class Exam(Assignment):
    def __init__(self, **kwargs): super().__init__(type="exam", **kwargs)
class Project(Assignment):
    def __init__(self, **kwargs): super().__init__(type="project", **kwargs)
class Homework(Assignment):
    def __init__(self, **kwargs): super().__init__(type="homework", **kwargs)
