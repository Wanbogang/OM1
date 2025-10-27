from setuptools import setup

package_name = 'smartfarm_ros2_nodes'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='SmartFarm Developer',
    maintainer_email='developer@smartfarm.com',
    description='ROS2 nodes for Smart Farm drone system',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
    'console_scripts': [
        'mavlink_bridge = smartfarm_ros2_nodes.mavlink_bridge.mavlink_bridge:main',
        'camera_driver = smartfarm_ros2_nodes.camera_driver:main',
        'gps_driver = smartfarm_ros2_nodes.gps_driver:main',
        'multispectral_driver = smartfarm_ros2_nodes.multispectral_driver:main',
        'sprayer_controller = smartfarm_ros2_nodes.sprayer_controller:main',
    ],
},
