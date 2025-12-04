import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import requests

from .singleton import singleton


@dataclass
class BatteryStatus:
    """
    Data class to represent the battery status of a teleops system.
    """

    battery_level: float
    temperature: float
    voltage: float
    timestamp: str
    charging_status: bool = False

    def to_dict(self) -> dict:
        """
        Convert the BatteryStatus object to a dictionary.
        """
        return {
            "battery_level": self.battery_level,
            "charging_status": self.charging_status,
            "temperature": self.temperature,
            "voltage": self.voltage,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BatteryStatus":
        """
        Populate the BatteryStatus object from a dictionary.
        """
        return cls(
            battery_level=data.get("battery_level", 0.0),
            charging_status=data.get("charging_status", False),
            temperature=data.get("temperature", 0.0),
            voltage=data.get("voltage", 0.0),
            timestamp=data.get("timestamp", time.time()),
        )


@dataclass
class CommandStatus:
    """
    Data class to represent the command status of a teleops system.
    """

    vx: float
    vy: float
    vyaw: float
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "vx": self.vx,
            "vy": self.vy,
            "vyaw": self.vyaw,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CommandStatus":
        return cls(
            vx=data.get("vx", 0.0),
            vy=data.get("vy", 0.0),
            vyaw=data.get("vyaw", 0.0),
            timestamp=data.get("timestamp", time.time()),
        )


class ActionType(Enum):
    AI = "AI"
    TELEOPS = "TELEOPS"
    CONTROLLER = "CONTROLLER"


@dataclass
class ActionStatus:
    action: ActionType
    timestamp: float

    def to_dict(self) -> dict:
        return {
            "action": self.action.value,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ActionStatus":
        return cls(
            action=ActionType(data.get("action", ActionType.AI.value)),
            timestamp=data.get("timestamp", time.time()),
        )


@dataclass
class TeleopsStatus:
    update_time: str
    battery_status: BatteryStatus
    action_status: ActionStatus = field(
        default_factory=lambda: ActionStatus(ActionType.AI, time.time())
    )
    machine_name: str = "unknown"
    video_connected: bool = False

    def to_dict(self) -> dict:
        return {
            "machine_name": self.machine_name,
            "update_time": self.update_time,
            "battery_status": self.battery_status.to_dict(),
            "action_status": self.action_status.to_dict(),
            "video_connected": self.video_connected,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TeleopsStatus":
        return cls(
            update_time=data.get("update_time", time.time()),
            battery_status=BatteryStatus.from_dict(data.get("battery_status", {})),
            action_status=ActionStatus.from_dict(data.get("action_status", {})),
            machine_name=data.get("machine_name", "unknown"),
            video_connected=data.get("video_connected", False),
        )


@singleton
class TeleopsStatusProvider:
    """
    Teleops Status provider reports the status of the machine.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openmind.org/api/core/teleops/status",
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.executor = ThreadPoolExecutor(max_workers=1)

    def get_status(self) -> dict:
        if self.api_key is None or self.api_key == "":
            logging.error("API key is missing. Cannot get status.")
            return {}

        api_key_id = self.api_key[9:25] if len(self.api_key) > 25 else self.api_key
        request = requests.get(
            f"{self.base_url}/{api_key_id}",
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        if request.status_code == 200:
            return request.json()
        else:
            logging.error(
                f"Failed to get status: {request.status_code} - {request.text}"
            )
            return {}

    def _share_status_worker(self, status: TeleopsStatus):
        """
        Worker function to share the status of the machine.
        This function runs in a separate thread to avoid blocking the main thread.
        """
        if self.api_key is None or self.api_key == "":
            logging.error("API key is missing. Cannot share status.")
            return

        try:
            request = requests.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=status.to_dict(),
                timeout=5,
            )

            if request.status_code == 200:
                logging.debug(f"Status shared successfully: {request.json()}")
            else:
                logging.error(
                    f"Failed to share status: {request.status_code} - {request.text}"
                )
        except Exception as e:
            logging.error(f"Error sharing status: {str(e)}")

    def share_status(self, status: TeleopsStatus):
        """
        Share the status of the machine.
        """
        self.executor.submit(self._share_status_worker, status)
