"""Integration tests for GitHub client utilities."""
import os
import pytest
from utils.github_client import GitHubClient

@pytest.fixture
def client():
    """Create test GitHub client instance."""
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        pytest.skip("GITHUB_TOKEN environment variable not set")
    
    return GitHubClient(
        api_base_url="https://api.github.com",
        token=token,
        org_name="test-org",
        commit_author_name="Test Bot",
        commit_author_email="bot@example.com"
    )

def test_repository_operations(client):
    """Test repository operations."""
    # Create test repository
    repo = client.get_repository(
        "test-repo",
        create=True,
        owning_team="developers"
    )
    assert repo is not None
    
    # Get default branch
    default_branch = client.get_default_branch("test-repo")
    assert default_branch in ["main", "master"]
    
    # Create new branch
    client.create_branch("test-repo", "test-branch")
    
    # Create file
    content = "# Test Repository\n\nThis is a test repository."
    client.write_file(
        repo,
        "README.md",
        content,
        branch="test-branch"
    )
    
    # Create pull request
    pr = client.create_pull_request(
        "test-repo",
        "Test PR",
        "This is a test pull request",
        "test-branch"
    )
    assert pr is not None
    assert pr.title == "Test PR"

def test_team_operations(client):
    """Test team permission operations."""
    repo = client.get_repository("test-repo")
    
    # Set team permissions
    client.set_team_access(repo, "developers", "admin")
    client.set_team_access(repo, "readers", "pull")

def test_repository_topics(client):
    """Test repository topic operations."""
    # Update topics
    topics = ["test", "integration", "template"]
    client.update_repository_topics("test-repo", topics)
    
    # Verify topics
    repo = client.get_repository("test-repo")
    assert set(repo.get_topics()) == set(topics)
