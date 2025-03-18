# GitHub Repository and Contributor Scraper

This project consists of two main components:
1. A GitHub scraper that collects repository and contributor data
2. A web dashboard to visualize the collected data

## Setup

### Prerequisites
- Python 3.8+
- Node.js 14+
- GitHub Personal Access Token

### Environment Setup

1. Create a `.env` file in the root directory based on the `.env.example` template:
   ```
   GITHUB_TOKEN=your_github_personal_access_token_here
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Scraper

1. Run the GitHub scraper to collect data:
   ```
   python github_scraper.py
   ```

   This will:
   - Search GitHub for repositories matching the specified keywords
   - Collect repository details
   - Gather information about contributors to these repositories
   - Save all data to CSV files in the `github_data` directory

## Running the Dashboard

1. Start the API server:
   ```
   python dashboard_api.py
   ```

2. In a separate terminal, navigate to the dashboard directory and install dependencies:
   ```
   cd dashboard
   npm install
   ```

3. Start the Next.js development server:
   ```
   npm run dev
   ```

4. Open your browser and navigate to `http://localhost:3000` to view the dashboard

## Dashboard Features

- Overview statistics of repositories and contributors
- Language distribution visualization
- Topic cloud showing popular topics
- Top repositories by star count
- Top contributors by follower count and contributions

## Customization

You can customize the keywords used for repository search by modifying the `keywords` list in the `main()` function of `github_scraper.py`.

## Data Files

The scraper generates the following CSV files in the `github_data` directory:
- `repositories_[timestamp].csv`: Basic repository information
- `repositories_detailed_[timestamp].csv`: Detailed repository information
- `contributors_[timestamp].csv`: Contributor information

These files are automatically used by the dashboard to visualize the data. 