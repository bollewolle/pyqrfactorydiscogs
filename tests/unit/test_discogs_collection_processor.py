"""
Unit tests for DiscogsCollectionProcessor class.

Tests the data extraction and CSV generation functionality.
"""

import pytest
import tempfile
import os
from services.discogs_collection_processor import DiscogsCollectionProcessor


class TestDiscogsCollectionProcessor:
    """Test suite for DiscogsCollectionProcessor"""

    def test_initialization(self):
        """Test processor initialization"""
        processor = DiscogsCollectionProcessor()
        assert processor is not None

    def test_extract_release_info_valid_data(self, mock_release_data):
        """Test extraction of release information with valid data"""
        processor = DiscogsCollectionProcessor()
        
        result = processor.extract_release_info(mock_release_data)
        
        assert len(result) == 2
        assert result[0]['artist'] == 'Artist One'
        assert result[0]['title'] == 'Album One'
        assert result[0]['url'] == 'https://www.discogs.com/release/100-Artist-One-Album-One'
        assert result[1]['artist'] == 'Artist Two'
        assert result[1]['title'] == 'Album Two'
        assert result[1]['url'] == 'https://www.discogs.com/release/101-Artist-Two-Album-Two'

    def test_extract_release_info_missing_fields(self):
        """Test extraction with missing required fields"""
        processor = DiscogsCollectionProcessor()
        
        # Missing artist field
        invalid_data = [{
            'title': 'Album One',
            'url': 'https://example.com/album-one'
        }]
        
        with pytest.raises(ValueError, match="Release entry missing required fields: \['artist'\]"):
            processor.extract_release_info(invalid_data)

    def test_extract_release_info_empty_list(self):
        """Test extraction with empty list"""
        processor = DiscogsCollectionProcessor()
        
        result = processor.extract_release_info([])
        assert result == []

    def test_extract_release_info_invalid_input_type(self):
        """Test extraction with invalid input type"""
        processor = DiscogsCollectionProcessor()
        
        with pytest.raises(ValueError, match="release_data must be a list"):
            processor.extract_release_info("not a list")

    def test_generate_collection_csv_valid_data(self, mock_release_data):
        """Test CSV generation with valid data"""
        processor = DiscogsCollectionProcessor()
        
        # Create a temporary template file
        template_content = """artist,title,url
{artist},{title},{url}"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as template_file:
            template_file.write(template_content)
            template_path = template_file.name
        
        try:
            # Create output path
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as output_file:
                output_path = output_file.name
            
            # Extract release info first
            release_info = processor.extract_release_info(mock_release_data)
            
            # Generate CSV
            processor.generate_collection_csv(release_info, template_path, output_path)
            
            # Verify output file was created and contains expected content
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                content = f.read()
                lines = content.strip().split('\n')
                
                # Should have header + 2 data lines
                assert len(lines) == 3
                assert lines[0] == 'artist,title,url'
                assert 'Artist One,Album One,https://www.discogs.com/release/100-Artist-One-Album-One' in lines[1]
                assert 'Artist Two,Album Two,https://www.discogs.com/release/101-Artist-Two-Album-Two' in lines[2]
        
        finally:
            # Clean up temporary files
            if os.path.exists(template_path):
                os.unlink(template_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_generate_collection_csv_missing_placeholders(self):
        """Test CSV generation with template missing required placeholders"""
        processor = DiscogsCollectionProcessor()
        
        # Create a template without required placeholders
        template_content = """artist,title,url
{artist},{title}"""  # Missing {url}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as template_file:
            template_file.write(template_content)
            template_path = template_file.name
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as output_file:
                output_path = output_file.name
            
            release_info = [{
                'artist': 'Test Artist',
                'title': 'Test Album',
                'url': 'https://example.com/test'
            }]
            
            with pytest.raises(ValueError, match="Template format line must contain {url} placeholder"):
                processor.generate_collection_csv(release_info, template_path, output_path)
        
        finally:
            # Clean up
            if os.path.exists(template_path):
                os.unlink(template_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_generate_collection_csv_nonexistent_template(self):
        """Test CSV generation with nonexistent template file"""
        processor = DiscogsCollectionProcessor()
        
        release_info = [{
            'artist': 'Test Artist',
            'title': 'Test Album',
            'url': 'https://example.com/test'
        }]
        
        with pytest.raises(FileNotFoundError):
            processor.generate_collection_csv(release_info, 'nonexistent_template.csv', 'output.csv')

    def test_generate_collection_csv_invalid_data_type(self):
        """Test CSV generation with invalid data type"""
        processor = DiscogsCollectionProcessor()
        
        with pytest.raises(ValueError, match="release_data must be a list"):
            processor.generate_collection_csv("not a list", 'template.csv', 'output.csv')