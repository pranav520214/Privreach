from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class TaskType(str, Enum):
    LITERATURE_REVIEW = "literature_review"
    DATA_EXTRACTION = "data_extraction"
    MATHEMATICAL_MODELING = "mathematical_modeling"
    CLAIM_VERIFICATION = "claim_verification"
    GENERAL_QA = "general_qa"

class RiskLevel(str, Enum):
    LOW = "low" # Standard QA, harmless failure
    MEDIUM = "medium" # Requires citations, moderate accuracy needed
    CRITICAL_RESEARCH = "critical_research" # Requires strict evidence pipeline, contradiction detection, and mathematical verification

class RequiredTools(str, Enum):
    HYBRID_SEARCH = "hybrid_search"
    SYMPY_MATH = "sympy_math"
    CITATION_CHECKER = "citation_checker"
    CODE_INTERPRETER = "code_interpreter"

class ExecutionPlan(BaseModel):
    domain: str = Field(description="The scientific domain of the query (e.g., 'Pharmacokinetics', 'Oncology')")
    task_type: TaskType = Field(description="The primary objective of the query")
    risk_level: RiskLevel = Field(description="The risk/criticality level of the query")
    requires_retrieval: bool = Field(description="Whether the system needs to search the scientific corpus for evidence")
    required_tools: List[RequiredTools] = Field(description="List of external tools required to solve the task")
    reasoning: str = Field(description="A brief explanation of why this execution plan was chosen")
