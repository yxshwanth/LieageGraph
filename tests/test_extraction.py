"""
Quick sanity check script to test table name extraction on a single test case.
Run this to verify extraction works correctly before running full evaluation.
"""

from eval_harness import GoldenDatasetEvaluator

def test_single_case():
    """Test extraction on the first test case"""
    ev = GoldenDatasetEvaluator()
    case = ev.dataset[0]  # 'What feeds into the revenue dashboard?'
    
    print("="*60)
    print("SANITY CHECK: Table Name Extraction")
    print("="*60)
    print(f"\nQuestion: {case['question']}")
    print(f"Expected tables: {case['expected_tables']}")
    
    # Run evaluation
    metric = ev.evaluate_single(case)
    
    print(f"\nGenerated answer:")
    print(f"  {metric.get('generated_answer', '')[:300]}...")
    
    print(f"\nExtracted tables: {metric['generated_tables']}")
    print(f"Expected tables: {metric['expected_tables']}")
    
    print(f"\nMetrics:")
    print(f"  Node Recall: {metric['node_recall']:.1%}")
    print(f"  Answer Relevance: {metric['answer_relevance']:.1%}")
    print(f"  Combined Score: {metric['combined_score']:.2f}")
    print(f"  Passed: {metric['passed']}")
    
    # Check if extraction is working
    extracted_set = set(metric['generated_tables'])
    expected_set = set(metric['expected_tables'])
    
    print(f"\nExtraction Analysis:")
    print(f"  Correctly found: {extracted_set & expected_set}")
    print(f"  Missed: {expected_set - extracted_set}")
    print(f"  False positives: {extracted_set - expected_set}")
    
    if extracted_set & expected_set:
        print(f"\n✓ Extraction is working! Found {len(extracted_set & expected_set)}/{len(expected_set)} expected tables.")
    else:
        print(f"\n✗ Extraction failed - no expected tables found in answer.")

if __name__ == "__main__":
    test_single_case()

