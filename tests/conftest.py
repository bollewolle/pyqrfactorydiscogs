"""
Pytest configuration and shared fixtures for the Discogs Collection to QR Factory CSV Generator tests.

This file contains shared fixtures and configuration that can be used across all test files.
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_discogs_client():
    """Fixture for creating a mocked DiscogsCollectionClient"""
    from services.discogs_api_client import DiscogsCollectionClient
    
    # Create client with test credentials
    client = DiscogsCollectionClient(
        consumer_key="test_key",
        consumer_secret="test_secret"
    )
    
    return client


@pytest.fixture
def mock_discogs_collection_processor():
    """Fixture for creating a DiscogsCollectionProcessor instance"""
    from services.discogs_collection_processor import DiscogsCollectionProcessor
    
    return DiscogsCollectionProcessor()


@pytest.fixture
def mock_release_data():
    """Fixture providing sample release data for testing"""
    return [
        {
            'id': 100,
            'title': 'Album One',
            'artist': 'Artist One',
            'year': 2020,
            'format': [{'name': 'Vinyl', 'qty': '1'}],
            'label': 'Label One',
            'url': 'https://www.discogs.com/release/100-Artist-One-Album-One'
        },
        {
            'id': 101,
            'title': 'Album Two',
            'artist': 'Artist Two',
            'year': 2021,
            'format': [{'name': 'CD', 'qty': '1'}],
            'label': 'Label Two',
            'url': 'https://www.discogs.com/release/101-Artist-Two-Album-Two'
        }
    ]


@pytest.fixture
def mock_folders():
    """Fixture providing mock collection folders"""
    return [
        Mock(id=1, name="Favorites"),
        Mock(id=2, name="Vinyl Collection"),
        Mock(id=3, name="Digital Music")
    ]


@pytest.fixture
def flask_test_client():
    """Fixture for Flask test client"""
    from app import create_app
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        yield client