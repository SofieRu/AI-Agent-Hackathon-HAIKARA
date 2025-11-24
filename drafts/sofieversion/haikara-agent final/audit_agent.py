"""
Audit Agent: Provides full traceability and audit trail
"""
from typing import List, Dict, Any
from datetime import datetime
from models import AuditLog
import json
import hashlib


class AuditAgent:
    """
    Records all decisions, Beckn transactions, and outcomes
    Provides cryptographic signatures for verification
    """
    
    def __init__(self):
        self.logs: List[AuditLog] = []
        
    def log_event(
        self, 
        event_type: str, 
        data: Dict[str, Any],
        job_id: str = None,
        beckn_transaction_id: str = None
    ):
        """Log an event with cryptographic signature"""
        
        log_entry = AuditLog(
            timestamp=datetime.now(),
            event_type=event_type,
            job_id=job_id,
            beckn_transaction_id=beckn_transaction_id,
            data=data
        )
        
        # Generate cryptographic signature
        log_entry.signature = self._generate_signature(log_entry)
        
        self.logs.append(log_entry)
        
        print(f"[Audit Agent] Logged: {event_type} "
              f"{f'(Job: {job_id})' if job_id else ''} "
              f"{f'(Txn: {beckn_transaction_id})' if beckn_transaction_id else ''}")
    
    def _generate_signature(self, log_entry: AuditLog) -> str:
        """Generate SHA-256 signature for log entry"""
        data_str = json.dumps({
            "timestamp": log_entry.timestamp.isoformat(),
            "event_type": log_entry.event_type,
            "job_id": log_entry.job_id,
            "beckn_transaction_id": log_entry.beckn_transaction_id,
            "data": log_entry.data
        }, sort_keys=True)
        
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def get_logs_for_job(self, job_id: str) -> List[AuditLog]:
        """Get all logs for a specific job"""
        return [log for log in self.logs if log.job_id == job_id]
    
    def get_logs_for_transaction(self, transaction_id: str) -> List[AuditLog]:
        """Get all logs for a Beckn transaction"""
        return [log for log in self.logs if log.beckn_transaction_id == transaction_id]
    
    def export_audit_trail(self, filepath: str = "audit_trail.json"):
        """Export complete audit trail to JSON file"""
        export_data = []
        
        for log in self.logs:
            export_data.append({
                "timestamp": log.timestamp.isoformat(),
                "event_type": log.event_type,
                "job_id": log.job_id,
                "beckn_transaction_id": log.beckn_transaction_id,
                "data": log.data,
                "signature": log.signature
            })
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"[Audit Agent] Exported {len(self.logs)} log entries to {filepath}")
    
    def generate_settlement_report(self) -> Dict[str, Any]:
        """Generate settlement report for P415 and cost savings"""
        
        # Extract key metrics from logs
        total_cost_savings = 0.0
        total_carbon_savings = 0.0
        total_p415_revenue = 0.0
        jobs_completed = 0
        
        for log in self.logs:
            if log.event_type == "schedule_optimized":
                savings = log.data.get("savings", {})
                total_cost_savings += savings.get("cost_savings", 0)
                total_carbon_savings += savings.get("carbon_savings_kg", 0)
                total_p415_revenue += savings.get("p415_revenue", 0)
            
            if log.event_type == "job_completed":
                jobs_completed += 1
        
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "total_jobs_completed": jobs_completed,
            "financial_metrics": {
                "total_cost_savings_gbp": round(total_cost_savings, 2),
                "total_p415_revenue_gbp": round(total_p415_revenue, 2),
                "net_benefit_gbp": round(total_cost_savings + total_p415_revenue, 2)
            },
            "environmental_metrics": {
                "total_carbon_savings_kg": round(total_carbon_savings, 2),
                "equivalent_trees_planted": round(total_carbon_savings / 25, 1)  # ~25kg CO2 per tree/year
            },
            "audit_trail_entries": len(self.logs)
        }
        
        print(f"\n[Audit Agent] Settlement Report Generated:")
        print(f"  Cost Savings: £{report['financial_metrics']['total_cost_savings_gbp']}")
        print(f"  P415 Revenue: £{report['financial_metrics']['total_p415_revenue_gbp']}")
        print(f"  Carbon Savings: {report['environmental_metrics']['total_carbon_savings_kg']} kg CO2")
        
        return report
    
    def verify_log_integrity(self) -> bool:
        """Verify that all logs have valid signatures"""
        for log in self.logs:
            expected_sig = self._generate_signature(log)
            if log.signature != expected_sig:
                print(f"[Audit Agent] WARNING: Integrity check failed for log at {log.timestamp}")
                return False
        
        print(f"[Audit Agent] Integrity check passed for all {len(self.logs)} logs")
        return True
