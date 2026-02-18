"""
Complete Pipeline V2 - Advanced Simulator + Advanced Training
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.data_generation.behavioral_simulator_v2 import (
    AdvancedBehavioralSimulator, SimulationConfig
)
from src.models.train_advanced import AdvancedModelTrainer


def main():
    """Run complete V2 pipeline"""
    
    print("\n" + "="*70)
    print("PRE-DELINQUENCY ENGINE - COMPLETE PIPELINE V2")
    print("="*70)
    print("\nEnhancements:")
    print("  ✓ Temporal realism (variable observation windows)")
    print("  ✓ Autocorrelation in behavioral signals")
    print("  ✓ Financial shocks (job loss, bonuses, emergencies)")
    print("  ✓ Correlated features (realistic dependencies)")
    print("  ✓ Rolling statistics (mean, std, trends)")
    print("  ✓ Non-linear label generation")
    print("  ✓ Ensemble models (XGBoost + LightGBM + CatBoost)")
    print("  ✓ SMOTE resampling")
    print("  ✓ 5-fold cross-validation")
    print("\nEstimated time: 20-30 minutes")
    print("="*70)
    
    start_time = time.time()
    
    # Step 1: Generate advanced dataset
    print("\n\n" + "="*70)
    print("STEP 1/2: ADVANCED DATA GENERATION")
    print("="*70)
    
    try:
        config = SimulationConfig(
            n_customers=30000,
            min_weeks=8,
            max_weeks=16,
            target_positive_rate=0.10,
            use_autocorrelation=True,
            autocorr_strength=0.7,
            enable_shocks=True,
            shock_probability=0.05,
            use_float32=True
        )
        
        simulator = AdvancedBehavioralSimulator(config)
        df = simulator.generate_dataset()
        
        # Save dataset
        output_path = "data/processed/behavioral_features_v2.csv"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"\n✅ Dataset saved to: {output_path}")
        
        # Save metadata
        import json
        metadata_path = output_path.replace('.csv', '_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(simulator.metadata, f, indent=2)
        print(f"✅ Metadata saved to: {metadata_path}")
        
    except Exception as e:
        print(f"\n❌ Data generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Step 2: Train advanced models
    print("\n\n" + "="*70)
    print("STEP 2/2: ADVANCED MODEL TRAINING")
    print("="*70)
    
    try:
        # Update config to use V2 dataset
        import yaml
        with open('config/training_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        config['dataset']['output_path'] = 'data/processed/behavioral_features_v2.csv'
        
        with open('config/training_config.yaml', 'w') as f:
            yaml.dump(config, f)
        
        trainer = AdvancedModelTrainer()
        trainer.run()
        print("\n✅ Model training complete!")
        
    except Exception as e:
        print(f"\n❌ Model training failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Summary
    elapsed = time.time() - start_time
    print("\n\n" + "="*70)
    print("🎉 COMPLETE PIPELINE V2 FINISHED!")
    print("="*70)
    print(f"\nTotal time: {elapsed/60:.1f} minutes")
    print("\nGenerated artifacts:")
    print("  📊 Dataset: data/processed/behavioral_features_v2.csv")
    print("  📋 Metadata: data/processed/behavioral_features_v2_metadata.json")
    print("  🤖 Models: XGBoost, LightGBM, CatBoost ensemble")
    print("  📈 Evaluation: Cross-validation results")
    
    print("\n" + "="*70)
    print("KEY IMPROVEMENTS:")
    print("="*70)
    print("  ✓ Temporal realism with variable observation windows")
    print("  ✓ Autocorrelated signals (AR(1) process)")
    print("  ✓ Financial shocks for realistic stress events")
    print("  ✓ Feature correlations (salary → payments → spending)")
    print("  ✓ Rolling statistics (mean, std, max, min, trends)")
    print("  ✓ Interaction features for non-linear effects")
    print("  ✓ Ensemble models for robust predictions")
    print("  ✓ SMOTE for class imbalance")
    print("  ✓ F2 score optimization (recall-weighted)")
    print("="*70 + "\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
