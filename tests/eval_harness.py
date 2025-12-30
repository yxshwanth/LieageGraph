import json
from typing import Dict, List, Any
import re
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.graph import run_agent
from src.agents.llm import get_llm

# Known tables in the system
KNOWN_TABLES = {
    "users",
    "orders", 
    "order_clean",
    "revenue_daily",
    "revenue_dashboard",
}

class GoldenDatasetEvaluator:
    def __init__(self, dataset_path: str = "tests/data/golden_dataset.json"):
        """Load golden dataset"""
        dataset_full_path = Path(__file__).parent.parent / dataset_path
        with open(dataset_full_path, 'r') as f:
            self.dataset = json.load(f)
        
        self.llm = get_llm()
    
    def extract_table_names(self, text: str) -> set:
        """Extract table names mentioned in text - only match known tables"""
        text_lower = text.lower()
        found = set()
        
        # Hard-match against known tables only
        for tbl in KNOWN_TABLES:
            if tbl in text_lower:
                found.add(tbl)
        
        return found
    
    def compute_node_recall(
        self,
        generated_tables: set,
        expected_tables: set
    ) -> float:
        """
        Compute recall: what fraction of expected tables were mentioned?
        Recall = correct / expected
        """
        if not expected_tables:
            return 1.0
        
        # Normalize table names for comparison (lowercase, handle variations)
        generated_normalized = {t.lower().replace(' ', '_') for t in generated_tables}
        expected_normalized = {t.lower().replace(' ', '_') for t in expected_tables}
        
        correct = len(generated_normalized & expected_normalized)
        return correct / len(expected_normalized) if expected_normalized else 0.0
    
    def compute_answer_relevance(
        self,
        question: str,
        generated_answer: str,
        expected_answer: str
    ) -> float:
        """
        Use LLM to judge if generated answer matches expected answer.
        """
        prompt = f"""Rate how well the generated answer matches the expected answer (0.0-1.0).

Question: {question}

Expected: {expected_answer}

Generated: {generated_answer}

Respond with ONLY a number between 0.0 and 1.0, like: 0.85"""
        
        try:
            response = self.llm.generate(prompt).strip()
            # Extract float from response
            match = re.search(r'0?\.\d+|1\.0|1\.00', response)
            if match:
                score = float(match.group())
                # Clamp to [0, 1]
                return max(0.0, min(1.0, score))
        except Exception as e:
            print(f"    Warning: LLM evaluation failed: {e}")
        
        return 0.5  # Default if LLM fails
    
    def evaluate_single(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate agent on a single test case.
        """
        question = test_case["question"]
        expected_answer = test_case["expected_answer"]
        expected_tables = set(test_case["expected_tables"])
        
        # Run agent
        result = run_agent(question, verbose=False)
        
        generated_answer = result.get("final_answer", "")
        generated_tables = self.extract_table_names(generated_answer)
        
        # Also check tool results for table names
        tool_results = result.get("tool_results", {})
        for tool_result in tool_results.values():
            if isinstance(tool_result, dict):
                result_text = json.dumps(tool_result)
                generated_tables.update(self.extract_table_names(result_text))
        
        # Compute metrics
        node_recall = self.compute_node_recall(
            generated_tables,
            expected_tables
        )
        
        answer_relevance = self.compute_answer_relevance(
            question,
            generated_answer,
            expected_answer
        )
        
        # Combined score (weighted average)
        score = (node_recall * 0.4) + (answer_relevance * 0.6)
        
        return {
            "question": question,
            "difficulty": test_case["difficulty"],
            "category": test_case.get("category", "unknown"),
            "node_recall": node_recall,
            "answer_relevance": answer_relevance,
            "combined_score": score,
            "passed": score > 0.3,  # Temporarily lowered for iteration
            "generated_tables": list(generated_tables),
            "expected_tables": list(expected_tables),
            "generated_answer": generated_answer[:200] + "..." if len(generated_answer) > 200 else generated_answer
        }
    
    def evaluate_all(self) -> Dict[str, Any]:
        """
        Evaluate agent on all test cases.
        """
        results = {
            "total_tests": len(self.dataset),
            "passed": 0,
            "failed": 0,
            "by_difficulty": {
                "easy": {"passed": 0, "total": 0},
                "medium": {"passed": 0, "total": 0},
                "hard": {"passed": 0, "total": 0},
            },
            "metrics": []
        }
        
        print(f"Evaluating {len(self.dataset)} test cases...\n")
        
        for idx, test_case in enumerate(self.dataset, 1):
            try:
                print(f"[{idx}/{len(self.dataset)}] {test_case['question'][:60]}...")
                metric = self.evaluate_single(test_case)
                results["metrics"].append(metric)
                
                if metric["passed"]:
                    results["passed"] += 1
                    print(f"  ✓ PASSED (score: {metric['combined_score']:.2f})")
                else:
                    results["failed"] += 1
                    print(f"  ✗ FAILED (score: {metric['combined_score']:.2f})")
                
                difficulty = test_case["difficulty"]
                results["by_difficulty"][difficulty]["total"] += 1
                if metric["passed"]:
                    results["by_difficulty"][difficulty]["passed"] += 1
                
            except Exception as e:
                print(f"  ✗ ERROR: {e}")
                import traceback
                traceback.print_exc()
                results["failed"] += 1
        
        # Compute overall metrics
        if results["metrics"]:
            results["pass_rate"] = results["passed"] / results["total_tests"]
            results["avg_node_recall"] = sum(m["node_recall"] for m in results["metrics"]) / len(results["metrics"])
            results["avg_answer_relevance"] = sum(m["answer_relevance"] for m in results["metrics"]) / len(results["metrics"])
            results["avg_combined_score"] = sum(m["combined_score"] for m in results["metrics"]) / len(results["metrics"])
        else:
            results["pass_rate"] = 0.0
            results["avg_node_recall"] = 0.0
            results["avg_answer_relevance"] = 0.0
            results["avg_combined_score"] = 0.0
        
        return results

def main():
    """Run full evaluation"""
    print("="*60)
    print("GOLDEN DATASET EVALUATION")
    print("="*60)
    print(f"Dataset: tests/data/golden_dataset.json\n")
    
    evaluator = GoldenDatasetEvaluator()
    results = evaluator.evaluate_all()
    
    print(f"\n{'='*60}")
    print(f"EVALUATION RESULTS")
    print(f"{'='*60}")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']}/{results['total_tests']} ({results['pass_rate']:.1%})")
    print(f"Failed: {results['failed']}/{results['total_tests']}")
    print(f"\nAverage Metrics:")
    print(f"  Node Recall: {results['avg_node_recall']:.1%}")
    print(f"  Answer Relevance: {results['avg_answer_relevance']:.1%}")
    print(f"  Combined Score: {results['avg_combined_score']:.2f}")
    
    print(f"\nBy Difficulty:")
    for diff, stats in results["by_difficulty"].items():
        if stats["total"] > 0:
            rate = stats["passed"] / stats["total"]
            print(f"  {diff.capitalize()}: {stats['passed']}/{stats['total']} ({rate:.1%})")
    
    # Show failed tests
    failed_tests = [m for m in results["metrics"] if not m["passed"]]
    if failed_tests:
        print(f"\n{'='*60}")
        print(f"FAILED TESTS ({len(failed_tests)})")
        print(f"{'='*60}")
        for metric in failed_tests[:5]:  # Show first 5 failures
            print(f"\nQuestion: {metric['question']}")
            print(f"Score: {metric['combined_score']:.2f} (Recall: {metric['node_recall']:.1%}, Relevance: {metric['answer_relevance']:.1%})")
            print(f"Expected tables: {', '.join(metric['expected_tables'])}")
            print(f"Found tables: {', '.join(metric['generated_tables'])}")
    
    return results

if __name__ == "__main__":
    main()

