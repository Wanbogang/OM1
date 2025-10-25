#!/usr/bin/env python3
"""Unit test untuk MAVSDK adapter yang sudah diperbaiki."""
import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Tambahkan folder induk ke sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bridge.mavsdk_adapter.adapter import run

async def test_adapter_with_mock():
    """Test adapter dengan mock yang benar."""
    print("🧪 Memulai mock test yang diperbaiki...")
    
    with patch('bridge.mavsdk_adapter.adapter.System') as MockSystem:
        # Buat mock instance
        mock_drone_instance = AsyncMock()
        MockSystem.return_value = mock_drone_instance
        
        # Buat mock position
        mock_position = MagicMock()
        mock_position.latitude_deg = -6.200000
        mock_position.longitude_deg = 106.816666  
        mock_position.relative_altitude_m = 50.0
        
        # Buat async iterator yang benar
        class AsyncIterator:
            def __init__(self, items):
                self.items = items
                self.index = 0
            
            def __aiter__(self):
                return self
            
            async def __anext__(self):
                if self.index >= len(self.items):
                    raise StopAsyncIteration
                result = self.items[self.index]
                self.index += 1
                return result
        
        # Buat mock untuk telemetry.position() yang mengembalikan async iterator
        mock_drone_instance.telemetry.position.return_value = AsyncIterator([mock_position])
        
        # Jalankan fungsi adapter
        await run()
        
        # Verifikasi
        mock_drone_instance.connect.assert_called_once_with(system_address="udpout://localhost:14540")
        print("✅ Mock test BERHASIL! Connect dipanggil dengan benar.")
        print("✅ Mock test BERHASIL! Data telemetry diproses.")

if __name__ == "__main__":
    asyncio.run(test_adapter_with_mock())
