#!/usr/bin/env python3
"""
Demo script untuk OM1 Smart Assistant Integration
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.emoji_bot import EmojiBot
from src.smart_assistant import SmartAssistantBridge, VoiceCommandProcessor


def demo_voice_commands():
    """Demo voice command processing"""
    print("🎤 Demo Voice Command Processing")
    print("=" * 50)

    vcp = VoiceCommandProcessor()

    test_commands = [
        "Tolong pesankan ☕ dan 🥐 untuk saya John",
        "Saya mau pesan 🍕 dan 🥤",
        "Cek status pesanan saya",
        "Batal pesan",
        "Buatkan saya ☕🍰🍔",
    ]

    for command in test_commands:
        print(f"\n📝 Command: '{command}'")
        result = vcp.process_voice_command(command)
        print(f"🎯 Intent: {result['intent']}")
        print(f"😀 Emojis: {result['emojis']}")
        print(f"👤 Customer: {result['customer_name']}")
        print("-" * 30)


def demo_smart_assistant_bridge():
    """Demo smart assistant bridge"""
    print("\n🏠 Demo Smart Assistant Bridge")
    print("=" * 50)

    # Mock mode (tanpa Home Assistant sebenarnya)
    bridge = SmartAssistantBridge()
    print(f"🔗 Smart Assistant Enabled: {bridge.enabled}")

    # Test notifications
    print("\n📢 Testing Notifications:")
    result1 = bridge.send_notification("Order Received", "New order #123")
    print(f"   Order notification: {result1}")

    result2 = bridge.send_notification(
        "Payment Success", "Order #123 paid successfully"
    )
    print(f"   Payment notification: {result2}")

    # Test order trigger
    print("\n🤖 Testing Order Trigger:")
    order_data = {
        "order_id": "test_123",
        "customer_name": "John Doe",
        "items": ["Coffee", "Croissant"],
        "total": 6.0,
    }
    result3 = bridge.trigger_order_action(order_data)
    print(f"   Order trigger: {result3}")

    # Test status update
    print("\n📊 Testing Status Update:")
    result4 = bridge.update_order_status("test_123", "paid")
    print(f"   Status update: {result4}")


def demo_full_workflow():
    """Demo full workflow dengan smart assistant"""
    print("\n🚀 Demo Full Workflow")
    print("=" * 50)

    # Initialize bot dengan smart assistant
    bot = EmojiBot(demo_mode=True)
    print(f"🤖 Bot initialized with smart assistant: {bot.smart_assistant.enabled}")

    # Test voice command order
    print("\n🎤 Processing Voice Order:")
    command = "Tolong pesankan ☕🥐 untuk saya Sarah"
    result = bot.process_voice_command(command, "Sarah")

    if "order_id" in result:
        print(f"✅ Order created: #{result['order_id']}")
        print(f"📦 Items: {result['items']}")
        print(f"💰 Total: ${result['total']}")

        # Update payment status
        print("\n💳 Updating Payment Status:")
        bot.update_payment_status_smart_assistant(result["order_id"], "paid")
        print("✅ Payment status updated")
    else:
        print(f"❌ Error: {result}")


def demo_api_endpoints():
    """Demo API endpoints usage"""
    print("\n🌐 Demo API Endpoints")
    print("=" * 50)

    print("📋 Available Smart Assistant Endpoints:")
    endpoints = [
        "POST /api/voice-command - Process voice commands",
        "POST /api/smart-order - Create order with smart assistant",
        "PUT /api/order/{order_id}/smart-status - Update order status",
        "GET /api/smart-assistant/status - Check connection status",
    ]

    for endpoint in endpoints:
        print(f"   {endpoint}")

    print("\n📝 Example API Usage:")
    print("curl -X POST http://localhost:8000/api/voice-command \\")
    print("  -H 'Content-Type: application/json' \\")
    print('  -d \'{"command": "pesan ☕🥐 untuk John", "customer_name": "John"}\'')


if __name__ == "__main__":
    print("🎉 OM1 Smart Assistant Integration Demo")
    print("=" * 60)

    try:
        demo_voice_commands()
        demo_smart_assistant_bridge()
        demo_full_workflow()
        demo_api_endpoints()

        print("\n✅ Demo completed successfully!")
        print("\n🚀 To start the server:")
        print("   python main.py")
        print("\n🌐 Then visit:")
        print("   http://localhost:8000/docs")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)
