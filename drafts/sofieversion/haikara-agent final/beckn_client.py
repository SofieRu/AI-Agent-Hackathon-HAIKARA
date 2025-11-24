"""
Beckn API Client: Handles all Beckn protocol communication with BAP Sandbox
"""
import requests
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from models import ScheduleDecision, ComputeWorkload


class BecknAPIClient:
    """
    Client for interacting with Beckn-enabled BAP Sandbox
    """
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.transaction_id = None
        self.message_id = None
        
    def _generate_context(self, action: str) -> Dict[str, Any]:
        """Generate Beckn context for request"""
        if not self.transaction_id:
            self.transaction_id = str(uuid.uuid4())
        
        self.message_id = str(uuid.uuid4())
        
        return {
            "domain": "energy:compute",
            "action": action,
            "version": "1.0.0",
            "bap_id": "haikara-agent",
            "bap_uri": "http://haikara.example.com",
            "transaction_id": self.transaction_id,
            "message_id": self.message_id,
            "timestamp": datetime.now().isoformat(),
            "ttl": "PT30S"
        }
    
    def search(self, schedule_decisions: list[ScheduleDecision]) -> Dict[str, Any]:
        """
        DISCOVER phase: Search for optimal energy windows
        """
        print(f"\n[Beckn API] DISCOVER: Searching for energy windows...")
        
        # Build search intent
        intent = {
            "item": {
                "descriptor": {
                    "name": "Flexible Compute Capacity"
                }
            },
            "fulfillment": {
                "type": "scheduled",
                "time_windows": []
            }
        }
        
        # Add time windows from schedule decisions
        for decision in schedule_decisions:
            intent["fulfillment"]["time_windows"].append({
                "start": decision.scheduled_start.isoformat(),
                "end": decision.scheduled_end.isoformat(),
                "energy_kw": decision.expected_cost / 0.25  # Rough estimate
            })
        
        request_body = {
            "context": self._generate_context("search"),
            "message": {
                "intent": intent
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/search",
                json=request_body,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            print(f"[Beckn API] ✓ Search successful (Txn: {self.transaction_id})")
            return result
        except Exception as e:
            print(f"[Beckn API] ✗ Search failed: {e}")
            # Return mock response for hackathon demo
            return self._mock_on_search(request_body)
    
    def select(self, selected_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        ORDER phase: Select specific energy window
        """
        print(f"[Beckn API] ORDER: Selecting energy window...")
        
        request_body = {
            "context": self._generate_context("select"),
            "message": {
                "order": {
                    "items": [selected_item],
                    "provider": {
                        "id": "grid-provider-1"
                    }
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/select",
                json=request_body,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            print(f"[Beckn API] ✓ Select successful")
            return result
        except Exception as e:
            print(f"[Beckn API] ✗ Select failed: {e}")
            return self._mock_on_select(request_body)
    
    def init(self, order_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        ORDER phase: Initialize order
        """
        print(f"[Beckn API] ORDER: Initializing order...")
        
        request_body = {
            "context": self._generate_context("init"),
            "message": {
                "order": order_details
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/init",
                json=request_body,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            print(f"[Beckn API] ✓ Init successful")
            return result
        except Exception as e:
            print(f"[Beckn API] ✗ Init failed: {e}")
            return self._mock_on_init(request_body)
    
    def confirm(self, order_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        ORDER phase: Confirm order
        """
        print(f"[Beckn API] ORDER: Confirming order...")
        
        request_body = {
            "context": self._generate_context("confirm"),
            "message": {
                "order": order_details
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/confirm",
                json=request_body,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            print(f"[Beckn API] ✓ Confirm successful")
            return result
        except Exception as e:
            print(f"[Beckn API] ✗ Confirm failed: {e}")
            return self._mock_on_confirm(request_body)
    
    def status(self, order_id: str) -> Dict[str, Any]:
        """
        FULFILLMENT phase: Check order status
        """
        print(f"[Beckn API] FULFILLMENT: Checking status...")
        
        request_body = {
            "context": self._generate_context("status"),
            "message": {
                "order_id": order_id
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/status",
                json=request_body,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            print(f"[Beckn API] ✓ Status check successful")
            return result
        except Exception as e:
            print(f"[Beckn API] ✗ Status check failed: {e}")
            return self._mock_on_status(request_body)
    
    def update(self, order_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        FULFILLMENT phase: Update order
        """
        print(f"[Beckn API] FULFILLMENT: Updating order...")
        
        request_body = {
            "context": self._generate_context("update"),
            "message": {
                "order_id": order_id,
                "update_target": "fulfillment",
                "order": update_data
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/update",
                json=request_body,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            print(f"[Beckn API] ✓ Update successful")
            return result
        except Exception as e:
            print(f"[Beckn API] ✗ Update failed: {e}")
            return self._mock_on_update(request_body)
    
    def rating(self, order_id: str, rating_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        POST-FULFILLMENT phase: Submit rating and feedback
        """
        print(f"[Beckn API] POST-FULFILLMENT: Submitting rating...")
        
        request_body = {
            "context": self._generate_context("rating"),
            "message": {
                "ratings": [{
                    "id": order_id,
                    "value": rating_data.get("rating", 5),
                    "feedback": rating_data.get("feedback", "")
                }]
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/rating",
                json=request_body,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            print(f"[Beckn API] ✓ Rating submitted")
            return result
        except Exception as e:
            print(f"[Beckn API] ✗ Rating failed: {e}")
            return self._mock_on_rating(request_body)
    
    # Mock response methods for hackathon demo when sandbox is unavailable
    
    def _mock_on_search(self, request: Dict) -> Dict:
        return {
            "context": request["context"],
            "message": {
                "catalog": {
                    "providers": [{
                        "id": "grid-provider-1",
                        "descriptor": {"name": "UK National Grid"},
                        "items": [{
                            "id": "energy-window-1",
                            "descriptor": {"name": "Off-peak Window"},
                            "price": {"value": "0.18", "currency": "GBP"},
                            "fulfillment": {
                                "start": request["message"]["intent"]["fulfillment"]["time_windows"][0]["start"]
                            }
                        }]
                    }]
                }
            }
        }
    
    def _mock_on_select(self, request: Dict) -> Dict:
        return {
            "context": request["context"],
            "message": {
                "order": {
                    "provider": request["message"]["order"]["provider"],
                    "items": request["message"]["order"]["items"],
                    "quote": {"price": {"value": "45.50", "currency": "GBP"}}
                }
            }
        }
    
    def _mock_on_init(self, request: Dict) -> Dict:
        return {
            "context": request["context"],
            "message": {
                "order": {
                    **request["message"]["order"],
                    "id": str(uuid.uuid4()),
                    "state": "INITIALIZED"
                }
            }
        }
    
    def _mock_on_confirm(self, request: Dict) -> Dict:
        return {
            "context": request["context"],
            "message": {
                "order": {
                    **request["message"]["order"],
                    "state": "CONFIRMED"
                }
            }
        }
    
    def _mock_on_status(self, request: Dict) -> Dict:
        return {
            "context": request["context"],
            "message": {
                "order": {
                    "id": request["message"]["order_id"],
                    "state": "IN_PROGRESS",
                    "fulfillment": {"state": "EXECUTING"}
                }
            }
        }
    
    def _mock_on_update(self, request: Dict) -> Dict:
        return {
            "context": request["context"],
            "message": {
                "order": {
                    "id": request["message"]["order_id"],
                    "state": "UPDATED"
                }
            }
        }
    
    def _mock_on_rating(self, request: Dict) -> Dict:
        return {
            "context": request["context"],
            "message": {"ack": {"status": "ACK"}}
        }
