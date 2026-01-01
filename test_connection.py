"""
Test script to verify Azure DevOps connection.

This script tests the connection to Azure DevOps using credentials
from the .env file.
"""
import sys
from src.ado.client import ADOClient
from src.config.settings import settings


def test_connection():
    """Test ADO connection and print results."""
    print("=" * 60)
    print("Azure DevOps Connection Test")
    print("=" * 60)
    print()
    
    # Check configuration
    if not settings.ado_org:
        print("ERROR: ADO_ORG not set in .env file")
        return False
    
    if not settings.ado_project:
        print("ERROR: ADO_PROJECT not set in .env file")
        return False
    
    if not settings.ado_pat:
        print("ERROR: ADO_PAT not set in .env file")
        return False
    
    print(f"Organization: {settings.ado_org}")
    print(f"Project: {settings.ado_project}")
    print(f"PAT: {'*' * min(len(settings.ado_pat), 20)}...")
    print()
    
    try:
        # Create client
        print("Creating ADO client...")
        client = ADOClient()
        
        # Test connection by fetching projects
        print("Testing connection...")
        response = client.get(
            "_apis/projects",
            params={"api-version": "7.1"}
        )
        
        data = response.json()
        projects = data.get("value", [])
        
        print()
        print("✓ Connection successful!")
        print(f"  Found {len(projects)} project(s) in organization")
        
        # Check if the configured project exists
        project_names = [p.get("name", "") for p in projects]
        if settings.ado_project in project_names:
            print(f"✓ Configured project '{settings.ado_project}' found")
        else:
            print(f"⚠ Warning: Configured project '{settings.ado_project}' not found")
            print(f"  Available projects: {', '.join(project_names[:5])}")
            if len(project_names) > 5:
                print(f"  ... and {len(project_names) - 5} more")
        
        print()
        return True
        
    except Exception as e:
        print()
        print("✗ Connection failed!")
        print(f"  Error: {str(e)}")
        print()
        print("Please check:")
        print("  1. Your .env file has correct ADO_ORG, ADO_PROJECT, and ADO_PAT")
        print("  2. Your PAT has proper permissions")
        print("  3. Your network connection is working")
        print()
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

