from pydantic import BaseModel


class IdeaModel(BaseModel):
    topic: str | None
    audience: str | None
    audience_knowledge: str | None
    audience_care: str | None
    desired_action: str | None
    goal: str | None
    perspective: str | None


class Evaluation(BaseModel):
    evaluation: str
    suggestions: str
    test_passed: bool


class TestResult(BaseModel):
    clarity: Evaluation
    alignment_with_objectives: Evaluation
    completeness: Evaluation
    overall_suggestions: str
