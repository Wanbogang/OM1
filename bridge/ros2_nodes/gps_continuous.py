#!/usr/bin/env python3
import time
import random
from datetime import datetime

class MockPublisher:
    def __init__(self, topic_name):
        self.topic_name = topic_name
    def publish(self, msg):
        if hasattr(msg, 'data'):
            print(f'[/gps/fix] Publishing: GPS(lat={msg.latitude:.6f}, lon={msg.longitude:.6f}, alt={msg.altitude:.1f}m)')

class MockNavSatFix:
    def __init__(self):
        self.latitude = -6.2088
        self.longitude = 106.8456
        self.altitude = 100.0

gps_pub = MockPublisher('/gps/fix')
print('🛰️ GPS Driver started (continuous mode)...')

while True:
    gps = MockNavSatFix()
    gps.latitude += (random.random() - 0.5) * 0.0001
    gps.longitude += (random.random() - 0.5) * 0.0001
    gps.altitude += (random.random() - 0.5) * 2.0
    gps_pub.publish(gps)
    time.sleep(0.1)  # 10Hz
