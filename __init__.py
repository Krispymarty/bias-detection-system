"""
FairLens - Ethical AI Middleware for Bias Audit Report Generation
================================================================

A production-ready middleware that interprets financial decision API outputs,
runs What-If simulations, generates professional Bias Audit Reports, and
prepares structured data for the backend pipeline:
TEXT → PDF → FILE PATH → DATABASE → EMAIL.

Usage:
    from fairlens import FairLensMiddleware
    middleware = FairLensMiddleware(predict_fn=my_api_caller)
    result = middleware.process(api_response, user_features=features,
                               user_email="user@example.com")
"""

from .middleware import FairLensMiddleware
from .interpreter import FairnessInterpreter
from .simulator import WhatIfSimulator
from .report_generator import ReportGenerator
from .formatter import PDFContentFormatter
from .storage_builder import StorageWorkflowBuilder
from .validator import InputValidator, InputValidationError

__version__ = "3.0.0"
__all__ = [
    "FairLensMiddleware",
    "FairnessInterpreter",
    "WhatIfSimulator",
    "ReportGenerator",
    "PDFContentFormatter",
    "StorageWorkflowBuilder",
    "InputValidator",
    "InputValidationError",
]
