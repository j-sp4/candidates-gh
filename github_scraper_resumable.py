import os
import csv
import json
import time
import requests
import pickle
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

# GitHub API token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Headers for GitHub API requests
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Directory to store data
DATA_DIR = "github_data"
CHECKPOINT_DIR = "checkpoints"

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

# Checkpoint file path
CHECKPOINT_FILE = os.path.join(CHECKPOINT_DIR, "scraper_checkpoint.pkl")

class GitHubScraper:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.repositories_file = os.path.join(DATA_DIR, f"repositories_{self.timestamp}.csv")
        self.repositories_detailed_file = os.path.join(DATA_DIR, f"repositories_detailed_{self.timestamp}.csv")
        self.contributors_file = os.path.join(DATA_DIR, f"contributors_{self.timestamp}.csv")
        
        # Checkpoint state
        self.checkpoint = {
            "last_processed_repo_index": 0,
            "processed_repos": set(),
            "processed_contributors": set(),
            "timestamp": self.timestamp
        }
        
        # Load checkpoint if exists
        self.load_checkpoint()
        
    def load_checkpoint(self):
        """Load checkpoint if it exists"""
        if os.path.exists(CHECKPOINT_FILE):
            try:
                with open(CHECKPOINT_FILE, 'rb') as f:
                    saved_checkpoint = pickle.load(f)
                
                # Update file paths with saved timestamp
                if "timestamp" in saved_checkpoint:
                    self.timestamp = saved_checkpoint["timestamp"]
                    self.repositories_file = os.path.join(DATA_DIR, f"repositories_{self.timestamp}.csv")
                    self.repositories_detailed_file = os.path.join(DATA_DIR, f"repositories_detailed_{self.timestamp}.csv")
                    self.contributors_file = os.path.join(DATA_DIR, f"contributors_{self.timestamp}.csv")
                
                self.checkpoint = saved_checkpoint
                print(f"Resuming from checkpoint: {self.checkpoint['last_processed_repo_index']} repositories processed")
            except Exception as e:
                print(f"Error loading checkpoint: {e}")
    
    def save_checkpoint(self):
        """Save current state to checkpoint file"""
        with open(CHECKPOINT_FILE, 'wb') as f:
            pickle.dump(self.checkpoint, f)
        print(f"Checkpoint saved: {self.checkpoint['last_processed_repo_index']} repositories processed")
    
    def search_repositories(self, keywords, min_stars=100, limit=5000):
        """Search for repositories matching keywords with at least min_stars stars"""
        all_repos = []
        
        # Create repositories CSV file if it doesn't exist
        if not os.path.exists(self.repositories_file):
            with open(self.repositories_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["id", "name", "full_name", "html_url", "description", "stargazers_count", "language"])
        
        for keyword in keywords:
            page = 1
            while len(all_repos) < limit:
                try:
                    query = f"{keyword} stars:>={min_stars}"
                    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&page={page}&per_page=100"
                    response = requests.get(url, headers=headers)
                    
                    if response.status_code == 403 and 'rate limit exceeded' in response.text.lower():
                        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                        sleep_time = max(reset_time - time.time(), 0) + 10
                        print(f"Rate limit exceeded. Sleeping for {sleep_time:.2f} seconds.")
                        time.sleep(sleep_time)
                        continue
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    if not data.get('items'):
                        break
                    
                    # Append to CSV file
                    with open(self.repositories_file, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        for repo in data['items']:
                            if repo['id'] not in self.checkpoint["processed_repos"]:
                                writer.writerow([
                                    repo['id'],
                                    repo['name'],
                                    repo['full_name'],
                                    repo['html_url'],
                                    repo.get('description', ''),
                                    repo['stargazers_count'],
                                    repo.get('language', '')
                                ])
                                all_repos.append(repo)
                    
                    page += 1
                    
                    # Check if we've reached the end of results
                    if len(data['items']) < 100:
                        break
                        
                except Exception as e:
                    print(f"Error searching repositories: {e}")
                    time.sleep(10)  # Wait before retrying
        
        return all_repos
    
    def get_repository_details(self, repositories):
        """Get detailed information for each repository"""
        # Create detailed repositories CSV file if it doesn't exist
        if not os.path.exists(self.repositories_detailed_file):
            with open(self.repositories_detailed_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "id", "name", "full_name", "html_url", "description", 
                    "stargazers_count", "forks_count", "open_issues_count", 
                    "language", "topics", "created_at", "updated_at", "size"
                ])
        
        # Start from the last processed repository
        start_idx = self.checkpoint["last_processed_repo_index"]
        
        for i, repo in enumerate(tqdm(repositories[start_idx:], initial=start_idx, total=len(repositories))):
            try:
                # Update the current index
                current_idx = start_idx + i
                self.checkpoint["last_processed_repo_index"] = current_idx
                
                # Skip if already processed
                if repo['id'] in self.checkpoint["processed_repos"]:
                    continue
                
                url = f"https://api.github.com/repos/{repo['full_name']}"
                response = requests.get(url, headers=headers)
                
                if response.status_code == 403 and 'rate limit exceeded' in response.text.lower():
                    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                    sleep_time = max(reset_time - time.time(), 0) + 10
                    print(f"Rate limit exceeded. Sleeping for {sleep_time:.2f} seconds.")
                    
                    # Save checkpoint before sleeping
                    self.save_checkpoint()
                    
                    time.sleep(sleep_time)
                    # Retry this repository
                    i -= 1
                    continue
                
                response.raise_for_status()
                repo_data = response.json()
                
                # Get topics
                topics = repo_data.get('topics', [])
                topics_str = ','.join(topics)
                
                # Write to CSV
                with open(self.repositories_detailed_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        repo_data['id'],
                        repo_data['name'],
                        repo_data['full_name'],
                        repo_data['html_url'],
                        repo_data.get('description', ''),
                        repo_data['stargazers_count'],
                        repo_data['forks_count'],
                        repo_data['open_issues_count'],
                        repo_data.get('language', ''),
                        topics_str,
                        repo_data['created_at'],
                        repo_data['updated_at'],
                        repo_data.get('size', 0)
                    ])
                
                # Get contributors
                self.get_contributors(repo_data['full_name'])
                
                # Mark as processed
                self.checkpoint["processed_repos"].add(repo['id'])
                
                # Save checkpoint every 10 repositories
                if (current_idx + 1) % 10 == 0:
                    self.save_checkpoint()
                
                # Respect rate limit
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error getting details for {repo['full_name']}: {e}")
                # Save checkpoint on error
                self.save_checkpoint()
                time.sleep(5)  # Wait before continuing
    
    def get_contributors(self, repo_full_name):
        """Get contributors for a repository"""
        # Create contributors CSV file if it doesn't exist
        if not os.path.exists(self.contributors_file):
            with open(self.contributors_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "id", "username", "name", "html_url", "contributions", 
                    "followers", "public_repos", "location", "company", "repository"
                ])
        
        try:
            url = f"https://api.github.com/repos/{repo_full_name}/contributors?per_page=100"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 403 and 'rate limit exceeded' in response.text.lower():
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                sleep_time = max(reset_time - time.time(), 0) + 10
                print(f"Rate limit exceeded. Sleeping for {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
                return self.get_contributors(repo_full_name)  # Retry
            
            if response.status_code == 404:
                print(f"Repository not found: {repo_full_name}")
                return
                
            response.raise_for_status()
            contributors = response.json()
            
            print(f"Found {len(contributors)} contributors for {repo_full_name}")
            
            for contributor in contributors:
                # Skip if already processed this contributor for this repo
                contrib_key = f"{contributor['id']}_{repo_full_name}"
                if contrib_key in self.checkpoint["processed_contributors"]:
                    continue
                
                try:
                    # Get user details
                    user_url = contributor['url']
                    user_response = requests.get(user_url, headers=headers)
                    
                    if user_response.status_code == 403 and 'rate limit exceeded' in user_response.text.lower():
                        reset_time = int(user_response.headers.get('X-RateLimit-Reset', 0))
                        sleep_time = max(reset_time - time.time(), 0) + 10
                        print(f"Rate limit exceeded. Sleeping for {sleep_time:.2f} seconds.")
                        time.sleep(sleep_time)
                        # Skip this contributor for now, will be processed on resume
                        continue
                    
                    if user_response.status_code != 200:
                        # Skip this contributor if we can't get details
                        continue
                        
                    user_data = user_response.json()
                    
                    # Write to CSV
                    with open(self.contributors_file, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            contributor['id'],
                            contributor['login'],
                            user_data.get('name', ''),
                            contributor['html_url'],
                            contributor['contributions'],
                            user_data.get('followers', 0),
                            user_data.get('public_repos', 0),
                            user_data.get('location', ''),
                            user_data.get('company', ''),
                            repo_full_name
                        ])
                    
                    # Mark as processed
                    self.checkpoint["processed_contributors"].add(contrib_key)
                    
                    # Respect rate limit
                    time.sleep(0.2)
                    
                except Exception as e:
                    print(f"Error getting details for contributor {contributor['login']}: {e}")
            
        except Exception as e:
            print(f"Error getting contributors for {repo_full_name}: {e}")

def main():
    # Keywords to search for
    keywords = [
        "machine learning", "deep learning", "artificial intelligence", 
        "data science", "neural network", "computer vision", "nlp",
        "natural language processing", "reinforcement learning", "ai"
    ]
    
    scraper = GitHubScraper()
    
    # Search for repositories
    print("Searching for repositories...")
    repositories = scraper.search_repositories(keywords, min_stars=500, limit=5000)
    
    # Get detailed information for each repository
    print(f"Getting details for {len(repositories)} repositories...")
    scraper.get_repository_details(repositories)
    
    # Save final checkpoint
    scraper.save_checkpoint()
    
    print("Done!")

if __name__ == "__main__":
    main() 