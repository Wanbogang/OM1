#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Header, Float32
from geometry_msgs.msg import PolygonStamped, Point32
import json
import time
import threading

class SprayerController(Node):
    def __init__(self):
        super().__init__('sprayer_controller')
        
        # Subscribers
        self.command_sub = self.create_subscription(String, '/sprayer/command', self.command_callback, 10)
        self.polygon_sub = self.create_subscription(PolygonStamped, '/sprayer/polygon', self.polygon_callback, 10)
        
        # Publishers
        self.status_pub = self.create_publisher(String, '/sprayer/status', 10)
        self.flow_rate_pub = self.create_publisher(Float32, '/sprayer/flow_rate', 10)
        
        # Sprayer state
        self.is_spraying = False
        self.current_flow_rate = 0.0
        self.target_polygon = None
        self.spray_thread = None
        
        self.get_logger().info('Sprayer Controller Node Started')
        
    def command_callback(self, msg):
        """Handle sprayer commands"""
        try:
            command = json.loads(msg.data)
            cmd_type = command.get('command', '')
            
            if cmd_type == 'start':
                self.start_spraying(command)
            elif cmd_type == 'stop':
                self.stop_spraying()
            elif cmd_type == 'set_flow':
                self.set_flow_rate(command.get('flow_rate', 0.0))
            elif cmd_type == 'status':
                self.publish_status()
            else:
                self.get_logger().warn(f'Unknown command: {cmd_type}')
                
        except json.JSONDecodeError:
            self.get_logger().error('Invalid JSON command')
            
    def polygon_callback(self, msg):
        """Handle spray polygon area"""
        self.target_polygon = msg
        self.get_logger().info(f'Received spray polygon with {len(msg.polygon.points)} points')
        
    def start_spraying(self, command):
        """Start spraying operation"""
        if self.is_spraying:
            self.get_logger().warn('Sprayer already running')
            return
            
        flow_rate = command.get('flow_rate', 1.0)
        duration = command.get('duration', 10.0)
        
        self.is_spraying = True
        self.current_flow_rate = flow_rate
        
        # Start spray thread
        self.spray_thread = threading.Thread(target=self.spray_operation, args=(duration,))
        self.spray_thread.start()
        
        status = {
            'status': 'started',
            'flow_rate': flow_rate,
            'duration': duration,
            'timestamp': time.time()
        }
        self.status_pub.publish(String(data=json.dumps(status)))
        self.flow_rate_pub.publish(Float32(data=flow_rate))
        
        self.get_logger().info(f'Started spraying at {flow_rate} L/min for {duration}s')
        
    def stop_spraying(self):
        """Stop spraying operation"""
        if not self.is_spraying:
            self.get_logger().warn('Sprayer not running')
            return
            
        self.is_spraying = False
        self.current_flow_rate = 0.0
        
        status = {
            'status': 'stopped',
            'timestamp': time.time()
        }
        self.status_pub.publish(String(data=json.dumps(status)))
        self.flow_rate_pub.publish(Float32(data=0.0))
        
        self.get_logger().info('Stopped spraying')
        
    def set_flow_rate(self, flow_rate):
        """Set spray flow rate"""
        self.current_flow_rate = max(0.0, min(10.0, flow_rate))  # Limit 0-10 L/min
        
        if self.is_spraying:
            self.flow_rate_pub.publish(Float32(data=self.current_flow_rate))
            
        status = {
            'status': 'flow_rate_set',
            'flow_rate': self.current_flow_rate,
            'timestamp': time.time()
        }
        self.status_pub.publish(String(data=json.dumps(status)))
        
        self.get_logger().info(f'Flow rate set to {self.current_flow_rate} L/min')
        
    def spray_operation(self, duration):
        """Execute spray operation"""
        self.get_logger().info(f'Spraying for {duration} seconds...')
        
        start_time = time.time()
        while time.time() - start_time < duration and self.is_spraying:
            time.sleep(0.1)  # Check every 100ms
            
        if self.is_spraying:
            self.stop_spraying()
            
    def publish_status(self):
        """Publish current sprayer status"""
        status = {
            'is_spraying': self.is_spraying,
            'flow_rate': self.current_flow_rate,
            'has_target_polygon': self.target_polygon is not None,
            'timestamp': time.time()
        }
        self.status_pub.publish(String(data=json.dumps(status)))

def main(args=None):
    rclpy.init(args=args)
    node = SprayerController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
