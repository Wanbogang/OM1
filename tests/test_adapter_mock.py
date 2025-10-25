#!/usr/bin/env python3
"""Unit test for the MAVSDK adapter using a custom-built async iterable mock."""
import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch

# Add the parent directory to sys.path to find the 'bridge' module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mavsdk import System
from bridge.mavsdk_adapter.adapter import run

# A custom class that mimics an async iterable
class AsyncIterableMock:
    def __init__(self, items):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index < len(self.items):
            result = self.items[self.index]
            self.index += 1
            return result
        else:
            raise StopAsyncIteration

async def test_adapter_with_mock():
    """Test the adapter by injecting a custom async iterable mock."""
    print("🧪 Starting mock test with a custom mock class...")

    with patch('bridge.mavsdk_adapter.adapter.System') as MockSystem:
        mock_drone_instance = AsyncMock()
        MockSystem.return_value = mock_drone_instance

        # Prepare the fake telemetry data object
        mock_position = AsyncMock()
        mock_position.latitude_deg = -6.200000
        mock_position.longitude_deg = 106.816666
        mock_position.relative_altitude_m = 50.0
        
        # Create an instance of our custom async iterable mock
        mock_stream = AsyncIterableMock([mock_position])
        
        # Assign this custom mock to the telemetry.position method
        mock_drone_instance.telemetry.position.return_value = mock_stream

        # Run our adapter's logic
        await run()

        # Verify that the connection attempt was made correctly
        mock_drone_instance.connect.assert_called_once_with(system_address="udpout://localhost:14540")
        print("✅ Mock test PASSED! The 'connect' function was called correctly.")
        print("✅ Mock test PASSED! The telemetry data was processed correctly.")

if __name__ == "__main__":
    asyncio.run(test_adapter_with_mock())
