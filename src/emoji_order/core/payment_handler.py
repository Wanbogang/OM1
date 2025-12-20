from typing import Dict

from ..utils.config import Config


class PaymentHandler:
    def __init__(self):
        self.config = Config()
        # Mock Coinbase integration for demo
        self.mock_payments = {}

    def create_payment_charge(self, order_data: Dict) -> Dict:
        """Create Coinbase payment charge (Mock for demo)"""
        try:
            # Mock charge creation
            charge_id = f"mock_charge_{order_data['order_id']}"

            mock_charge = {
                "id": charge_id,
                "hosted_url": f"https://commerce.coinbase.com/checkout/{charge_id}",
                "status": "PENDING",
            }

            self.mock_payments[charge_id] = mock_charge

            return {
                "success": True,
                "charge_id": charge_id,
                "hosted_url": mock_charge["hosted_url"],
                "amount": order_data["total_price"],
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def verify_payment(self, charge_id: str) -> Dict:
        """Verify payment status (Mock for demo)"""
        try:
            if charge_id in self.mock_payments:
                # Simulate payment completion
                self.mock_payments[charge_id]["status"] = "COMPLETED"

                return {
                    "success": True,
                    "status": "COMPLETED",
                    "paid_at": "2025-01-19T10:30:00Z",
                }
            else:
                return {"success": False, "error": "Charge not found"}

        except Exception as e:
            return {"success": False, "error": str(e)}
