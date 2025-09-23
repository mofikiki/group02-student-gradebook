
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from .models import Student, Assignment
from .exceptions import InvalidGradeError, DuplicateEntityError, NotFoundError, WeightError

def default_gpa_scale() -> List[Tuple[float, float]]:
    """5.0 max scale (Nigeria common variant)."""
    return [
        (70.0, 5.0),
        (60.0, 4.0),
        (50.0, 3.0),
        (45.0, 2.0),
        (40.0, 1.0),
        (0.0, 0.0),
    ]

@dataclass
class Gradebook:
    students: Dict[str, Student] = field(default_factory=dict)
    assignments: Dict[str, Assignment] = field(default_factory=dict)
    grades: Dict[str, Dict[str, float]] = field(default_factory=dict)
    strict_weights: bool = False
    gpa_scale: List[Tuple[float, float]] = field(default_factory=default_gpa_scale)

    # ---- CRUD: Students ----
    def add_student(self, student: Student) -> None:
        if student.student_id in self.students:
            raise DuplicateEntityError("Student id already exists")
        self.students[student.student_id] = student
        self.grades.setdefault(student.student_id, {})

    def get_student(self, student_id: str) -> Student:
        if student_id not in self.students:
            raise NotFoundError("Student id not found")
        return self.students[student_id]

    def update_student(self, student_id: str, **updates) -> None:
        st = self.get_student(student_id)
        data = st.__dict__.copy()
        data.update(updates)
        self.students[student_id] = Student(**data)

    def delete_student(self, student_id: str) -> None:
        if student_id not in self.students:
            raise NotFoundError("Student id not found")
        del self.students[student_id]
        self.grades.pop(student_id, None)

    # ---- CRUD: Assignments ----
    def add_assignment(self, assignment: Assignment) -> None:
        if assignment.assignment_id in self.assignments:
            raise DuplicateEntityError("Assignment id already exists")
        self.assignments[assignment.assignment_id] = assignment

    def get_assignment(self, assignment_id: str) -> Assignment:
        if assignment_id not in self.assignments:
            raise NotFoundError("Assignment id not found")
        return self.assignments[assignment_id]

    def update_assignment(self, assignment_id: str, **updates) -> None:
        a = self.get_assignment(assignment_id)
        data = a.__dict__.copy()
        data.update(updates)
        self.assignments[assignment_id] = Assignment(**data)

    def delete_assignment(self, assignment_id: str) -> None:
        if assignment_id not in self.assignments:
            raise NotFoundError("Assignment id not found")
        del self.assignments[assignment_id]
        for sid in list(self.grades.keys()):
            self.grades[sid].pop(assignment_id, None)

    # ---- Grades ----
    def enter_grade(self, student_id: str, assignment_id: str, score: float) -> None:
        if student_id not in self.students:
            raise NotFoundError("Student id not found")
        if assignment_id not in self.assignments:
            raise NotFoundError("Assignment id not found")
        if not isinstance(score, (int, float)):
            raise InvalidGradeError("Score must be numeric")
        maxp = self.assignments[assignment_id].max_points
        if score < 0 or score > maxp:
            raise InvalidGradeError(f"Score must be between 0 and {maxp}")
        self.grades.setdefault(student_id, {})[assignment_id] = float(score)

    # ---- Calculations ----
    def _weights_ok(self):
        wsum = sum(a.weight for a in self.assignments.values())
        return (abs(wsum - 1.0) < 1e-6, wsum)

    def _normalized_weights(self):
        wsum = sum(a.weight for a in self.assignments.values())
        if wsum <= 0:
            raise WeightError("Total assignment weight is zero; cannot compute final grades")
        return {aid: (a.weight / wsum) for aid, a in self.assignments.items()}

    def student_percentage(self, student_id: str) -> float:
        if self.strict_weights:
            ok, wsum = self._weights_ok()
            if not ok:
                raise WeightError(f"Weights must sum to 1.0 when strict; got {wsum:.3f}")
            weights = {aid: a.weight for aid, a in self.assignments.items()}
        else:
            weights = self._normalized_weights()

        total = 0.0
        for aid, a in self.assignments.items():
            score = self.grades.get(student_id, {}).get(aid)
            s = 0.0 if score is None else (score / a.max_points)
            total += s * weights[aid] * 100.0
        return total

    def student_gpa(self, student_id: str) -> float:
        pct = self.student_percentage(student_id)
        for threshold, gpa in self.gpa_scale:
            if pct >= threshold:
                return gpa
        return 0.0

    def class_average(self) -> float:
        if not self.students:
            return 0.0
        return sum(self.student_percentage(sid) for sid in self.students) / len(self.students)

    # ---- Curve tools ----
    def curve_add(self, points: float) -> None:
        for sid, gdict in self.grades.items():
            for aid, score in list(gdict.items()):
                maxp = self.assignments[aid].max_points
                gdict[aid] = min(score + points, maxp)

    def curve_scale(self, factor: float) -> None:
        for sid, gdict in self.grades.items():
            for aid, score in list(gdict.items()):
                maxp = self.assignments[aid].max_points
                gdict[aid] = min(score * factor, maxp)
