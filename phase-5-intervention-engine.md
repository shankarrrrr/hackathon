# PHASE 5: INTERVENTION ENGINE (Days 16-18)

## Overview

This phase implements the intervention decision engine that converts risk scores into actionable interventions with empathetic messaging.

## Key Components

1. **InterventionDecisionEngine** - Business logic for intervention decisions
2. **InterventionTracker** - Track outcomes and measure effectiveness
3. **Message Generator** - Create empathetic, personalized messages
4. **Integration with API** - Trigger interventions via API endpoints

## Complete Implementation

Create src/intervention/decision_engine.py:

```python
"""
Intervention decision engine
Converts risk scores into actionable interventions with empathetic messaging
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List
from sqlalchemy import create_engine
import pandas as pd
import os

class InterventionDecisionEngine:
    """
    Business logic for intervention decisions
    Determines when, how, and what type of intervention to trigger
    """
    
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv('DATABASE_URL')
        self.engine = create_engine(self.db_url)
        
        # Risk thresholds
        self.risk_thresholds = {
            'critical': 0.80,
            'high': 0.60,
            'medium': 0.40,
            'low': 0.20
        }
        
        # Intervention cooloff period (days)
        self.cooloff_period_days = 7
    
    def decide_intervention(
        self,
        customer_id: str,
        risk_score: float,
        risk_level: str,
        explanation: Dict
    ) -> Optional[Dict]:
        """
        Determine if intervention is needed and what type
        
        Returns:
            Intervention details or None if no intervention needed
        """
        
        # Rule 1: Check cooloff period
        if self._in_cooloff_period(customer_id):
            print(f"  ℹ️ Customer {customer_id} in cooloff period")
            return None
        
        # Rule 2: Check if payment already missed
        if self._has_recent_default(customer_id):
            print(f"  ℹ️ Customer {customer_id} already in default")
            return None
        
        # Rule 3: Check risk trend
        risk_trend = self._get_risk_trend(customer_id)
        
        if risk_trend not in ['increasing', 'stable_high']:
            print(f"  ℹ️ Risk trend is {risk_trend}, no intervention")
            return None
        
        # Rule 4: Determine intervention type
        intervention = self._select_intervention_type(
            risk_score, 
            risk_level, 
            explanation,
            risk_trend
        )
        
        if intervention is None:
            return None
        
        # Generate personalized message
        intervention['message'] = self._generate_message(
            customer_id,
            intervention['type'],
            explanation
        )
        
        # Add metadata
        intervention['customer_id'] = customer_id
        intervention['risk_score'] = risk_score
        intervention['risk_level'] = risk_level
        intervention['decided_at'] = datetime.now().isoformat()
        
        return intervention
    
    def _select_intervention_type(
        self,
        risk_score: float,
        risk_level: str,
        explanation: Dict,
        risk_trend: str
    ) -> Optional[Dict]:
        """Select appropriate intervention type"""
        
        if risk_score >= self.risk_thresholds['critical']:
            return {
                'type': 'payment_assistance',
                'urgency': 'critical',
                'actions': [
                    'Offer payment holiday (1-3 months)',
                    'Suggest EMI restructuring',
                    'Connect with financial counselor',
                    'Provide emergency loan option'
                ],
                'timeline': 'Contact within 24 hours',
                'channels': ['phone', 'email']
            }
        
        elif risk_score >= self.risk_thresholds['high']:
            return {
                'type': 'flexible_payment',
                'urgency': 'high',
                'actions': [
                    'Send payment reminder with flexibility options',
                    'Offer budget planning tools',
                    'Highlight payment extension options',
                    'Provide financial wellness resources'
                ],
                'timeline': 'Contact within 3-5 days',
                'channels': ['email', 'sms', 'app_notification']
            }
        
        elif risk_score >= self.risk_thresholds['medium'] and risk_trend == 'increasing':
            return {
                'type': 'payment_reminder',
                'urgency': 'medium',
                'actions': [
                    'Send gentle payment reminder',
                    'Highlight upcoming due dates',
                    'Offer automatic payment setup',
                    'Share budgeting tips'
                ],
                'timeline': 'Contact within 7 days',
                'channels': ['email', 'app_notification']
            }
        
        else:
            return None
    
    def _generate_message(
        self,
        customer_id: str,
        intervention_type: str,
        explanation: Dict
    ) -> Dict[str, str]:
        """
        Generate empathetic, personalized messages
        
        Returns:
            Dictionary with messages for different channels
        """
        
        customer_name = self._get_customer_name(customer_id)
        top_drivers = explanation.get('top_drivers', [])
        
        if intervention_type == 'payment_assistance':
            return {
                'email_subject': 'We\'re Here to Help - Payment Support Options',
                'email_body': f"""
Hi {customer_name},

We've noticed some changes in your account activity and want to reach out with support.

We understand that financial challenges can happen to anyone, and we're here to help you navigate through this time.

**Support Options Available:**
- Temporary payment holiday (no impact on credit)
- Flexible EMI restructuring
- 1-on-1 financial counseling session
- Emergency assistance program

**No Judgment. Just Support.**

Your financial wellbeing is important to us. Please reply to this email or call us at 1-800-XXX-XXXX to discuss options that work for you.

We're here to help,
Your Bank Team

P.S. All conversations are confidential and handled with care.
                """,
                'sms_body': f"""
Hi {customer_name}, we noticed changes in your account and want to help. We have flexible payment options available with no judgment. Call us at 1-800-XXX-XXXX or reply HELP. - Your Bank
                """,
                'app_notification': f"""
💙 We're here to support you. Flexible payment options available - tap to learn more.
                """
            }
        
        elif intervention_type == 'flexible_payment':
            return {
                'email_subject': 'Payment Flexibility Options for Your Upcoming Bill',
                'email_body': f"""
Hi {customer_name},

Your payment of $XXX is coming up on [DUE DATE]. We wanted to let you know about flexible options available to you:

**Payment Options:**
✓ Extend due date by 15 days (no fee)
✓ Split payment into 2 installments
✓ Set up automatic payments for convenience
✓ Access our budget planning tool

If you need more time or have questions, we're just an email or call away.

**Need help?** Reply to this email or call 1-800-XXX-XXXX

Thank you,
Your Bank Team
                """,
                'sms_body': f"""
Hi {customer_name}, your payment is due soon. We have flexible options available including payment extensions. Reply OPTIONS or call 1-800-XXX-XXXX - Your Bank
                """,
                'app_notification': f"""
📅 Payment due soon. Flexible options available - tap to view.
                """
            }
        
        elif intervention_type == 'payment_reminder':
            return {
                'email_subject': 'Friendly Reminder: Upcoming Payment',
                'email_body': f"""
Hi {customer_name},

Just a friendly reminder that your payment of $XXX is due on [DUE DATE].

**Quick Actions:**
- Pay now (one-click payment)
- Set up auto-pay
- View payment history
- Adjust payment date

If you need any assistance or have questions, we're here to help.

Best regards,
Your Bank Team
                """,
                'sms_body': f"""
Reminder: Payment of $XXX due on [DATE]. Pay now at [LINK] or reply HELP for options. - Your Bank
                """,
                'app_notification': f"""
💰 Payment reminder: $XXX due on [DATE]. Tap to pay or set up auto-pay.
                """
            }
        
        else:
            return {
                'email_subject': 'Financial Wellness Resources',
                'email_body': f"""
Hi {customer_name},

We wanted to share some helpful financial wellness resources with you.

**Free Tools & Resources:**
- Budget planning calculator
- Savings goal tracker
- Financial health score
- Educational webinars

Visit our Financial Wellness Hub: [LINK]

Best regards,
Your Bank Team
                """,
                'app_notification': f"""
💡 New financial wellness tools available - check them out!
                """
            }
    
    def log_intervention(
        self,
        intervention: Dict,
        delivery_status: str = 'pending'
    ) -> str:
        """
        Log intervention to database
        
        Returns:
            intervention_id
        """
        try:
            data = {
                'customer_id': intervention['customer_id'],
                'intervention_date': datetime.now(),
                'intervention_type': intervention['type'],
                'risk_score': intervention['risk_score'],
                'message_sent': intervention['message'].get('email_body', ''),
                'delivery_status': delivery_status,
                'created_at': datetime.now()
            }
            
            df = pd.DataFrame([data])
            df.to_sql('interventions', self.engine, if_exists='append', index=False)
            
            # Get the intervention_id
            query = f"""
            SELECT intervention_id 
            FROM interventions 
            WHERE customer_id = '{intervention['customer_id']}'
            ORDER BY intervention_date DESC 
            LIMIT 1
            """
            result = pd.read_sql(query, self.engine)
            
            intervention_id = result.iloc[0]['intervention_id']
            
            print(f"✅ Intervention logged: {intervention_id}")
            
            return intervention_id
        
        except Exception as e:
            print(f"❌ Failed to log intervention: {str(e)}")
            return None
    
    # Helper methods
    
    def _in_cooloff_period(self, customer_id: str) -> bool:
        """Check if customer was recently contacted"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.cooloff_period_days)
            
            query = f"""
            SELECT COUNT(*) as count
            FROM interventions
            WHERE customer_id = '{customer_id}'
              AND intervention_date >= '{cutoff_date}'
            """
            
            df = pd.read_sql(query, self.engine)
            
            return df.iloc[0]['count'] > 0
        
        except:
            return False
    
    def _has_recent_default(self, customer_id: str) -> bool:
        """Check if customer has recently missed payments"""
        try:
            recent_date = datetime.now() - timedelta(days=7)
            
            query = f"""
            SELECT COUNT(*) as count
            FROM payments
            WHERE customer_id = '{customer_id}'
              AND status = 'missed'
              AND due_date >= '{recent_date.date()}'
            """
            
            df = pd.read_sql(query, self.engine)
            
            return df.iloc[0]['count'] > 0
        
        except:
            return False
    
    def _get_risk_trend(self, customer_id: str) -> str:
        """
        Determine risk trend: increasing, decreasing, stable_high, stable_low
        """
        try:
            query = f"""
            SELECT risk_score, score_date
            FROM risk_scores
            WHERE customer_id = '{customer_id}'
            ORDER BY score_date DESC
            LIMIT 5
            """
            
            df = pd.read_sql(query, self.engine)
            
            if len(df) < 2:
                return 'unknown'
            
            # Recent vs older scores
            recent_avg = df.head(2)['risk_score'].mean()
            older_avg = df.tail(2)['risk_score'].mean()
            
            change = recent_avg - older_avg
            
            if recent_avg >= 0.6:
                if change > 0.05:
                    return 'increasing'
                else:
                    return 'stable_high'
            elif change > 0.10:
                return 'increasing'
            elif change < -0.10:
                return 'decreasing'
            else:
                return 'stable_low'
        
        except:
            return 'unknown'
    
    def _get_customer_name(self, customer_id: str) -> str:
        """Get customer name (or default)"""
        return "Valued Customer"


class InterventionTracker:
    """
    Track intervention outcomes and measure effectiveness
    """
    
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv('DATABASE_URL')
        self.engine = create_engine(self.db_url)
    
    def record_customer_response(
        self,
        intervention_id: str,
        response_type: str,
        notes: Optional[str] = None
    ):
        """
        Record customer response to intervention
        
        Args:
            intervention_id: Intervention identifier
            response_type: accepted_offer, engaged, no_response, opted_out
            notes: Additional notes
        """
        try:
            update_query = f"""
            UPDATE interventions
            SET customer_response = '{response_type}',
                response_date = '{datetime.now()}',
                updated_at = '{datetime.now()}'
            WHERE intervention_id = '{intervention_id}'
            """
            
            with self.engine.connect() as conn:
                conn.execute(update_query)
            
            print(f"✅ Response recorded for intervention {intervention_id}")
        
        except Exception as e:
            print(f"❌ Failed to record response: {str(e)}")
    
    def measure_intervention_success(
        self,
        lookback_days: int = 30
    ) -> Dict:
        """
        Calculate intervention success metrics
        
        Success = customer did NOT default after intervention
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=lookback_days)
            
            query = f"""
            WITH interventions_with_outcomes AS (
                SELECT 
                    i.intervention_id,
                    i.customer_id,
                    i.intervention_date,
                    i.intervention_type,
                    i.customer_response,
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 
                            FROM payments p 
                            WHERE p.customer_id = i.customer_id
                              AND p.status = 'missed'
                              AND p.due_date BETWEEN i.intervention_date::date 
                                  AND (i.intervention_date::date + INTERVAL '30 days')
                        ) THEN 1 
                        ELSE 0 
                    END as defaulted_after
                FROM interventions i
                WHERE i.intervention_date >= '{cutoff_date}'
            )
            SELECT 
                COUNT(*) as total_interventions,
                SUM(CASE WHEN defaulted_after = 0 THEN 1 ELSE 0 END) as prevented_defaults,
                SUM(CASE WHEN defaulted_after = 1 THEN 1 ELSE 0 END) as defaults_occurred,
                AVG(CASE WHEN defaulted_after = 0 THEN 1.0 ELSE 0.0 END) as success_rate,
                intervention_type,
                COUNT(DISTINCT customer_id) as unique_customers
            FROM interventions_with_outcomes
            GROUP BY intervention_type
            """
            
            df = pd.read_sql(query, self.engine)
            
            # Aggregate metrics
            total_interventions = df['total_interventions'].sum()
            prevented_defaults = df['prevented_defaults'].sum()
            
            overall_success_rate = prevented_defaults / total_interventions if total_interventions > 0 else 0
            
            results = {
                'total_interventions': int(total_interventions),
                'prevented_defaults': int(prevented_defaults),
                'defaults_occurred': int(df['defaults_occurred'].sum()),
                'success_rate': float(overall_success_rate),
                'by_intervention_type': df.to_dict('records'),
                'period_days': lookback_days,
                'measured_at': datetime.now().isoformat()
            }
            
            print(f"\n📊 Intervention Success Metrics ({lookback_days} days):")
            print(f"  Total: {total_interventions}")
            print(f"  Prevented: {prevented_defaults}")
            print(f"  Success Rate: {overall_success_rate:.1%}")
            
            return results
        
        except Exception as e:
            print(f"❌ Failed to measure success: {str(e)}")
            return {}

if __name__ == "__main__":
    # Example usage
    engine = InterventionDecisionEngine()
    tracker = InterventionTracker()
    
    # Example: Decide intervention for high-risk customer
    intervention = engine.decide_intervention(
        customer_id="test_customer_123",
        risk_score=0.75,
        risk_level="HIGH",
        explanation={
            'top_drivers': [
                {'feature': 'Salary Delay', 'impact': 0.25},
                {'feature': 'Savings Drawdown', 'impact': 0.20}
            ]
        }
    )
    
    if intervention:
        print("\n" + "="*60)
        print("INTERVENTION DECISION")
        print("="*60)
        print(f"\nType: {intervention['type']}")
        print(f"Urgency: {intervention['urgency']}")
        print(f"Timeline: {intervention['timeline']}")
        print(f"\nMessage:")
        print(intervention['message']['email_body'])
        
        # Log it
        intervention_id = engine.log_intervention(intervention)
    
    # Measure success
    metrics = tracker.measure_intervention_success(lookback_days=30)
```

## Integration with API

Add to src/serving/api.py:

```python
from src.intervention.decision_engine import InterventionDecisionEngine, InterventionTracker

# Initialize on startup
intervention_engine = None
intervention_tracker = None

@app.on_event("startup")
async def startup_event():
    global intervention_engine, intervention_tracker
    
    # ... existing code ...
    
    # Initialize intervention engine
    print("💌 Initializing intervention engine...")
    intervention_engine = InterventionDecisionEngine(db_url=db_url)
    intervention_tracker = InterventionTracker(db_url=db_url)
    print("  ✅ Intervention engine initialized")

@app.post("/trigger_intervention/{customer_id}")
async def trigger_intervention(customer_id: str):
    """
    Evaluate and trigger intervention for a customer
    """
    try:
        # Get latest risk score
        query = f"""
        SELECT risk_score, risk_level, score_date
        FROM risk_scores
        WHERE customer_id = '{customer_id}'
        ORDER BY score_date DESC
        LIMIT 1
        """
        
        df = pd.read_sql(query, db_engine)
        
        if len(df) == 0:
            raise HTTPException(status_code=404, detail="No risk score found")
        
        risk_score = df.iloc[0]['risk_score']
        risk_level = df.iloc[0]['risk_level']
        
        # Decide intervention
        intervention = intervention_engine.decide_intervention(
            customer_id=customer_id,
            risk_score=risk_score,
            risk_level=risk_level,
            explanation={'top_drivers': []}
        )
        
        if intervention is None:
            return {
                "status": "no_intervention_needed",
                "customer_id": customer_id,
                "risk_score": float(risk_score)
            }
        
        # Log intervention
        intervention_id = intervention_engine.log_intervention(intervention)
        
        return {
            "status": "intervention_triggered",
            "intervention_id": intervention_id,
            "intervention": intervention
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/intervention_metrics")
async def get_intervention_metrics(days: int = 30):
    """Get intervention success metrics"""
    try:
        metrics = intervention_tracker.measure_intervention_success(lookback_days=days)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Intervention Types

### 1. Payment Assistance (Critical Risk)
- Payment holiday options
- EMI restructuring
- Financial counseling
- Emergency assistance

### 2. Flexible Payment (High Risk)
- Payment extensions
- Budget planning tools
- Payment flexibility options

### 3. Payment Reminder (Medium Risk)
- Gentle reminders
- Auto-pay setup
- Budgeting tips

### 4. Financial Wellness (Low Risk)
- Educational resources
- Financial tools
- Wellness programs

## Testing

```bash
# Test intervention decision
python src/intervention/decision_engine.py

# Test via API
curl -X POST "http://localhost:8000/trigger_intervention/customer_id_here"

# Get metrics
curl "http://localhost:8000/intervention_metrics?days=30"
```

## Next Steps

After intervention engine:
1. Test intervention logic
2. Verify message generation
3. Check database logging
4. Proceed to Phase 6 (Dashboard)
