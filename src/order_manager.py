import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from .emoji_processor import MenuItem


class OrderStatus(Enum):
    """Enumeration for order status."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    PAID = "paid"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Order:
    """Represents a customer order."""

    id: str
    items: List[MenuItem]
    total_amount: float
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    customer_name: Optional[str] = None
    payment_url: Optional[str] = None

    def __post_init__(self):
        """Ensure timestamps are set correctly."""
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.updated_at:
            self.updated_at = datetime.now()


class OrderManager:
    """Manages order lifecycle and storage."""

    def __init__(self):
        # In-memory storage for orders (in production, use a database)
        self.orders: Dict[str, Order] = {}

    def create_order(
        self, items: List[MenuItem], customer_name: Optional[str] = None
    ) -> Order:
        """
        Create a new order.

        Args:
            items: List of menu items in the order
            customer_name: Optional customer name

        Returns:
            Created Order object
        """
        order_id = str(uuid.uuid4())[:8]  # Short UUID for demo
        total_amount = sum(item.price for item in items)

        order = Order(
            id=order_id,
            items=items,
            total_amount=total_amount,
            status=OrderStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            customer_name=customer_name,
        )

        self.orders[order_id] = order
        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        """Retrieve an order by ID."""
        return self.orders.get(order_id)

    def update_order_status(self, order_id: str, status: OrderStatus) -> bool:
        """
        Update the status of an order.

        Args:
            order_id: ID of the order to update
            status: New status for the order

        Returns:
            True if update was successful, False if order not found
        """
        if order_id in self.orders:
            self.orders[order_id].status = status
            self.orders[order_id].updated_at = datetime.now()
            return True
        return False

    def list_orders(self, status_filter: Optional[OrderStatus] = None) -> List[Order]:
        """
        List all orders, optionally filtered by status.

        Args:
            status_filter: Optional status to filter by

        Returns:
            List of orders
        """
        orders = list(self.orders.values())

        if status_filter:
            orders = [order for order in orders if order.status == status_filter]

        # Sort by creation time (newest first)
        return sorted(orders, key=lambda x: x.created_at, reverse=True)

    def set_payment_url(self, order_id: str, payment_url: str) -> bool:
        """Set the payment URL for an order."""
        if order_id in self.orders:
            self.orders[order_id].payment_url = payment_url
            self.orders[order_id].updated_at = datetime.now()
            return True
        return False

    def format_order_summary(self, order: Order) -> str:
        """
        Format an order for display.

        Args:
            order: Order to format

        Returns:
            Formatted string representation of the order
        """
        lines = [
            f"📝 Order #{order.id}",
            f"👤 Customer: {order.customer_name or 'Guest'}",
            f"📅 Created: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"📊 Status: {order.status.value.upper()}",
            "",
            "🛍️ Items:",
        ]

        # Group items by type and count
        item_counts = {}
        for item in order.items:
            if item.emoji in item_counts:
                item_counts[item.emoji] = (item_counts[item.emoji][0] + 1, item)
            else:
                item_counts[item.emoji] = (1, item)

        for emoji, (count, item) in item_counts.items():
            lines.append(f"  {emoji}x{count} {item.name} - ${item.price * count:.2f}")

        lines.extend(
            [
                "",
                f"💰 Total: ${order.total_amount:.2f}",
                f"⏰ Updated: {order.updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            ]
        )

        if order.payment_url:
            lines.append(f"💳 Payment: {order.payment_url}")

        return "\n".join(lines)

    def get_statistics(self) -> Dict[str, any]:
        """Get order statistics."""
        total_orders = len(self.orders)
        status_counts = {}
        total_revenue = 0.0

        for order in self.orders.values():
            status = order.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            if order.status == OrderStatus.COMPLETED:
                total_revenue += order.total_amount

        return {
            "total_orders": total_orders,
            "status_counts": status_counts,
            "total_revenue": total_revenue,
            "average_order_value": total_revenue / max(1, total_orders),
        }
