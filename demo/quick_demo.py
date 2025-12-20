#!/usr/bin/env python3
"""
Emoji Order Assistant - Quick Demo
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from emoji_order.integrations.messaging_bot import bot

console = Console()


def print_banner():
    console.print(
        Panel.fit(
            "[bold cyan]🎉 Emoji Order Assistant Demo[/bold cyan]\n"
            "[green]Order food with just emojis! 🚀[/green]",
            border_style="cyan",
        )
    )


def show_menu():
    table = Table(title="📋 Emoji Menu")
    table.add_column("Emoji", style="cyan", no_wrap=True)
    table.add_column("Item", style="magenta")
    table.add_column("Price", style="green")

    table.add_row("☕", "Coffee", "$3.50")
    table.add_row("☕☕", "Large Coffee", "$5.00")
    table.add_row("🍕", "Pizza", "$12.00")
    table.add_row("🥗", "Salad", "$8.00")
    table.add_row("🥤", "Smoothie", "$6.00")
    table.add_row("", "", "")
    table.add_row("🚀", "Express (+$2.00)", "")
    table.add_row("📍", "Delivery (+$3.00)", "")
    table.add_row("💪", "Protein Boost (+$2.50)", "")

    console.print(table)


def demo_order(emoji_string: str, user_id: str = "demo_user"):
    console.print(f"\n[bold yellow]📱 Testing: {emoji_string}[/bold yellow]")

    result = bot.process_message(emoji_string, user_id)

    if result["success"]:
        console.print(
            Panel.fit(
                result["response"], title="✅ Order Created", border_style="green"
            )
        )

        # Simulate payment
        console.print("\n[cyan]💳 Simulating payment...[/cyan]")
        import time

        time.sleep(2)

        console.print("[green]✅ Payment confirmed![/green]")
        console.print("[green]👨‍🍳 Order is being prepared...[/green]")
        time.sleep(2)
        console.print("[green]🎉 Order ready for pickup![/green]")

    else:
        console.print(
            Panel.fit(result["response"], title="❌ Order Failed", border_style="red")
        )


def main():
    print_banner()
    show_menu()

    # Demo orders
    demo_orders = [
        "☕",  # Simple coffee
        "🍕🚀",  # Express pizza
        "🥗💪📍",  # Salad with protein + delivery
        "❌",  # Invalid emoji
        "🥤☕☕",  # Multiple items
    ]

    for order in demo_orders:
        demo_order(order)
        console.print("\n" + "=" * 50 + "\n")

    console.print(
        Panel.fit(
            "[bold green]🎉 Demo Complete![/bold green]\n"
            "[cyan]Try it yourself: Send any emoji combination![/cyan]\n"
            "[yellow]Ready for Home Assistant integration! 🏠[/yellow]",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()
