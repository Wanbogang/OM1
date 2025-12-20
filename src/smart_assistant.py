import logging
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)


class SmartAssistantBridge:
    """Bridge untuk menghubungkan OM1 dengan Smart Assistant (Home Assistant)"""

    def __init__(self, ha_url: str = None, ha_token: str = None):
        self.ha_url = ha_url
        self.ha_token = ha_token
        self.enabled = ha_url and ha_token

    def send_notification(self, title: str, message: str) -> bool:
        """Kirim notifikasi ke Home Assistant"""
        if not self.enabled:
            logger.info(f"Mock notification: {title} - {message}")
            return True

        try:
            url = f"{self.ha_url}/api/services/notify/notify"
            headers = {
                "Authorization": f"Bearer {self.ha_token}",
                "Content-Type": "application/json",
            }
            data = {"title": title, "message": message}

            response = requests.post(url, headers=headers, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send HA notification: {e}")
            return False

    def trigger_order_action(self, order_data: Dict[str, Any]) -> bool:
        """Trigger order action di Home Assistant"""
        if not self.enabled:
            logger.info(f"Mock order trigger: {order_data}")
            return True

        try:
            url = f"{self.ha_url}/api/services/automation/trigger"
            headers = {
                "Authorization": f"Bearer {self.ha_token}",
                "Content-Type": "application/json",
            }
            data = {
                "entity_id": "automation.om1_order_received",
                "variables": order_data,
            }

            response = requests.post(url, headers=headers, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to trigger HA automation: {e}")
            return False

    def update_order_status(self, order_id: str, status: str) -> bool:
        """Update order status di Home Assistant"""
        if not self.enabled:
            logger.info(f"Mock status update: Order {order_id} - {status}")
            return True

        try:
            url = f"{self.ha_url}/api/states/input_text.om1_order_{order_id}_status"
            headers = {
                "Authorization": f"Bearer {self.ha_token}",
                "Content-Type": "application/json",
            }
            data = {
                "state": status,
                "attributes": {
                    "friendly_name": f"OM1 Order {order_id} Status",
                    "order_id": order_id,
                },
            }

            response = requests.post(url, headers=headers, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to update HA status: {e}")
            return False


class VoiceCommandProcessor:
    """Processor untuk voice command dari smart assistant"""

    def __init__(self):
        self.command_patterns = {
            "order": ["order", "pesan", "beli", "buatkan"],
            "status": ["status", "cek", "lihat"],
            "cancel": ["cancel", "batal", "hapus"],
        }

    def process_voice_command(self, command: str) -> Dict[str, Any]:
        """Process voice command dan ekstrak intent"""
        command_lower = command.lower()

        # Detect intent
        intent = None
        for key, patterns in self.command_patterns.items():
            if any(pattern in command_lower for pattern in patterns):
                intent = key
                break

        # Extract emojis from command
        emojis = "".join([char for char in command if ord(char) > 127])

        # Extract customer name (simple pattern matching)
        name = self._extract_name(command)

        return {
            "intent": intent,
            "emojis": emojis,
            "customer_name": name,
            "raw_command": command,
        }

    def _extract_name(self, command: str) -> str:
        """Extract customer name dari command"""
        # Simple implementation - bisa dikembangkan
        name_patterns = ["nama saya", "name is", "saya", "my name is"]

        for pattern in name_patterns:
            if pattern.lower() in command.lower():
                parts = command.split(pattern)
                if len(parts) > 1 and parts[1].strip():
                    words = parts[1].strip().split()
                    if words:
                        return words[0]

        return "Customer"
