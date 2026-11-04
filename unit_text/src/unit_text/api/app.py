from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from unit_text.core import IdeaModel, TestResult, run_tests

app = FastAPI()


class TestRequest(BaseModel):
    draft: str
    idea: IdeaModel


@app.get("/")
async def root():
    return {"message": "Welcome to the unit-text API!"}


@app.post("/test")
async def test(request: TestRequest) -> TestResult:
    print("Running tests...")

    try:
        return run_tests(request.draft, request.idea)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
