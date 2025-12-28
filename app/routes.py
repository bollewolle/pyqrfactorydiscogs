"""
Flask route handlers for Discogs Collection to QR Factory CSV Generator
"""

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, flash, current_app, send_file
)
import os
import csv
import io
from datetime import datetime
from dotenv import load_dotenv, set_key, get_key

# Import local modules
from services.discogs_api_client import DiscogsCollectionClient
from services.discogs_collection_processor import DiscogsCollectionProcessor

USERAGENT = os.getenv("USERAGENT", "pyqrfactorydiscogs/1.0")
DOTENV_PATH = ".env"

def is_test_environment() -> bool:
    """
    Check if the code is running in a test environment.
    
    Returns:
        bool: True if running in test environment, False otherwise
    """
    return os.getenv("PYTEST_CURRENT_TEST", "") != "" or os.getenv("TESTING", "") == "1" or os.getenv("FLASK_TESTING", "") == "1"

bp = Blueprint('main', __name__)

@bp.route('/')
def landing():
    """Landing page with selection options"""
    # Skip auto-authentication during tests
    if not is_test_environment() and os.path.exists('.env'):
        load_dotenv(DOTENV_PATH)
        
        # Get credentials from environment
        consumer_key = os.getenv('DISCOGS_CONSUMER_KEY')
        consumer_secret = os.getenv('DISCOGS_CONSUMER_SECRET')
        oauth_token = os.getenv('DISCOGS_OAUTH_TOKEN')
        oauth_secret = os.getenv('DISCOGS_OAUTH_TOKEN_SECRET')
        
        # If all credentials are present and user is not already authenticated, auto-authenticate
        if (consumer_key and consumer_secret and oauth_token and oauth_secret and
            ('oauth_token' not in session or 'oauth_secret' not in session)):
            try:
                # Initialize client with credentials from .env
                client = DiscogsCollectionClient(
                    consumer_key=consumer_key,
                    consumer_secret=consumer_secret,
                    useragent=USERAGENT,
                    oauth_token=oauth_token,
                    oauth_token_secret=oauth_secret
                )
                
                # Authenticate with Discogs API
                client.authenticate()
                
                # Store credentials in session for later use
                session['consumer_key'] = consumer_key
                session['consumer_secret'] = consumer_secret
                session['oauth_token'] = oauth_token
                session['oauth_secret'] = oauth_secret
                
                flash('Successfully authenticated using .env credentials!', 'success')
                return redirect(url_for('main.landing'))
                
            except Exception as e:
                current_app.logger.error(f"Auto-authentication error: {str(e)}")
                # If auto-authentication fails, continue to show the landing page
                pass
     
    # Check if user is authenticated
    authenticated = 'oauth_token' in session and 'oauth_secret' in session
    
    return render_template('landing.html', authenticated=authenticated)

@bp.route('/authenticate-page')
def authenticate_page():
    """Authentication page for Discogs credentials"""
    return render_template('index.html')

@bp.route('/select-by-folders')
def select_by_folders():
    """Route for selecting releases by folders"""
    # Check if authenticated
    if 'oauth_token' not in session or 'oauth_secret' not in session:
        flash('Please authenticate first', 'error')
        return redirect(url_for('main.authenticate_page'))
    
    return redirect(url_for('main.folders'))

@bp.route('/select-by-date')
def select_by_date():
    """Route for selecting releases by date added (placeholder for future functionality)"""
    # Check if authenticated
    if 'oauth_token' not in session or 'oauth_secret' not in session:
        flash('Please authenticate first', 'error')
        return redirect(url_for('main.authenticate_page'))
    
    flash('Select releases by date added functionality is coming soon!', 'info')
    return redirect(url_for('main.landing'))

@bp.route('/authenticate', methods=['POST'])
def authenticate():
    """
    Handle OAuth authentication with Discogs API
    """
    consumer_key = request.form.get('consumer_key')
    consumer_secret = request.form.get('consumer_secret')

    if not consumer_key or not consumer_secret:
        flash('Consumer key and secret are required', 'error')
        return redirect(url_for('main.authenticate_page'))

    try:
        # Initialize client with credentials from form
        client = DiscogsCollectionClient(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            useragent=USERAGENT
        )

        # Check if OAuth tokens exist in .env file
        existing_oauth_token = get_key('.env', 'DISCOGS_OAUTH_TOKEN') or ''
        existing_oauth_secret = get_key('.env', 'DISCOGS_OAUTH_TOKEN_SECRET') or ''
        existing_oauth_token = existing_oauth_token.strip()
        existing_oauth_secret = existing_oauth_secret.strip()

        if existing_oauth_token and existing_oauth_secret:
            # Use existing tokens if available
            client.oauth_token = existing_oauth_token
            client.oauth_token_secret = existing_oauth_secret
            client.authenticate()
        else:
            # Start web-based OAuth flow
            # Store consumer credentials in session for callback
            session['consumer_key'] = consumer_key
            session['consumer_secret'] = consumer_secret

            # Generate callback URL
            callback_url = url_for('main.oauth_callback', _external=True)

            # Get authorization URL with callback
            request_token, request_token_secret, authorize_url = client.get_authorize_url_with_callback(callback_url)

            # Store request tokens in session for callback
            session['request_token'] = request_token
            session['request_token_secret'] = request_token_secret

            # Redirect user to Discogs authorization page
            return redirect(authorize_url)

        # Store credentials in session for later use
        session['consumer_key'] = consumer_key
        session['consumer_secret'] = consumer_secret

        # Store tokens in session
        session['oauth_token'] = client.oauth_token
        session['oauth_secret'] = client.oauth_token_secret

        # Store credentials in .env file (but not during tests)
        if not is_test_environment():
            try:
                # Update or create .env file with credentials
                set_key('.env', 'DISCOGS_CONSUMER_KEY', consumer_key)
                set_key('.env', 'DISCOGS_CONSUMER_SECRET', consumer_secret)
                if client.oauth_token:
                    set_key('.env', 'DISCOGS_OAUTH_TOKEN', str(client.oauth_token))
                if client.oauth_token_secret:
                    set_key('.env', 'DISCOGS_OAUTH_TOKEN_SECRET', str(client.oauth_token_secret))
                
                current_app.logger.info('Credentials stored in .env file')
            except Exception as env_error:
                current_app.logger.error(f"Failed to update .env file: {str(env_error)}")

        flash('Successfully authenticated!', 'success')
        return redirect(url_for('main.landing'))

    except Exception as e:
        current_app.logger.error(f"Authentication error: {str(e)}")
        flash('An error occurred during authentication', 'error')
        return redirect(url_for('main.landing'))

@bp.route('/oauth-callback')
def oauth_callback():
    """
    Handle OAuth callback from Discogs after user authorization
    """
    try:
        # Get OAuth verifier from query parameters
        oauth_verifier = request.args.get('oauth_verifier')
        oauth_token = request.args.get('oauth_token')

        if not oauth_verifier or not oauth_token:
            error_message = 'Invalid OAuth callback - missing verifier or token'
            current_app.logger.error(error_message)
            return render_template('oauth_callback.html', success=False, error_message=error_message)

        # Retrieve consumer credentials and request tokens from session
        consumer_key = session.get('consumer_key')
        consumer_secret = session.get('consumer_secret')
        request_token = session.get('request_token')
        request_token_secret = session.get('request_token_secret')

        if not all([consumer_key, consumer_secret, request_token, request_token_secret]):
            error_message = 'Session expired - please start authentication again'
            current_app.logger.error(error_message)
            return render_template('oauth_callback.html', success=False, error_message=error_message)

        # Initialize client with consumer credentials
        client = DiscogsCollectionClient(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            useragent=USERAGENT,
            oauth_token=request_token,
            oauth_token_secret=request_token_secret
        )

        # Complete OAuth flow
        access_token, access_token_secret = client.complete_oauth(oauth_verifier)

        # Store tokens in session
        session['oauth_token'] = access_token
        session['oauth_secret'] = access_token_secret

        # Store credentials in .env file (but not during tests)
        if not is_test_environment():
            try:
                set_key('.env', 'DISCOGS_CONSUMER_KEY', consumer_key)
                set_key('.env', 'DISCOGS_CONSUMER_SECRET', consumer_secret)
                set_key('.env', 'DISCOGS_OAUTH_TOKEN', str(access_token))
                set_key('.env', 'DISCOGS_OAUTH_TOKEN_SECRET', str(access_token_secret))
                current_app.logger.info('OAuth credentials stored in .env file')
            except Exception as env_error:
                current_app.logger.error(f"Failed to update .env file: {str(env_error)}")

        # Show success page and then redirect
        return render_template('oauth_callback.html', success=True)

    except Exception as e:
        current_app.logger.error(f"OAuth callback error: {str(e)}")
        error_message = f'An error occurred during OAuth callback: {str(e)}'
        return render_template('oauth_callback.html', success=False, error_message=error_message)

@bp.route('/folders', methods=['GET', 'POST'])
def folders():
    """
    Display collection folders from Discogs
    """

    # Handle POST request when folder is selected
    if request.method == 'POST':
        folder_id = request.form.get('folder_id')

        if folder_id:
            return redirect(url_for('main.releases', folder_id=folder_id))

    # Check if authenticated
    if 'oauth_token' not in session or 'oauth_secret' not in session:
        flash('Please authenticate first', 'error')
        return redirect(url_for('main.authenticate_page'))

    try:
        # Initialize client with credentials and tokens from session
        client = DiscogsCollectionClient(
            consumer_key=session.get('consumer_key', ''),
            consumer_secret=session.get('consumer_secret', ''),
            useragent=USERAGENT,
            oauth_token=session.get('oauth_token', ''),
            oauth_token_secret=session.get('oauth_secret', '')
        )

        # Authenticate with Discogs API
        client.authenticate()


        # Get collection folders
        folders_list = client.get_collection_folders()


        if not folders_list:
            flash('No folders found in your collection', 'info')
            return render_template('folders.html', folders=[], has_folders=False)
        return render_template('folders.html', folders=folders_list, has_folders=True)

    except Exception as e:
        current_app.logger.error(f"Error fetching folders: {str(e)}")
        flash('Failed to retrieve collection folders', 'error')
        return redirect(url_for('main.landing'))

@bp.route('/releases/<int:folder_id>', methods=['GET', 'POST'])
def releases(folder_id):
    """
    Display releases from a specific folder
    """

    # Handle POST request when releases are selected and preview is to be generated
    if request.method == 'POST' and 'action' in request.form:
        

        release_ids = request.form.getlist('release_ids')
        

        if release_ids:
            return redirect(url_for('main.preview_csv', release_ids=release_ids))

    # Check if authenticated
    if 'oauth_token' not in session or 'oauth_secret' not in session:
        flash('Please authenticate first', 'error')
        return redirect(url_for('main.authenticate_page'))

    try:
        # Initialize client with credentials and tokens from session
        client = DiscogsCollectionClient(
            consumer_key=session.get('consumer_key', ''),
            consumer_secret=session.get('consumer_secret', ''),
            useragent=USERAGENT,
            oauth_token=session.get('oauth_token', ''),
            oauth_token_secret=session.get('oauth_secret', '')
        )

        # Authenticate with Discogs API
        client.authenticate()


        # Get releases from folder
        releases_dict = client.get_collection_releases_by_folder(folder_id)


        if not releases_dict:
            flash('No releases found in this folder', 'info')
            return redirect(url_for('main.folders'))

        # Convert dict values to list for easier processing
        releases_list = []
        for folder_releases in releases_dict.values():
            releases_list.append(folder_releases)


        # Handle POST requests (e.g., sorting)
        if request.method == 'POST':
            # If sorting was requested, redirect back to same page with sort parameter
            if 'sort_only' in request.form:
                sort_order = request.form.get('sort_order', 'newest_first')
                return redirect(url_for('main.releases', folder_id=folder_id, sort=sort_order))

        # Get sort parameter from URL
        sort_order = request.args.get('sort', 'artist_az')

        # Sort releases based on sort order
        if sort_order == 'artist_az':
            sorted_releases = sorted(
                releases_list,
                key=lambda x: (
                    x.get('artist', '').lower(),
                    int(x.get('year', 0)) if str(x.get('year', '')).isdigit() else 0
                ),
                reverse=False
            )
        elif sort_order == 'artist_za':
            sorted_releases = sorted(
                releases_list,
                key=lambda x: (
                    x.get('artist', '').lower(),
                    int(x.get('year', 0)) if str(x.get('year', '')).isdigit() else 0
                ),
                reverse=True
            )
        elif sort_order == 'oldest_first':
            sorted_releases = sorted(
                releases_list,
                key=lambda x: int(x.get('year', 0)) if str(x.get('year', '')).isdigit() else 0,
                reverse=False
            )
        elif sort_order == 'date_added':
            sorted_releases = sorted(
                releases_list,
                key=lambda x: x.get('date_added', ''),
                reverse=True
            )
        else:  # Default: newest_first
            sorted_releases = sorted(
                releases_list,
                key=lambda x: int(x.get('year', 0)) if str(x.get('year', '')).isdigit() else 0,
                reverse=True
            )

        # Get the actual folder name
        folder_name = client.get_folder_name_by_id(folder_id)

        return render_template(
            'releases.html',
            folder_id=folder_id,
            releases=sorted_releases,
            sort_by=request.args.get('sort', 'date'),
            folder_name=folder_name
        )

    except Exception as e:
        current_app.logger.error(f"Error fetching releases: {str(e)}")
        flash('Failed to retrieve releases from folder', 'error')
        return redirect(url_for('main.landing'))


@bp.route('/preview/', methods=['GET', 'POST'])
def preview_csv():
    """
    Generate CSV preview based on selected releases and redirect to editable preview
    """

    # Check if authenticated
    if 'oauth_token' not in session or 'oauth_secret' not in session:
        flash('Please authenticate first', 'error')
        return redirect(url_for('main.authenticate_page'))

    try:
        # Get selected release IDs from form
        selected_ids = request.args.getlist('release_ids')

        if not selected_ids:
            flash('No releases selected', 'error')
            return redirect(request.referrer or url_for('main.folders'))

        client = DiscogsCollectionClient(
            consumer_key=session.get('consumer_key', ''),
            consumer_secret=session.get('consumer_secret', ''),
            useragent=USERAGENT,
            oauth_token=session.get('oauth_token', ''),
            oauth_token_secret=session.get('oauth_secret', '')
        )

        # Authenticate with Discogs API
        client.authenticate()

        # Get releases for selected IDs directly using release IDs
        # This is more efficient than getting all folders and filtering
        releases_data = []
        counter = 0
        for release_id in selected_ids:
            try:
               # Convert to int explicitly as get_release_by_releaseid expects int
                release_id_int = int(str(release_id))
                release = client.get_release_by_releaseid(release_id_int)
                if release:
                    releases_data.append(release)
                counter = counter + 1
                current_app.logger.info(f"Processing release {counter} of selected id's")
            except Exception as e:
                current_app.logger.warning(f"Error fetching release {release_id}: {str(e)}")
                continue

        # Convert to list of dicts for processing (each item is already a dict)
        if not isinstance(releases_data, list):
            releases_data = [releases_data]

        if not releases_data:
            flash('No valid releases selected', 'error')
            return redirect(request.referrer or url_for('main.folders'))

        # Process releases for CSV
        processor = DiscogsCollectionProcessor()
        csv_rows = []

        for release in releases_data:
            try:
                # Create the expected format for extract_release_info (wrap in list)
                release_format = [{
                    'id': release.get('id'),
                    'title': release.get('title'),
                    'artist': release.get('artist'),
                    'year': release.get('year'),
                    'format': release.get('format', [])[0].get('name') if release.get('format') else None,
                    'label': release.get('label'),
                    'url': release.get('url')
                }]
                row = processor.extract_release_info(release_format)
                if row:
                    csv_rows.append(row[0])  # Extract the single dict from list
            except Exception as e:
                current_app.logger.warning(f"Error processing release: {str(e)}")
                continue

        # Store preview data in session
        session['csv_preview'] = csv_rows
        session['selected_releases_count'] = len(csv_rows)

        # Redirect to editable preview instead of showing basic preview
        return redirect(url_for('main.editable_preview'))

    except Exception as e:
        current_app.logger.error(f"Error generating preview: {str(e)}")
        flash('Failed to generate CSV preview', 'error')
        return redirect(request.referrer or url_for('main.folders'))

@bp.route('/editable-preview/', methods=['GET'])
def editable_preview():
    """
    Show editable CSV preview based on selected releases
    """
    # Check if authenticated
    if 'oauth_token' not in session or 'oauth_secret' not in session:
        flash('Please authenticate first', 'error')
        return redirect(url_for('main.authenticate_page'))

    # Check if preview exists
    if 'csv_preview' not in session:
        flash('No CSV preview available', 'error')
        return redirect(url_for('main.folders'))

    try:
        # Get the preview data from session
        csv_preview_data = session['csv_preview']
        
        # Create full CSV rows with all template fields
        csv_rows = []
        
        # Read template to get the format
        with open('templates/qrfactory_discogs_collection_template.csv', 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            template_format = next(reader)
        
        # Create full rows for each release
        for release in csv_preview_data:
            # Start with template format
            row_data = {}
             
            # Map the basic fields
            for i, field_name in enumerate(header):
                if field_name == 'Type':
                    row_data[field_name] = template_format[i]  # Keep template value
                elif field_name == 'OutputSize':
                    row_data[field_name] = template_format[i]
                elif field_name == 'FileType':
                    row_data[field_name] = template_format[i]
                elif field_name == 'ColorSpace':
                    row_data[field_name] = template_format[i]
                elif field_name == 'RotationAngle':
                    row_data[field_name] = template_format[i]
                elif field_name == 'ReliabilityLevel':
                    row_data[field_name] = template_format[i]
                elif field_name == 'UseAutoReliabilityLevel':
                    row_data[field_name] = template_format[i]
                elif field_name == 'PixelRoundness':
                    row_data[field_name] = template_format[i]
                elif field_name == 'PixelColorType':
                    row_data[field_name] = template_format[i]
                elif field_name == 'BackgroundColorType':
                    row_data[field_name] = template_format[i]
                elif field_name == 'BackgroundColor':
                    row_data[field_name] = template_format[i]
                elif field_name == 'PixelColorStart':
                    row_data[field_name] = template_format[i]
                elif field_name == 'PixelColorEnd':
                    row_data[field_name] = template_format[i]
                elif field_name == 'GradientAngle':
                    row_data[field_name] = template_format[i]
                elif field_name == 'IconPath':
                    row_data[field_name] = template_format[i]
                elif field_name == 'IconLockToSquares':
                    row_data[field_name] = template_format[i]
                elif field_name == 'IconSizePercent':
                    row_data[field_name] = template_format[i]
                elif field_name == 'IconBorderType':
                    row_data[field_name] = template_format[i]
                elif field_name == 'IconBorderPercent':
                    row_data[field_name] = template_format[i]
                elif field_name == 'IconBorderSquareCornerSize':
                    row_data[field_name] = template_format[i]
                elif field_name == 'IconBorderColor':
                    row_data[field_name] = template_format[i]
                elif field_name == 'BottomText':
                    bottom_text = template_format[i]
                    bottom_text = bottom_text.replace('{artist}', release.get('artist', ''))
                    bottom_text = bottom_text.replace('{title}', release.get('title', ''))
                    bottom_text = bottom_text.replace('{year}', str(release.get('year', '')))
                    row_data[field_name] = bottom_text
                elif field_name == 'BottomTextSize':
                    row_data[field_name] = template_format[i]
                elif field_name == 'BottomTextColor':
                    row_data[field_name] = template_format[i]
                elif field_name == 'BottomTextFont':
                    row_data[field_name] = template_format[i]
                elif field_name == 'BottomTextFontStyle':
                    row_data[field_name] = template_format[i]
                elif field_name == 'SafeZonePercent':
                    row_data[field_name] = template_format[i]
                elif field_name == 'SafeZoneColor':
                    row_data[field_name] = template_format[i]
                elif field_name == 'Content':
                    row_data[field_name] = template_format[i].replace('{url}', release.get('url', ''))
                elif field_name == 'FileName':
                    filename = template_format[i].replace('{filename}', str(release.get('id', '')))
                    row_data[field_name] = filename
                elif field_name == 'Artist':
                    row_data[field_name] = release.get('Artist', '')
                elif field_name == 'Title':
                    row_data[field_name] = release.get('Title', '')
                elif field_name == 'URL':
                    row_data[field_name] = release.get('URL', '')
                else:
                    row_data[field_name] = ''
             
            csv_rows.append(row_data)

        return render_template(
            'editable_preview.html',
            csv_rows=csv_rows,
            count=len(csv_rows)
        )

    except Exception as e:
        current_app.logger.error(f"Error showing editable preview: {str(e)}")
        flash('Failed to show editable CSV preview', 'error')
        return redirect(url_for('main.folders'))

@bp.route('/generate-editable-csv', methods=['POST'])
def generate_editable_csv():
    """
    Generate CSV from editable preview data
    """
    # Check if authenticated
    if 'oauth_token' not in session or 'oauth_secret' not in session:
        flash('Please authenticate first', 'error')
        return redirect(url_for('main.authenticate_page'))

    try:
        # Get row count
        row_count = int(request.form.get('row_count', 0))
        
        if row_count == 0:
            flash('No data to generate CSV', 'error')
            return redirect(url_for('main.folders'))
        
        # Read template header
        with open('templates/qrfactory_discogs_collection_template.csv', 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
        
        # Collect all editable data
        csv_rows = []
        for i in range(1, row_count + 1):
            row_data = {}
            
            # Get all fields from form
            for field_name in header:
                # Convert field name to parameter name
                if field_name == 'Artist':
                    row_data[field_name] = request.form.get(f'artist_{i}', '')
                elif field_name == 'Title':
                    row_data[field_name] = request.form.get(f'title_{i}', '')
                elif field_name == 'URL':
                    row_data[field_name] = request.form.get(f'url_{i}', '')
                elif field_name == 'Type':
                    row_data[field_name] = request.form.get(f'type_{i}', '')
                elif field_name == 'OutputSize':
                    row_data[field_name] = request.form.get(f'output_size_{i}', '')
                elif field_name == 'FileType':
                    row_data[field_name] = request.form.get(f'file_type_{i}', '')
                elif field_name == 'ColorSpace':
                    row_data[field_name] = request.form.get(f'color_space_{i}', '')
                elif field_name == 'RotationAngle':
                    row_data[field_name] = request.form.get(f'rotation_angle_{i}', '')
                elif field_name == 'ReliabilityLevel':
                    row_data[field_name] = request.form.get(f'reliability_level_{i}', '')
                elif field_name == 'UseAutoReliabilityLevel':
                    row_data[field_name] = request.form.get(f'use_auto_reliability_{i}', '')
                elif field_name == 'PixelRoundness':
                    row_data[field_name] = request.form.get(f'pixel_roundness_{i}', '')
                elif field_name == 'PixelColorType':
                    row_data[field_name] = request.form.get(f'pixel_color_type_{i}', '')
                elif field_name == 'BackgroundColorType':
                    row_data[field_name] = request.form.get(f'background_color_type_{i}', '')
                elif field_name == 'BackgroundColor':
                    row_data[field_name] = request.form.get(f'background_color_{i}', '')
                elif field_name == 'PixelColorStart':
                    row_data[field_name] = request.form.get(f'pixel_color_start_{i}', '')
                elif field_name == 'PixelColorEnd':
                    row_data[field_name] = request.form.get(f'pixel_color_end_{i}', '')
                elif field_name == 'GradientAngle':
                    row_data[field_name] = request.form.get(f'gradient_angle_{i}', '')
                elif field_name == 'IconPath':
                    row_data[field_name] = request.form.get(f'icon_path_{i}', '')
                elif field_name == 'IconLockToSquares':
                    row_data[field_name] = request.form.get(f'icon_lock_{i}', '')
                elif field_name == 'IconSizePercent':
                    row_data[field_name] = request.form.get(f'icon_size_{i}', '')
                elif field_name == 'IconBorderType':
                    row_data[field_name] = request.form.get(f'icon_border_type_{i}', '')
                elif field_name == 'IconBorderPercent':
                    row_data[field_name] = request.form.get(f'icon_border_percent_{i}', '')
                elif field_name == 'IconBorderSquareCornerSize':
                    row_data[field_name] = request.form.get(f'icon_border_corner_{i}', '')
                elif field_name == 'IconBorderColor':
                    row_data[field_name] = request.form.get(f'icon_border_color_{i}', '')
                elif field_name == 'BottomText':
                    row_data[field_name] = request.form.get(f'bottom_text_{i}', '')
                elif field_name == 'BottomTextSize':
                    row_data[field_name] = request.form.get(f'bottom_text_size_{i}', '')
                elif field_name == 'BottomTextColor':
                    row_data[field_name] = request.form.get(f'bottom_text_color_{i}', '')
                elif field_name == 'BottomTextFont':
                    row_data[field_name] = request.form.get(f'bottom_text_font_{i}', '')
                elif field_name == 'BottomTextFontStyle':
                    row_data[field_name] = request.form.get(f'bottom_text_font_style_{i}', '')
                elif field_name == 'SafeZonePercent':
                    row_data[field_name] = request.form.get(f'safe_zone_percent_{i}', '')
                elif field_name == 'SafeZoneColor':
                    row_data[field_name] = request.form.get(f'safe_zone_color_{i}', '')
                elif field_name == 'Content':
                    row_data[field_name] = request.form.get(f'content_{i}', '')
                elif field_name == 'FileName':
                    row_data[field_name] = request.form.get(f'filename_{i}', '')
                else:
                    row_data[field_name] = ''
            
            csv_rows.append(row_data)
        
        # Generate CSV content
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        
        # Write header
        writer.writerow(header)
        
        # Write data rows
        for row in csv_rows:
            row_values = [row.get(field, '') for field in header]
            writer.writerow(row_values)
        
        csv_content = csv_buffer.getvalue()

        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'discogs_collection_{timestamp}.csv'

        # Return as downloadable file
        return send_file(
            io.BytesIO(csv_content.encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        current_app.logger.error(f"Error generating editable CSV: {str(e)}")
        flash('Failed to generate CSV file', 'error')
        return redirect(url_for('main.folders'))

@bp.route('/download-csv', methods=['POST'])
def download_csv():
    """
    Generate and download the final CSV file
    """
    # Check if authenticated
    if 'oauth_token' not in session or 'oauth_secret' not in session:
        flash('Please authenticate first', 'error')
        return redirect(url_for('main.authenticate_page'))

    # Check if preview exists
    if 'csv_preview' not in session:
        flash('No CSV preview available', 'error')
        return redirect(url_for('main.folders'))

    try:
        # Generate CSV content in memory (as bytes)
        import io

        # Create CSV content directly (simplified approach)
        csv_buffer = io.StringIO()

        # Add header from template
        with open('templates/qrfactory_discogs_collection_template.csv', 'r') as f:
            reader = csv.reader(f)
            header = next(reader)

        writer = csv.writer(csv_buffer)
        writer.writerow(header)

        # Add data rows
        for release in session['csv_preview']:
            row = [
                release.get('Artist', ''),
                release.get('Title', ''),
                release.get('URL', '')
            ]
            writer.writerow(row)

        csv_content = csv_buffer.getvalue()

        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'discogs_collection_{timestamp}.csv'

        # Return as downloadable file
        return send_file(
            io.BytesIO(csv_content.encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        current_app.logger.error(f"Error generating CSV: {str(e)}")
        flash('Failed to generate CSV file', 'error')
        return redirect(url_for('main.folders'))

@bp.route('/clear-session', methods=['POST'])
def clear_session():
    """
    Clear user session data
    """
    session.clear()
    flash('Session cleared', 'info')
    return redirect(url_for('main.landing'))
