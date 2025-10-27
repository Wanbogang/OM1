#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from std_msgs.msg import Header
import cv2
import numpy as np

class CameraDriver(Node):
    def __init__(self):
        super().__init__('camera_driver')
        
        # Publishers
        self.image_pub = self.create_publisher(Image, '/sensor/camera/image_raw', 10)
        self.camera_info_pub = self.create_publisher(CameraInfo, '/sensor/camera/camera_info', 10)
        
        # Timer untuk simulate camera capture
        self.timer = self.create_timer(0.1, self.capture_image)  # 10 FPS
        
        self.get_logger().info('Camera Driver Node Started')
        
    def capture_image(self):
        """Simulate image capture"""
        # Create dummy image (bisa diganti dengan real camera)
        height, width = 480, 640
        image_data = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
        
        # Create ROS2 Image message
        msg = Image()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera_link'
        msg.height = height
        msg.width = width
        msg.encoding = 'bgr8'
        msg.is_bigendian = False
        msg.step = width * 3
        msg.data = image_data.tobytes()
        
        self.image_pub.publish(msg)
        
        # Publish camera info
        camera_info = CameraInfo()
        camera_info.header = msg.header
        camera_info.height = height
        camera_info.width = width
        camera_info.distortion_model = 'plumb_bob'
        camera_info.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        camera_info.k = [500.0, 0.0, 320.0, 0.0, 500.0, 240.0, 0.0, 0.0, 1.0]
        camera_info.p = [500.0, 0.0, 320.0, 0.0, 0.0, 500.0, 240.0, 0.0, 0.0, 0.0, 1.0, 0.0]
        
        self.camera_info_pub.publish(camera_info)

def main(args=None):
    rclpy.init(args=args)
    node = CameraDriver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
