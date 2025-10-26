#!/usr/bin/env python3
"""
Unit Test for MAVSDK Adapter with Mocking
Tests the adapter logic without requiring actual drone hardware
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os
import sys

# Add the bridge directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../bridge/mavsdk_adapter'))

from server_writer import MAVSDKWriter
from server_reader import MAVSDKReader

class TestMAVSDKAdapter(unittest.TestCase):
    """Test MAVSDK Adapter functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.command_file = self.temp_file.name
        
    def tearDown(self):
        """Cleanup test environment"""
        if os.path.exists(self.command_file):
            os.unlink(self.command_file)
    
    def test_writer_initialization(self):
        """Test MAVSDK Writer initialization"""
        writer = MAVSDKWriter(self.command_file)
        
        # Check if command file is created
        self.assertTrue(os.path.exists(self.command_file))
        
        # Check initial file content
        with open(self.command_file, 'r') as f:
            data = json.load(f)
        
        self.assertIn('commands', data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'ready')
        self.assertEqual(len(data['commands']), 0)
    
    def test_command_validation(self):
        """Test command validation"""
        writer = MAVSDKWriter(self.command_file)
        
        # Valid command
        valid_cmd = {
            'type': 'goto',
            'agent': 'perception',
            'latitude': -6.1751,
            'longitude': 106.8650
        }
        self.assertTrue(writer._validate_command(valid_cmd))
        
        # Invalid command - missing type
        invalid_cmd1 = {
            'agent': 'perception',
            'latitude': -6.1751,
            'longitude': 106.8650
        }
        self.assertFalse(writer._validate_command(invalid_cmd1))
        
        # Invalid command - missing agent
        invalid_cmd2 = {
            'type': 'goto',
            'latitude': -6.1751,
            'longitude': 106.8650
        }
        self.assertFalse(writer._validate_command(invalid_cmd2))
        
        # Invalid command - invalid type
        invalid_cmd3 = {
            'type': 'invalid_type',
            'agent': 'perception'
        }
        self.assertFalse(writer._validate_command(invalid_cmd3))
        
        # Invalid command - goto missing coordinates
        invalid_cmd4 = {
            'type': 'goto',
            'agent': 'perception'
        }
        self.assertFalse(writer._validate_command(invalid_cmd4))
    
    def test_write_command(self):
        """Test writing commands to file"""
        writer = MAVSDKWriter(self.command_file)
        
        command = {
            'type': 'goto',
            'agent': 'perception',
            'latitude': -6.1751,
            'longitude': 106.8650
        }
        
        # Write command
        writer._write_command({
            'id': 1,
            'timestamp': '2024-01-01T00:00:00',
            'command': command,
            'status': 'pending'
        })
        
        # Check file content
        with open(self.command_file, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(len(data['commands']), 1)
        self.assertEqual(data['commands'][0]['command']['type'], 'goto')
        self.assertEqual(data['commands'][0]['status'], 'pending')

if __name__ == '__main__':
    print("🧪 Running MAVSDK Adapter Unit Tests")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestMAVSDKAdapter))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("🎉 All tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed")
    
    print(f"Tests run: {result.testsRun}")
    print("=" * 50)
