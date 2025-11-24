"""
Grid Agent: Fetches real-time energy signals from grid APIs
"""
from typing import List, Dict
from datetime import datetime, timedelta
from models import EnergySignal
import random


class GridAgent:
    """
    Fetches energy price, carbon intensity, and P415 flexibility events
    """
    
    def __init__(self, carbon_api_key: str = None, energy_api_key: str = None):
        self.carbon_api_key = carbon_api_key
        self.energy_api_key = energy_api_key
        self.cached_signals: List[EnergySignal] = []
        
    def get_current_signals(self) -> EnergySignal:
        """Get current energy signals"""
        # In production, this would call real APIs:
        # - National Grid Carbon Intensity API
        # - Octopus Energy API
        # - P415 events from grid operator
        
        signal = self._fetch_real_time_data()
        print(f"[Grid Agent] Current price: £{signal.price_per_kwh:.4f}/kWh, "
              f"Carbon: {signal.carbon_intensity_g_per_kwh:.1f}g/kWh")
        return signal
    
    def get_forecast_signals(self, hours_ahead: int = 24) -> List[EnergySignal]:
        """
        Get forecasted energy signals for next N hours
        Uses Prophet for time-series forecasting in production
        """
        signals = []
        now = datetime.now()
        
        for hour in range(hours_ahead):
            timestamp = now + timedelta(hours=hour)
            signal = self._generate_forecast_for_time(timestamp)
            signals.append(signal)
        
        print(f"[Grid Agent] Generated forecast for next {hours_ahead} hours")
        return signals
    
    def check_p415_events(self) -> Dict[str, any]:
        """Check for active P415 demand flexibility events"""
        # In production, poll P415 event API
        # For now, simulate random events
        
        is_active = random.random() < 0.65  # 65% chance of P415 event (for demo visibility)
        
        if is_active:
            event = {
                "active": True,
                "start_time": datetime.now(),
                "end_time": datetime.now() + timedelta(hours=2),
                "revenue_per_kwh": 0.15,  # £0.15/kWh flexibility payment
                "required_reduction_kw": 200
            }
            print(f"[Grid Agent] P415 event active! Revenue: £{event['revenue_per_kwh']}/kWh")
            return event
        else:
            return {"active": False}
    
    def _fetch_real_time_data(self) -> EnergySignal:
        """
        Fetch real-time data from APIs
        For hackathon: simulated realistic data
        """
        # Simulate realistic UK energy prices and carbon intensity
        base_price = 0.25  # £0.25/kWh base
        hour = datetime.now().hour
        
        # Higher prices during peak hours (4-8 PM)
        if 16 <= hour <= 20:
            price_multiplier = 1.5
        else:
            price_multiplier = random.uniform(0.8, 1.2)
        
        price = base_price * price_multiplier
        
        # Carbon intensity varies by time (lower at night, renewables)
        if 22 <= hour or hour <= 6:
            carbon = random.uniform(150, 250)  # Lower at night
        else:
            carbon = random.uniform(250, 400)  # Higher during day
        
        p415_event = self.check_p415_events()
        
        return EnergySignal(
            timestamp=datetime.now(),
            price_per_kwh=price,
            carbon_intensity_g_per_kwh=carbon,
            grid_availability=random.uniform(0.85, 1.0),
            p415_event_active=p415_event["active"],
            p415_revenue_per_kwh=p415_event.get("revenue_per_kwh", 0.0)
        )
    
    def _generate_forecast_for_time(self, timestamp: datetime) -> EnergySignal:
        """Generate forecasted signal for specific time"""
        hour = timestamp.hour
        
        # Peak hours pricing
        if 16 <= hour <= 20:
            price = random.uniform(0.30, 0.45)
            carbon = random.uniform(300, 450)
        # Off-peak
        elif 22 <= hour or hour <= 6:
            price = random.uniform(0.15, 0.25)
            carbon = random.uniform(150, 250)
        # Standard
        else:
            price = random.uniform(0.20, 0.32)
            carbon = random.uniform(200, 350)
        
        # P415 event probability
        p415_active = random.random() < 0.40  # 40% in forecasts (realistic but visible)
        
        return EnergySignal(
            timestamp=timestamp,
            price_per_kwh=price,
            carbon_intensity_g_per_kwh=carbon,
            grid_availability=random.uniform(0.85, 1.0),
            p415_event_active=p415_active,
            p415_revenue_per_kwh=0.15 if p415_active else 0.0
        )
