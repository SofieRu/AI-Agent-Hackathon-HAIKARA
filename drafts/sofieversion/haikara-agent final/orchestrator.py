"""
Haikara Orchestrator: Main coordination engine
Coordinates all agents and executes complete Beckn journey
"""
from typing import List, Dict
from datetime import datetime
import time

from compute_agent import ComputeAgent
from grid_agent import GridAgent
from decision_agent import DecisionAgent
from audit_agent import AuditAgent
from beckn_client import BecknAPIClient
from models import ScheduleDecision


class HaikaraOrchestrator:
    """
    Main orchestration system that coordinates:
    - Compute Agent (workload data)
    - Grid Agent (energy signals)
    - Decision Agent (optimization)
    - Audit Agent (logging)
    - Beckn API Client (protocol execution)
    """
    
    def __init__(self, config: Dict):
        print("\n" + "="*60)
        print("🌟 Initializing Haikara Multi-Agent System")
        print("="*60)
        
        # Initialize all agents
        self.compute_agent = ComputeAgent(
            max_capacity_kw=config.get('max_capacity_kw', 1000)
        )
        self.grid_agent = GridAgent(
            carbon_api_key=config.get('carbon_api_key'),
            energy_api_key=config.get('energy_api_key')
        )
        self.decision_agent = DecisionAgent(
            carbon_weight=config.get('carbon_weight', 0.6),
            cost_weight=config.get('cost_weight', 0.4),
            carbon_cap_kg=config.get('carbon_cap_kg')
        )
        self.audit_agent = AuditAgent()
        
        # Initialize Beckn client
        self.beckn_client = BecknAPIClient(
            base_url=config.get('bap_sandbox_url', 'http://localhost:3000'),
            timeout=config.get('bap_timeout', 30)
        )
        
        self.config = config
        
        print("✓ All agents initialized successfully\n")
    
    def run_optimization_cycle(self):
        """
        Main execution flow:
        1. Gather data from Compute and Grid agents
        2. Run optimization
        3. Execute Beckn journey
        4. Audit and report
        """
        print("\n" + "="*60)
        print("🚀 Starting Optimization Cycle")
        print("="*60 + "\n")
        
        # STEP 1: Data Gathering
        print("📊 STEP 1: Data Gathering")
        print("-" * 60)
        
        self.audit_agent.log_event("cycle_started", {
            "timestamp": datetime.now().isoformat()
        })
        
        # Get flexible workloads
        workloads = self.compute_agent.get_flexible_workloads()
        if not workloads:
            print("⚠️  No flexible workloads available. Exiting.")
            return
        
        self.audit_agent.log_event("workloads_gathered", {
            "count": len(workloads),
            "workload_ids": [w.job_id for w in workloads]
        })
        
        # Get current energy signals
        current_signal = self.grid_agent.get_current_signals()
        
        # Get forecasted signals
        forecast_horizon = self.config.get('forecast_horizon_hours', 24)
        forecast_signals = self.grid_agent.get_forecast_signals(forecast_horizon)
        
        self.audit_agent.log_event("energy_signals_gathered", {
            "current_price": current_signal.price_per_kwh,
            "current_carbon": current_signal.carbon_intensity_g_per_kwh,
            "forecast_hours": len(forecast_signals)
        })
        
        # STEP 2: Optimization
        print("\n🧠 STEP 2: Optimization")
        print("-" * 60)
        
        schedule_decisions = self.decision_agent.optimize_schedule(
            workloads, forecast_signals
        )
        
        if not schedule_decisions:
            print("⚠️  Optimization failed. No valid schedule found.")
            return
        
        # Calculate savings
        savings = self.decision_agent.calculate_savings(
            schedule_decisions, workloads, forecast_signals
        )
        
        print(f"\n💰 Optimization Results:")
        print(f"  Cost Savings: £{savings['cost_savings']:.2f} ({savings['cost_savings_percent']:.1f}%)")
        print(f"  Carbon Savings: {savings['carbon_savings_kg']:.2f} kg CO2 ({savings['carbon_savings_percent']:.1f}%)")
        print(f"  P415 Revenue: £{savings['p415_revenue']:.2f}")
        print(f"  Total Benefit: £{savings['total_benefit']:.2f}")
        
        self.audit_agent.log_event("schedule_optimized", {
            "decisions_count": len(schedule_decisions),
            "savings": savings
        })
        
        # STEP 3: Beckn Journey Execution
        print("\n🔄 STEP 3: Beckn Protocol Journey")
        print("-" * 60)
        
        order_id = self.execute_beckn_journey(schedule_decisions)
        
        # STEP 4: Audit & Settlement
        print("\n📝 STEP 4: Audit & Settlement")
        print("-" * 60)
        
        settlement_report = self.audit_agent.generate_settlement_report()
        
        # Export audit trail
        self.audit_agent.export_audit_trail("audit_trail.json")
        
        # Verify integrity
        self.audit_agent.verify_log_integrity()
        
        print("\n" + "="*60)
        print("✅ Optimization Cycle Complete")
        print("="*60 + "\n")
        
        return {
            "schedule": schedule_decisions,
            "savings": savings,
            "settlement": settlement_report,
            "order_id": order_id
        }
    
    def execute_beckn_journey(self, schedule_decisions: List[ScheduleDecision]) -> str:
        """
        Execute complete Beckn protocol journey:
        DISCOVER → ORDER → FULFILLMENT → POST-FULFILLMENT
        """
        
        # DISCOVER PHASE
        print("\n🔍 DISCOVER Phase")
        search_response = self.beckn_client.search(schedule_decisions)
        
        self.audit_agent.log_event("beckn_search", {
            "transaction_id": self.beckn_client.transaction_id,
            "schedule_count": len(schedule_decisions)
        }, beckn_transaction_id=self.beckn_client.transaction_id)
        
        time.sleep(1)  # Simulate processing time
        
        # ORDER PHASE - SELECT
        print("\n📦 ORDER Phase - Select")
        
        # Extract first available item from catalog
        selected_item = self._extract_best_item(search_response)
        select_response = self.beckn_client.select(selected_item)
        
        self.audit_agent.log_event("beckn_select", {
            "selected_item": selected_item
        }, beckn_transaction_id=self.beckn_client.transaction_id)
        
        time.sleep(1)
        
        # ORDER PHASE - INIT
        print("\n📦 ORDER Phase - Init")
        
        order_details = self._build_order_details(select_response)
        init_response = self.beckn_client.init(order_details)
        
        self.audit_agent.log_event("beckn_init", {
            "order_details": order_details
        }, beckn_transaction_id=self.beckn_client.transaction_id)
        
        time.sleep(1)
        
        # ORDER PHASE - CONFIRM
        print("\n📦 ORDER Phase - Confirm")
        
        confirm_response = self.beckn_client.confirm(order_details)
        order_id = confirm_response.get("message", {}).get("order", {}).get("id", "ORDER-" + self.beckn_client.transaction_id[:8])
        
        self.audit_agent.log_event("beckn_confirm", {
            "order_id": order_id
        }, beckn_transaction_id=self.beckn_client.transaction_id)
        
        print(f"✓ Order confirmed: {order_id}")
        
        # FULFILLMENT PHASE
        print("\n⚙️  FULFILLMENT Phase")
        
        # Check status
        status_response = self.beckn_client.status(order_id)
        
        self.audit_agent.log_event("beckn_status", {
            "order_id": order_id,
            "status": status_response.get("message", {}).get("order", {}).get("state", "UNKNOWN")
        }, beckn_transaction_id=self.beckn_client.transaction_id)
        
        # Send update (simulating workload progress)
        update_data = {
            "fulfillment": {
                "state": "IN_PROGRESS",
                "current_load_kw": 150,
                "progress_percent": 50
            }
        }
        update_response = self.beckn_client.update(order_id, update_data)
        
        self.audit_agent.log_event("beckn_update", {
            "order_id": order_id,
            "update_data": update_data
        }, beckn_transaction_id=self.beckn_client.transaction_id)
        
        # POST-FULFILLMENT PHASE
        print("\n🏁 POST-FULFILLMENT Phase")
        
        # Submit rating and performance data
        rating_data = {
            "rating": 5,
            "feedback": "Successfully optimized workload scheduling",
            "carbon_saved_kg": sum(d.expected_carbon for d in schedule_decisions) / 1000,
            "cost_saved_gbp": sum(d.expected_cost for d in schedule_decisions),
            "p415_revenue_gbp": sum(d.expected_p415_revenue for d in schedule_decisions)
        }
        
        rating_response = self.beckn_client.rating(order_id, rating_data)
        
        self.audit_agent.log_event("beckn_rating", {
            "order_id": order_id,
            "rating_data": rating_data
        }, beckn_transaction_id=self.beckn_client.transaction_id)
        
        print(f"✓ Beckn journey completed for order {order_id}")
        
        return order_id
    
    def _extract_best_item(self, search_response: Dict) -> Dict:
        """Extract best item from search catalog"""
        try:
            catalog = search_response.get("message", {}).get("catalog", {})
            providers = catalog.get("providers", [])
            if providers:
                items = providers[0].get("items", [])
                if items:
                    return items[0]
        except:
            pass
        
        # Return default if extraction fails
        return {
            "id": "default-energy-window",
            "descriptor": {"name": "Standard Energy Window"},
            "price": {"value": "0.20", "currency": "GBP"}
        }
    
    def _build_order_details(self, select_response: Dict) -> Dict:
        """Build order details from select response"""
        try:
            order = select_response.get("message", {}).get("order", {})
            return order
        except:
            pass
        
        # Return default if extraction fails
        return {
            "provider": {"id": "grid-provider-1"},
            "items": [self._extract_best_item(select_response)],
            "billing": {
                "name": "Haikara Data Center",
                "email": "billing@haikara.example.com"
            },
            "fulfillment": {
                "type": "scheduled",
                "start_time": datetime.now().isoformat()
            }
        }
