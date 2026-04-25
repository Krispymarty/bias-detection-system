"""
FairSight AI — Mock Data Generators
Provides realistic demo data for dashboard, charts, simulator, FAQ, and tutorials.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def get_dashboard_metrics():
    """Dashboard metric card values."""
    return {
        "fairness_score": 94.7,
        "fairness_delta": 2.3,
        "bias_index": 0.12,
        "bias_delta": -0.03,
        "accuracy": 97.2,
        "accuracy_delta": 0.8,
        "models_analyzed": 1247,
        "models_delta": 156,
    }


def get_fairness_trend_data():
    """Generate 30-day fairness trend for line charts."""
    dates = pd.date_range(end=datetime.now(), periods=30, freq="D")
    np.random.seed(42)
    fairness = np.cumsum(np.random.randn(30) * 0.5) + 88
    fairness = np.clip(fairness, 70, 100)
    bias = np.abs(np.cumsum(np.random.randn(30) * 0.02)) + 0.05
    bias = np.clip(bias, 0, 0.5)
    accuracy = np.cumsum(np.random.randn(30) * 0.3) + 93
    accuracy = np.clip(accuracy, 85, 100)
    return pd.DataFrame(
        {
            "Date": dates,
            "Fairness Score": np.round(fairness, 1),
            "Bias Index": np.round(bias, 3),
            "Accuracy": np.round(accuracy, 1),
        }
    )


def get_model_distribution():
    """Category-level fairness and bias risk data."""
    return pd.DataFrame(
        {
            "Category": ["Gender", "Race", "Age", "Income", "Education"],
            "Fairness": [92, 88, 95, 84, 91],
            "Bias Risk": [8, 12, 5, 16, 9],
        }
    )


def get_activity_feed():
    """Recent activity feed items for the dashboard."""
    return [
        {"time": "2 min ago", "action": "Model fairness scan completed", "icon": "✅", "type": "success"},
        {"time": "15 min ago", "action": "New bias alert detected in Model-7B", "icon": "⚠️", "type": "warning"},
        {"time": "1 hr ago", "action": "Dashboard report generated", "icon": "📊", "type": "info"},
        {"time": "2 hrs ago", "action": "What-If simulation completed", "icon": "🔬", "type": "info"},
        {"time": "3 hrs ago", "action": "AI Agent analyzed 3 datasets", "icon": "🤖", "type": "success"},
        {"time": "5 hrs ago", "action": "Settings updated by admin", "icon": "⚙️", "type": "info"},
        {"time": "1 day ago", "action": "New model version deployed", "icon": "🚀", "type": "success"},
    ]


def get_whatif_result(gender_ratio, age_range, income_level, education_bias):
    """Simulate what-if scenario results based on slider inputs."""
    base_fairness = 85
    base_bias = 0.15

    fairness_adj = (gender_ratio - 50) * -0.1
    age_adj = (age_range[1] - age_range[0]) * 0.05
    income_adj = income_level * 0.5
    edu_adj = education_bias * -0.2

    fairness = min(100, max(0, base_fairness + fairness_adj + age_adj + income_adj + edu_adj))
    bias = max(0, min(1, base_bias - (fairness - 85) * 0.005))
    accuracy = min(100, max(60, 90 + (fairness - 85) * 0.3))

    return {
        "fairness": round(fairness, 1),
        "bias": round(bias, 3),
        "accuracy": round(accuracy, 1),
        "risk_level": "Low" if bias < 0.1 else ("Medium" if bias < 0.2 else "High"),
        "risk_color": "#00FFD1" if bias < 0.1 else ("#FFD700" if bias < 0.2 else "#FF5050"),
    }


def get_ai_responses():
    """Pre-defined AI agent responses keyed by prompt text."""
    return {
        "What is algorithmic fairness?": (
            "Algorithmic fairness refers to the design and implementation of algorithms "
            "that make decisions without systematically discriminating against specific groups. "
            "Key concepts include:\n\n"
            "• **Demographic Parity** — Equal positive outcome rates across groups\n"
            "• **Equalized Odds** — Equal true positive and false positive rates\n"
            "• **Individual Fairness** — Similar individuals receive similar outcomes\n"
            "• **Counterfactual Fairness** — Outcome doesn't change if sensitive attribute changes\n\n"
            "FairSight AI helps you measure and improve these metrics across your ML models."
        ),
        "How does bias detection work?": (
            "Bias detection in FairSight AI uses a multi-layered approach:\n\n"
            "1. **Data Analysis** — We scan your training data for representation imbalances\n"
            "2. **Model Auditing** — We test model predictions across demographic groups\n"
            "3. **Statistical Testing** — We apply fairness metrics (SPD, DI, EOD) to quantify bias\n"
            "4. **Intersectional Analysis** — We check for compound biases across multiple attributes\n\n"
            "Our system provides actionable recommendations to mitigate detected biases."
        ),
        "Show me fairness metrics": (
            "Here are the key fairness metrics we track:\n\n"
            "📊 **Statistical Parity Difference (SPD)**: Measures the difference in positive outcome "
            "rates between groups. Target: < 0.1\n\n"
            "📊 **Disparate Impact (DI)**: Ratio of positive outcomes between groups. Target: 0.8 – 1.2\n\n"
            "📊 **Equal Opportunity Difference (EOD)**: Difference in true positive rates. Target: < 0.1\n\n"
            "📊 **Predictive Parity**: Equal precision across groups. Target: < 0.05 difference\n\n"
            "Your current model scores well on SPD and DI but needs improvement on EOD."
        ),
        "default": (
            "I'm FairSight AI's analytical assistant. I can help you understand:\n\n"
            "• Algorithmic fairness concepts\n"
            "• Bias detection methods\n"
            "• How to interpret fairness metrics\n"
            "• Best practices for ethical AI\n"
            "• What-If scenario analysis\n\n"
            "Please ask me anything about AI fairness and I'll provide detailed insights!"
        ),
    }


def get_faq_data():
    """FAQ entries for the help & support page."""
    return [
        {
            "question": "What is FairSight AI?",
            "answer": "FairSight AI is a comprehensive platform for detecting, analyzing, and mitigating bias in artificial intelligence and machine learning models. It provides tools for fairness auditing, what-if simulations, and AI-powered bias analysis.",
        },
        {
            "question": "How does FairSight AI detect bias?",
            "answer": "FairSight AI uses statistical analysis, demographic parity testing, equalized odds evaluation, and intersectional analysis to detect bias across multiple dimensions including gender, race, age, and socioeconomic factors.",
        },
        {
            "question": "Is my data secure?",
            "answer": "Absolutely. FairSight AI uses end-to-end encryption, complies with GDPR and SOC 2 standards, and never shares your data with third parties. All analysis is performed in isolated environments.",
        },
        {
            "question": "Can I integrate FairSight AI with my existing ML pipeline?",
            "answer": "Yes! FairSight AI provides REST APIs and Python SDK for seamless integration with popular ML frameworks like TensorFlow, PyTorch, scikit-learn, and major MLOps platforms.",
        },
        {
            "question": "What types of models can I analyze?",
            "answer": "FairSight AI supports classification models, regression models, NLP models, recommendation systems, and computer vision models. We support tabular, text, and image data formats.",
        },
        {
            "question": "How often should I run fairness audits?",
            "answer": "We recommend running fairness audits after every model update, when training data changes significantly, and on a regular schedule (at least monthly for production models).",
        },
    ]


def get_tutorial_steps():
    """Step-by-step tutorial data."""
    return [
        {
            "step": 1,
            "title": "Upload Your Model",
            "description": "Upload your trained model or connect to your ML pipeline. We support TensorFlow, PyTorch, scikit-learn, and ONNX formats.",
            "icon": "📤",
        },
        {
            "step": 2,
            "title": "Configure Fairness Criteria",
            "description": "Define protected attributes (gender, race, age) and select fairness metrics to evaluate. Set acceptable thresholds for each metric.",
            "icon": "⚙️",
        },
        {
            "step": 3,
            "title": "Run Bias Analysis",
            "description": "Our AI engine analyzes your model's predictions across demographic groups, identifying potential biases and disparate impacts.",
            "icon": "🔍",
        },
        {
            "step": 4,
            "title": "Review Results",
            "description": "Explore detailed reports with interactive charts, statistical tests, and intersectional analysis. Understand where and why bias exists.",
            "icon": "📊",
        },
        {
            "step": 5,
            "title": "Apply Mitigations",
            "description": "Use AI-recommended strategies to reduce bias: re-sampling, re-weighting, adversarial debiasing, or threshold adjustment.",
            "icon": "🛡️",
        },
        {
            "step": 6,
            "title": "Monitor & Iterate",
            "description": "Set up continuous monitoring to catch bias drift. Receive alerts when fairness metrics fall below thresholds.",
            "icon": "📡",
        },
    ]
