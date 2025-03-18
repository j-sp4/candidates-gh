import os
import csv
import time
import json
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

# Load environment variables
load_dotenv()

# GitHub API configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable is not set")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Rate limiting parameters
MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds

def search_repositories(keywords: List[str], min_stars: int = 10, limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Search GitHub repositories based on keywords.
    
    Args:
        keywords: List of keywords to search for
        min_stars: Minimum number of stars for repositories
        limit: Maximum number of repositories to return
        
    Returns:
        List of repository data dictionaries
    """
    all_repos = []
    
    for keyword in keywords:
        print(f"Searching repositories with keyword: {keyword}")
        page = 1
        per_page = 100  # GitHub API maximum
        
        while len(all_repos) < limit:
            query = f"{keyword} in:description stars:>={min_stars}"
            url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&page={page}&per_page={per_page}"
            
            response = make_github_request(url)
            if not response:
                break
                
            repos = response.get("items", [])
            if not repos:
                break
                
            # Extract relevant information from each repository
            for repo in repos:
                repo_data = {
                    "id": repo.get("id"),
                    "name": repo.get("name"),
                    "full_name": repo.get("full_name"),
                    "html_url": repo.get("html_url"),
                    "description": repo.get("description"),
                    "created_at": repo.get("created_at"),
                    "updated_at": repo.get("updated_at"),
                    "pushed_at": repo.get("pushed_at"),
                    "homepage": repo.get("homepage"),
                    "size": repo.get("size"),
                    "stargazers_count": repo.get("stargazers_count"),
                    "watchers_count": repo.get("watchers_count"),
                    "language": repo.get("language"),
                    "forks_count": repo.get("forks_count"),
                    "open_issues_count": repo.get("open_issues_count"),
                    "license": (repo.get("license") or {}).get("name"),
                    "topics": repo.get("topics", []),
                    "has_wiki": repo.get("has_wiki"),
                    "has_pages": repo.get("has_pages"),
                    "has_projects": repo.get("has_projects"),
                    "has_downloads": repo.get("has_downloads"),
                    "archived": repo.get("archived"),
                    "disabled": repo.get("disabled"),
                    "visibility": repo.get("visibility"),
                    "default_branch": repo.get("default_branch"),
                    "matched_keyword": keyword
                }
                
                # Check if repo is already in the list (from another keyword)
                if not any(r["id"] == repo_data["id"] for r in all_repos):
                    all_repos.append(repo_data)
                    
                if len(all_repos) >= limit:
                    break
            
            # Check if we've reached the last page
            if len(repos) < per_page:
                break
                
            page += 1
            time.sleep(1)  # Be nice to the API
    
    print(f"Found {len(all_repos)} unique repositories")
    return all_repos

def get_repository_details(repo_full_name: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific repository.
    
    Args:
        repo_full_name: Full name of the repository (owner/repo)
        
    Returns:
        Dictionary with repository details or None if request fails
    """
    url = f"https://api.github.com/repos/{repo_full_name}"
    return make_github_request(url)

def get_repository_languages(repo_full_name: str) -> Dict[str, int]:
    """
    Get language breakdown for a repository.
    
    Args:
        repo_full_name: Full name of the repository (owner/repo)
        
    Returns:
        Dictionary mapping language names to byte counts
    """
    url = f"https://api.github.com/repos/{repo_full_name}/languages"
    response = make_github_request(url)
    return response or {}

def get_repository_contributors(repo_full_name: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get contributors for a repository.
    
    Args:
        repo_full_name: Full name of the repository (owner/repo)
        limit: Maximum number of contributors to return
        
    Returns:
        List of contributor data dictionaries
    """
    contributors = []
    page = 1
    per_page = 100  # GitHub API maximum
    
    while len(contributors) < limit:
        url = f"https://api.github.com/repos/{repo_full_name}/contributors?page={page}&per_page={per_page}"
        response = make_github_request(url)
        
        if not response or not isinstance(response, list):
            break
            
        if not response:
            break
            
        contributors.extend(response)
        
        if len(response) < per_page:
            break
            
        page += 1
        time.sleep(1)  # Be nice to the API
    
    # Limit the number of contributors
    return contributors[:limit]

def get_user_details(username: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a GitHub user.
    
    Args:
        username: GitHub username
        
    Returns:
        Dictionary with user details or None if request fails
    """
    url = f"https://api.github.com/users/{username}"
    return make_github_request(url)

def make_github_request(url: str) -> Optional[Any]:
    """
    Make a request to the GitHub API with retry logic for rate limiting.
    
    Args:
        url: GitHub API URL
        
    Returns:
        JSON response data or None if all retries fail
    """
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=HEADERS)
            
            # Check for rate limiting
            if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers and int(response.headers['X-RateLimit-Remaining']) == 0:
                reset_time = int(response.headers['X-RateLimit-Reset'])
                sleep_time = max(reset_time - time.time(), 0) + 1
                print(f"Rate limit exceeded. Sleeping for {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
                continue
                
            # Check for other errors
            if response.status_code != 200:
                print(f"Error: {response.status_code} - {response.text}")
                time.sleep(RETRY_DELAY)
                continue
                
            return response.json()
            
        except Exception as e:
            print(f"Request error: {str(e)}")
            time.sleep(RETRY_DELAY)
    
    print(f"Failed to get data from {url} after {MAX_RETRIES} attempts")
    return None

def save_to_csv(data: List[Dict[str, Any]], filename: str, fieldnames: Optional[List[str]] = None) -> None:
    """
    Save data to a CSV file.
    
    Args:
        data: List of dictionaries to save
        filename: Output filename
        fieldnames: List of field names for CSV header (optional)
    """
    if not data:
        print(f"No data to save to {filename}")
        return
        
    # If fieldnames not provided, use keys from first item
    if not fieldnames:
        fieldnames = list(data[0].keys())
        
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in data:
            # Handle lists and dictionaries by converting to JSON strings
            row = {}
            for key, value in item.items():
                if key in fieldnames:
                    if isinstance(value, (list, dict)):
                        row[key] = json.dumps(value)
                    else:
                        row[key] = value
            writer.writerow(row)
            
    print(f"Data saved to {filename}")

def process_repositories(keywords: List[str], min_stars: int = 10, repo_limit: int = 1000, 
                        contributor_limit: int = 50) -> None:
    """
    Main function to process repositories and contributors.
    
    Args:
        keywords: List of keywords to search for
        min_stars: Minimum number of stars for repositories
        repo_limit: Maximum number of repositories to process
        contributor_limit: Maximum number of contributors per repository
    """
    # Create output directory
    output_dir = Path("github_data_2")
    output_dir.mkdir(exist_ok=True)
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Search repositories
    repositories = search_repositories(keywords, min_stars, repo_limit)
    
    if not repositories:
        print("No repositories found matching the criteria")
        return
        
    # Save repositories to CSV
    repo_filename = output_dir / f"repositories_{timestamp}.csv"
    save_to_csv(repositories, repo_filename)
    
    # Process each repository for additional details and contributors
    # Using a dict to track aggregated contributor data keyed by username
    all_contributors: Dict[str, Dict[str, Any]] = {} 
    
    for i, repo in enumerate(repositories):
        repo_full_name = repo["full_name"]
        print(f"Processing repository {i+1}/{len(repositories)}: {repo_full_name}")
        
        # Get repository languages and add to repo data
        languages = get_repository_languages(repo_full_name)
        repo["languages"] = languages
        
        # Get contributors for the repository
        contributors = get_repository_contributors(repo_full_name, contributor_limit)
        print(f"Found {len(contributors)} contributors for {repo_full_name}")
        
        # Process each contributor
        for contributor in contributors:
            username = contributor.get("login")
            if not username:
                continue
            
            # Prepare contribution details for the current repository
            contribution_info = {
                "repository": repo_full_name,
                "contributions": contributor.get("contributions"),
                "repository_stars": repo.get("stargazers_count"),
                "repository_language": repo.get("language")
            }
            
            if username in all_contributors:
                # Already processed: update aggregated info
                all_contributors[username]["repository_contributions"].append(contribution_info)
                all_contributors[username]["total_contributions"] += contributor.get("contributions", 0)
            else:
                # New contributor, fetch detailed user information
                user_details = get_user_details(username)
                if not user_details:
                    continue
                all_contributors[username] = {
                    "username": username,
                    "name": user_details.get("name"),
                    "company": user_details.get("company"),
                    "blog": user_details.get("blog"),
                    "location": user_details.get("location"),
                    "email": user_details.get("email"),
                    "bio": user_details.get("bio"),
                    "twitter_username": user_details.get("twitter_username"),
                    "public_repos": user_details.get("public_repos"),
                    "public_gists": user_details.get("public_gists"),
                    "followers": user_details.get("followers"),
                    "following": user_details.get("following"),
                    "created_at": user_details.get("created_at"),
                    "updated_at": user_details.get("updated_at"),
                    "html_url": user_details.get("html_url"),
                    "type": user_details.get("type"),
                    "site_admin": user_details.get("site_admin"),
                    "total_contributions": contributor.get("contributions", 0),
                    "repository_contributions": [contribution_info]
                }
                
        # Save updated repository and contributor data periodically
        if (i + 1) % 10 == 0 or i == len(repositories) - 1:
            repo_filename = output_dir / f"repositories_detailed_{timestamp}.csv"
            save_to_csv(repositories, repo_filename)
            
            # Convert the contributors dict to a list for CSV export
            all_contributors_list = list(all_contributors.values())
            if all_contributors_list:
                contributor_filename = output_dir / f"contributors_{timestamp}.csv"
                save_to_csv(all_contributors_list, contributor_filename)
                
        time.sleep(1)  # Be kind to the GitHub API
    
    print(f"Processed {len(repositories)} repositories and tracked contributions from {len(all_contributors)} contributors")

def main():
    """Main entry point for the script."""
    # Define keywords to search for
    keywords = [
    "data pipeline",
    "ETL",
    "data engineering",
    "data infrastructure",
    "data warehouse",
    "data lake",
    "data mesh",
    "data orchestration",
    "data transformation",
    "data integration",
    "ELT",
    "batch processing",
    "stream processing",
    "Apache Airflow",
    "Dagster",
    "Prefect",
    "Luigi",
    "dbt",
    "Apache Spark",
    "Apache Flink",
    "Apache Beam",
    "Kafka",
    "Apache Kafka",
    "streaming data",
    "data ingestion",
    "data catalog",
    "CDC",  # Change Data Capture
    "extract transform load",
    "workflow orchestration",
    "data modeling",
    "data validation",
    "data quality",
    "data governance",
    "data lineage",
    "metadata management",
    "data scheduling",
    "distributed processing",
    "big data",
    "real-time data",
    "Snowflake",
    "BigQuery",
    "Redshift",
    "Athena",
    "lakehouse",
    "Delta Lake",
    "Apache Hudi",
    "Apache Iceberg",
    "OLAP",
    "analytics engineering",
    "SQL transformations",
    "data observability",
    "Fivetran",
    "Stitch",
    "Singer",
    "OpenMetadata",
    "Apache NiFi",
    "workflow scheduler",
    "data automation",
    "schema evolution",
    "data migration",
    "event-driven architecture"
    ]  
    
    # Process repositories with the given keywords
    process_repositories(
        keywords=keywords,
        min_stars=50,  # Repositories with at least 50 stars
        repo_limit=5000,  # Process up to 500 repositories
        contributor_limit=100  # Get up to 30 contributors per repository
    )

if __name__ == "__main__":
    main() 