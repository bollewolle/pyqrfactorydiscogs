# Flask Discogs Collection to QR Factory CSV Generator

A web application that allows users to authenticate with Discogs API, retrieve their collection folders and releases, select specific releases, sort them by date, preview and edit the generated CSV, and download it in the format expected by QR Factory 3.

## Features

- ✅ OAuth authentication with Discogs API (web-based flow)
- ✅ Auto-authentication using `.env` credentials if available
- ✅ Retrieve collection folders from Discogs
- ✅ Browse releases within selected folders
- ✅ Sort releases by release year (newest first)
- ✅ Select individual releases or all releases
- ✅ Preview CSV output before final generation
- ✅ Edit CSV data in a web interface before download
- ✅ Download CSV in QR Factory 3 compatible format
- ✅ Session management with clear session functionality

## Installation

### Prerequisites

- Python 3.8+
- pip or uv package manager
- mise (optional but recommended for easiest setup)

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
# or using pyproject.toml:
uv pip install .
# or with mise (recommended):
mise run install
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

Or using the application factory:

```bash
python -m flask --app app run --debug
```

Or with mise (recommended):

```bash
mise run flask_debug
```

The application will be available at `http://localhost:5000`

### User Workflow

1. **Authentication**

   - Enter your Discogs API Consumer Key and Consumer Secret
   - Click "Authenticate" to generate OAuth token and secret
   - If `.env` file exists with valid credentials, auto-authentication occurs

2. **Folder Selection**

   - View all folders in your Discogs collection
   - Select the folder you want to process

3. **Release Browsing**

   - View all releases in the selected folder
   - Sort by release year (newest first)
   - Select individual releases or "Select All"

4. **CSV Preview & Editing**

   - Review the generated CSV data before final download
   - Edit any field values in the web interface
   - Make any adjustments if needed

5. **Download**
   - Click "Generate CSV" to download the final file in QR Factory 3 format
   - CSV includes all QR Factory 3 template fields with your release data

## Project Structure

```
.
├── app/                          # Flask application
│   ├── __init__.py               # Flask app initialization
│   ├── routes.py                 # Route handlers
│   └── templates/                # HTML templates
│       ├── base.html             # Base template
│       ├── index.html            # Authentication page
│       ├── oauth_callback.html    # OAuth callback page
│       ├── folders.html          # Folder selection page
│       ├── releases.html         # Release browsing page
│       ├── preview.html          # Basic CSV preview page
│       └── editable_preview.html # Editable CSV preview page
├── services/                     # Service modules
│   ├── discogs_api_client.py     # Discogs API client implementation
│   └── discogs_collection_processor.py # CSV data processing logic
├── templates/                    # Template files
│   └── qrfactory_discogs_collection_template.csv # QR Factory 3 template
├── example/                      # Example files
│   └── example_qrfactor3_expected_csv_format.csv # Example output format
├── tests/                       # Test suite
│   ├── unit/                     # Unit tests
│   │   ├── test_discogs_api_client.py
│   │   └── test_discogs_collection_processor.py
│   ├── integration/              # Integration tests
│   │   ├── test_flask_app.py
│   │   └── test_workflow.py
│   ├── e2e/                      # End-to-end tests
│   └── fixtures/                 # Test fixtures
├── .env.example                 # Environment variable template
├── .mise.toml                   # Mise environment configuration
├── pyproject.toml               # Python project configuration
├── requirements.txt              # Python dependencies
├── generate_oauth_tokens.py     # OAuth token generation script
└── README.md                     # This file
```

## Technical Details

### Discogs API Client

The `DiscogsCollectionClient` class in `services/discogs_api_client.py` handles all interactions with the Discogs API:

- OAuth authentication flow (web-based and CLI)
- Retrieving collection folders
- Getting releases by folder ID
- Fetching individual releases by release ID
- Automatic credential management with `.env` file

### CSV Processor

The `DiscogsCollectionProcessor` class in `services/discogs_collection_processor.py` handles data processing:

- Validates required fields (artist, title, url)
- Extracts release information from Discogs API responses
- Prepares data for CSV generation

### Flask Routes

- `/` - Authentication page (auto-authenticates if `.env` credentials exist)
- `/authenticate` - OAuth authentication handler
- `/oauth-callback` - OAuth callback handler
- `/folders` - Folder selection page
- `/releases/<folder_id>` - Release browsing page with sorting
- `/preview/` - CSV preview generation
- `/editable-preview/` - Editable CSV preview page
- `/generate-editable-csv` - Generate CSV from editable data
- `/download-csv` - Final CSV download
- `/clear-session` - Clear user session

## Testing

The project uses pytest for testing with a comprehensive test suite:

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run tests with coverage
pytest --cov

# Run specific test file
pytest tests/unit/test_discogs_api_client.py

# Or with mise (recommended):
mise run test
mise run test-cov
```

Test structure:

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test interactions between components
- **End-to-end tests**: Test complete user workflows (in `tests/e2e/`)

## QR Factory 3 Format

The generated CSV uses the QR Factory 3 template format with placeholders that are replaced with actual release data:

- `BottomText` field: `{artist} – {title}` (e.g., "SOHN – Albadas")
- `Content` field: `{url}` (e.g., "https://www.discogs.com/release/12345678")
- `FileName` field: `{BottomText}` (e.g., "SOHN – Albadas.png")

The template includes all QR Factory 3 configuration fields:

```
Type,OutputSize,FileType,ColorSpace,RotationAngle,ReliabilityLevel,UseAutoReliabilityLevel,PixelRoundness,PixelColorType,BackgroundColorType,BackgroundColor,PixelColorStart,PixelColorEnd,GradientAngle,IconPath,IconLockToSquares,IconSizePercent,IconBorderType,IconBorderPercent,IconBorderSquareCornerSize,IconBorderColor,BottomText,BottomTextSize,BottomTextColor,BottomTextFont,BottomTextFontStyle,SafeZonePercent,SafeZoneColor,Content,FileName
```

This format allows QR Factory 3 to generate QR codes with dynamic content and proper formatting for each release.

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

This project is licensed under the MIT License.
