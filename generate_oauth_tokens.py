#!/usr/bin/env python3
"""
CLI tool to generate Discogs OAuth tokens for use with the web application.

This script helps you generate the required OAuth tokens that the web application
needs to authenticate with the Discogs API.
"""

import os
from services.discogs_api_client import DiscogsCollectionClient
from dotenv import load_dotenv, set_key

def main():
    print("=== Discogs OAuth Token Generator ===")
    print()
    
    # Load existing .env file if it exists
    if os.path.exists('.env'):
        load_dotenv()
        
        # Check if consumer credentials are already in .env
        consumer_key = os.getenv('DISCOGS_CONSUMER_KEY', '')
        consumer_secret = os.getenv('DISCOGS_CONSUMER_SECRET', '')
        
        if consumer_key and consumer_secret:
            print(f"Found existing consumer credentials in .env:")
            print(f"  Consumer Key: {consumer_key}")
            print(f"  Consumer Secret: {'*' * len(consumer_secret)}")
            use_existing = input("Use these credentials? [Y/n]: ").strip().lower()
            
            if use_existing != 'n':
                proceed_with_auth(consumer_key, consumer_secret)
                return
    
    # Get consumer credentials from user
    print("Please enter your Discogs API credentials:")
    consumer_key = input("Consumer Key: ").strip()
    consumer_secret = input("Consumer Secret: ").strip()
    
    if not consumer_key or not consumer_secret:
        print("Error: Both Consumer Key and Consumer Secret are required")
        return
    
    # Save consumer credentials to .env
    try:
        set_key('.env', 'DISCOGS_CONSUMER_KEY', consumer_key)
        set_key('.env', 'DISCOGS_CONSUMER_SECRET', consumer_secret)
        print("✓ Consumer credentials saved to .env file")
    except Exception as e:
        print(f"Warning: Could not save to .env file: {e}")
    
    proceed_with_auth(consumer_key, consumer_secret)

def proceed_with_auth(consumer_key, consumer_secret):
    """Proceed with OAuth authentication flow"""
    print("\n=== Starting OAuth Authentication ===")
    
    try:
        # Create client and authenticate
        client = DiscogsCollectionClient(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )
        
        print("Attempting to authenticate with Discogs API...")
        client.authenticate()
        
        print("\n✓ Authentication successful!")
        print(f"User: {client.user.username if client.user else 'Unknown'}")
        print(f"OAuth Token: {client.oauth_token}")
        print(f"OAuth Token Secret: {'*' * len(client.oauth_token_secret) if client.oauth_token_secret else 'None'}")
        
        # Save OAuth tokens to .env
        if client.oauth_token and client.oauth_token_secret:
            try:
                set_key('.env', 'DISCOGS_OAUTH_TOKEN', client.oauth_token)
                set_key('.env', 'DISCOGS_OAUTH_TOKEN_SECRET', client.oauth_token_secret)
                print("\n✓ OAuth tokens saved to .env file")
                print("\nYou can now run the web application:")
                print("  flask run --debug")
            except Exception as e:
                print(f"\nWarning: Could not save OAuth tokens to .env file: {e}")
                print(f"\nPlease manually add these to your .env file:")
                print(f"DISCOGS_OAUTH_TOKEN={client.oauth_token}")
                print(f"DISCOGS_OAUTH_TOKEN_SECRET={client.oauth_token_secret}")
        
    except Exception as e:
        print(f"\n✗ Authentication failed: {e}")
        print("\nPlease check:")
        print("  1. Your consumer key and secret are correct")
        print("  2. You have API access enabled in Discogs developer settings")
        print("  3. Your network connection is working")

if __name__ == "__main__":
    main()