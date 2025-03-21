import os
import csv
import json
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pathlib import Path
from datetime import datetime
import logging
import sys
import requests

app = FastAPI(title="GitHub Data Dashboard API")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging (if not already configured)
logging.basicConfig(level=logging.INFO)

# Models
class Repository(BaseModel):
    id: int
    name: str
    full_name: str
    html_url: str
    description: Optional[str] = None
    stargazers_count: int
    forks_count: int
    language: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    matched_keyword: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True

class Contributor(BaseModel):
    username: str
    name: Optional[str] = None
    company: Optional[str] = None
    blog: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    twitter_username: Optional[str] = None
    public_repos: Optional[int] = None
    public_gists: Optional[int] = None
    followers: Optional[int] = None
    following: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    html_url: Optional[str] = None
    account_type: Optional[str] = Field(None, alias="type")
    site_admin: Optional[bool] = None
    total_contributions: int
    repository_contributions: Optional[str] = None  # Change to string to match CSV data
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True

class DashboardStats(BaseModel):
    total_repositories: int
    total_contributors: int
    top_languages: List[Dict[str, Any]]
    top_topics: List[Dict[str, Any]]
    repositories_by_stars: List[Dict[str, Any]]
    contributors_by_followers: List[Dict[str, Any]]

# Helper functions
def get_latest_data_files() -> Dict[str, Path]:
    """Get the latest data files from the github_data directory."""
    data_dir = Path("github_data_2")
    if not data_dir.exists():
        raise HTTPException(status_code=404, detail="No data directory found")
    
    # Find the latest timestamp
    timestamps = set()
    for file in data_dir.glob("*_*.csv"):
        parts = file.stem.split("_")
        if len(parts) >= 2:
            try:
                timestamp = "_".join(parts[-2:])
                timestamps.add(timestamp)
            except (ValueError, IndexError):
                continue
    
    if not timestamps:
        raise HTTPException(status_code=404, detail="No data files found")
    
    latest_timestamp = sorted(timestamps)[-1]
    
    # Get the files with the latest timestamp
    files = {
        "repositories": data_dir / f"repositories_{latest_timestamp}.csv",
        "repositories_detailed": data_dir / f"repositories_detailed_{latest_timestamp}.csv",
        "contributors": data_dir / f"contributors_{latest_timestamp}.csv"
    }
    
    # Verify files exist
    for key, file_path in files.items():
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"{key} data file not found")
    
    return files

def read_csv_file(file_path: str) -> List[Dict[str, Any]]:
    """Read a CSV file and return a list of dictionaries."""
    try:
        # Increase CSV field size limit to handle very large fields
        max_field_limit = sys.maxsize
        while True:
            try:
                csv.field_size_limit(max_field_limit)
                break
            except OverflowError:
                max_field_limit = int(max_field_limit / 10)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            # Get the header row
            reader = csv.reader(f)
            header = next(reader)
            
            # Log the headers for debugging
            logging.info(f"CSV headers for {file_path}: {header}")
            
            # Normalize header names
            normalized_header = []
            for field in header:
                field_name = field.strip().lower().replace(' ', '_')
                
                normalized_header.append(field_name)
            
            # Read the data
            data = []
            for row in reader:
                if len(row) != len(normalized_header):
                    # Skip malformed rows
                    logging.warning(f"Skipping malformed row: {row}")
                    continue
                    
                item = {}
                for i, field in enumerate(normalized_header):
                    # Handle empty values
                    value = row[i].strip() if i < len(row) else ""
                    
                    # Try to convert numeric values
                    if field in ["total_contributions", "followers", "public_repos", "stargazers_count", "forks_count"]:
                        try:
                            value = int(value) if value else 0
                        except ValueError:
                            value = 0
                    
                    item[field] = value
                
                # Special handling for contributions
                # Check if there's any field that might contain contribution data
                # for i, field_name in enumerate(normalized_header):
                #     if 'contribution' in field_name and row[i].strip():
                #         try:
                #             item['contributions'] = int(row[i].strip())
                #             break
                #         except ValueError:
                #             pass
                
                data.append(item)
            
            return data
    except Exception as e:
        logging.error(f"Error reading CSV file {file_path}: {e}")
        raise

# API Routes
@app.get("/")
async def root():
    return {"message": "GitHub Data Dashboard API"}

@app.get("/api/repositories", response_model=List[Repository])
async def get_repositories(
    limit: int = Query(20, description="Number of repositories to return"),
    offset: int = Query(0, description="Offset for pagination"),
    sort_by: str = Query("stargazers_count", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    language: Optional[str] = Query(None, description="Filter by programming language"),
    min_stars: Optional[int] = Query(None, description="Minimum number of stars"),
    keyword: Optional[str] = Query(None, description="Search keyword in name or description")
):
    """Get a list of repositories."""
    try:
        repositories = read_csv_file(get_latest_data_files()["repositories_detailed"])
        
        # Apply filters
        if language:
            repositories = [
                r for r in repositories 
                if r.get("language") and r.get("language").lower() == language.lower()
            ]
            
        if min_stars is not None:
            repositories = [
                r for r in repositories
                if r.get("stargazers_count") and int(r.get("stargazers_count", 0)) >= min_stars
            ]
            
        if keyword:
            repositories = [
                r for r in repositories
                if (r.get("name") and keyword.lower() in r.get("name", "").lower()) or
                   (r.get("description") and keyword.lower() in r.get("description", "").lower())
            ]
        
        # Sort the results
        reverse_sort = sort_order.lower() == "desc"
        
        if sort_by == "stargazers_count":
            repositories.sort(
                key=lambda x: int(x.get("stargazers_count", 0)), 
                reverse=reverse_sort
            )
        elif sort_by == "forks_count":
            repositories.sort(
                key=lambda x: int(x.get("forks_count", 0)), 
                reverse=reverse_sort
            )
        elif sort_by == "updated_at":
            repositories.sort(
                key=lambda x: x.get("updated_at", ""), 
                reverse=reverse_sort
            )
        
        # Process topics field for each repository
        for repo in repositories:
            # Convert topics from string to list
            if "topics" in repo:
                try:
                    if isinstance(repo["topics"], str):
                        # If it's a string that looks like a JSON array, parse it
                        if repo["topics"].startswith("[") and repo["topics"].endswith("]"):
                            try:
                                repo["topics"] = json.loads(repo["topics"])
                            except json.JSONDecodeError:
                                # If JSON parsing fails, split by commas and strip quotes
                                topics_str = repo["topics"].strip("[]")
                                repo["topics"] = [t.strip(' "\'') for t in topics_str.split(",") if t.strip()]
                        else:
                            # Otherwise, just use it as a single-item list
                            repo["topics"] = [repo["topics"]] if repo["topics"] else []
                except Exception as e:
                    logging.error(f"Error processing topics for repo {repo.get('full_name')}: {e}")
                    repo["topics"] = []
            else:
                repo["topics"] = []
        
        # Apply pagination
        paginated_repos = repositories[offset:offset+limit]
        
        return paginated_repos
        
    except Exception as e:
        logging.exception(f"Error fetching repositories: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching repositories: {str(e)}")

@app.get("/api/contributors", response_model=List[Contributor])
async def get_contributors(limit: int = 20) -> List[Contributor]:
    """Get a list of contributors with flattened repository contributions."""
    try:
        files = get_latest_data_files()
        contributors_data = read_csv_file(files["contributors"])
        flattened_contributors: List[Dict[str, Any]] = []
        
        for row in contributors_data:
            # Process the 'repository_contributions' field to extract required values.
            repo_contribs = []
            if "repository_contributions" in row and row["repository_contributions"]:
                try:
                    repo_contribs = json.loads(row["repository_contributions"])
                except json.JSONDecodeError:
                    repo_contribs = []
            
            if repo_contribs:
                # Use the first repository contribution as the primary one.
                primary = repo_contribs[0]
                row["contributions"] = int(primary.get("contributions", 0))
                row["repository"] = primary.get("repository", "")
                row["repository_stars"] = int(primary.get("repository_stars", 0))
            else:
                row["contributions"] = 0
                row["repository"] = ""
                row["repository_stars"] = 0
            
            flattened_contributors.append(row)
        
        return flattened_contributors[:limit]
    
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Error fetching contributors")
        raise HTTPException(status_code=500, detail=f"Error fetching contributors: {e}")

@app.get("/api/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get aggregated statistics for the dashboard."""
    try:
        files = get_latest_data_files()
        repositories = read_csv_file(files["repositories_detailed"])
        contributors = read_csv_file(files["contributors"])
        
        # Count unique repositories and contributors
        unique_repos = set(repo.get("id", "") for repo in repositories)
        unique_contributors = set(contrib.get("username", "") for contrib in contributors)
        
        # Aggregate languages
        languages_count = {}
        for repo in repositories:
            lang = repo.get("language")
            if lang:
                languages_count[lang] = languages_count.get(lang, 0) + 1
        
        top_languages = [
            {"name": lang, "count": count}
            for lang, count in sorted(languages_count.items(), key=lambda x: x[1], reverse=True)
        ][:10]
        
        # Aggregate topics with enhanced type checking and logging
        topics_count = {}
        for repo in repositories:
            raw_topics = repo.get("topics")
            cleaned_topics = []
            if raw_topics is None:
                cleaned_topics = []
            elif isinstance(raw_topics, list):
                cleaned_topics = raw_topics
            elif isinstance(raw_topics, str):
                try:
                    parsed = json.loads(raw_topics)
                    if isinstance(parsed, list):
                        cleaned_topics = parsed
                    else:
                        cleaned_topics = []
                        logging.warning(
                            "Repository %s: topics after JSON parsing is not a list: %s",
                            repo.get("id"), parsed
                        )
                except json.JSONDecodeError:
                    cleaned_topics = []
                    logging.warning(
                        "Repository %s: failed to decode topics JSON from: %s",
                        repo.get("id"), raw_topics
                    )
            else:
                cleaned_topics = []
                logging.warning(
                    "Repository %s: topics has unexpected type %s: %s",
                    repo.get("id"), type(raw_topics), raw_topics
                )
            
            for topic in cleaned_topics:
                topics_count[topic] = topics_count.get(topic, 0) + 1
        
        top_topics = [
            {"name": topic, "count": count}
            for topic, count in sorted(topics_count.items(), key=lambda x: x[1], reverse=True)
        ][:10]
        
        # Top repositories by stars
        repositories_by_stars = [
            {
                "name": repo.get("name", ""),
                "full_name": repo.get("full_name", ""),
                "stars": repo.get("stargazers_count", 0)
            }
            for repo in sorted(repositories, key=lambda x: x.get("stargazers_count", 0), reverse=True)
        ][:10]
        
        # Top contributors by followers
        contributors_by_followers = [
            {
                "username": contrib.get("username", ""),
                "name": contrib.get("name", ""),
                "followers": contrib.get("followers", 0)
            }
            for contrib in sorted(contributors, key=lambda x: x.get("followers", 0), reverse=True)
        ][:10]
        
        return {
            "total_repositories": len(unique_repos),
            "total_contributors": len(unique_contributors),
            "top_languages": top_languages,
            "top_topics": top_topics,
            "repositories_by_stars": repositories_by_stars,
            "contributors_by_followers": contributors_by_followers
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Error fetching dashboard stats")
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")

@app.get("/api/contributors/multi-repo", response_model=List[Dict[str, Any]])
async def get_multi_repo_contributors(min_repos: int = 2):
    """Get contributors who contribute to multiple repositories."""
    try:
        contributors_data = read_csv_file(get_latest_data_files()["contributors"])
        
        # Group contributors by username and count repositories
        contributor_repos = {}
        for contrib in contributors_data:
            username = contrib.get("username")
            repo = contrib.get("repository")
            
            if not username or not repo:
                continue
                
            if username not in contributor_repos:
                contributor_repos[username] = {
                    "username": username,
                    "name": contrib.get("name", ""),
                    "repositories": set(),
                    "total_contributions": 0,
                    "followers": contrib.get("followers", 0),
                    "location": contrib.get("location", "Unknown"),
                    "company": contrib.get("company", ""),
                    "html_url": contrib.get("html_url", "")
                }
            
            contributor_repos[username]["repositories"].add(repo)
            # contributor_repos[username]["total_contributions"] += int(contrib.get("contributions", 0))
        
        # Filter contributors with multiple repositories
        multi_repo_contributors = [
            {
                **contrib,
                "repositories": list(contrib["repositories"]),
                "repository_count": len(contrib["repositories"])
            }
            for contrib in contributor_repos.values()
            if len(contrib["repositories"]) >= min_repos
        ]
        
        # Sort by number of repositories (descending)
        multi_repo_contributors.sort(key=lambda x: x["repository_count"], reverse=True)
        
        return multi_repo_contributors
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching multi-repo contributors: {str(e)}")

@app.get("/api/contributors/by-location", response_model=List[Dict[str, Any]])
async def get_contributors_by_location():
    """Get contributors grouped by location."""
    try:
        contributors_data = read_csv_file(get_latest_data_files()["contributors"])
        
        # Group contributors by location
        locations = {}
        for contrib in contributors_data:
            location = contrib.get("location", "Unknown")
            if not location or location.lower() in ["null", "none", ""]:
                location = "Unknown"
            
            if location not in locations:
                locations[location] = {
                    "location": location,
                    "count": 0,
                    "contributors": []
                }
            
            # Check if this contributor is already counted
            username = contrib.get("username")
            if not any(c.get("username") == username for c in locations[location]["contributors"]):
                locations[location]["count"] += 1
                locations[location]["contributors"].append({
                    "username": username,
                    "name": contrib.get("name", ""),
                    "followers": contrib.get("followers", 0),
                    "total_contributions": contrib.get("total_contributions", 0),
                    "repository": contrib.get("repository", ""),
                    "html_url": contrib.get("html_url", "")
                })
        
        # Convert to list and sort by count
        location_list = list(locations.values())
        location_list.sort(key=lambda x: x["count"], reverse=True)
        
        return location_list
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching contributors by location: {str(e)}")

@app.get("/api/stats/extended", response_model=Dict[str, Any])
async def get_extended_stats():
    """Get extended dashboard statistics."""
    try:
        repositories = read_csv_file(get_latest_data_files()["repositories_detailed"])
        contributors = read_csv_file(get_latest_data_files()["contributors"])
        
        # Basic stats from the original endpoint
        basic_stats = await get_dashboard_stats()
        
        # Additional stats
        
        # 1. Activity timeline - repositories created by month/year
        timeline = {}
        for repo in repositories:
            created_at = repo.get("created_at", "")
            if created_at:
                try:
                    date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    month_year = date.strftime("%Y-%m")
                    
                    if month_year not in timeline:
                        timeline[month_year] = 0
                    timeline[month_year] += 1
                except:
                    pass
        
        # Convert to sorted list
        activity_timeline = [
            {"date": k, "count": v}
            for k, v in sorted(timeline.items())
        ]
        
        # 2. Repository size distribution
        size_ranges = {
            "Small (<1MB)": 0,
            "Medium (1-10MB)": 0,
            "Large (10-100MB)": 0,
            "Very Large (>100MB)": 0
        }
        
        for repo in repositories:
            # Convert size to integer, handling the case where it's a string
            try:
                size_kb = int(repo.get("size", 0))
            except (ValueError, TypeError):
                size_kb = 0
                
            size_mb = size_kb / 1024  # Convert KB to MB
            
            if size_mb < 1:
                size_ranges["Small (<1MB)"] += 1
            elif size_mb < 10:
                size_ranges["Medium (1-10MB)"] += 1
            elif size_mb < 100:
                size_ranges["Large (10-100MB)"] += 1
            else:
                size_ranges["Very Large (>100MB)"] += 1
        
        size_distribution = [
            {"category": k, "count": v}
            for k, v in size_ranges.items()
        ]
        
        # 3. Contributors with company affiliations
        companies = {}
        for contrib in contributors:
            company = contrib.get("company", "")
            if company and company.lower() not in ["null", "none", ""]:
                if company not in companies:
                    companies[company] = 0
                companies[company] += 1
        
        top_companies = [
            {"name": k, "count": v}
            for k, v in sorted(companies.items(), key=lambda x: x[1], reverse=True)
        ][:10]
        
        return {
            **basic_stats,
            "activity_timeline": activity_timeline,
            "size_distribution": size_distribution,
            "top_companies": top_companies
        }
    
    except Exception as e:
        logging.exception(f"Error fetching extended stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching extended stats: {str(e)}")

@app.get("/api/debug/file-structure", response_model=Dict[str, Any])
async def debug_file_structure():
    """Debug endpoint to check the structure of the data files."""
    try:
        files = get_latest_data_files()
        result = {}
        
        for file_type, file_path in files.items():
            try:
                # Read the first row to get headers
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    headers = next(reader)
                    first_row = next(reader, None)
                
                result[file_type] = {
                    "path": file_path,
                    "headers": headers,
                    "sample_row": first_row if first_row else []
                }
            except Exception as e:
                result[file_type] = {
                    "path": file_path,
                    "error": str(e)
                }
        
        return result
    except Exception as e:
        logging.exception("Error in debug endpoint")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/debug/contributor/{username}", response_model=Dict[str, Any])
async def debug_contributor_data(username: str):
    """Debug endpoint to get raw contributor data."""
    try:
        contributors_data = read_csv_file(get_latest_data_files()["contributors"])
        
        # Filter contributors by username
        contributor_entries = [
            c for c in contributors_data 
            if c.get("username") == username
        ]
        
        if not contributor_entries:
            raise HTTPException(status_code=404, detail=f"Contributor {username} not found")
        
        # Get the headers from the first entry
        headers = list(contributor_entries[0].keys())
        
        # Extract repository_contributions if present
        repo_contributions = None
        if "repository_contributions" in contributor_entries[0]:
            repo_contributions_raw = contributor_entries[0].get("repository_contributions")
            try:
                if isinstance(repo_contributions_raw, str):
                    repo_contributions = json.loads(repo_contributions_raw)
            except json.JSONDecodeError:
                repo_contributions = repo_contributions_raw
        
        return {
            "username": username,
            "entries_count": len(contributor_entries),
            "headers": headers,
            "entries": contributor_entries,
            "repository_contributions": repo_contributions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error fetching debug data for contributor {username}")
        raise HTTPException(status_code=500, detail=f"Error fetching debug data: {str(e)}")

@app.get("/api/contributors/{username}", response_model=Dict[str, Any])
async def get_contributor_details(
    username: str,
    page: int = Query(1, description="Page number"),
    page_size: int = Query(20, description="Number of results per page"),
    sort_by: str = Query("contributions", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)")
):
    """Get detailed information about a contributor and their repositories."""
    try:
        contributors_data = read_csv_file(get_latest_data_files()["contributors"])
        
        # Log the username we're looking for
        logging.info(f"Looking for contributor with username: {username}")
        
        # Filter contributors by username
        contributor_entries = [
            c for c in contributors_data 
            if c.get("username") == username
        ]
        
        # Log how many entries we found
        logging.info(f"Found {len(contributor_entries)} entries for contributor {username}")
        
        if not contributor_entries:
            raise HTTPException(status_code=404, detail=f"Contributor {username} not found")
        
        # Get the contributor profile from the first entry
        contributor_profile = {k: v for k, v in contributor_entries[0].items() 
                              if k != "repository" and k != "contributions" and k != "repository_contributions"}
        
        # Get all repositories this contributor has contributed to
        contributor_repos = []
        
        # Check for repository_contributions field which contains JSON data
        for entry in contributor_entries:
            repo_contributions = entry.get("repository_contributions")
            if repo_contributions:
                try:
                    # Log the raw repository_contributions field
                    logging.info(f"Raw repository_contributions: {repo_contributions}")
                    
                    # Try to parse as JSON
                    if isinstance(repo_contributions, str):
                        repo_data_list = json.loads(repo_contributions)
                        logging.info(f"Successfully parsed repository_contributions as JSON: {repo_data_list}")
                        
                        if isinstance(repo_data_list, list):
                            for repo_data in repo_data_list:
                                if isinstance(repo_data, dict) and "repository" in repo_data:
                                    # Ensure contributions is an integer
                                    contributions = 0
                                    try:
                                        # The field is named "contributions" in the JSON
                                        contributions = int(repo_data.get("contributions", 0))
                                        logging.info(f"Found contributions: {contributions} for repo {repo_data['repository']}")
                                    except (ValueError, TypeError):
                                        pass
                                    
                                    # Create repository entry
                                    repo_entry = {
                                        "repository": repo_data["repository"],
                                        "contributions": contributions
                                    }
                                    
                                    # Add additional fields if available
                                    if "repository_stars" in repo_data:
                                        repo_entry["stars"] = repo_data["repository_stars"]
                                    if "repository_language" in repo_data:
                                        repo_entry["language"] = repo_data["repository_language"]
                                    
                                    contributor_repos.append(repo_entry)
                                    logging.info(f"Added repository from JSON: {repo_data['repository']} with {contributions} contributions")
                except json.JSONDecodeError as e:
                    logging.error(f"Error parsing repository_contributions as JSON: {e}")
                except Exception as e:
                    logging.error(f"Unexpected error parsing repository_contributions: {e}")
        
        # If no repositories found from repository_contributions, try other methods
        if not contributor_repos:
            logging.info(f"No repositories found in repository_contributions, trying other methods")
            
            # Try to get repositories from the repository field
            for entry in contributor_entries:
                repo_name = entry.get("repository")
                if repo_name:
                    # Log the repository we found
                    logging.info(f"Found repository {repo_name} for contributor {username}")
                    
                    # Get contributions for this repo
                    contributions = 0
                    try:
                        contributions = int(entry.get("contributions", 0))
                    except (ValueError, TypeError):
                        pass
                    
                    contributor_repos.append({
                        "repository": repo_name,
                        "contributions": contributions
                    })
            
            # If still no repositories, try to fetch from GitHub API
            if not contributor_repos:
                logging.info(f"No repositories found in data, trying to fetch from GitHub API")
                
                try:
                    # Fetch repositories from GitHub API
                    github_token = os.environ.get("GITHUB_TOKEN")
                    headers = {}
                    if github_token:
                        headers["Authorization"] = f"token {github_token}"
                    
                    # Make the API request
                    api_url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
                    response = requests.get(api_url, headers=headers)
                    
                    if response.status_code == 200:
                        repos_data = response.json()
                        
                        # Process each repository
                        for repo_data in repos_data:
                            # Only include repositories owned by the user
                            if repo_data.get("owner", {}).get("login") == username:
                                contributor_repos.append({
                                    "repository": repo_data.get("full_name"),
                                    "contributions": 0,  # We don't know the exact contributions
                                    "stars": repo_data.get("stargazers_count", 0),
                                    "forks": repo_data.get("forks_count", 0),
                                    "language": repo_data.get("language", ""),
                                    "description": repo_data.get("description", "")
                                })
                        
                        logging.info(f"Fetched {len(contributor_repos)} repositories from GitHub API")
                    else:
                        logging.error(f"Failed to fetch repositories from GitHub API: {response.status_code}")
                except Exception as e:
                    logging.error(f"Error fetching repositories from GitHub API: {e}")
        
        # If still no repositories, create a dummy entry for the user's own repositories
        if not contributor_repos and contributor_entries[0].get("total_contributions"):
            logging.info(f"Creating dummy repository entry for user's own repositories")
            
            # Get the total contributions
            total_contributions = 0
            try:
                total_contributions = int(contributor_entries[0].get("total_contributions", 0))
            except (ValueError, TypeError):
                pass
            
            # Create a dummy repository entry
            contributor_repos.append({
                "repository": f"{username}/{username}",
                "contributions": total_contributions,
                "stars": 0,
                "language": "",
                "description": "User's own repositories"
            })
        
        # Log the total number of repositories found
        logging.info(f"Total repositories found for {username}: {len(contributor_repos)}")
        
        # Ensure numeric fields
        for repo in contributor_repos:
            # Ensure contributions is an integer
            try:
                repo["contributions"] = int(repo.get("contributions", 0))
            except (ValueError, TypeError):
                repo["contributions"] = 0
            
            # Ensure stars is an integer
            if "stars" not in repo:
                repo["stars"] = 0
            else:
                try:
                    repo["stars"] = int(repo["stars"])
                except (ValueError, TypeError):
                    repo["stars"] = 0
        
        # Sort the repositories
        reverse_sort = sort_order.lower() == "desc"
        
        if sort_by == "contributions":
            contributor_repos.sort(
                key=lambda x: x.get("contributions", 0), 
                reverse=reverse_sort
            )
        elif sort_by == "name":
            contributor_repos.sort(
                key=lambda x: x.get("repository", ""), 
                reverse=reverse_sort
            )
        elif sort_by == "stars":
            contributor_repos.sort(
                key=lambda x: x.get("stars", 0), 
                reverse=reverse_sort
            )
        
        # Add repository details if not already present
        try:
            repos_data = read_csv_file(get_latest_data_files()["repositories"])
            repos_by_name = {repo.get("full_name"): repo for repo in repos_data}
            
            for repo in contributor_repos:
                repo_name = repo.get("repository")
                if repo_name in repos_by_name:
                    repo_details = repos_by_name[repo_name]
                    
                    # Only set these fields if they're not already set
                    if "stars" not in repo or repo["stars"] == 0:
                        repo["stars"] = int(repo_details.get("stargazers_count", 0))
                    
                    if "forks" not in repo:
                        repo["forks"] = int(repo_details.get("forks_count", 0))
                    
                    if "language" not in repo or not repo["language"]:
                        repo["language"] = repo_details.get("language", "")
                    
                    if "description" not in repo:
                        repo["description"] = repo_details.get("description", "")
                else:
                    if "stars" not in repo:
                        repo["stars"] = 0
                    if "forks" not in repo:
                        repo["forks"] = 0
                    if "language" not in repo:
                        repo["language"] = ""
                    if "description" not in repo:
                        repo["description"] = ""
        except Exception as e:
            logging.error(f"Error adding repository details: {e}")
        
        # Calculate pagination
        total = len(contributor_repos)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # Get the current page of results
        page_results = contributor_repos[start_idx:end_idx]
        
        # Calculate total contributions
        total_contributions = 0
        try:
            # First try to get from the total_contributions field
            if "total_contributions" in contributor_entries[0]:
                total_contributions = int(contributor_entries[0].get("total_contributions", 0))
            else:
                # Otherwise sum from repositories
                total_contributions = sum(repo.get("contributions", 0) for repo in contributor_repos)
        except (ValueError, TypeError):
            pass
        
        contributor_profile["total_contributions"] = total_contributions
        
        return {
            "profile": contributor_profile,
            "repositories": {
                "items": page_results,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error fetching details for contributor {username}")
        raise HTTPException(status_code=500, detail=f"Error fetching contributor details: {str(e)}")

@app.get("/api/repositories/{repo_name}/contributors", response_model=Dict[str, Any])
async def get_repository_contributors(
    repo_name: str,
    page: int = Query(1, description="Page number"),
    page_size: int = Query(20, description="Number of results per page"),
    sort_by: str = Query("contributions", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)")
):
    """Get contributors for a specific repository."""
    try:
        contributors_data = read_csv_file(get_latest_data_files()["contributors"])
        
        # Filter contributors for this repository
        repo_contributors = []
        
        # First check for direct repository matches
        for contributor in contributors_data:
            if contributor.get("repository") == repo_name:
                repo_contributors.append(contributor)
        
        # If no direct matches, check repository_contributions field
        if not repo_contributors:
            for contributor in contributors_data:
                repo_contributions = contributor.get("repository_contributions")
                if repo_contributions:
                    try:
                        # Try to parse as JSON
                        if isinstance(repo_contributions, str):
                            repo_data_list = json.loads(repo_contributions)
                            
                            if isinstance(repo_data_list, list):
                                for repo_data in repo_data_list:
                                    if isinstance(repo_data, dict) and repo_data.get("repository") == repo_name:
                                        # Create a new contributor entry for this repository
                                        contributor_entry = {k: v for k, v in contributor.items() 
                                                           if k != "repository" and k != "contributions" and k != "repository_contributions"}
                                        
                                        # Add repository-specific fields
                                        contributor_entry["repository"] = repo_name
                                        contributor_entry["contributions"] = repo_data.get("contributions", 0)
                                        
                                        repo_contributors.append(contributor_entry)
                    except json.JSONDecodeError:
                        pass
                    except Exception as e:
                        logging.error(f"Error parsing repository_contributions: {e}")
        
        # Ensure numeric fields
        for contributor in repo_contributors:
            # Ensure contributions is an integer
            try:
                contributor["contributions"] = int(contributor.get("contributions", 0))
            except (ValueError, TypeError):
                contributor["contributions"] = 0
                
            # Ensure followers is an integer
            try:
                contributor["followers"] = int(contributor.get("followers", 0))
            except (ValueError, TypeError):
                contributor["followers"] = 0
        
        # Sort the results
        reverse_sort = sort_order.lower() == "desc"
        
        if sort_by == "contributions":
            repo_contributors.sort(
                key=lambda x: x.get("contributions", 0), 
                reverse=reverse_sort
            )
        elif sort_by == "followers":
            repo_contributors.sort(
                key=lambda x: x.get("followers", 0), 
                reverse=reverse_sort
            )
        
        # Get repository details
        repo_details = None
        try:
            repos_data = read_csv_file(get_latest_data_files()["repositories_detailed"])
            for repo in repos_data:
                if repo.get("full_name") == repo_name:
                    repo_details = repo
                    break
        except Exception as e:
            logging.error(f"Error reading detailed repositories: {e}")
            
        if not repo_details:
            try:
                repos_data = read_csv_file(get_latest_data_files()["repositories"])
                for repo in repos_data:
                    if repo.get("full_name") == repo_name:
                        repo_details = repo
                        break
            except Exception as e:
                logging.error(f"Error reading repositories: {e}")
        
        # Calculate pagination
        total = len(repo_contributors)
        total_pages = (total + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # Get the current page of results
        page_results = repo_contributors[start_idx:end_idx]
        
        return {
            "repository": repo_details,
            "contributors": {
                "items": page_results,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        }
        
    except Exception as e:
        logging.exception(f"Error fetching contributors for repository {repo_name}")
        raise HTTPException(status_code=500, detail=f"Error fetching repository contributors: {str(e)}")

@app.get("/api/debug/stats-extended", response_model=Dict[str, Any])
async def debug_extended_stats():
    """Debug endpoint for extended stats."""
    try:
        repositories = read_csv_file(get_latest_data_files()["repositories_detailed"])
        contributors = read_csv_file(get_latest_data_files()["contributors"])
        
        # Get sample data
        repo_sample = repositories[:5] if repositories else []
        contrib_sample = contributors[:5] if contributors else []
        
        # Check for required fields
        repo_fields = set()
        contrib_fields = set()
        
        for repo in repo_sample:
            repo_fields.update(repo.keys())
        
        for contrib in contrib_sample:
            contrib_fields.update(contrib.keys())
        
        # Check size field specifically
        size_types = {}
        for repo in repositories[:20]:  # Check first 20 repos
            size_value = repo.get("size")
            size_type = type(size_value).__name__
            if size_type not in size_types:
                size_types[size_type] = []
            if len(size_types[size_type]) < 3:  # Store up to 3 examples per type
                size_types[size_type].append(size_value)
        
        return {
            "repository_count": len(repositories),
            "contributor_count": len(contributors),
            "repository_fields": sorted(list(repo_fields)),
            "contributor_fields": sorted(list(contrib_fields)),
            "repository_sample": repo_sample,
            "contributor_sample": contrib_sample,
            "size_field_types": size_types
        }
    except Exception as e:
        logging.exception("Error in debug extended stats endpoint")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.api_route("/api/health", methods=["GET", "HEAD"])
async def health_check():
    """Health check endpoint to verify API is running"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/api/candidates", response_model=Dict[str, Any])
async def get_candidates(
    page: int = Query(1, description="Page number"),
    page_size: int = Query(20, description="Number of results per page"),
    sort_by: str = Query("total_contributions", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    location: Optional[str] = Query(None, description="Filter by location"),
    language: Optional[str] = Query(None, description="Filter by programming language"),
    min_followers: Optional[int] = Query(None, description="Minimum number of followers"),
    min_contributions: Optional[int] = Query(None, description="Minimum number of contributions")
):
    """Get a list of candidates (contributors) with pagination and filtering."""
    try:
        contributors_data = read_csv_file(get_latest_data_files()["contributors"])
        
        # Process each contributor
        for contributor in contributors_data:
            # Parse repository_contributions if it's a string
            if "repository_contributions" in contributor and isinstance(contributor["repository_contributions"], str):
                try:
                    # If it's a JSON string, parse it
                    if contributor["repository_contributions"].startswith("[") and contributor["repository_contributions"].endswith("]"):
                        contributor["repository_contributions_parsed"] = json.loads(contributor["repository_contributions"])
                    else:
                        contributor["repository_contributions_parsed"] = []
                except json.JSONDecodeError:
                    contributor["repository_contributions_parsed"] = []
            else:
                contributor["repository_contributions_parsed"] = []
            
            # Ensure contributions is an integer
            try:
                contributor["total_contributions"] = int(contributor.get("total_contributions", 0))
            except (ValueError, TypeError):
                contributor["total_contributions"] = 0
                
            # Ensure followers is an integer
            try:
                contributor["followers"] = int(contributor.get("followers", 0))
            except (ValueError, TypeError):
                contributor["followers"] = 0
                
            # Ensure public_repos is an integer
            try:
                contributor["public_repos"] = int(contributor.get("public_repos", 0))
            except (ValueError, TypeError):
                contributor["public_repos"] = 0
        
        # Apply filters
        filtered_contributors = contributors_data
        
        if location:
            filtered_contributors = [
                c for c in filtered_contributors 
                if c.get("location") and location.lower() in c.get("location", "").lower()
            ]
            
        if language:
            # We need to join with repositories to get language info
            try:
                repos_data = read_csv_file(get_latest_data_files()["repositories_detailed"])
                repos_by_name = {repo.get("full_name"): repo for repo in repos_data}
                
                filtered_contributors = [
                    c for c in filtered_contributors
                    if c.get("repository") in repos_by_name and 
                    repos_by_name[c.get("repository")].get("language", "").lower() == language.lower()
                ]
            except Exception as e:
                logging.error(f"Error filtering by language: {e}")
                # If we can't load the repositories file, skip language filtering
                if language:
                    return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}
            
        if min_followers is not None:
            filtered_contributors = [
                c for c in filtered_contributors
                if c.get("followers") and int(c.get("followers", 0)) >= min_followers
            ]
            
        if min_contributions is not None:
            filtered_contributors = [
                c for c in filtered_contributors
                if c.get("total_contributions") and int(c.get("total_contributions", 0)) >= min_contributions
            ]
        
        # Sort the results
        reverse_sort = sort_order.lower() == "desc"
        
        if sort_by == "total_contributions":
            filtered_contributors.sort(
                key=lambda x: x.get("total_contributions", 0), 
                reverse=reverse_sort
            )
        elif sort_by == "followers":
            filtered_contributors.sort(
                key=lambda x: x.get("followers", 0), 
                reverse=reverse_sort
            )
        elif sort_by == "repositories":
            # Count repositories per contributor
            contributor_repos = {}
            for c in filtered_contributors:
                username = c.get("username")
                if username not in contributor_repos:
                    contributor_repos[username] = set()
                contributor_repos[username].add(c.get("repository"))
            
            filtered_contributors.sort(
                key=lambda x: len(contributor_repos.get(x.get("username"), set())), 
                reverse=reverse_sort
            )
        
        # Calculate pagination
        total = len(filtered_contributors)
        total_pages = (total + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # Get the current page of results
        page_results = filtered_contributors[start_idx:end_idx]
        
        # Enhance with repository stars
        try:
            repos_data = read_csv_file(get_latest_data_files()["repositories_detailed"])
            repos_by_name = {repo.get("full_name"): repo for repo in repos_data}
            
            for contributor in page_results:
                repo_name = contributor.get("repository")
                if repo_name in repos_by_name:
                    try:
                        contributor["repository_stars"] = int(repos_by_name[repo_name].get("stargazers_count", 0))
                    except (ValueError, TypeError):
                        contributor["repository_stars"] = 0
                else:
                    contributor["repository_stars"] = 0
        except Exception as e:
            logging.error(f"Error enhancing with repository stars: {e}")
            # If we can't load the repositories file, set stars to 0
            for contributor in page_results:
                contributor["repository_stars"] = 0
        
        return {
            "items": page_results,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
        
    except Exception as e:
        logging.exception("Error fetching candidates")
        raise HTTPException(status_code=500, detail=f"Error fetching candidates: {str(e)}")

@app.get("/api/candidates/languages", response_model=List[Dict[str, Any]])
async def get_candidate_languages():
    """Get programming languages used by candidates for filtering."""
    try:
        repos_data = read_csv_file(get_latest_data_files()["repositories_detailed"])
        
        # Count languages
        languages = {}
        for repo in repos_data:
            lang = repo.get("language")
            if lang and lang.lower() not in ["null", "none", ""]:
                if lang not in languages:
                    languages[lang] = 0
                languages[lang] += 1
        
        # Convert to list of objects
        language_list = [
            {"name": lang, "count": count}
            for lang, count in languages.items()
        ]
        
        # Sort by count (descending)
        language_list.sort(key=lambda x: x["count"], reverse=True)
        
        return language_list
        
    except Exception as e:
        logging.exception("Error fetching candidate languages")
        raise HTTPException(status_code=500, detail=f"Error fetching candidate languages: {str(e)}")

@app.get("/api/candidates/locations", response_model=List[Dict[str, Any]])
async def get_candidate_locations():
    """Get locations of candidates for filtering."""
    try:
        contributors_data = read_csv_file(get_latest_data_files()["contributors"])
        
        # Count locations
        locations = {}
        for contributor in contributors_data:
            location = contributor.get("location")
            if location and location.lower() not in ["null", "none", ""]:
                if location not in locations:
                    locations[location] = 0
                locations[location] += 1
        
        # Convert to list of objects
        location_list = [
            {"name": loc, "count": count}
            for loc, count in locations.items()
        ]
        
        # Sort by count (descending)
        location_list.sort(key=lambda x: x["count"], reverse=True)
        
        return location_list
        
    except Exception as e:
        logging.exception("Error fetching candidate locations")
        raise HTTPException(status_code=500, detail=f"Error fetching candidate locations: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 