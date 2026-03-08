"""
Configuration Module

Handles loading and validating the topics configuration file.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml


class TopicConfig:
    """Represents a single topic configuration."""
    
    def __init__(
        self,
        name: str,
        queries: List[str],
        categories: List[str],
        description: Optional[str] = None
    ):
        """
        Initialize topic configuration.
        
        Args:
            name: Topic name
            queries: List of search queries
            categories: List of arXiv categories
            description: Optional description
        """
        self.name = name
        self.queries = queries
        self.categories = categories
        self.description = description
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TopicConfig':
        """Create TopicConfig from dictionary."""
        return cls(
            name=data['name'],
            queries=data.get('queries', []),
            categories=data.get('categories', []),
            description=data.get('description')
        )


class Config:
    """Main configuration class."""
    
    def __init__(
        self,
        topics: List[TopicConfig],
        max_results_per_topic: int = 20,
        lookback_days: int = 7
    ):
        """
        Initialize configuration.
        
        Args:
            topics: List of topic configurations
            max_results_per_topic: Maximum papers to fetch per topic
            lookback_days: Only fetch papers from last N days
        """
        self.topics = topics
        self.max_results_per_topic = max_results_per_topic
        self.lookback_days = lookback_days
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Config':
        """Create Config from dictionary."""
        topics = [TopicConfig.from_dict(t) for t in data.get('topics', [])]
        return cls(
            topics=topics,
            max_results_per_topic=data.get('max_results_per_topic', 20),
            lookback_days=data.get('lookback_days', 7)
        )
    
    def validate(self) -> List[str]:
        """
        Validate the configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not self.topics:
            errors.append("No topics configured")
        
        for i, topic in enumerate(self.topics):
            if not topic.name:
                errors.append(f"Topic {i}: Missing name")
            if not topic.queries and not topic.categories:
                errors.append(f"Topic '{topic.name}': Must have at least one query or category")
        
        if self.max_results_per_topic < 1:
            errors.append("max_results_per_topic must be at least 1")
        
        if self.lookback_days < 1:
            errors.append("lookback_days must be at least 1")
        
        return errors


def load_config(config_path: str) -> Config:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to YAML config file
        
    Returns:
        Config object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid or YAML parsing fails
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML syntax: {e}")
    
    if not isinstance(data, dict):
        raise ValueError("Config file must contain a YAML dictionary")
    
    config = Config.from_dict(data)
    
    # Validate
    errors = config.validate()
    if errors:
        raise ValueError(f"Config validation errors: {'; '.join(errors)}")
    
    return config


def get_default_config_path() -> str:
    """Get the default configuration file path."""
    return os.path.join("config", "topics.yaml")
