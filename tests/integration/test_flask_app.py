"""
Integration tests for Flask application.

Tests the Flask routes and application functionality.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestFlaskApp:
    """Test suite for Flask application"""

    def test_index_route(self, flask_test_client):
        """Test the index route"""
        response = flask_test_client.get('/')
        assert response.status_code == 200
        assert b'Discogs Collection to QR Factory CSV Generator' in response.data

    def test_health_check_route(self, flask_test_client):
        """Test the health check endpoint"""
        response = flask_test_client.get('/health')
        assert response.status_code == 200
        assert response.data == b'OK'

    def test_authenticate_route_empty_credentials(self, flask_test_client):
        """Test authentication with empty credentials"""
        response = flask_test_client.post('/authenticate', data={
            'consumer_key': '',
            'consumer_secret': ''
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Consumer key and secret are required' in response.data

    def test_authenticate_route_valid_credentials(self, flask_test_client):
        """Test authentication with valid credentials"""
        with patch('app.routes.DiscogsCollectionClient') as mock_client_class:
            # Mock the client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Mock authentication
            mock_client.authenticate.return_value = None
            mock_client.user = MagicMock()
            mock_client.user.username = "test_user"
            
            response = flask_test_client.post('/authenticate', data={
                'consumer_key': 'test_key',
                'consumer_secret': 'test_secret'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            # Should redirect to folders page after successful authentication
            assert b'Collection Folders' in response.data or b'folders' in response.data

    def test_folders_route_unauthenticated(self, flask_test_client):
        """Test folders route when not authenticated"""
        response = flask_test_client.get('/folders')
        # Should redirect to index
        assert response.status_code == 302

    def test_folders_route_authenticated(self, flask_test_client):
        """Test folders route when authenticated"""
        with flask_test_client.session_transaction() as sess:
            sess['authenticated'] = True
            sess['consumer_key'] = 'test_key'
            sess['consumer_secret'] = 'test_secret'
        
        with patch('app.routes.DiscogsCollectionClient') as mock_client_class:
            # Mock the client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Mock folder retrieval
            mock_folder1 = MagicMock()
            mock_folder1.id = 1
            mock_folder1.name = "Favorites"
            
            mock_folder2 = MagicMock()
            mock_folder2.id = 2
            mock_folder2.name = "Vinyl Collection"
            
            mock_client.get_collection_folders.return_value = [mock_folder1, mock_folder2]
            
            response = flask_test_client.get('/folders')
            assert response.status_code == 200
            assert b'Favorites' in response.data
            assert b'Vinyl Collection' in response.data

    def test_releases_route_unauthenticated(self, flask_test_client):
        """Test releases route when not authenticated"""
        response = flask_test_client.get('/releases/1')
        # Should redirect to index
        assert response.status_code == 302

    def test_releases_route_authenticated(self, flask_test_client):
        """Test releases route when authenticated"""
        with flask_test_client.session_transaction() as sess:
            sess['authenticated'] = True
            sess['consumer_key'] = 'test_key'
            sess['consumer_secret'] = 'test_secret'
        
        with patch('app.routes.DiscogsCollectionClient') as mock_client_class:
            # Mock the client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Mock release retrieval
            mock_release_data = {
                0: {
                    'id': 100,
                    'title': 'Album One',
                    'artist': 'Artist One',
                    'year': 2020,
                    'format': [{'name': 'Vinyl', 'qty': '1'}],
                    'label': 'Label One',
                    'url': 'https://www.discogs.com/release/100-Artist-One-Album-One'
                }
            }
            
            mock_client.get_collection_releases_by_folder.return_value = mock_release_data
            
            response = flask_test_client.get('/releases/1')
            assert response.status_code == 200
            assert b'Album One' in response.data
            assert b'Artist One' in response.data

    def test_generate_csv_route(self, flask_test_client):
        """Test CSV generation route"""
        with flask_test_client.session_transaction() as sess:
            sess['authenticated'] = True
            sess['consumer_key'] = 'test_key'
            sess['consumer_secret'] = 'test_secret'
        
        # Mock form data
        test_data = {
            'release_ids': ['100', '101'],
            'sort_by': 'year',
            'sort_order': 'desc'
        }
        
        with patch('app.routes.DiscogsCollectionClient') as mock_client_class, \
             patch('app.routes.DiscogsCollectionProcessor') as mock_processor_class:
            
            # Mock the client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Mock the processor
            mock_processor = MagicMock()
            mock_processor_class.return_value = mock_processor
            
            # Mock release data
            mock_release_data = [
                {
                    'id': 100,
                    'title': 'Album One',
                    'artist': 'Artist One',
                    'year': 2020,
                    'format': [{'name': 'Vinyl', 'qty': '1'}],
                    'label': 'Label One',
                    'url': 'https://www.discogs.com/release/100-Artist-One-Album-One'
                }
            ]
            
            def get_release_mock(rid):
                return next((r for r in mock_release_data if r['id'] == rid), None)
            
            mock_client.get_release_by_releaseid.side_effect = get_release_mock
            
            # Mock extracted info
            mock_processor.extract_release_info.return_value = [
                {
                    'artist': 'Artist One',
                    'title': 'Album One',
                    'url': 'https://www.discogs.com/release/100-Artist-One-Album-One'
                }
            ]
            
            response = flask_test_client.post('/generate-csv', data=test_data)
            
            # Should return CSV file
            assert response.status_code == 200
            assert response.content_type == 'text/csv'
            assert 'attachment; filename=discogs_collection.csv' in response.headers.get('Content-Disposition', '')