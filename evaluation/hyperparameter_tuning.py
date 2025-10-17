"""
Hyperparameter Tuning for Car Chatbot

This script performs grid search hyperparameter tuning on the car chatbot by:
1. Testing different combinations of temperature and max_tokens
2. Using the existing evaluation framework from run_evaluation.py
3. Tracking correctness scores for each configuration
4. Identifying the best performing parameter combination
"""

import os
import sys
import time
import yaml
import json
import shutil
from datetime import datetime
from typing import Dict, Any, List
from langsmith import Client

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import evaluation components from run_evaluation.py
from evaluation.run_evaluation import rag_bot, correctness, client

# Define hyperparameter grid
# TEMPERATURE_VALUES = [0.0, 0.1, 0.3, 0.5]
# MAX_TOKENS_VALUES = [800, 1200, 1500, 2000]

TEMPERATURE_VALUES = [0.0, 0.3, 0.8]
MAX_TOKENS_VALUES = [10, 1000]

# Paths
CONFIG_PATH = os.path.join(project_root, "chatbot", "chatbot_config.yaml")
CONFIG_BACKUP_PATH = os.path.join(project_root, "chatbot", "chatbot_config.yaml.backup")


class TuningResults:
    """Store and manage tuning results."""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.best_config: Dict[str, Any] = None
        self.best_score: float = 0.0

    def add_result(self, temperature: float, max_tokens: int,
                   correctness: float, duration: float):
        """Add a result from one configuration test."""
        result = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            "correctness_score": correctness,
            "duration_seconds": duration
        }
        self.results.append(result)

        # Track best configuration
        if correctness > self.best_score:
            self.best_score = correctness
            self.best_config = {
                "temperature": temperature,
                "max_tokens": max_tokens
            }

    def save_to_file(self, filepath: str):
        """Save results to JSON file."""
        output = {
            "tuning_date": datetime.now().isoformat(),
            "parameter_grid": {
                "temperature": TEMPERATURE_VALUES,
                "max_tokens": MAX_TOKENS_VALUES
            },
            "best_configuration": self.best_config,
            "best_score": self.best_score,
            "all_results": self.results
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)

    def print_summary(self):
        """Print summary of tuning results."""
        print("\n" + "="*80)
        print("HYPERPARAMETER TUNING SUMMARY")
        print("="*80)

        if not self.results:
            print("No results available.")
            return

        # Sort by correctness score
        sorted_results = sorted(self.results,
                               key=lambda x: x['correctness_score'],
                               reverse=True)

        print(f"\n🏆 Best Configuration:")
        print(f"   Temperature: {self.best_config['temperature']}")
        print(f"   Max Tokens: {self.best_config['max_tokens']}")
        print(f"   Correctness Score: {self.best_score:.2%}")

        print(f"\n📊 Top 5 Configurations:")
        for i, result in enumerate(sorted_results[:5], 1):
            print(f"   {i}. temp={result['temperature']}, "
                  f"tokens={result['max_tokens']}: "
                  f"{result['correctness_score']:.2%}")

        print(f"\n📈 Performance by Temperature (avg correctness):")
        temp_scores = {}
        for result in self.results:
            temp = result['temperature']
            if temp not in temp_scores:
                temp_scores[temp] = []
            temp_scores[temp].append(result['correctness_score'])

        for temp in sorted(temp_scores.keys()):
            avg_score = sum(temp_scores[temp]) / len(temp_scores[temp])
            print(f"   Temperature {temp}: {avg_score:.2%}")

        print(f"\n📈 Performance by Max Tokens (avg correctness):")
        token_scores = {}
        for result in self.results:
            tokens = result['max_tokens']
            if tokens not in token_scores:
                token_scores[tokens] = []
            token_scores[tokens].append(result['correctness_score'])

        for tokens in sorted(token_scores.keys()):
            avg_score = sum(token_scores[tokens]) / len(token_scores[tokens])
            print(f"   Max Tokens {tokens}: {avg_score:.2%}")

        print("="*80)


def backup_config():
    """Create backup of original config."""
    shutil.copy2(CONFIG_PATH, CONFIG_BACKUP_PATH)
    print(f"✅ Config backed up to: {CONFIG_BACKUP_PATH}")


def restore_config():
    """Restore original config from backup."""
    if os.path.exists(CONFIG_BACKUP_PATH):
        shutil.copy2(CONFIG_BACKUP_PATH, CONFIG_PATH)
        os.remove(CONFIG_BACKUP_PATH)
        print(f"✅ Original config restored")


def update_config(temperature: float, max_tokens: int):
    """Update chatbot_config.yaml with new hyperparameters."""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Update OpenAI parameters
    if 'openai' not in config:
        config['openai'] = {}
    config['openai']['temperature'] = temperature
    config['openai']['max_tokens'] = max_tokens

    # Write updated config
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def evaluate_configuration(dataset_name: str,
                          temperature: float, max_tokens: int,
                          config_num: int, total_configs: int) -> float:
    """
    Evaluate chatbot with specific hyperparameter configuration.

    Args:
        dataset_name: Name of evaluation dataset
        temperature: Temperature value to test
        max_tokens: Max tokens value to test
        config_num: Current configuration number
        total_configs: Total number of configurations

    Returns:
        Correctness score (0.0 to 1.0)
    """
    print(f"\n{'='*80}")
    print(f"[{config_num}/{total_configs}] Testing Configuration:")
    print(f"  Temperature: {temperature}")
    print(f"  Max Tokens: {max_tokens}")
    print(f"{'='*80}")

    # Update configuration
    update_config(temperature, max_tokens)
    print("✅ Config updated")

    # Wait a moment for config to be reloaded
    time.sleep(2)

    # Custom wrapper to add delay between evaluations
    evaluation_count = 0
    def target_with_delay(inputs: dict) -> dict:
        nonlocal evaluation_count

        # Add 10 second delay between examples (but not before the first one)
        if evaluation_count > 0:
            print(f"⏳ Waiting 10 seconds before next evaluation...")
            time.sleep(10)

        evaluation_count += 1
        return rag_bot(inputs["question"])

    # Run evaluation
    start_time = time.time()
    experiment_results = client.evaluate(
        target_with_delay,
        data=dataset_name,
        evaluators=[correctness],
        experiment_prefix=f"hyperparameter-tuning-temp{temperature}-tokens{max_tokens}",
        metadata={
            "temperature": temperature,
            "max_tokens": max_tokens,
            "tuning_run": True
        },
    )
    duration = time.time() - start_time

    # Extract correctness score
    df = experiment_results.to_pandas()
    correctness_scores = []

    for idx, row in df.iterrows():
        if 'feedback.correctness' in row and row['feedback.correctness'] is not None:
            correctness_scores.append(1.0 if row['feedback.correctness'] else 0.0)
        elif 'evaluators.correctness' in row and row['evaluators.correctness'] is not None:
            correctness_scores.append(1.0 if row['evaluators.correctness'] else 0.0)

    if correctness_scores:
        avg_correctness = sum(correctness_scores) / len(correctness_scores)
        correct_count = sum(correctness_scores)
        total_count = len(correctness_scores)

        print(f"\n📊 Results:")
        print(f"   Correctness: {avg_correctness:.2%} ({int(correct_count)}/{total_count})")
        print(f"   Duration: {duration:.1f}s")

        return avg_correctness
    else:
        print("⚠️ No correctness scores found")
        return 0.0


def run_hyperparameter_tuning():
    """Main function to run hyperparameter tuning."""
    print("\n" + "="*80)
    print("🔍 HYPERPARAMETER TUNING FOR CAR CHATBOT")
    print("="*80)

    # Display parameter grid
    print(f"\nParameter Grid:")
    print(f"  Temperature values: {TEMPERATURE_VALUES}")
    print(f"  Max tokens values: {MAX_TOKENS_VALUES}")
    total_configs = len(TEMPERATURE_VALUES) * len(MAX_TOKENS_VALUES)
    print(f"  Total configurations to test: {total_configs}")
    print(f"\nEach configuration will be evaluated on the full dataset.")
    print(f"Estimated time: ~{total_configs * 5} minutes\n")

    # Initialize results tracker
    results = TuningResults()
    dataset_name = "Car Selector Chatbot Evaluation Dataset"

    # Backup original config
    backup_config()

    try:
        # Grid search
        config_num = 0
        for temperature in TEMPERATURE_VALUES:
            for max_tokens in MAX_TOKENS_VALUES:
                config_num += 1

                # Evaluate configuration
                start_time = time.time()
                correctness_score = evaluate_configuration(
                    dataset_name, temperature, max_tokens,
                    config_num, total_configs
                )
                duration = time.time() - start_time

                # Store result
                results.add_result(temperature, max_tokens,
                                 correctness_score, duration)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(
            os.path.dirname(__file__),
            f"tuning_results_{timestamp}.json"
        )
        results.save_to_file(results_file)
        print(f"\n✅ Results saved to: {results_file}")

        # Print summary
        results.print_summary()

    finally:
        # Always restore original config
        restore_config()


if __name__ == "__main__":
    run_hyperparameter_tuning()
