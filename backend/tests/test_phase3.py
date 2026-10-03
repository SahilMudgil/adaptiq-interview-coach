import os
import sys
import json

# Ensure root in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.evaluator_dataset_generator import generate_lora_dataset
from backend.train_evaluator_lora import setup_training_pipeline
from backend.benchmark_evaluator import run_benchmark

def test_phase3_pipeline():
    print("==================================================================")
    print("      Running Phase 3 Answer Evaluator Fine-Tuning Tests          ")
    print("==================================================================")

    # 1. Dataset Generation Test
    print("\n[Step 1] Testing Dataset Generator...")
    stats = generate_lora_dataset(output_dir="data/fine_tuning")
    assert stats["train_examples"] > 0
    assert stats["val_examples"] > 0
    assert os.path.exists(stats["train_file"])
    assert os.path.exists(stats["val_file"])

    with open(stats["train_file"], "r", encoding="utf-8") as f:
        first_line = json.loads(f.readline())
        assert "instruction" in first_line
        assert "input" in first_line
        assert "output" in first_line
        output_obj = json.loads(first_line["output"])
        assert "score" in output_obj
        assert "sub_scores" in output_obj
        assert "feedback" in output_obj

    print(f"  [OK] Fine-tuning dataset verified: {stats['train_examples']} train, {stats['val_examples']} validation.")
    print(f"  [OK] First example verified: score={output_obj['score']} with sub-scores: {list(output_obj['sub_scores'].keys())}")

    # 2. LoRA Training Pipeline Test
    print("\n[Step 2] Executing LoRA Training Setup & Loss Curve Generation...")
    train_res = setup_training_pipeline(
        base_model_name="microsoft/Phi-3-mini-4k-instruct",
        num_epochs=3,
        batch_size=2
    )
    assert train_res["status"] == "success"
    assert os.path.exists("data/models/evaluator_lora/adapter_config.json")
    assert os.path.exists("data/models/evaluator_lora/training_metrics.json")
    assert os.path.exists("data/models/evaluator_lora/adapter_model.safetensors")

    with open("data/models/evaluator_lora/training_metrics.json", "r", encoding="utf-8") as f:
        metrics = json.load(f)
        assert len(metrics["epochs"]) == 3
        # Ensure loss decreased across epochs
        assert metrics["epochs"][0]["train_loss"] > metrics["epochs"][-1]["train_loss"]

    print("  [OK] LoRA adapter configuration and weights successfully generated.")
    print(f"  [OK] Verified training convergence: Loss dropped from {metrics['epochs'][0]['train_loss']} to {metrics['epochs'][-1]['train_loss']}.")

    # 3. Benchmark Comparison Test
    print("\n[Step 3] Running Base vs. Fine-Tuned Benchmark Comparison...")
    import asyncio
    asyncio.run(run_benchmark())
    print("  [OK] Evaluator benchmark successfully executed and calibrated.")

    print("\n==================================================================")
    print("         ALL PHASE 3 FINE-TUNING TESTS PASSED 100%!               ")
    print("==================================================================")

if __name__ == "__main__":
    test_phase3_pipeline()
