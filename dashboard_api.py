import os
import csv
import json
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
import logging
import sys

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
    topics: List[str] = []
    created_at: str
    updated_at: str
    matched_keyword: Optional[str] = None

class Contributor(BaseModel):
    username: str
    contributions: int
    repository: str
    repository_stars: int
    name: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    twitter_username: Optional[str] = None
    followers: Optional[int] = None
    public_repos: Optional[int] = None
    html_url: Optional[str] = None

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

def read_csv_file(file_path: Path) -> List[Dict[str, Any]]:
    """Read a CSV file and return its contents as a list of dictionaries."""
    # Increase CSV field size limit to handle very large fields
    max_field_limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(max_field_limit)
            break
        except OverflowError:
            max_field_limit = int(max_field_limit / 10)

    if not file_path.exists():
        return []
    
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Process special fields
            for key, value in row.items():
                if key in ["topics", "languages"]:
                    if value in [None, "", "None", "null"]:
                        row[key] = []
                    else:
                        try:
                            row[key] = json.loads(value)
                        except json.JSONDecodeError:
                            row[key] = []
                elif key in ["stargazers_count", "forks_count", "watchers_count", 
                             "open_issues_count", "size", "id", "contributions",
                             "followers", "following", "public_repos", "public_gists"]:
                    try:
                        row[key] = int(value) if value else 0
                    except ValueError:
                        row[key] = 0
                elif value == "None" or value == "null":
                    row[key] = None
            data.append(row)
    
    return data

# API Routes
@app.get("/")
async def root():
    return {"message": "GitHub Data Dashboard API"}

@app.get("/api/repositories", response_model=List[Repository])
async def get_repositories(
    keyword: Optional[str] = None,
    language: Optional[str] = None,
    min_stars: Optional[int] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get repositories with optional filtering."""
    try:
        files = get_latest_data_files()
        repositories = read_csv_file(files["repositories_detailed"])
        
        # Apply filters
        if keyword:
            repositories = [
                repo for repo in repositories 
                if keyword.lower() in (repo.get("description") or "").lower() or
                keyword.lower() in (repo.get("name") or "").lower() or
                keyword.lower() in (repo.get("matched_keyword") or "").lower()
            ]
        
        if language:
            repositories = [
                repo for repo in repositories 
                if language.lower() == (repo.get("language") or "").lower()
            ]
        
        if min_stars is not None:
            repositories = [
                repo for repo in repositories 
                if repo.get("stargazers_count", 0) >= min_stars
            ]
        
        # Sort by stars (descending)
        repositories.sort(key=lambda x: x.get("stargazers_count", 0), reverse=True)
        
        return repositories[:limit]
    
    except HTTPException:
        raise
    except Exception as e:
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
            contributor_repos[username]["total_contributions"] += int(contrib.get("contributions", 0))
        
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
                    "contributions": contrib.get("contributions", 0),
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
            size_kb = repo.get("size", 0)
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
        raise HTTPException(status_code=500, detail=f"Error fetching extended stats: {str(e)}")

@app.api_route("/api/health", methods=["GET", "HEAD"])
async def health_check():
    """Health check endpoint to verify API is running"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 