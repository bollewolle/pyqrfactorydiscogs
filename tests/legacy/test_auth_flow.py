#!/usr/bin/env python3
"""
Test script to verify Discogs API authentication flow
"""

import os
from services.discogs_api_client import DiscogsCollectionClient

# Get credentials from environment
consumer_key = os.getenv("DISCOGS_CONSUMER_KEY", "").strip()
consumer_secret = os.getenv("DISCOGS_CONSUMER_SECRET", "").strip()
oauth_token = os.getenv("DISCOGS_OAUTH_TOKEN", "").strip()
oauth_token_secret = os.getenv("DISCOGS_OAUTH_TOKEN_SECRET", "").strip()

print("Testing Discogs API Client...")
print(f"Consumer Key: {'*' * len(consumer_key) if consumer_key else 'NOT SET'}")
print(f"Consumer Secret: {'*' * len(consumer_secret) if consumer_secret else 'NOT SET'}")
print(f"OAuth Token: {'*' * len(oauth_token) if oauth_token else 'NOT SET'}")
print(f"OAuth Token Secret: {'*' * len(oauth_token_secret) if oauth_token_secret else 'NOT SET'}")
print()

if not consumer_key or not consumer_secret:
    print("ERROR: Consumer credentials not set in environment")
    exit(1)

try:
    # Initialize client with all credentials
    client = DiscogsCollectionClient(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        useragent="pyqrfactorydiscogs/1.0",
        oauth_token=oauth_token,
        oauth_token_secret=oauth_token_secret
    )

    print("Client initialized successfully")
    print(f"  - OAuth Token set: {bool(client.oauth_token)}")
    print(f"  - OAuth Secret set: {bool(client.oauth_token_secret)}")
    print()

    # Authenticate
    client.authenticate()
    print("Authentication successful!")
    print(f"User: {client.user.username if client.user else 'None'}")
    print()

    # Get folders
    folders = client.get_collection_folders()
    print(f"Found {len(folders)} folder(s):")
    for folder in folders:
        print(f"  - ID: {folder.id}, Name: {folder.name}")

except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

print()
print("Test completed successfully!")