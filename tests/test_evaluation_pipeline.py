import pytest
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from eval_harness import GoldenDatasetEvaluator

@pytest.fixture
def evaluator():
    """Initialize evaluator for tests"""
    return GoldenDatasetEvaluator()

def test_evaluation_runs(evaluator):
    """Test that evaluation completes"""
    results = evaluator.evaluate_all()
    
    assert results is not None
    assert "pass_rate" in results
    print(f"\nPass rate: {results['pass_rate']:.0%}")

def test_pass_rate_threshold(evaluator):
    """Test that agent meets minimum performance"""
    results = evaluator.evaluate_all()
    
    # Minimum acceptable: 70% pass rate
    assert results["pass_rate"] >= 0.70, f"Pass rate {results['pass_rate']:.0%} below 70%"

def test_node_recall_threshold(evaluator):
    """Test node recall metric"""
    results = evaluator.evaluate_all()
    
    # Minimum: mention 70% of expected tables
    assert results["avg_node_recall"] >= 0.70

def test_answer_relevance_threshold(evaluator):
    """Test answer relevance"""
    results = evaluator.evaluate_all()
    
    # Minimum: 65% of answers relevant
    assert results["avg_answer_relevance"] >= 0.65

def test_no_test_failures(evaluator):
    """Ensure no test cases cause errors"""
    results = evaluator.evaluate_all()
    
    # Should evaluate all test cases without crashing
    assert results["total_tests"] == len(results["metrics"])

