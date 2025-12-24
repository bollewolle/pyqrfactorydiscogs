"""
Discogs API Client for authenticating and retrieving collection data.

This module provides a client class to authenticate with the Discogs API using OAuth
and retrieve collection information including releases organized by folders.
The class handles both existing OAuth credentials and new OAuth flows when needed.
"""

import os
from typing import Dict, List, Optional
import logging

import discogs_client
from discogs_client.models import CollectionFolder
from discogs_client.exceptions import HTTPError, DiscogsAPIError

from dotenv import load_dotenv, set_key, get_key

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5000")
DOTENV_PATH = "../.env"

logger = logging.getLogger(__name__)

def is_test_environment() -> bool:
    """
    Check if the code is running in a test environment.
    
    Returns:
        bool: True if running in test environment, False otherwise
    """
    # Check if we're running in a pytest context by checking if pytest is in the call stack
    import sys
    is_pytest = any('pytest' in module.__name__ for module in sys.modules.values() if hasattr(module, '__name__'))
    
    # Also check environment variables as fallback
    pytest_current_test = os.getenv("PYTEST_CURRENT_TEST", "")
    testing = os.getenv("TESTING", "")
    flask_testing = os.getenv("FLASK_TESTING", "")
    env_result = pytest_current_test != "" or testing == "1" or flask_testing == "1"
    
    result = is_pytest or env_result
    print(f"DEBUG: is_pytest={is_pytest}, PYTEST_CURRENT_TEST='{pytest_current_test}', TESTING='{testing}', FLASK_TESTING='{flask_testing}', is_test_environment={result}")
    return result

class DiscogsCollectionClient:
    """
    A client for interacting with the Discogs API to retrieve collection data.

    This class handles authentication via OAuth user token and provides methods
    to fetch collection items organized by folders from a user's Discogs account.
    """

    def __init__(self, consumer_key: str, consumer_secret: str, useragent: str, oauth_token: Optional[str] = None, oauth_token_secret: Optional[str] = None) -> None:
        """
        Initialize the Discogs client with API credentials.

        Args:
            consumer_key (str): The OAuth consumer key for authentication
            consumer_secret (str): The OAuth consumer secret for authentication
            useragent (str): The useragent to pass onto Discogs
            oauth_token (str, optional): The OAuth access token. Defaults to None.
            oauth_token_secret (str, optional): The OAuth access token secret. Defaults to None.

        Raises:
            ValueError: If credentials are empty or not strings
        """
        if not isinstance(consumer_key, str) or not isinstance(consumer_secret, str):
            raise ValueError("consumer_key and consumer_secret must be strings")
        # Allow empty strings for testing purposes
        if consumer_key is None:
            consumer_key = ""
        if consumer_secret is None:
            consumer_secret = ""

        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.useragent = useragent
        self.oauth_token = oauth_token
        self.oauth_token_secret = oauth_token_secret
        self.client = None
        self.user = None

    def authenticate(self) -> None:
        """
        Authenticate with the Discogs API using OAuth flow.

        This method uses OAuth credentials passed during initialization.
        If no OAuth tokens were provided, it retrieves them from environment variables,
        and if still not found, initiates an automatic OAuth flow without manual intervention.

        Returns:
            None: Sets up client authentication

        Raises:
            ConnectionError: If authentication fails
            ValueError: If consumer credentials are not set or invalid
        """
        try:
            # Load existing .env file
            load_dotenv(DOTENV_PATH)

            # Check if OAuth tokens were provided during initialization
            if self.oauth_token and self.oauth_token_secret:
                # Use the tokens provided during initialization
                self.client = discogs_client.Client(
                    consumer_key=self.consumer_key,
                    consumer_secret=self.consumer_secret,
                    user_agent=self.useragent,
                    token=self.oauth_token,
                    secret=self.oauth_token_secret
                )
            else:
                # If no tokens were passed during init, check environment variables
                current_oauth_token = os.getenv("DISCOGS_OAUTH_TOKEN", "").strip()
                current_oauth_token_secret = os.getenv("DISCOGS_OAUTH_TOKEN_SECRET", "").strip()

                # When tokens exist in environment, create a Client instance with them
                if current_oauth_token and current_oauth_token_secret:
                    self.oauth_token = current_oauth_token
                    self.oauth_token_secret = current_oauth_token_secret

                    # Instantiating the Client class with the consumer key and secret
                    self.client = discogs_client.Client(
                        consumer_key=self.consumer_key,
                        consumer_secret=self.consumer_secret,
                        user_agent=self.useragent,
                        token=self.oauth_token,
                        secret=self.oauth_token_secret
                    )

            # When there are no OAuth credentials, connect to Discogs API and ask to create them (CLI only)
            if not self.oauth_token or not self.oauth_token_secret:
                print("No Discogs API OAuth credentials provided, so let's get them first.")

                # Instantiating the Client class with the consumer key and secret
                self.client = discogs_client.Client(
                    consumer_key=self.consumer_key,
                    consumer_secret=self.consumer_secret,
                    user_agent=self.useragent
                )

                # Get authorization URL and tokens
                self.oauth_token, self.oauth_token_secret, url = self.client.get_authorize_url()

                # Also persist to .env file if possible (but not during tests)
                if not is_test_environment():
                    try:
                        from dotenv import set_key
                        set_key('.env', 'DISCOGS_OAUTH_TOKEN', self.oauth_token)
                        set_key('.env', 'DISCOGS_OAUTH_TOKEN_SECRET', self.oauth_token_secret)
                    except ImportError:
                        # If dotenv is not available, just set environment variables
                        pass

                print(" == Request Token == ")
                print(f"    * oauth_token        = {self.oauth_token}")
                print(f"    * oauth_token_secret = {self.oauth_token_secret}")
                print()
                print(f"Please browse to the following URL: {url}")

                accepted = "n"
                while accepted.lower() == "n":
                    print()
                    accepted = input(f"Have you authorized me at {url} [y/n] :")

                # Get OAuth verifier from user
                oauth_verifier = input("Verification code : ")

                try:
                    self.oauth_token, self.oauth_token_secret = self.client.get_access_token(oauth_verifier)

                    # Update environment variables with final tokens
                    os.environ['DISCOGS_OAUTH_TOKEN'] = self.oauth_token
                    os.environ['DISCOGS_OAUTH_TOKEN_SECRET'] = self.oauth_token_secret

                    # Also persist to .env file if possible (but not during tests)
                    if not is_test_environment():
                        try:
                            from dotenv import set_key
                            set_key('.env', 'DISCOGS_OAUTH_TOKEN', self.oauth_token)
                            set_key('.env', 'DISCOGS_OAUTH_TOKEN_SECRET', self.oauth_token_secret)
                        except ImportError:
                            # If dotenv is not available, just set environment variables
                            pass

                except HTTPError as error:
                    raise ConnectionError(f"Unable to authenticate with Discogs API: {error}")

            # Get user identity from client
            if self.client is not None:
                try:
                    self.user = self.client.identity()
                except AttributeError as error:
                    raise ValueError(f"Discogs client missing identity method: {error}")
            else:
                raise ConnectionError("Client was not initialized properly")

        except Exception as error:
            raise ConnectionError(f"Failed to authenticate with Discogs API: {error}")

    def get_authorize_url_with_callback(self, callback_url: str) -> tuple:
        """
        Get authorization URL with callback for web-based OAuth flow.

        This method initiates the OAuth flow and returns the authorization URL
        along with request token and secret that should be stored temporarily.

        Args:
            callback_url (str): The callback URL to redirect to after authorization

        Returns:
            tuple: (request_token, request_token_secret, authorize_url)

        Raises:
            ConnectionError: If unable to get authorization URL
            ValueError: If consumer credentials are not set or invalid
        """
        if not self.consumer_key or not self.consumer_secret:
            raise ValueError("Consumer key and secret must be set")

        try:
            # Create client without OAuth tokens for initial authorization
            self.client = discogs_client.Client(
                consumer_key=self.consumer_key,
                consumer_secret=self.consumer_secret,
                user_agent=self.useragent
            )

            # Get authorization URL with callback
            request_token, request_token_secret, authorize_url = self.client.get_authorize_url(callback_url=callback_url)

            # Store request tokens temporarily
            self.oauth_token = request_token
            self.oauth_token_secret = request_token_secret

            return request_token, request_token_secret, authorize_url

        except Exception as error:
            raise ConnectionError(f"Failed to get authorization URL: {error}")

    def complete_oauth(self, oauth_verifier: str) -> tuple:
        """
        Complete the OAuth flow by exchanging verifier for access tokens.

        Args:
            oauth_verifier (str): The OAuth verifier received from Discogs callback

        Returns:
            tuple: (access_token, access_token_secret)

        Raises:
            ConnectionError: If unable to complete OAuth flow
            ValueError: If required tokens are missing
        """
        if not self.oauth_token or not self.oauth_token_secret:
            raise ValueError("Request token and secret must be set before completing OAuth")

        try:
            # Ensure client is initialized with request tokens
            if self.client is None:
                self.client = discogs_client.Client(
                    consumer_key=self.consumer_key,
                    consumer_secret=self.consumer_secret,
                    user_agent=self.useragent,
                    token=self.oauth_token,
                    secret=self.oauth_token_secret
                )

            # Exchange verifier for access tokens
            access_token, access_token_secret = self.client.get_access_token(oauth_verifier)

            # Update tokens
            self.oauth_token = access_token
            self.oauth_token_secret = access_token_secret

            # Get user identity
            self.user = self.client.identity()

            # Update environment variables with final tokens (but not during tests)
            if not is_test_environment():
                os.environ['DISCOGS_OAUTH_TOKEN'] = self.oauth_token
                os.environ['DISCOGS_OAUTH_TOKEN_SECRET'] = self.oauth_token_secret

            return access_token, access_token_secret

        except Exception as error:
            raise ConnectionError(f"Failed to complete OAuth: {error}")

    def get_collection_folders(self) -> List[CollectionFolder]:
        """
        Retrieve a list of all collection folders from the authenticated user's Discogs account.

        This method fetches the CollectionFolder objects containing folder names and IDs.
        It requires successful authentication with the Discogs API before calling.

        Returns:
            List[discogs_client.models.CollectionFolder]: List of CollectionFolder objects
            Each object contains folder metadata like id, name, and releases

        Raises:
            ConnectionError: If API request fails or user is not authenticated
        """
        if self.user is not None:
            try:
                # Get all collection folders and their items
                folders = []
                folders = self.user.collection_folders
                
                # Extract just the folder names
                return folders

            except DiscogsAPIError as error:
                raise ConnectionError(f"Failed to retrieve collection folders: {error}")
        else:
            print("User is None")
            return []

    def get_collection_releases_by_folder(self, folder_id: int = 0) -> Dict[int, List[Dict]]:
        """
        Retrieves releases from a specific collection folder.

        Args:
            folder_id (int): The ID of the folder to retrieve releases from. Defaults to 0.

        Returns:
            Dict[int, List[Dict]]: Dictionary where keys are folder IDs and values are lists
            of release dictionaries containing metadata like id, title, artist, year,
            format, label and url

        Raises:
            ConnectionError: If API request fails or user is not authenticated
            KeyError: If the specified folder_id doesn't exist in collection folders
        """
        try:
            # Get all collection folders first
            collection_folders = self.get_collection_folders()

            # Find the folder with matching ID
            folder_with_id = None
            for folder in collection_folders:
                if folder.id == folder_id:
                    folder_with_id = folder
                    break

            if folder_with_id is None:
                raise KeyError(f"Folder with ID {folder_id} not found in collection folders")

            # Organize releases for the selected folder
            release_data = []

            # Extract release details from the releases in this folder
            for r in folder_with_id.releases:
                release_data.append({
                    'id': r.id,
                    'title': r.release.title,
                    'artist': r.release.artists[0].name if r.release.artists else None,
                    'year': r.release.year,
                    'format': r.release.formats,
                    'label': r.release.labels[0].name if r.release.labels else None,
                    'url': r.release.url.split('-', 1)[0],
                    'date_added': r.date_added
                })

            # Convert list to dictionary format as expected by type annotation
            folder_dict = {}
            for idx, releases in enumerate(release_data):
                folder_dict[idx] = releases
            return folder_dict

        except DiscogsAPIError as error:
            raise ConnectionError(f"Failed to retrieve collection items: {error}")

    def get_release_by_releaseid(self, release_id: int) -> Dict:
        """
        Retrieves a specific release by its ID from the Discogs API.

        Args:
            release_id (int): The ID of the release to retrieve

        Returns:
            Dict: Dictionary containing release metadata including id, title, artist,
            year, format, label and url in the same format as get_collection_releases_by_folder

        Raises:
            ConnectionError: If API request fails or user is not authenticated
            ValueError: If release_id is invalid or release data cannot be retrieved
        """
        if self.client is None:
            raise ConnectionError("Client not initialized")

        try:
            # Get the release from Discogs API
            rel_id = self.client.release(release_id)

            # Extract release details in the same format as get_collection_releases_by_folder
            release_data = {
                'id': rel_id.id,
                'title': rel_id.title,
                'artist': rel_id.artists[0].name if rel_id.artists else None,
                'year': rel_id.year,
                'format': rel_id.formats,
                'label': rel_id.labels[0].name if rel_id.labels else None,
                'url': rel_id.url.split('-', 1)[0]
            }

            return release_data

        except DiscogsAPIError as error:
            raise ConnectionError(f"Failed to retrieve release {release_id}: {error}")
        except (AttributeError, IndexError) as error:
            raise ValueError(f"Invalid release data format for release {release_id}: {error}")


def main() -> None:
    """
    Example usage demonstrating Discogs API OAuth authentication and collection data retrieval.

    This main block shows how to:
    1. Initialize the client with consumer credentials from environment variables
    2. Authenticate with the Discogs API (initiating OAuth flow if needed)
    3. Retrieve and display user's collection folders
    4. Fetch releases from a specific folder

    Note: This is for demonstration purposes only.
    """

    # Retrieve credentials from environment variables
    consumer_key = os.getenv("DISCOGS_CONSUMER_KEY", "").strip()
    consumer_secret = os.getenv("DISCOGS_CONSUMER_SECRET", "").strip()

    if not consumer_key or not consumer_secret:
        raise ValueError("Discogs API credentials must be set in environment variables")

    # Create an instance
    collection = DiscogsCollectionClient(
        consumer_key=consumer_key, 
        consumer_secret=consumer_secret, 
        useragent="pyqrfactorydiscogs/1.0"
    )

    # Authenticate with Discogs API
    collection.authenticate()

    user = collection.user

    if user is not None:
        print()
        print(" == User ==")
        print(f"    * username           = {user.username}")
        print(f"    * name               = {user.name}")
        print(" == Access Token ==")
        print(f"    * oauth_token        = {collection.oauth_token}")
        print(f"    * oauth_token_secret = {collection.oauth_token_secret}")
        print(" Authentication complete. Future requests will be signed with the above tokens.")
        
        collection_folders = collection.get_collection_folders()

        # Print list of Folders
        print("The following folders exist in you Collection:")
        for folder in collection_folders:
            print(f"Folder ID: {folder.id} - Folder Name: {folder.name}")
            # print(folder)

        selected_folder = 0
        selected_folder = int(input("Please enter the Folder ID of the folder you want to retrieve the releases for: "))

        # Get releases from selected folder (returns dict format)
        collection_folder_releases = collection.get_collection_releases_by_folder(selected_folder)

        # Print the dictionary of releases
        print(collection_folder_releases)

        # Print releases from the selected folder
        for r in collection_folder_releases.values():
            # Handle dictionary access properly
            release_id = r.get("id", "N/A")
            artist = r.get("artist", "N/A")
            title = r.get("title", "N/A")
            url = r.get("url", "N/A")

            print(f"Release ID: {release_id} - Release Name: {artist} - {title} - URL: {url}")
        

        release_id_single = int(input("Please enter a Release ID of the release you want to retrieve the information for: "))
        release_id_single_result = collection.get_release_by_releaseid(release_id_single)
        print(f"Release ID: {release_id_single_result.get('id', 'N/A')} - Release Name: {release_id_single_result.get('artist', 'N/A')} - {release_id_single_result.get('title', 'N/A')} - URL: {release_id_single_result.get('url', 'N/A')}")

    else:
        print("User is None")


if __name__ == "__main__":
    main()
