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
from typing import List, Dict, Any

# Import local modules
from discogs_api_client import DiscogsCollectionClient
from discogs_collection_processor import DiscogsCollectionProcessor

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Main page with authentication form"""
    return render_template('index.html')

@bp.route('/authenticate', methods=['POST'])
def authenticate():
    """
    Handle OAuth authentication with Discogs API
    """
    consumer_key = request.form.get('consumer_key')
    consumer_secret = request.form.get('consumer_secret')

    if not consumer_key or not consumer_secret:
        flash('Consumer key and secret are required', 'error')
        return redirect(url_for('main.index'))

    try:
        # Initialize client
        client = DiscogsCollectionClient(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )

        # Authenticate with Discogs API (method doesn't return value, sets client attributes)
        client.authenticate()

        # Store credentials in session for later use
        session['consumer_key'] = consumer_key
        session['consumer_secret'] = consumer_secret

        # Store tokens in session
        session['oauth_token'] = client.oauth_token
        session['oauth_secret'] = client.oauth_token_secret

        flash('Successfully authenticated!', 'success')
        return redirect(url_for('main.folders'))

    except Exception as e:
        current_app.logger.error(f"Authentication error: {str(e)}")
        flash('An error occurred during authentication', 'error')
        return redirect(url_for('main.index'))

@bp.route('/folders')
def folders():
    """
    Display collection folders from Discogs
    """
    # Check if authenticated
    if 'oauth_token' not in session or 'oauth_secret' not in session:
        flash('Please authenticate first', 'error')
        return redirect(url_for('main.index'))

    try:
        # Initialize client with credentials from session
        client = DiscogsCollectionClient(
            consumer_key=session.get('consumer_key', ''),
            consumer_secret=session.get('consumer_secret', '')
        )

        # Set OAuth tokens if they exist in session
        if 'oauth_token' in session and 'oauth_secret' in session:
            client.oauth_token = session['oauth_token']
            client.oauth_token_secret = session['oauth_secret']

        # Get collection folders
        folders_list = client.get_collection_folders()

        if not folders_list:
            flash('No folders found in your collection', 'info')
            return render_template('folders.html', folders=[], has_folders=False)
        return render_template('folders.html', folders=folders_list, has_folders=True)

    except Exception as e:
        current_app.logger.error(f"Error fetching folders: {str(e)}")
        flash('Failed to retrieve collection folders', 'error')
        return redirect(url_for('main.index'))

@bp.route('/releases/<int:folder_id>')
def releases(folder_id):
    """
    Display releases from a specific folder
    """
    # Check if authenticated
    if 'oauth_token' not in session or 'oauth_secret' not in session:
        flash('Please authenticate first', 'error')
        return redirect(url_for('main.index'))

    try:
        # Initialize client with credentials from session
        client = DiscogsCollectionClient(
            consumer_key=session.get('consumer_key', ''),
            consumer_secret=session.get('consumer_secret', '')
        )

        # Set OAuth tokens if they exist in session
        if 'oauth_token' in session and 'oauth_secret' in session:
            client.oauth_token = session['oauth_token']
            client.oauth_token_secret = session['oauth_secret']

        # Get releases from folder
        releases_dict = client.get_collection_releases_by_folder(folder_id)

        if not releases_dict:
            flash('No releases found in this folder', 'info')
            return redirect(url_for('main.folders'))

        # Convert dict values to list for easier processing
        releases_list = []
        for folder_releases in releases_dict.values():
            releases_list.extend(folder_releases)

        # Sort by date (newest first)
        sorted_releases = sorted(
            releases_list,
            key=lambda x: x.get('year', 0),
            reverse=True
        )

        return render_template(
            'releases.html',
            folder_id=folder_id,
            releases=sorted_releases,
            sort_by=request.args.get('sort', 'date')
        )

    except Exception as e:
        current_app.logger.error(f"Error fetching releases: {str(e)}")
        flash('Failed to retrieve releases from folder', 'error')
        return redirect(url_for('main.folders'))

@bp.route('/preview', methods=['POST'])
def preview_csv():
    """
    Generate CSV preview based on selected releases
    """
    # Check if authenticated
    if 'oauth_token' not in session or 'oauth_secret' not in session:
        flash('Please authenticate first', 'error')
        return redirect(url_for('main.index'))

    try:
        # Get selected release IDs from form
        selected_ids = request.form.getlist('release_ids')

        if not selected_ids:
            flash('No releases selected', 'error')
            return redirect(request.referrer or url_for('main.folders'))

        client = DiscogsCollectionClient(
            consumer_key=session.get('consumer_key', ''),
            consumer_secret=session.get('consumer_secret', '')
        )

        # Set OAuth tokens if they exist in session
        if 'oauth_token' in session and 'oauth_secret' in session:
            client.oauth_token = session['oauth_token']
            client.oauth_token_secret = session['oauth_secret']

        # Get releases for selected IDs - need to get all folders first
        # Then find the releases with matching IDs
        all_folders = client.get_collection_folders()

        releases_data = []
        for folder in all_folders:
            try:
                # Get releases from this specific folder - convert to int explicitly
                folder_id = int(str(folder.id))
                folder_releases_dict = client.get_collection_releases_by_folder(folder_id)
                if folder_releases_dict:
                    # Iterate through all release lists in the dictionary
                    for release_list in folder_releases_dict.values():
                        # Filter releases by selected IDs
                        filtered_releases = [
                            r for r in release_list
                            if str(r.get('id')) in selected_ids
                        ]
                        releases_data.extend(filtered_releases)
            except Exception as e:
                current_app.logger.warning(f"Error fetching releases from folder {folder.id}: {str(e)}")
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
                    'format': release.get('format'),
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

        return render_template(
            'preview.html',
            csv_rows=csv_rows,
            count=len(csv_rows)
        )

    except Exception as e:
        current_app.logger.error(f"Error generating preview: {str(e)}")
        flash('Failed to generate CSV preview', 'error')
        return redirect(request.referrer or url_for('main.folders'))

@bp.route('/download-csv', methods=['POST'])
def download_csv():
    """
    Generate and download the final CSV file
    """
    # Check if authenticated
    if 'oauth_token' not in session or 'oauth_secret' not in session:
        flash('Please authenticate first', 'error')
        return redirect(url_for('main.index'))

    # Check if preview exists
    if 'csv_preview' not in session:
        flash('No CSV preview available', 'error')
        return redirect(url_for('main.folders'))

    try:
        processor = DiscogsCollectionProcessor()

        # Generate CSV content in memory (as bytes)
        import io

        # Create CSV content directly (simplified approach)
        csv_buffer = io.StringIO()

        # Add header from template
        with open('qrfactory_discogs_collection_template.csv', 'r') as f:
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
    return redirect(url_for('main.index'))