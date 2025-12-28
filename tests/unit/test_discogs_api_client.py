"""
Unit tests for DiscogsCollectionClient class.

Tests the authentication, folder retrieval, and release retrieval functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from services.discogs_api_client import DiscogsCollectionClient


class TestDiscogsCollectionClient:
    """Test suite for DiscogsCollectionClient"""

    def test_initialization(self):
        """Test client initialization with valid credentials"""
        client = DiscogsCollectionClient(
            consumer_key="test_key",
            consumer_secret="test_secret",
            useragent="pyqrfactorydiscogs/1.0"
        )
        
        assert client.consumer_key == "test_key"
        assert client.consumer_secret == "test_secret"
        assert client.useragent == "pyqrfactorydiscogs/1.0"
        assert client.oauth_token is None
        assert client.oauth_token_secret is None
        assert client.client is None
        assert client.user is None

    def test_initialization_with_tokens(self):
        """Test client initialization with OAuth tokens"""
        client = DiscogsCollectionClient(
            consumer_key="test_key",
            consumer_secret="test_secret",
            useragent="pyqrfactorydiscogs/1.0",
            oauth_token="test_token",
            oauth_token_secret="test_token_secret"
        )
        
        assert client.oauth_token == "test_token"
        assert client.oauth_token_secret == "test_token_secret"

    def test_initialization_invalid_credentials(self):
        """Test client initialization with invalid credential types"""
        with pytest.raises(ValueError):
            DiscogsCollectionClient(123, "test_secret", "useragent")
        
        with pytest.raises(ValueError):
            DiscogsCollectionClient("test_key", 456, "useragent")

    @patch('services.discogs_api_client.os.getenv')
    @patch('services.discogs_api_client.discogs_client.Client')
    def test_authenticate_with_tokens(self, mock_client_class, mock_getenv):
        """Test authentication when OAuth tokens are provided"""
        # Setup mock environment variables
        mock_getenv.side_effect = lambda key, default: {
            'DISCOGS_OAUTH_TOKEN': 'env_token',
            'DISCOGS_OAUTH_TOKEN_SECRET': 'env_token_secret'
        }.get(key, default)
        
        client = DiscogsCollectionClient(
            consumer_key="test_key",
            consumer_secret="test_secret",
            useragent="pyqrfactorydiscogs/1.0"
        )
        
        # Mock the client and identity
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_identity = Mock()
        mock_identity.username = "test_user"
        mock_client.identity.return_value = mock_identity
        
        # Call authenticate
        client.authenticate()
        
        # Verify client was created with correct parameters
        mock_client_class.assert_called_once_with(
            consumer_key='test_key',
            consumer_secret='test_secret',
            user_agent='pyqrfactorydiscogs/1.0',
            token='env_token',
            secret='env_token_secret'
        )
        
        assert client.user == mock_identity

    @patch('services.discogs_api_client.os.getenv')
    @patch('services.discogs_api_client.discogs_client.Client')
    @patch('builtins.input')
    def test_authenticate_interactive_flow(self, mock_input, mock_client_class, mock_getenv):
        """Test authentication with interactive OAuth flow"""
        # Setup mock environment variables to return empty strings
        mock_getenv.return_value = ""
        
        client = DiscogsCollectionClient(
            consumer_key="test_key",
            consumer_secret="test_secret",
            useragent="pyqrfactorydiscogs/1.0"
        )
        
        # Mock the client
        mock_client = MagicMock()
        mock_client.get_authorize_url.return_value = ("request_token", "request_secret", "https://auth.url")
        mock_client.get_access_token.return_value = ("access_token", "access_secret")
        mock_client_class.return_value = mock_client
        
        # Mock user input
        mock_input.side_effect = ["y", "verifier_code"]
        
        # Mock identity
        mock_identity = Mock()
        mock_identity.username = "test_user"
        mock_client.identity.return_value = mock_identity
        
        # Call authenticate
        client.authenticate()
        
        # Verify OAuth flow was initiated
        mock_client.get_authorize_url.assert_called_once()
        mock_client.get_access_token.assert_called_once_with("verifier_code")
        
        assert client.oauth_token == "access_token"
        assert client.oauth_token_secret == "access_secret"
        assert client.user == mock_identity

    def test_get_collection_folders_no_authentication(self):
        """Test folder retrieval when not authenticated"""
        client = DiscogsCollectionClient(
            consumer_key="test_key",
            consumer_secret="test_secret",
            useragent="pyqrfactorydiscogs/1.0"
        )
        
        # Should return empty list when user is None
        folders = client.get_collection_folders()
        assert folders == []

    def test_get_folder_name_by_id(self):
        """Test getting folder name by ID"""
        client = DiscogsCollectionClient(
            consumer_key="test_key",
            consumer_secret="test_secret",
            useragent="pyqrfactorydiscogs/1.0"
        )
        
        # Mock the user and folder structure
        mock_user = Mock()
        mock_folder1 = Mock()
        mock_folder1.id = 1
        mock_folder1.name = "Favorites"
        
        mock_folder2 = Mock()
        mock_folder2.id = 2
        mock_folder2.name = "Vinyl Collection"
        
        mock_user.collection_folders = [mock_folder1, mock_folder2]
        client.user = mock_user
        
        # Test getting existing folder name
        folder_name = client.get_folder_name_by_id(1)
        assert folder_name == "Favorites"
        
        # Test getting another existing folder name
        folder_name = client.get_folder_name_by_id(2)
        assert folder_name == "Vinyl Collection"
        
        # Test getting non-existing folder name
        folder_name = client.get_folder_name_by_id(999)
        assert folder_name == "Unknown Folder"
        
        # Test with no authentication (no user)
        client.user = None
        folder_name = client.get_folder_name_by_id(1)
        assert folder_name == "Unknown Folder"

    @patch.object(DiscogsCollectionClient, 'authenticate')
    def test_get_collection_releases_by_folder(self, mock_authenticate):
        """Test release retrieval by folder"""
        client = DiscogsCollectionClient(
            consumer_key="test_key",
            consumer_secret="test_secret",
            useragent="pyqrfactorydiscogs/1.0"
        )
        
        # Mock the user and folder structure
        mock_user = Mock()
        mock_folder = Mock()
        mock_folder.id = 1
        mock_folder.name = "Test Folder"
        
        # Mock releases
        mock_release1 = Mock()
        mock_release1.id = 100
        mock_release1.release.title = "Album One"
        mock_artist1 = Mock()
        mock_artist1.name = "Artist One"
        mock_release1.release.artists = [mock_artist1]
        mock_release1.release.year = 2020
        mock_release1.release.formats = [{'name': 'Vinyl', 'qty': '1'}]
        mock_label1 = Mock()
        mock_label1.name = "Label One"
        mock_release1.release.labels = [mock_label1]
        mock_release1.release.url = "https://www.discogs.com/release/100-Artist-One-Album-One"
        
        mock_release2 = Mock()
        mock_release2.id = 101
        mock_release2.release.title = "Album Two"
        mock_artist2 = Mock()
        mock_artist2.name = "Artist Two"
        mock_release2.release.artists = [mock_artist2]
        mock_release2.release.year = 2021
        mock_release2.release.formats = [{'name': 'CD', 'qty': '1'}]
        mock_label2 = Mock()
        mock_label2.name = "Label Two"
        mock_release2.release.labels = [mock_label2]
        mock_release2.release.url = "https://www.discogs.com/release/101-Artist-Two-Album-Two"
        
        mock_folder.releases = [mock_release1, mock_release2]
        mock_user.collection_folders = [mock_folder]
        
        client.user = mock_user
        
        # Call method
        result = client.get_collection_releases_by_folder(1)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert len(result) == 2
        assert result[0]['id'] == 100
        assert result[0]['title'] == "Album One"
        assert result[0]['artist'] == "Artist One"
        assert result[1]['id'] == 101
        assert result[1]['title'] == "Album Two"
        assert result[1]['artist'] == "Artist Two"

    @patch('services.discogs_api_client.discogs_client.Client')
    def test_get_release_by_releaseid(self, mock_client_class):
        """Test retrieving a single release by ID"""
        client = DiscogsCollectionClient(
            consumer_key="test_key",
            consumer_secret="test_secret",
            useragent="pyqrfactorydiscogs/1.0"
        )
        
        # Mock the client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock release
        mock_rel = Mock()
        mock_rel.id = 100
        mock_rel.title = "Album One"
        mock_artist = Mock()
        mock_artist.name = "Artist One"
        mock_rel.artists = [mock_artist]
        mock_rel.year = 2020
        mock_rel.formats = [{'name': 'Vinyl', 'qty': '1'}]
        mock_label = Mock()
        mock_label.name = "Label One"
        mock_rel.labels = [mock_label]
        mock_rel.url = "https://www.discogs.com/release/100-Artist-One-Album-One"
        
        mock_client.release.return_value = mock_rel
        client.client = mock_client
        
        # Call method
        result = client.get_release_by_releaseid(100)
        
        # Verify result
        assert result['id'] == 100
        assert result['title'] == "Album One"
        assert result['artist'] == "Artist One"
        # The URL is processed by split('-', 1)[0] in the actual code
        assert result['url'] == "https://www.discogs.com/release/100"

    def test_get_authorize_url_with_callback_validation(self):
        """Test validation in get_authorize_url_with_callback method"""
        client = DiscogsCollectionClient(
            consumer_key="",
            consumer_secret="",
            useragent="pyqrfactorydiscogs/1.0"
        )
        
        # Should raise ValueError when credentials are not set
        with pytest.raises(ValueError, match="Consumer key and secret must be set"):
            client.get_authorize_url_with_callback("http://callback.url")

    @patch('services.discogs_api_client.discogs_client.Client')
    def test_get_authorize_url_with_callback_success(self, mock_client_class):
        """Test successful get_authorize_url_with_callback method"""
        client = DiscogsCollectionClient(
            consumer_key="test_key",
            consumer_secret="test_secret",
            useragent="pyqrfactorydiscogs/1.0"
        )
        
        # Mock the client
        mock_client = MagicMock()
        mock_client.get_authorize_url.return_value = (
            "request_token",
            "request_token_secret",
            "https://www.discogs.com/oauth/authorize?oauth_token=request_token"
        )
        mock_client_class.return_value = mock_client
        
        # Call method
        callback_url = "http://localhost:5000/oauth-callback"
        request_token, request_token_secret, authorize_url = client.get_authorize_url_with_callback(callback_url)
        
        # Verify results
        assert request_token == "request_token"
        assert request_token_secret == "request_token_secret"
        assert authorize_url == "https://www.discogs.com/oauth/authorize?oauth_token=request_token"
        assert client.oauth_token == "request_token"
        assert client.oauth_token_secret == "request_token_secret"
        
        # Verify client was created with correct parameters
        mock_client_class.assert_called_once_with(
            consumer_key="test_key",
            consumer_secret="test_secret",
            user_agent="pyqrfactorydiscogs/1.0"
        )
        
        # Verify get_authorize_url was called with callback
        mock_client.get_authorize_url.assert_called_once_with(callback_url=callback_url)

    def test_complete_oauth_validation(self):
        """Test validation in complete_oauth method"""
        client = DiscogsCollectionClient(
            consumer_key="test_key",
            consumer_secret="test_secret",
            useragent="pyqrfactorydiscogs/1.0"
        )
        
        # Should raise ValueError when request tokens are not set
        with pytest.raises(ValueError, match="Request token and secret must be set before completing OAuth"):
            client.complete_oauth("verifier_code")

    @patch('services.discogs_api_client.discogs_client.Client')
    def test_complete_oauth_success(self, mock_client_class):
        """Test successful complete_oauth method"""
        client = DiscogsCollectionClient(
            consumer_key="test_key",
            consumer_secret="test_secret",
            useragent="pyqrfactorydiscogs/1.0",
            oauth_token="request_token",
            oauth_token_secret="request_token_secret"
        )
        
        # Mock the client
        mock_client = MagicMock()
        mock_client.get_access_token.return_value = ("access_token", "access_token_secret")
        mock_client_class.return_value = mock_client
        
        # Mock identity
        mock_identity = Mock()
        mock_identity.username = "test_user"
        mock_client.identity.return_value = mock_identity
        
        # Call method
        access_token, access_token_secret = client.complete_oauth("verifier_code")
        
        # Verify results
        assert access_token == "access_token"
        assert access_token_secret == "access_token_secret"
        assert client.oauth_token == "access_token"
        assert client.oauth_token_secret == "access_token_secret"
        assert client.user == mock_identity
        
        # Verify get_access_token was called with verifier
        mock_client.get_access_token.assert_called_once_with("verifier_code")
        
        # Verify identity was retrieved
        mock_client.identity.assert_called_once()

    @patch('services.discogs_api_client.discogs_client.Client')
    def test_complete_oauth_client_initialization(self, mock_client_class):
        """Test client initialization in complete_oauth when client is None"""
        client = DiscogsCollectionClient(
            consumer_key="test_key",
            consumer_secret="test_secret",
            useragent="pyqrfactorydiscogs/1.0",
            oauth_token="request_token",
            oauth_token_secret="request_token_secret"
        )
        client.client = None  # Simulate client not being initialized
        
        # Mock the client
        mock_client = MagicMock()
        mock_client.get_access_token.return_value = ("access_token", "access_token_secret")
        mock_client_class.return_value = mock_client
        
        # Mock identity
        mock_identity = Mock()
        mock_identity.username = "test_user"
        mock_client.identity.return_value = mock_identity
        
        # Call method
        access_token, access_token_secret = client.complete_oauth("verifier_code")
        
        # Verify client was initialized
        mock_client_class.assert_called_once_with(
            consumer_key="test_key",
            consumer_secret="test_secret",
            user_agent="pyqrfactorydiscogs/1.0",
            token='request_token',
            secret='request_token_secret'
        )
        
        assert client.client == mock_client