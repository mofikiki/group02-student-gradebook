class GradebookError(Exception): pass
class InvalidGradeError(GradebookError): pass
class DuplicateEntityError(GradebookError): pass
class NotFoundError(GradebookError): pass
class WeightError(GradebookError): pass
