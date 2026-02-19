#!/bin/bash
# Generate risk scores for V2 customers

cd ~/hackathon-1/pre-delinquency-engine

echo "🚀 Generating risk scores for V2 customers..."
python3 generate_risk_scores_v2.py

echo ""
echo "✅ Done! Check dashboard at http://15.206.72.35:8501"
