"""
Discogs Collection Data Processor for generating QR factory collection files.

This module provides classes and methods to:
1. Process Discogs collection data retrieved by DiscogsCollectionClient
2. Generate CSV files based on templates with release information
3. Extract artist, title, and URL from each release entry

Classes:
- DiscogsCollectionProcessor: Main class for processing collection data
"""

import csv
from typing import Dict, List

class DiscogsCollectionProcessor:
    """
    A processor for handling Discogs collection data.

    This class takes the output from DiscogsCollectionClient.get_collection_releases_by_folder()
    and formats it into a structured dictionary containing just artist, title, and URL information.
    It also provides methods to generate CSV files based on templates.
    """

    def __init__(self) -> None:
        """
        Initialize the Discogs collection processor.

        Args:
            None: This class doesn't require any initialization parameters
        """
        pass

    def extract_release_info(self, release_data: List[Dict]) -> List[Dict]:
        """
        Extract artist, title, year, and URL information from each release entry.

        Args:
            release_data (List[Dict]): List of release dictionaries containing 'artist',
                'title', 'year', and 'url' fields. Other fields like 'id', 'format',
                'label', etc. are ignored by this method.

        Returns:
            List[Dict]: List of dictionaries with just 'artist', 'title', 'year', and 'url' keys

        Raises:
            ValueError: If input data is not a list or contains invalid entries
            ValueError: If any release entry is missing required fields ('artist', 'title', or 'url')

        Note:
            The method validates that each release dictionary contains the three required fields.
            If any field is missing, it raises a ValueError with details about which fields are missing.
            The resulting list contains simplified dictionaries with artist, title, year, and URL information.
            The 'year' field is optional and will be included if present in the release data.
        """
        if not isinstance(release_data, list):
            raise ValueError("release_data must be a list")

        extracted_info = []

        for release in release_data:
            # Validate required fields exist
            required_fields = ['artist', 'title', 'url']
            missing_fields = [field for field in required_fields if field not in release]

            if missing_fields:
                raise ValueError(f"Release entry missing required fields: {missing_fields}")

            # Create simplified dictionary with just the needed info
            release_info = {
                'artist': release['artist'],
                'title': release['title'],
                'url': release['url']
            }
            
            # Include year if available
            if 'year' in release:
                release_info['year'] = release['year']

            extracted_info.append(release_info)

        return extracted_info

    def generate_collection_csv(self, release_data: List[Dict], template_path: str, output_path: str) -> None:
        """
        Generate a CSV file based on the Discogs collection template.

        Args:
            release_data (List[Dict]): List of release dictionaries containing 'artist',
                'title', 'year', and 'url' fields. Other fields are ignored.
            template_path (str): Path to the CSV template file containing header and format line
            output_path (str): Path where the generated CSV should be saved

        Returns:
            None: Writes CSV file to specified path

        Raises:
            ValueError: If input data is not a list or contains invalid entries,
                or if template format line doesn't contain required placeholders {artist}, {title}, and {url}
            FileNotFoundError: If template file doesn't exist
            IOError: If there are issues reading the template or writing the output file

        Note:
            The method reads the first two lines from the template CSV:
            - First line is used as header (column names)
            - Second line contains format placeholders {artist}, {title}, {year}, and {url}
            These placeholders are replaced with actual values from each release entry.
            The resulting CSV will have one row per release containing artist, title, year, and URL information.
        """
        if not isinstance(release_data, list):
            raise ValueError("release_data must be a list")

        # Read template header and format line
        try:
            with open(template_path, 'r', encoding='utf-8') as template_file:
                reader = csv.reader(template_file)
                template_header = next(reader)  # Get first line (header)
                template_format_line = next(reader)  # Get second line (format)

                # Validate template format contains required placeholders
                if '{artist}' not in ','.join(template_format_line) or '{title}' not in ','.join(template_format_line):
                    raise ValueError("Template format line must contain {artist} and {title} placeholders")
                if '{url}' not in ','.join(template_format_line):
                    raise ValueError("Template format line must contain {url} placeholder")

        except FileNotFoundError as error:
            raise FileNotFoundError(f"Template file not found: {error}")
        except IOError as error:
            raise IOError(f"Failed to read template file: {error}")

        # Generate CSV content
        csv_content = []

        # Add header line from template
        csv_content.append(template_header)

        # # Add format line from template (unchanged)
        # csv_content.append(','.join(template_format_line))

        # Add data lines for each release
        for release in release_data:
            # Replace placeholders with actual values
            artist = release.get('artist', '')
            title = release.get('title', '')
            year = release.get('year', '')
            url = release.get('url', '')

            # Create new line by replacing placeholders in the format template
            template_str = ','.join(template_format_line)
            new_line = template_str.replace('{artist}', str(artist))
            new_line = new_line.replace('{title}', str(title))
            new_line = new_line.replace('{year}', str(year))
            new_line = new_line.replace('{url}', str(url))

            new_line = new_line.split(',')

            csv_content.append(new_line)

        # Write CSV file
        try:
            with open(output_path, 'w', encoding='utf-8', newline='') as output_file:
                writer = csv.writer(output_file)
                writer.writerows(csv_content)
        except IOError as error:
            raise IOError(f"Failed to write CSV file: {error}")

def main() -> None:
    """
    Example usage demonstrating Discogs collection data processing.

    This main block shows how to:
    1. Create a processor instance
    2. Extract release information from collection data
    3. Generate a CSV file based on the template

    Note: This is for demonstration purposes only.
    """

    # Example collection data (simplified version of what get_collection_releases_by_folder returns)
    example_release_data = [
        {
            'id': 12345678,
            'title': 'Albadas',
            'artist': 'SOHN',
            'year': 2023,
            'format': 'Vinyl, 12"',
            'label': 'City Slang',
            'url': 'https://www.discogs.com/release/12345678-Albadas-by-SOHN'
        },
        {
            'id': 87654321,
            'title': 'Lazarus',
            'artist': 'Kamasi Washington',
            'year': 2022,
            'format': 'CD, Album',
            'label': 'Brainfeeder',
            'url': 'https://www.discogs.com/release/87654321-Lazarus-by-Kamasi-Washington'
        }
    ]

    # Create processor instance
    processor = DiscogsCollectionProcessor()

    # Extract just artist, title, and url info
    extracted_info = processor.extract_release_info(example_release_data)

    print("Extracted release information:")
    for release in extracted_info:
        print(f"  Artist: {release['artist']}")
        print(f"  Title: {release['title']}")
        print(f"  URL: {release['url']}")
    print()

    # Generate CSV file
    template_path = 'templates/qrfactory_discogs_collection_template.csv'
    output_path = 'generated_collection.csv'

    processor.generate_collection_csv(extracted_info, template_path, output_path)

    print(f"Successfully generated collection CSV at: {output_path}")

if __name__ == "__main__":
    main()