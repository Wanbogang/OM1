import logging
import os
import uuid
from typing import Any, Dict, Optional

from coinbase_commerce.client import Client

from .order_manager import Order


class PaymentHandler:
    """Handles payment processing using Coinbase Commerce."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize payment handler.

        Args:
            api_key: Coinbase Commerce API key (defaults to environment variable)
        """
        self.api_key = api_key or os.getenv("COINBASE_COMMERCE_API_KEY")
        self.webhook_secret = os.getenv("COINBASE_COMMERCE_WEBHOOK_SECRET")

        # Initialize Coinbase Commerce client
        if self.api_key:
            self.client = Client(api_key=self.api_key)
        else:
            # For demo purposes, we'll run without a real API key
            self.client = None
            logging.warning(
                "No Coinbase Commerce API key provided. Running in demo mode."
            )

    def create_payment_charge(
        self, order: Order, redirect_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a payment charge for an order.

        Args:
            order: Order to create payment for
            redirect_url: URL to redirect to after payment

        Returns:
            Dictionary containing charge information
        """
        if not self.client:
            # Demo mode - return mock payment URL
            return self._create_demo_charge(order, redirect_url)

        try:
            charge_data = {
                "name": f"Order #{order.id}",
                "description": f"Payment for order with {len(order.items)} items",
                "local_price": {"amount": str(order.total_amount), "currency": "USD"},
                "pricing_type": "fixed_price",
                "metadata": {
                    "order_id": order.id,
                    "customer_name": order.customer_name or "Guest",
                },
            }

            if redirect_url:
                charge_data["redirect_url"] = redirect_url

            charge = self.client.charge.create(**charge_data)

            return {
                "success": True,
                "charge_id": charge.id,
                "hosted_url": charge.hosted_url,
                "amount": order.total_amount,
                "currency": "USD",
            }

        except Exception as e:
            logging.error(f"Error creating payment charge: {e}")
            return {"success": False, "error": str(e)}

    def _create_demo_charge(
        self, order: Order, redirect_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a demo payment charge (mock implementation).

        Args:
            order: Order to create payment for
            redirect_url: URL to redirect to after payment

        Returns:
            Dictionary containing mock charge information
        """
        # Generate a mock payment URL
        mock_charge_id = f"demo_{uuid.uuid4().hex[:12]}"
        mock_payment_url = f"https://demo-payment.example.com/charges/{mock_charge_id}"

        return {
            "success": True,
            "charge_id": mock_charge_id,
            "hosted_url": mock_payment_url,
            "amount": order.total_amount,
            "currency": "USD",
            "demo_mode": True,
            "message": "This is a demo payment URL. No actual payment will be processed.",
        }

    def get_charge_status(self, charge_id: str) -> Optional[str]:
        """
        Get the status of a payment charge.

        Args:
            charge_id: ID of the charge to check

        Returns:
            Charge status or None if not found
        """
        if not self.client:
            # Demo mode - return mock status
            return "demo_mode"

        try:
            charge = self.client.charge.retrieve(charge_id)
            return charge.get("status")
        except Exception as e:
            logging.error(f"Error retrieving charge status: {e}")
            return None
