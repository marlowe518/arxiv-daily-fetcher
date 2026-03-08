"""
Tests for the configuration module.
"""

import tempfile
import unittest
from pathlib import Path

from src.config import TopicConfig, Config, load_config


class TestTopicConfig(unittest.TestCase):
    """Test the TopicConfig class."""
    
    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            'name': 'Test Topic',
            'queries': ['query1', 'query2'],
            'categories': ['cs.LG'],
            'description': 'A test topic'
        }
        
        topic = TopicConfig.from_dict(data)
        
        self.assertEqual(topic.name, 'Test Topic')
        self.assertEqual(topic.queries, ['query1', 'query2'])
        self.assertEqual(topic.categories, ['cs.LG'])
        self.assertEqual(topic.description, 'A test topic')
    
    def test_from_dict_minimal(self):
        """Test creating from minimal dictionary."""
        data = {
            'name': 'Test Topic',
            'queries': [],
            'categories': []
        }
        
        topic = TopicConfig.from_dict(data)
        
        self.assertEqual(topic.name, 'Test Topic')
        self.assertEqual(topic.queries, [])
        self.assertEqual(topic.categories, [])
        self.assertIsNone(topic.description)


class TestConfig(unittest.TestCase):
    """Test the Config class."""
    
    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            'max_results_per_topic': 10,
            'lookback_days': 5,
            'topics': [
                {
                    'name': 'Topic 1',
                    'queries': ['q1'],
                    'categories': ['cs.LG']
                },
                {
                    'name': 'Topic 2',
                    'queries': ['q2'],
                    'categories': ['cs.AI']
                }
            ]
        }
        
        config = Config.from_dict(data)
        
        self.assertEqual(config.max_results_per_topic, 10)
        self.assertEqual(config.lookback_days, 5)
        self.assertEqual(len(config.topics), 2)
    
    def test_from_dict_defaults(self):
        """Test default values."""
        data = {
            'topics': [
                {'name': 'Topic 1', 'queries': ['q1'], 'categories': []}
            ]
        }
        
        config = Config.from_dict(data)
        
        self.assertEqual(config.max_results_per_topic, 20)
        self.assertIsNone(config.lookback_days)  # Default is None (disabled)
    
    def test_validate_valid(self):
        """Test validation with valid config."""
        config = Config(
            topics=[
                TopicConfig(name='Test', queries=['q1'], categories=['cs.LG'])
            ]
        )
        
        errors = config.validate()
        
        self.assertEqual(errors, [])
    
    def test_validate_no_topics(self):
        """Test validation with no topics."""
        config = Config(topics=[])
        
        errors = config.validate()
        
        self.assertIn("No topics configured", errors)
    
    def test_validate_missing_name(self):
        """Test validation with missing topic name."""
        config = Config(
            topics=[TopicConfig(name='', queries=['q1'], categories=[])]
        )
        
        errors = config.validate()
        
        self.assertTrue(any('Missing name' in e for e in errors))
    
    def test_validate_no_query_or_category(self):
        """Test validation with neither query nor category."""
        config = Config(
            topics=[TopicConfig(name='Test', queries=[], categories=[])]
        )
        
        errors = config.validate()
        
        self.assertTrue(any('query or category' in e for e in errors))
    
    def test_validate_invalid_max_results(self):
        """Test validation with invalid max_results."""
        config = Config(
            topics=[TopicConfig(name='Test', queries=['q1'], categories=[])],
            max_results_per_topic=0
        )
        
        errors = config.validate()
        
        self.assertTrue(any('max_results_per_topic' in e for e in errors))


class TestLoadConfig(unittest.TestCase):
    """Test the load_config function."""
    
    def test_load_valid_config(self):
        """Test loading a valid config file."""
        yaml_content = """
max_results_per_topic: 10
lookback_days: 5
topics:
  - name: Test Topic
    queries:
      - "machine learning"
    categories:
      - cs.LG
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            
            self.assertEqual(config.max_results_per_topic, 10)
            self.assertEqual(len(config.topics), 1)
            self.assertEqual(config.topics[0].name, 'Test Topic')
        finally:
            Path(temp_path).unlink()
    
    def test_load_nonexistent_file(self):
        """Test loading non-existent file."""
        with self.assertRaises(FileNotFoundError):
            load_config('/nonexistent/path.yaml')
    
    def test_load_invalid_yaml(self):
        """Test loading invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("not valid yaml: [{")
            temp_path = f.name
        
        try:
            with self.assertRaises(ValueError):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()


if __name__ == '__main__':
    unittest.main()
