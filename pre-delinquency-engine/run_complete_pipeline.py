#!/usr/bin/env python3
"""
Complete End-to-End Pipeline
1. Generate behavioral dataset
2. Train optimized model with hyperparameter tuning
3. Evaluate and save artifacts
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_generation.behavioral_simulator import generate_and_save_dataset
from src.models.train_optimized import ModelTrainer

def main():
    print("\n" + "="*70)
    print("PRE-DELINQUENCY ENGINE - COMPLETE PIPELINE")
    print("="*70)
    
    # Step 1: Generate dataset
    print("\n" + "="*70)
    print("STEP 1: GENERATE BEHAVIORAL DATASET")
    print("="*70)
    
    dataset = generate_and_save_dataset(
        n_customers=30000,
        output_path='data/processed/behavioral_features.csv',
        seed=42
    )
    
    # Step 2: Train model
    print("\n" + "="*70)
    print("STEP 2: TRAIN OPTIMIZED MODEL")
    print("="*70)
    
    trainer = ModelTrainer(config_path='config/training_config.yaml')
    trainer.run()
    
    print("\n" + "="*70)
    print("✅ PIPELINE COMPLETE!")
    print("="*70)
    print("\nNext steps:")
    print("1. Review metrics in: data/models/evaluation/metrics.json")
    print("2. Update API to use: data/models/production/model.json")
    print("3. Restart API service")
    print("="*70)

if __name__ == '__main__':
    main()
