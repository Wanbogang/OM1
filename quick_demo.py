#!/usr/bin/env python3
"""
Quick Demo Script for Emoji Order Assistant
Run this script to see the emoji ordering system in action!
"""

import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.emoji_bot import EmojiBot


def main():
    """Main demo function."""
    print("🚀 Starting Emoji Order Assistant Demo...")
    print("=" * 50)

    # Create the bot in demo mode
    bot = EmojiBot(demo_mode=True)

    # Display menu
    print("\n📋 Available Menu Items:")
    for emoji, item in bot.emoji_processor.emoji_to_item.items():
        print(f"  {emoji} {item.name} - ${item.price:.2f}")

    print("\n" + "=" * 50)
    print("🎯 Demo: Processing some sample orders...")
    print("=" * 50)

    # Sample orders to demonstrate the system
    sample_orders = [
        ("☕🥐", "Coffee Lover"),
        ("🍕🥤", "Quick Lunch"),
        ("🍣🧋", "Asian Fusion"),
        ("🥪🍪", "Light Meal"),
        ("🍔🥗🥤", "Healthy Combo"),
    ]

    for i, (emojis, customer) in enumerate(sample_orders, 1):
        print(f"\n📝 Order #{i}: {emojis} (Customer: {customer})")
        print("-" * 30)

        # Process the order
        result = bot.process_emoji_order(emojis, customer)

        if result["success"]:
            order = result["order"]
            print("✅ Order Created Successfully!")
            print(f"   Order ID: {order.id}")
            print(f"   Customer: {order.customer_name}")
            print(f"   Status: {order.status.value}")

            # Show items
            item_counts = {}
            for item in order.items:
                if item.emoji in item_counts:
                    item_counts[item.emoji] = (item_counts[item.emoji][0] + 1, item)
                else:
                    item_counts[item.emoji] = (1, item)

            print("   Items:")
            for emoji, (count, item) in item_counts.items():
                print(f"     {emoji}x{count} {item.name} - ${item.price * count:.2f}")

            print(f"   Total: ${order.total_amount:.2f}")
            if result.get("payment_url"):
                print(f"   Payment URL: {result['payment_url']}")
        else:
            print(f"❌ Error: {result['error']}")

    print("\n" + "=" * 50)
    print("📊 Order Statistics:")
    print("=" * 50)

    # Display statistics
    stats = bot.order_manager.get_statistics()
    print(f"Total Orders: {stats['total_orders']}")
    print(f"Total Revenue: ${stats['total_revenue']:.2f}")
    print(f"Average Order Value: ${stats['average_order_value']:.2f}")

    print("\nOrders by Status:")
    for status, count in stats["status_counts"].items():
        print(f"  {status.upper()}: {count}")

    print("\n" + "=" * 50)
    print("🎉 Demo completed! The Emoji Order Assistant is working perfectly!")
    print("💡 You can now start the API server with: python main.py")
    print("🌐 Then visit http://localhost:8000 to use the web interface!")
    print("=" * 50)


if __name__ == "__main__":
    main()
