"""
LLM-as-a-judge evaluation framework.

Minimal __init__ to avoid pulling in client deps when only sub-pieces are imported.
Use explicit imports:
    from evaluation.judge.orchestrator import evaluate_batch, FULL_MODULES
    from evaluation.judge.io import save_results, load_reference_csv
    from evaluation.judge.stats import compare_experiments, compute_summary
    from evaluation.judge.modules.pairwise import PairwiseJudge
"""
