"""
Run Advanced Training Pipeline
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.models.train_advanced import AdvancedModelTrainer


def main():
    print("\n" + "="*70)
    print("PRE-DELINQUENCY ENGINE - ADVANCED TRAINING")
    print("="*70)
    print("\nThis will:")
    print("  1. Apply advanced feature engineering")
    print("  2. Train XGBoost, LightGBM, and CatBoost")
    print("  3. Create weighted ensemble")
    print("  4. Perform 5-fold cross-validation")
    print("  5. Optimize threshold using F2 score")
    print("\nEstimated time: 15-25 minutes")
    print("="*70)
    
    try:
        trainer = AdvancedModelTrainer()
        trainer.run()
        
        print("\n✅ Advanced training complete!")
        print("\nNext steps:")
        print("  1. Review model performance")
        print("  2. Deploy ensemble to production")
        print("  3. Monitor performance metrics")
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
