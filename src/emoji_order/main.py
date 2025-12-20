import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rich.console import Console

from .core.order_manager import OrderManager
from .core.payment_handler import PaymentHandler
from .integrations.smart_assistant import (SmartAssistantBridge,
                                           VoiceCommandProcessor)

# Setup logging
logger = logging.getLogger(__name__)

app = FastAPI(title="Emoji Order Assistant", version="1.0.0")
console = Console()
order_manager = OrderManager()
payment_handler = PaymentHandler()
voice_processor = VoiceCommandProcessor()
smart_assistant = SmartAssistantBridge()


class EmojiOrderRequest(BaseModel):
    emoji_string: str
    user_id: str


class VoiceCommandRequest(BaseModel):
    command: str
    customer_name: str = None


class PaymentRequest(BaseModel):
    order_id: str


@app.post("/api/emoji-order")
async def create_emoji_order(request: EmojiOrderRequest):
    """Create order from emoji string"""
    try:
        order = order_manager.create_order(request.emoji_string, request.user_id)
        if "error" in order:
            raise HTTPException(status_code=400, detail=order["error"])
        console.print(f"[green]✅ Order created: {order['order_id']}[/green]")
        return order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice-command")
async def process_voice_command(request: VoiceCommandRequest):
    """Process voice command with natural language"""
    try:
        # Process voice command
        processed = voice_processor.process_voice_command(request.command)

        if processed["intent"] == "order" and processed["emojis"]:
            # Create order from extracted emojis
            customer_name = request.customer_name or processed["customer_name"]
            order = order_manager.create_order(processed["emojis"], customer_name)

            if "error" in order:
                raise HTTPException(status_code=400, detail=order["error"])

            # Send notification to smart assistant
            smart_assistant.send_notification(
                f"New Voice Order #{order['order_id']}",
                f"Customer: {customer_name}, Command: {request.command}",
            )

            console.print(f"[green]🎤 Voice order created: {order['order_id']}[/green]")
            return {
                **order,
                "voice_command": request.command,
                "processed_intent": processed["intent"],
                "extracted_emojis": processed["emojis"],
                "customer_name": customer_name,
            }
        else:
            raise HTTPException(
                status_code=400, detail="No order intent found in command"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/payment")
async def create_payment(request: PaymentRequest):
    """Create payment for order"""
    try:
        order = order_manager.get_order(request.order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        payment = payment_handler.create_payment_charge(order)
        if not payment["success"]:
            raise HTTPException(status_code=400, detail=payment["error"])
        console.print(f"[green]💳 Payment created: {payment['charge_id']}[/green]")
        return payment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/order/{order_id}")
async def get_order_status(order_id: str):
    """Get order status"""
    order = order_manager.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.get("/")
async def root():
    return {
        "message": "Emoji Order Assistant API",
        "status": "running",
        "version": "1.0.0",
        "features": ["emoji_orders", "voice_commands", "smart_assistant_integration"],
    }


@app.post("/api/smart-home")
async def smart_home_webhook(request: dict):
    """Smart Assistant webhook endpoint"""
    try:
        from .integrations.smart_assistant import SmartAssistantBridge

        # Initialize smart assistant bridge
        bridge = SmartAssistantBridge()

        order_id = request.get("order_id")
        message = request.get("message", "New order received")
        title = request.get("title", "🍕 OM1 New Order")

        # Send notification
        success = bridge.send_notification(title, message)

        return {
            "success": success,
            "message": (
                "Smart home notification sent"
                if success
                else "Failed to send notification"
            ),
            "order_id": order_id,
            "timestamp": str(datetime.now()),
        }

    except Exception as e:
        logger.error(f"Smart home webhook error: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to process smart home notification",
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
