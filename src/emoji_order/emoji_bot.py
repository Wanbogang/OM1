import logging
from typing import Any, Dict, Optional

from .emoji_processor import EmojiProcessor
from .order_manager import OrderManager
from .payment_handler import PaymentHandler
from .smart_assistant import SmartAssistantBridge, VoiceCommandProcessor


class EmojiBot:
    """Main bot class for emoji-based ordering with smart assistant integration"""

    def __init__(self, demo_mode=True, ha_url=None, ha_token=None):
        self.demo_mode = demo_mode
        self.emoji_processor = EmojiProcessor()
        self.order_manager = OrderManager()
        self.payment_handler = PaymentHandler() if not demo_mode else None

        # Smart Assistant integration
        self.smart_assistant = SmartAssistantBridge(ha_url, ha_token)
        self.voice_processor = VoiceCommandProcessor()

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

        # Send notification when bot starts
        try:
            self.smart_assistant.send_notification(
                "OM1 Bot Started", "Emoji Order Assistant is ready to receive orders!"
            )
        except Exception as e:
            self.logger.info(f"Smart assistant notification failed: {e}")

    def process_emoji_order(
        self, emoji_string: str, customer_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process emoji order (original method)"""
        try:
            # Process emojis
            menu_items = self.emoji_processor.process_emojis(emoji_string)

            if not menu_items:
                return {"error": "No valid menu items found"}

            # Create order
            order = self.order_manager.create_order(menu_items, customer_name)

            # Process payment if not demo mode
            if not self.demo_mode and self.payment_handler:
                payment_result = self.payment_handler.process_payment(order)
                order["payment_url"] = payment_result.get("payment_url")

            return order

        except Exception as e:
            self.logger.error(f"Error processing order: {e}")
            return {"error": str(e)}

    def process_voice_command(self, command: str, customer_name: str = None) -> dict:
        """Process voice command from smart assistant"""
        try:
            processed = self.voice_processor.process_voice_command(command)

            if processed["intent"] == "order" and processed["emojis"]:
                # Use emojis from voice command
                customer = customer_name or processed["customer_name"]
                result = self.process_emoji_order(processed["emojis"], customer)

                if "error" not in result:
                    # Extract order info for smart assistant
                    order_info = {
                        "order_id": result.get("order", {}).get("id", "unknown"),
                        "customer_name": customer,
                        "items": [
                            {"name": item.name, "price": item.price}
                            for item in result.get("order", {}).get("items", [])
                        ],
                        "total": result.get("order", {}).get("total_amount", 0),
                    }

                    # Trigger action di smart assistant
                    self.smart_assistant.trigger_order_action(order_info)

                    return {
                        "success": True,
                        "order_id": order_info["order_id"],
                        "items": [
                            item.name
                            for item in result.get("order", {}).get("items", [])
                        ],
                        "total": order_info["total"],
                        "payment_url": result.get("payment_url"),
                    }
                else:
                    return result

            elif processed["intent"] == "status":
                return self.get_order_status()
            elif processed["intent"] == "cancel":
                return {"message": "Cancel functionality not implemented yet"}
            else:
                return {"error": "Command not recognized"}

        except Exception as e:
            return {"error": f"Failed to process voice command: {str(e)}"}

    def get_order_status(self) -> dict:
        """Get order statistics"""
        return self.order_manager.get_statistics()

    def create_order_with_smart_assistant(
        self, emoji_string: str, customer_name: str = "Customer"
    ) -> dict:
        """Create order with smart assistant integration"""
        try:
            # Create order seperti biasa
            result = self.process_emoji_order(emoji_string, customer_name)

            if "error" not in result:
                order_info = {
                    "order_id": result.get("order", {}).get("id", "unknown"),
                    "customer_name": customer_name,
                    "items": [
                        {"name": item.name, "price": item.price}
                        for item in result.get("order", {}).get("items", [])
                    ],
                    "total": result.get("order", {}).get("total_amount", 0),
                }

                # Send notification ke smart assistant
                self.smart_assistant.send_notification(
                    f"New Order #{order_info['order_id']}",
                    f"Customer: {customer_name}, Items: {len(order_info['items'])}, Total: ${order_info['total']}",
                )

                # Update status di smart assistant
                self.smart_assistant.update_order_status(
                    order_info["order_id"], "received"
                )

                # Trigger automation
                self.smart_assistant.trigger_order_action(
                    {
                        "order_id": order_info["order_id"],
                        "customer_name": customer_name,
                        "items": order_info["items"],
                        "total": order_info["total"],
                        "payment_url": result.get("payment_url"),
                    }
                )

                return {
                    "success": True,
                    "order_id": order_info["order_id"],
                    "items": [
                        item.name for item in result.get("order", {}).get("items", [])
                    ],
                    "total": order_info["total"],
                    "payment_url": result.get("payment_url"),
                }

            return result

        except Exception as e:
            # Send error notification
            self.smart_assistant.send_notification(
                "Order Creation Failed", f"Error: {str(e)}"
            )
            return {"error": f"Failed to create order: {str(e)}"}

    def update_payment_status_smart_assistant(self, order_id: str, status: str) -> bool:
        """Update payment status with smart assistant notification"""
        try:
            # Update status di smart assistant
            self.smart_assistant.update_order_status(order_id, status)

            # Send notification
            status_messages = {
                "paid": "Payment received successfully!",
                "pending": "Payment is pending",
                "failed": "Payment failed",
            }

            message = status_messages.get(status, f"Payment status: {status}")
            self.smart_assistant.send_notification(
                f"Order #{order_id} - {status.upper()}", message
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to update smart assistant: {e}")
            return False
