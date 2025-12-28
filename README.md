# Flask Discogs Collection to QR Factory CSV Generator

A web application that allows users to authenticate with Discogs API, retrieve their collection folders and releases, select specific releases, sort them by date, preview and edit the generated CSV, and download it in the format expected by QR Factory 3.

## Features

- ✅ OAuth authentication with Discogs API (web-based flow with callback)
- ✅ Auto-authentication using `.env` credentials if available
- ✅ Retrieve collection folders from Discogs
- ✅ Browse releases within selected folders
- ✅ Sort releases by multiple criteria (Artist A-Z, Artist Z-A, Newest First, Oldest First, Date Added)
- ✅ Select individual releases, all releases, or by artist starting letter
- ✅ Preview CSV output before final generation
- ✅ Edit CSV data in a web interface before download
- ✅ Download CSV in QR Factory 3 compatible format
- ✅ Session management with clear session functionality
- ✅ Landing page with multiple selection options

## Installation

### Prerequisites

- Python 3.8+
- pip or uv package manager
- mise (optional but recommended for easiest setup)

### Setup

1. **Create a Discogs Application** (Required):

   - Go to [Discogs](https://www.discogs.com/) → Settings → Developers
   - Click "Create an application"
   - As **Application Name**, enter: `pyqrfactorydiscogs`
   - As **Description** (optional), enter: "Create CSV list of Discogs collection in the format expected to be imported in QR Factory 3 to print out QR codes with URL links to each release in the collection"
   - As **Callback URL**, enter: `http://127.0.0.1:5000/auth/callback`
   - Save the changes and note the generated **Consumer Key** and **Consumer Secret**

2. Clone this repository:

```bash
git clone https://github.com/yourusername/pyqrfactorydiscogs.git
cd pyqrfactorydiscogs
```

3. Install dependencies:

```bash
pip install -r requirements.txt
# or with uv:
uv pip install -r requirements.txt
# or using pyproject.toml:
uv pip install .
# or with mise (recommended):
mise run install
```

4. Create a `.env` file based on `.env.example` and add your Discogs API credentials:

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

1. **Landing Page**

   - Choose between different selection methods
   - Select releases by folders or by date added (coming soon)

2. **Authentication**

   - Enter your Discogs API Consumer Key and Consumer Secret (obtained from creating a Discogs application as described in Setup step 1)
   - Click "Authenticate" to generate OAuth token and secret
   - If `.env` file exists with valid credentials, auto-authentication occurs

3. **Folder Selection**

   - View all folders in your Discogs collection
   - Select the folder you want to process

4. **Release Browsing**

   - View all releases in the selected folder
   - Sort by multiple criteria: Artist (A-Z), Artist (Z-A), Newest First, Oldest First, Date Added
   - Select individual releases, "Select All", or select by artist starting letter
   - Advanced filtering with letter-based selection dropdown

5. **CSV Preview & Editing**

   - Review the generated CSV data before final download
   - Edit any field values in the web interface
   - Make any adjustments if needed

6. **Download**
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
│       ├── landing.html          # Landing page with selection options
│       ├── oauth_callback.html    # OAuth callback page
│       ├── folders.html          # Folder selection page
│       ├── releases.html         # Release browsing page with advanced sorting
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

- OAuth authentication flow (web-based with callback and CLI)
- Web-based OAuth flow with callback URL support
- Retrieving collection folders
- Getting releases by folder ID
- Fetching individual releases by release ID
- Automatic credential management with `.env` file
- Complete OAuth flow with access token exchange

### CSV Processor

The `DiscogsCollectionProcessor` class in `services/discogs_collection_processor.py` handles data processing:

- Validates required fields (artist, title, url)
- Extracts release information from Discogs API responses
- Prepares data for CSV generation

### Flask Routes

- `/` - Landing page (auto-authenticates if `.env` credentials exist)
- `/authenticate-page` - OAuth authentication page
- `/authenticate` - OAuth authentication handler
- `/oauth-callback` - OAuth callback handler
- `/select-by-folders` - Route for selecting releases by folders
- `/select-by-date` - Route for selecting releases by date added (placeholder)
- `/folders` - Folder selection page
- `/releases/<folder_id>` - Release browsing page with advanced sorting and filtering
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

## Advanced Features

### Sorting Options

The application provides multiple sorting options for releases:

- **Artist (A-Z)**: Sort releases alphabetically by artist name (ascending)
- **Artist (Z-A)**: Sort releases alphabetically by artist name (descending)
- **Newest First**: Sort releases by year (newest to oldest)
- **Oldest First**: Sort releases by year (oldest to newest)
- **Date Added**: Sort releases by when they were added to your collection

### Letter-Based Selection

The releases page includes an advanced letter-based selection feature:

- Select releases by artist starting letter using a dropdown interface
- Choose multiple letters at once for batch selection
- Search and filter letters for easy navigation
- Select or deselect all releases starting with specific letters
- Supports letters A-Z, numbers (0-9), and other characters

### Selection Methods

- **Select All**: Quickly select all releases in the current view
- **Deselect All**: Clear all current selections
- **Select by Letter**: Select releases based on artist starting letter
- **Deselect by Letter**: Remove selections based on artist starting letter
- **Individual Selection**: Check individual releases for precise control

## QR Factory 3 Format

The generated CSV uses the QR Factory 3 template format with placeholders that are replaced with actual release data:

- `BottomText` field: `{artist} – {title} [{year}]` (e.g., "SOHN – Albadas [2023]")
- `Content` field: `{url}` (e.g., "https://www.discogs.com/release/12345678")
- `FileName` field: `{filename}` (e.g., "12345678")

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

4. **OAuth Callback URL Issues**
   - Ensure your Discogs application has the correct callback URL: `http://127.0.0.1:5000/auth/callback`
   - If you change the callback URL in your Discogs application, update the `.env` file accordingly
   - Make sure your local development server is running on port 5000

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a new Pull Request

## License

This project is licensed under the MIT License.
