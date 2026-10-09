"""Tests for RLCD Router and QueryAnalyzer."""

import pytest
from unittest.mock import MagicMock
from privearch.schemas import QueryAnalysis, RiskLevel, TaskType
from privearch.models.query_analyzer import QueryAnalyzer
from privearch.models.client import LocalModelClient


def test_query_analyzer_fallback():
    mock_client = MagicMock(spec=LocalModelClient)
    mock_client.generate.side_effect = Exception("Model unreachable")

    analyzer = QueryAnalyzer(mock_client)
    result = analyzer.analyze("Calculate the equilibrium constant of ammonia synthesis at 500K")

    assert isinstance(result, QueryAnalysis)
    assert result.task_type in [TaskType.CALCULATION_DERIVATION, TaskType.LITERATURE_REVIEW, TaskType.MECHANISTIC_SYNTHESIS]
    assert len(result.lexical_keywords) > 0


def test_query_analyzer_parsing():
    mock_client = MagicMock(spec=LocalModelClient)
    mock_client.generate.return_value = """{
      "risk_level": "HIGH",
      "task_type": "CALCULATION_DERIVATION",
      "scientific_domain": "Physical Chemistry",
      "key_entities": ["NH3", "Equilibrium Constant"],
      "lexical_keywords": ["equilibrium", "constant", "ammonia"],
      "semantic_queries": ["How to calculate equilibrium constant of ammonia?"],
      "adversarial_audit_required": false,
      "analysis_rationale": "High temperature equilibrium calculation"
    }"""

    analyzer = QueryAnalyzer(mock_client)
    result = analyzer.analyze("What is the equilibrium constant of NH3?")

    assert result.risk_level == RiskLevel.HIGH
    assert result.task_type == TaskType.CALCULATION_DERIVATION
    assert "ammonia" in result.lexical_keywords
