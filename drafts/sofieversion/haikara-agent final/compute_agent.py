"""
Compute Agent: Manages data center workload information
"""
from typing import List, Dict
from datetime import datetime, timedelta
from models import ComputeWorkload, WorkloadPriority, WorkloadStatus
import random


class ComputeAgent:
    """
    Manages compute workloads and provides flexibility information
    """
    
    def __init__(self, max_capacity_kw: float = 1000):
        self.max_capacity_kw = max_capacity_kw
        self.workloads: List[ComputeWorkload] = []
        self.current_load_kw = 0.0
        
    def add_workload(self, workload: ComputeWorkload):
        """Add a new workload to the queue"""
        self.workloads.append(workload)
        print(f"[Compute Agent] Added workload {workload.job_id}: {workload.name}")
        
    def get_flexible_workloads(self) -> List[ComputeWorkload]:
        """
        Get workloads that can be flexibly scheduled
        (i.e., have time window before SLA deadline)
        """
        now = datetime.now()
        flexible = []
        
        for workload in self.workloads:
            if workload.status == WorkloadStatus.PENDING:
                time_until_deadline = (workload.sla_deadline - now).total_seconds() / 3600
                # If we have more than 2 hours until deadline, it's flexible
                if time_until_deadline > workload.duration_hours + 2:
                    flexible.append(workload)
                    
        print(f"[Compute Agent] Found {len(flexible)} flexible workloads")
        return flexible
    
    def get_total_capacity(self) -> Dict[str, float]:
        """Get capacity information"""
        return {
            "max_capacity_kw": self.max_capacity_kw,
            "current_load_kw": self.current_load_kw,
            "available_capacity_kw": self.max_capacity_kw - self.current_load_kw
        }
    
    def update_workload_status(self, job_id: str, status: WorkloadStatus):
        """Update status of a workload"""
        for workload in self.workloads:
            if workload.job_id == job_id:
                workload.status = status
                print(f"[Compute Agent] Updated {job_id} status to {status}")
                break
    
    def generate_sample_workloads(self, count: int = 5):
        """Generate sample workloads for testing"""
        now = datetime.now()
        
        workload_templates = [
            {"name": "ML Model Training", "energy": 150, "duration": 4},
            {"name": "Data Processing Pipeline", "energy": 80, "duration": 2},
            {"name": "Batch Analytics", "energy": 120, "duration": 3},
            {"name": "Video Rendering", "energy": 200, "duration": 6},
            {"name": "Database Backup", "energy": 50, "duration": 1.5},
        ]
        
        for i in range(count):
            template = workload_templates[i % len(workload_templates)]
            
            workload = ComputeWorkload(
                job_id=f"JOB-{i+1:03d}",
                name=f"{template['name']} #{i+1}",
                energy_usage_kw=template['energy'],
                duration_hours=template['duration'],
                priority=random.choice(list(WorkloadPriority)),
                sla_deadline=now + timedelta(hours=random.randint(12, 48)),
                earliest_start=now,
                status=WorkloadStatus.PENDING
            )
            
            self.add_workload(workload)
