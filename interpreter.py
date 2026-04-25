"""
FairLens — Fairness Interpreter (Step 1)
========================================

Computes the Bias Score from the fairness score returned by the model API,
applies threshold logic, and determines the bias status.

Decision Rules:
    - Bias Score = 100 - fairness.score
    - Bias Threshold = 10
    - If Bias Score > Threshold → Bias needs adjustment
    - If Bias Score ≤ Threshold → System is acceptable
"""

from typing import Dict, Any, Optional


# Immutable threshold constant
BIAS_THRESHOLD = 10


class FairnessInterpreter:
    """Interprets the fairness block from a financial decision API response."""

    def __init__(self, threshold: float = BIAS_THRESHOLD):
        self.threshold = threshold

    def interpret(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts fairness data from the API response and computes bias metrics.

        Parameters
        ----------
        api_response : dict
            The full JSON response from the model API, expected to contain
            a 'fairness' key with nested 'score', 'badge', 'bias_source',
            and 'bias_metrics'.

        Returns
        -------
        dict
            A structured interpretation result with the following keys:
            - prediction (str)
            - probability (float)
            - recommendation (str)
            - fairness_score (float)
            - bias_score (float)
            - bias_status (str): "Needs Adjustment" or "Acceptable"
            - bias_exceeded (bool)
            - badge (str)
            - bias_source (str)
            - bias_metrics (dict)
            - threshold (float)
        """
        # Extract top-level fields — never invent missing data
        prediction = api_response.get("prediction")
        probability = api_response.get("probability")
        recommendation = api_response.get("recommendation")

        # Extract the fairness block
        fairness = api_response.get("fairness", {})
        fairness_score = fairness.get("score")
        badge = fairness.get("badge")
        bias_source = fairness.get("bias_source")
        bias_metrics = fairness.get("bias_metrics", {})

        # Compute Bias Score
        if fairness_score is not None:
            bias_score = round(100 - fairness_score, 2)
        else:
            bias_score = None

        # Determine threshold status
        if bias_score is not None:
            bias_exceeded = bias_score > self.threshold
            bias_status = "Needs Adjustment" if bias_exceeded else "Acceptable"
        else:
            bias_exceeded = None
            bias_status = "Unknown — fairness score not provided"

        return {
            "prediction": prediction,
            "probability": probability,
            "recommendation": recommendation,
            "fairness_score": fairness_score,
            "bias_score": bias_score,
            "bias_status": bias_status,
            "bias_exceeded": bias_exceeded,
            "badge": badge,
            "bias_source": bias_source,
            "bias_metrics": bias_metrics,
            "threshold": self.threshold,
        }
