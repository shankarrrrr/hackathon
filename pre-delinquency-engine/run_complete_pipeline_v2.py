#!/usr/bin/env python3
"""
Complete V2 Pipeline: Generate data + Train model
"""
import subprocess
import sys

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode != 0:
        print(f"\n❌ Failed: {description}")
        sys.exit(1)
    
    print(f"\n✅ Completed: {description}")

def main():
    print("🎯 Complete V2 Pipeline")
    print("=" * 60)
    
    # Step 1: Generate V2 data (skip if already exists)
    import os
    if not os.path.exists('data/processed/behavioral_features_v2.csv'):
        run_command(
            "python src/data_generation/behavioral_simulator_v2.py",
            "Step 1: Generate V2 behavioral data"
        )
    else:
        print("\n✓ V2 data already exists, skipping generation")
    
    # Step 2: Train advanced model
    run_command(
        "python src/models/train_advanced.py",
        "Step 2: Train advanced ensemble model"
    )
    
    print("\n" + "=" * 60)
    print("✅ Pipeline Complete!")
    print("=" * 60)
    print("\nGenerated files:")
    print("  📊 data/processed/behavioral_features_v2.csv")
    print("  🤖 data/models/production/model.json")
    print("  📈 data/models/evaluation/metrics.json")
    print("\nNext steps:")
    print("  1. git add -f data/models/production/* data/models/evaluation/*")
    print("  2. git commit -m 'Train V2 model'")
    print("  3. git push")
    print("  4. On EC2: git pull && python3 generate_simple_scores.py")

if __name__ == '__main__':
    main()
