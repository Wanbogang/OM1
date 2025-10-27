#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
from std_msgs.msg import Header
import random

class GPSDriver(Node):
    def __init__(self):
        super().__init__('gps_driver')
        
        # Publisher
        self.gps_pub = self.create_publisher(NavSatFix, '/sensor/gps/fix', 10)
        
        # Timer untuk simulate GPS data
        self.timer = self.create_timer(1.0, self.publish_gps_data)  # 1 Hz
        
        # Default GPS coordinates (Bandung)
        self.base_lat = -6.9175
        self.base_lon = 107.6191
        self.base_alt = 10.0
        
        self.get_logger().info('GPS Driver Node Started')
        
    def publish_gps_data(self):
        """Simulate GPS data"""
        msg = NavSatFix()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'gps_link'
        
        # Add small random variation
        msg.latitude = self.base_lat + random.uniform(-0.0001, 0.0001)
        msg.longitude = self.base_lon + random.uniform(-0.0001, 0.0001)
        msg.altitude = self.base_alt + random.uniform(-0.5, 0.5)
        
        # GPS status
        msg.status.status = 0  # Fix available
        msg.status.service = 1  # GPS service
        
        # Covariance (dummy values)
        msg.position_covariance = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        msg.position_covariance_type = 1  # Diagonal known
        
        self.gps_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = GPSDriver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
