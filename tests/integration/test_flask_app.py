"""
Integration tests for Flask application.

Tests the Flask routes and application functionality.
"""

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
            sess['oauth_token'] = 'test_token'
            sess['oauth_secret'] = 'test_secret'
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
            sess['oauth_token'] = 'test_token'
            sess['oauth_secret'] = 'test_secret'
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
            sess['oauth_token'] = 'test_token'
            sess['oauth_secret'] = 'test_secret'
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
            
            response = flask_test_client.post('/preview/?release_ids=100&release_ids=101', data=test_data, follow_redirects=True)
            
            # Should redirect to editable preview
            assert response.status_code == 200
            assert b'Artist One' in response.data or b'Album One' in response.data

    def test_releases_sorting_functionality(self, flask_test_client):
            """Test releases sorting functionality"""
            with flask_test_client.session_transaction() as sess:
                sess['oauth_token'] = 'test_token'
                sess['oauth_secret'] = 'test_secret'
                sess['consumer_key'] = 'test_key'
                sess['consumer_secret'] = 'test_secret'
              
            with patch('app.routes.DiscogsCollectionClient') as mock_client_class:
                # Mock the client
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                # Mock release retrieval with multiple releases including same artist with different years
                mock_release_data = {
                    0: {
                        'id': 100,
                        'title': 'Album One',
                        'artist': 'Muse',
                        'year': 2015,
                        'format': [{'name': 'Vinyl', 'qty': '1'}],
                        'label': 'Label One',
                        'url': 'https://www.discogs.com/release/100-Muse-Album-One',
                        'date_added': '2020-01-01'
                    },
                    1: {
                        'id': 101,
                        'title': 'Album Two',
                        'artist': 'Muse',
                        'year': 2009,
                        'format': [{'name': 'CD', 'qty': '1'}],
                        'label': 'Label Two',
                        'url': 'https://www.discogs.com/release/101-Muse-Album-Two',
                        'date_added': '2018-01-01'
                    },
                    2: {
                        'id': 102,
                        'title': 'Album Three',
                        'artist': 'Muse',
                        'year': 2012,
                        'format': [{'name': 'Vinyl', 'qty': '1'}],
                        'label': 'Label Three',
                        'url': 'https://www.discogs.com/release/102-Muse-Album-Three',
                        'date_added': '2022-01-01'
                    },
                    3: {
                        'id': 103,
                        'title': 'Album Four',
                        'artist': 'Beatles',
                        'year': 1969,
                        'format': [{'name': 'Vinyl', 'qty': '1'}],
                        'label': 'Label Four',
                        'url': 'https://www.discogs.com/release/103-Beatles-Album-Four',
                        'date_added': '2019-01-01'
                    },
                    4: {
                        'id': 104,
                        'title': 'Album Five',
                        'artist': 'Beatles',
                        'year': 1967,
                        'format': [{'name': 'Vinyl', 'qty': '1'}],
                        'label': 'Label Five',
                        'url': 'https://www.discogs.com/release/104-Beatles-Album-Five',
                        'date_added': '2017-01-01'
                    },
                    5: {
                        'id': 105,
                        'title': 'Album Six',
                        'artist': 'Beatles',
                        'year': 1971,
                        'format': [{'name': 'Vinyl', 'qty': '1'}],
                        'label': 'Label Six',
                        'url': 'https://www.discogs.com/release/105-Beatles-Album-Six',
                        'date_added': '2021-01-01'
                    }
                }
                
                mock_client.get_collection_releases_by_folder.return_value = mock_release_data
                
                # Test default sorting (artist A-Z)
                response = flask_test_client.get('/releases/1')
                assert response.status_code == 200
                # Should show artists in alphabetical order (Beatles, Muse)
                data = response.data.decode('utf-8')
                
                # Check that Beatles come before Muse (alphabetical order)
                beatles_pos = data.find('Beatles')
                muse_pos = data.find('Muse')
                assert beatles_pos > 0 and muse_pos > 0
                assert beatles_pos < muse_pos
                
                # Test oldest first sorting
                response = flask_test_client.get('/releases/1?sort=oldest_first')
                assert response.status_code == 200
                # Should show oldest first (1967, 1969, 1971, 2009, 2012, 2015)
                data = response.data.decode('utf-8')
                year_positions = []
                for year in ['1967', '1969', '1971', '2009', '2012', '2015']:
                    year_positions.append((year, data.find(year)))
                # Check that years appear in ascending order
                assert year_positions[0][1] < year_positions[1][1] < year_positions[2][1] < year_positions[3][1] < year_positions[4][1] < year_positions[5][1]
                
                # Test artist A-Z sorting with secondary year sorting
                response = flask_test_client.get('/releases/1?sort=artist_az')
                assert response.status_code == 200
                # Should show artists in alphabetical order (Beatles, Muse)
                # And within each artist, albums should be sorted by year (oldest to newest)
                data = response.data.decode('utf-8')
                
                # Check that Beatles come before Muse (alphabetical order)
                beatles_pos = data.find('Beatles')
                muse_pos = data.find('Muse')
                assert beatles_pos > 0 and muse_pos > 0
                assert beatles_pos < muse_pos
                
                # Check that Beatles albums are sorted by year (1967, 1969, 1971)
                year_1967_pos = data.find('1967')
                year_1969_pos = data.find('1969')
                year_1971_pos = data.find('1971')
                assert year_1967_pos > 0 and year_1969_pos > 0 and year_1971_pos > 0
                assert year_1967_pos < year_1969_pos < year_1971_pos
                
                # Test artist Z-A sorting with secondary year sorting
                response = flask_test_client.get('/releases/1?sort=artist_za')
                assert response.status_code == 200
                # Should show artists in reverse alphabetical order (Muse, Beatles)
                # And within each artist, albums should be sorted by year (newest to oldest)
                data = response.data.decode('utf-8')
                
                # Check that Muse comes before Beatles (reverse alphabetical order)
                muse_pos = data.find('Muse')
                beatles_pos = data.find('Beatles')
                assert muse_pos > 0 and beatles_pos > 0
                assert muse_pos < beatles_pos
                
                # Check that Muse albums are sorted by year (2015, 2012, 2009)
                year_2015_pos = data.find('2015')
                year_2012_pos = data.find('2012')
                year_2009_pos = data.find('2009')
                assert year_2015_pos > 0 and year_2012_pos > 0 and year_2009_pos > 0
                assert year_2015_pos < year_2012_pos < year_2009_pos
                
                # Test date added sorting
                response = flask_test_client.get('/releases/1?sort=date_added')
                assert response.status_code == 200
                # Should show most recently added first (2022, 2021, 2020, 2019, 2018, 2017)
                data = response.data.decode('utf-8')
                date_positions = []
                for date in ['2022-01-01', '2021-01-01', '2020-01-01', '2019-01-01', '2018-01-01', '2017-01-01']:
                    date_positions.append((date, data.find(date)))
                # Check that dates appear in descending order (newest added first)
                assert date_positions[0][1] < date_positions[1][1] < date_positions[2][1] < date_positions[3][1] < date_positions[4][1] < date_positions[5][1]

    def test_releases_letter_selection_ui(self, flask_test_client):
       """Test that the letter selection UI is present on releases page"""
       with flask_test_client.session_transaction() as sess:
           sess['oauth_token'] = 'test_token'
           sess['oauth_secret'] = 'test_secret'
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

           # Check that letter selection UI elements are present
           data = response.data.decode('utf-8')
           assert 'Select by Artist Starting Letter:' in data
           assert 'letter-select' in data
           assert 'select-by-letter' in data
           assert 'deselect-by-letter' in data

           # Check that all letter options are present
           for letter in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '0-9', 'other']:
               assert f'value="{letter}"' in data
