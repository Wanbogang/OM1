import uuid
from datetime import datetime
from typing import Dict, Optional

from .emoji_processor import EmojiProcessor


class OrderManager:
    def __init__(self):
        self.emoji_processor = EmojiProcessor()
        self.active_orders = {}

    def create_order(self, emoji_string: str, user_id: str) -> Dict:
        """Create new order from emoji string"""
        # Process emojis
        processed = self.emoji_processor.process_emoji_string(emoji_string)

        if "error" in processed:
            return processed

        # Create order
        order_id = str(uuid.uuid4())[:8]
        order = {
            "order_id": order_id,
            "user_id": user_id,
            "items": processed["items"],
            "modifiers": processed["modifiers"],
            "total_price": processed["total_price"],
            "status": "pending_payment",
            "created_at": datetime.now().isoformat(),
            "emoji_string": emoji_string,
        }

        self.active_orders[order_id] = order
        return order

    def update_order_status(self, order_id: str, status: str) -> Dict:
        """Update order status"""
        if order_id in self.active_orders:
            self.active_orders[order_id]["status"] = status
            self.active_orders[order_id]["updated_at"] = datetime.now().isoformat()
            return self.active_orders[order_id]
        return {"error": "Order not found"}

    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order by ID"""
        return self.active_orders.get(order_id)
