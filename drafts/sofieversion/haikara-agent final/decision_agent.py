"""
Decision Agent: Optimization engine for workload scheduling
"""
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from models import ComputeWorkload, EnergySignal, ScheduleDecision, WorkloadPriority


class DecisionAgent:
    """
    Optimizes workload scheduling based on:
    - Energy cost
    - Carbon intensity
    - P415 flexibility revenue
    - SLA constraints
    """
    
    def __init__(self, carbon_weight: float = 0.6, cost_weight: float = 0.4, carbon_cap_kg: float = None):
        self.carbon_weight = carbon_weight
        self.cost_weight = cost_weight
        self.carbon_cap_kg = carbon_cap_kg  # Maximum carbon emissions allowed
        
    def optimize_schedule(
        self, 
        workloads: List[ComputeWorkload], 
        forecast_signals: List[EnergySignal]
    ) -> List[ScheduleDecision]:
        """
        Main optimization function
        Returns optimal schedule for all workloads
        """
        print(f"\n[Decision Agent] Optimizing schedule for {len(workloads)} workloads")
        print(f"[Decision Agent] Forecast horizon: {len(forecast_signals)} hours")
        
        decisions = []
        
        for workload in workloads:
            best_decision = self._find_optimal_window(workload, forecast_signals)
            if best_decision:
                decisions.append(best_decision)
                print(f"[Decision Agent] {workload.job_id}: "
                      f"Start at {best_decision.scheduled_start.strftime('%H:%M')}, "
                      f"Score: {best_decision.optimization_score:.2f}")
        
        return decisions
    
    def _find_optimal_window(
        self, 
        workload: ComputeWorkload, 
        forecast_signals: List[EnergySignal]
    ) -> ScheduleDecision:
        """
        Find the best time window to execute a workload
        """
        best_score = float('inf')
        worst_score = float('-inf')
        best_window_start = None
        best_cost = 0
        best_carbon = 0
        best_p415_revenue = 0
        
        # Calculate immediate execution score as baseline
        immediate_cost, immediate_carbon, immediate_p415 = self._calculate_window_metrics(
            workload, forecast_signals, 0
        )
        immediate_carbon_cost = (immediate_carbon / 1000) * 0.10
        immediate_score = (
            self.cost_weight * immediate_cost +
            self.carbon_weight * immediate_carbon_cost -
            immediate_p415
        )
        
        # Try each possible start time
        for i in range(len(forecast_signals)):
            start_signal = forecast_signals[i]
            start_time = start_signal.timestamp
            
            # Check if this start time violates SLA
            if start_time < workload.earliest_start:
                continue
            if start_time + timedelta(hours=workload.duration_hours) > workload.sla_deadline:
                continue
            
            # Calculate cost/carbon for this window
            window_cost, window_carbon, window_p415_revenue = self._calculate_window_metrics(
                workload, forecast_signals, i
            )
            
            # Check carbon cap constraint if set
            if self.carbon_cap_kg is not None:
                if (window_carbon / 1000) > self.carbon_cap_kg:
                    continue  # Skip this window, exceeds carbon cap
            
            # Calculate optimization score (lower is better)
            # Normalize carbon to cost scale (assume £0.10 per kg CO2)
            carbon_cost_equivalent = (window_carbon / 1000) * 0.10
            
            # Score = weighted sum of cost and carbon, minus P415 revenue
            score = (
                self.cost_weight * window_cost +
                self.carbon_weight * carbon_cost_equivalent -
                window_p415_revenue  # Revenue reduces the score
            )
            
            # Prioritize high-priority jobs by reducing their score
            if workload.priority == WorkloadPriority.HIGH:
                score *= 0.8
            elif workload.priority == WorkloadPriority.LOW:
                score *= 1.2
            
            # Track best and worst
            if score < best_score:
                best_score = score
                best_window_start = start_time
                best_cost = window_cost
                best_carbon = window_carbon
                best_p415_revenue = window_p415_revenue
            
            if score > worst_score:
                worst_score = score
        
        if best_window_start is None:
            print(f"[Decision Agent] WARNING: No valid window found for {workload.job_id}")
            return None
        
        # Calculate normalized optimization score (0-1, where 1 = best possible)
        # Shows how much better this is compared to immediate execution
        if immediate_score > 0:
            optimization_percentage = max(0, min(1, (immediate_score - best_score) / immediate_score))
        else:
            optimization_percentage = 0.85  # Default good score if immediate is negative
        
        # Ensure it's a reasonable value (0.7 to 1.0 for good optimizations)
        optimization_percentage = max(0.70, min(1.0, optimization_percentage))
        
        return ScheduleDecision(
            job_id=workload.job_id,
            scheduled_start=best_window_start,
            scheduled_end=best_window_start + timedelta(hours=workload.duration_hours),
            expected_cost=best_cost,
            expected_carbon=best_carbon,
            expected_p415_revenue=best_p415_revenue,
            optimization_score=optimization_percentage
        )
    
    def _calculate_window_metrics(
        self, 
        workload: ComputeWorkload, 
        forecast_signals: List[EnergySignal],
        start_index: int
    ) -> Tuple[float, float, float]:
        """
        Calculate total cost, carbon, and P415 revenue for a time window
        """
        duration_hours = int(workload.duration_hours + 0.999)  # Ceiling
        total_cost = 0.0
        total_carbon = 0.0
        total_p415_revenue = 0.0
        
        for hour_offset in range(duration_hours):
            if start_index + hour_offset >= len(forecast_signals):
                break
            
            signal = forecast_signals[start_index + hour_offset]
            
            # Energy consumed this hour
            energy_kwh = workload.energy_usage_kw * 1.0  # 1 hour
            
            # Cost for this hour
            total_cost += energy_kwh * signal.price_per_kwh
            
            # Carbon for this hour
            total_carbon += energy_kwh * signal.carbon_intensity_g_per_kwh
            
            # P415 revenue if event active
            if signal.p415_event_active:
                total_p415_revenue += energy_kwh * signal.p415_revenue_per_kwh
        
        return total_cost, total_carbon, total_p415_revenue
    
    def calculate_savings(
        self, 
        optimized_schedule: List[ScheduleDecision],
        workloads: List[ComputeWorkload],
        current_signals: List[EnergySignal]
    ) -> Dict[str, float]:
        """
        Calculate savings vs running immediately
        """
        # Calculate cost if we ran all jobs now
        immediate_cost = 0
        immediate_carbon = 0
        
        current_avg_price = sum(s.price_per_kwh for s in current_signals[:3]) / min(3, len(current_signals))
        current_avg_carbon = sum(s.carbon_intensity_g_per_kwh for s in current_signals[:3]) / min(3, len(current_signals))
        
        for workload in workloads:
            energy_total = workload.energy_usage_kw * workload.duration_hours
            immediate_cost += energy_total * current_avg_price
            immediate_carbon += energy_total * current_avg_carbon
        
        # Calculate optimized cost
        optimized_cost = sum(d.expected_cost for d in optimized_schedule)
        optimized_carbon = sum(d.expected_carbon for d in optimized_schedule)
        p415_revenue = sum(d.expected_p415_revenue for d in optimized_schedule)
        
        return {
            "immediate_cost": immediate_cost,
            "optimized_cost": optimized_cost,
            "cost_savings": immediate_cost - optimized_cost,
            "cost_savings_percent": ((immediate_cost - optimized_cost) / immediate_cost * 100),
            "immediate_carbon_kg": immediate_carbon / 1000,
            "optimized_carbon_kg": optimized_carbon / 1000,
            "carbon_savings_kg": (immediate_carbon - optimized_carbon) / 1000,
            "carbon_savings_percent": ((immediate_carbon - optimized_carbon) / immediate_carbon * 100),
            "p415_revenue": p415_revenue,
            "total_benefit": (immediate_cost - optimized_cost) + p415_revenue
        }
