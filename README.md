# Flask Discogs Collection to QR Factory CSV Generator

A web application that allows users to authenticate with Discogs API, retrieve their collection folders and releases, select specific releases, sort them by date, preview the generated CSV, and download it in the format expected by QR Factory 3.

## Features

- ✅ OAuth authentication with Discogs API
- ✅ Retrieve collection folders from Discogs
- ✅ Browse releases within selected folders
- ✅ Sort releases by release year (newest first)
- ✅ Select individual releases or all releases
- ✅ Preview CSV output before final generation
- ✅ Download CSV in QR Factory 3 compatible format

## Installation

### Prerequisites

- Python 3.8+
- pip or uv package manager

### Setup

1. Clone this repository:

```bash
git clone https://github.com/yourusername/pyqrfactorydiscogs.git
cd pyqrfactorydiscogs
```

2. Install dependencies:

```bash
pip install -r requirements.txt
# or with uv:
uv pip install -r requirements.txt
```

3. Create a `.env` file based on `.env.example` and add your Discogs API credentials:

```bash
cp .env.example .env
# Edit .env with your consumer key and secret from Discogs developer settings
```

## Usage

### Running the Application

Start the Flask development server:

```bash
export FLASK_APP=app
flask run --debug
```

Or with uv:

```bash
uv run flask --app app run --debug
```

The application will be available at `http://localhost:5000`

### User Workflow

1. **Authentication**

   - Enter your Discogs API Consumer Key and Consumer Secret
   - Click "Authenticate" to generate OAuth token and secret

2. **Folder Selection**

   - View all folders in your Discogs collection
   - Select the folder you want to process

3. **Release Browsing**

   - View all releases in the selected folder
   - Sort by release year (newest first)
   - Select individual releases or "Select All"

4. **CSV Preview**

   - Review the generated CSV data before final download
   - Make any adjustments if needed

5. **Download**
   - Click "Generate CSV" to download the final file in QR Factory 3 format

## Project Structure

```
.
├── app/                          # Flask application
│   ├── __init__.py               # Flask app initialization
│   ├── routes.py                 # Route handlers
│   └── templates/                # HTML templates
│       ├── base.html             # Base template
│       ├── index.html            # Authentication page
│       ├── folders.html          # Folder selection page
│       ├── releases.html         # Release browsing page
│       └── preview.html          # CSV preview page
├── discogs_api_client.py         # Discogs API client implementation
├── discogs_collection_processor.py # CSV generation logic
├── qrfactory_discogs_collection_template.csv # QR Factory 3 template
├── requirements.txt              # Python dependencies
├── test_flask_app.py             # Unit tests
├── test_workflow.py              # Integration workflow tests
└── README.md                     # This file
```

## Technical Details

### Discogs API Client

The `DiscogsCollectionClient` class handles all interactions with the Discogs API:

- OAuth authentication flow
- Retrieving collection folders
- Getting releases by folder ID

### CSV Processor

The `DiscogsCollectionProcessor` class generates QR Factory 3 compatible CSVs:

- Validates required fields (artist, title, url)
- Replaces placeholders in template with actual data
- Generates properly formatted CSV files

### Flask Routes

- `/` - Authentication page
- `/folders` - Folder selection page
- `/releases/<folder_id>` - Release browsing page
- `/preview` - CSV preview page
- `/download` - Final CSV download

## Testing

Run the test suite to verify all functionality:

```bash
python test_flask_app.py
```

Run the workflow tests for integration testing:

```bash
python test_workflow.py
```

## QR Factory 3 Format

The generated CSV uses placeholders in the `BottomText` column that QR Factory 3 will replace with actual data:

```
Artist: {artist}
Title: {title}
URL: {url}
```

This format allows QR Factory to generate QR codes with dynamic content based on each release.

## Troubleshooting

### Common Issues

1. **Authentication Failed**

   - Verify your consumer key and secret are correct
   - Check that the `.env` file is properly formatted
   - Ensure you have API access enabled in Discogs developer settings

2. **No Folders Found**

   - Make sure you have at least one folder in your Discogs collection
   - Verify your authentication token is valid

3. **CSV Generation Errors**
   - Check that all releases have the required fields (artist, title, url)
   - Verify the template file exists and is readable

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a new Pull Request

## License

MIT License - see LICENSE file for details.
