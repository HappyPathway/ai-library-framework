"""Integration tests for GitHub client."""
import os
import pytest
from utils.github_client import GitHubClient

def test_github_token():
    """Test GitHub token validity and provide setup instructions."""
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        pytest.skip("""
        GITHUB_TOKEN environment variable not set.
        
        To fix this:
        1. Go to https://github.com/settings/tokens
        2. Click "Generate new token (classic)"
        3. Give it a name like "Python Dev Template Tests"
        4. Select these scopes:
           - repo (Full control of private repositories)
           - read:org (Read org and team membership)
        5. Click "Generate token"
        6. Copy the token and add it to your .env file:
           GITHUB_TOKEN=your_token_here
           
        Note: The token will only be shown once when created!
        """)
    
    if len(token) < 30:
        pytest.skip("""
        GitHub token is too short. Personal access tokens should be much longer.
        Please generate a new token following the instructions above.
        """)

@pytest.fixture
def client():
    """Create test GitHub client instance."""
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        pytest.skip("GITHUB_TOKEN environment variable not set")
    
    try:
        # First try without organization
        client = GitHubClient(
            api_base_url="https://api.github.com",
            token=token,
            commit_author_name="Test Bot",
            commit_author_email="bot@example.com"
        )
        
        # Test authentication by getting user info
        client.client.get_user().login
        return client
    except Exception as e:
        if "401" in str(e) or "Bad credentials" in str(e):
            pytest.skip("""
            GitHub token is invalid. Please generate a new token at:
            https://github.com/settings/tokens
            
            Required scopes:
            - repo (Full control of private repositories)
            - read:org (Read org and team membership)
            
            Then update your .env file:
            GITHUB_TOKEN=your_new_token_here
            """)
        raise

@pytest.mark.integration
def test_repository_operations(client):
    """Test repository operations."""
    try:
        # Get current user's login name
        username = client.client.get_user().login
        
        # First try to get user's repos
        user_repos = list(client.client.get_user().get_repos())
        if not user_repos:
            # Create a test repo if none exist
            repo = client.client.get_user().create_repo(
                "test-repo",
                description="Test repository for Python template",
                auto_init=True
            )
            repo_name = repo.full_name
        else:
            # Use the first repo we find
            repo_name = user_repos[0].full_name
        
        assert repo_name, "Could not find or create a test repository"
        
        # Test basic repository operations
        repo = client.get_repository(repo_name)
        assert repo is not None, "Failed to get test repository"
        
        # Test getting default branch
        default_branch = repo.default_branch
        assert default_branch in ["main", "master"], f"Unexpected default branch: {default_branch}"
        
    except Exception as e:
        if "404" in str(e):
            pytest.skip("No repositories available for testing")
        elif "403" in str(e):
            pytest.skip("Insufficient permissions. Token needs 'repo' scope.")
        raise

@pytest.mark.integration
def test_team_operations(client):
    """Test team permission operations."""
    org_name = os.getenv('GITHUB_ORG_NAME')
    if not org_name:
        pytest.skip("Skipping team operations - GITHUB_ORG_NAME not set")
        
    try:
        # Try to access organization
        org = client.client.get_organization(org_name)
        teams = list(org.get_teams())
        if not teams:
            pytest.skip("No teams available in organization")
    except Exception as e:
        if "404" in str(e):
            pytest.skip("Organization not found or not accessible")
        elif "403" in str(e):
            pytest.skip("Insufficient permissions. Token needs 'read:org' scope.")
        raise

@pytest.mark.integration
def test_repository_topics(client):
    """Test repository topic operations."""
    try:
        # Get user's repositories
        repos = list(client.client.get_user().get_repos())
        if not repos:
            pytest.skip("No repositories available for testing")
            
        # Use the first repository for testing
        repo = repos[0]
        repo_name = repo.full_name
        
        # Save original topics
        original_topics = repo.get_topics()
        
        try:
            # Test adding a test topic
            test_topics = list(set(original_topics + ["test-topic"]))
            client.update_repository_topics(repo_name, test_topics)
            
            # Verify the test topic was added
            updated_topics = repo.get_topics()
            assert "test-topic" in updated_topics
            
        finally:
            # Restore original topics
            client.update_repository_topics(repo_name, original_topics)
            
    except Exception as e:
        if "404" in str(e):
            pytest.skip("No repositories available")
        elif "403" in str(e):
            pytest.skip("Insufficient permissions. Token needs 'repo' scope.")
        raise
