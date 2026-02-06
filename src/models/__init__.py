"""
Models package - Pydantic schemas for inputs and outputs.
"""
from src.models.inputs import (
    StartupSubmission,
    SubmitInput,
    AnswerInput,
    UpgradeInput,
    AdminUpdate,
    ValidationState,
)
from src.models.outputs import (
    ViabilityScores,
    GoNoGoScores,
    FreeReportOutput,
    BasicReportOutput,
    StandardReportOutput,
    PremiumReportOutput,
)

__all__ = [
    # Inputs
    "StartupSubmission",
    "SubmitInput",
    "AnswerInput",
    "UpgradeInput",
    "AdminUpdate",
    "ValidationState",
    # Outputs
    "ViabilityScores",
    "GoNoGoScores",
    "FreeReportOutput",
    "BasicReportOutput",
    "StandardReportOutput",
    "PremiumReportOutput",
]
