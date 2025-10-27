#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Header, Float32MultiArray
import numpy as np

class MultispectralDriver(Node):
    def __init__(self):
        super().__init__('multispectral_driver')
        
        # Publishers
        self.ndvi_pub = self.create_publisher(Image, '/sensor/multispectral/ndvi', 10)
        self.spectral_pub = self.create_publisher(Float32MultiArray, '/sensor/multispectral/bands', 10)
        
        # Timer untuk simulate sensor data
        self.timer = self.create_timer(0.5, self.publish_spectral_data)  # 2 Hz
        
        self.get_logger().info('Multispectral Sensor Driver Node Started')
        
    def publish_spectral_data(self):
        """Simulate multispectral sensor data"""
        # Simulate spectral bands (RGB + NIR)
        bands = np.random.rand(4, 100, 100)  # 4 bands, 100x100 resolution
        
        # Calculate NDVI (NIR - Red) / (NIR + Red)
        nir = bands[3]
        red = bands[0]
        ndvi = (nir - red) / (nir + red + 0.001)  # Avoid division by zero
        
        # Publish spectral bands
        spectral_msg = Float32MultiArray()
        spectral_msg.data = bands.flatten().tolist()
        self.spectral_pub.publish(spectral_msg)
        
        # Publish NDVI as image
        ndvi_msg = Image()
        ndvi_msg.header = Header()
        ndvi_msg.header.stamp = self.get_clock().now().to_msg()
        ndvi_msg.header.frame_id = 'multispectral_link'
        ndvi_msg.height = 100
        ndvi_msg.width = 100
        ndvi_msg.encoding = '32FC1'
        ndvi_msg.is_bigendian = False
        ndvi_msg.step = 100 * 4
        ndvi_msg.data = ndvi.astype(np.float32).tobytes()
        
        self.ndvi_pub.publish(ndvi_msg)

def main(args=None):
    rclpy.init(args=args)
    node = MultispectralDriver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
