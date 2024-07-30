import requests
import pandas as pd
import os

# Your GitHub API token
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# Define headers for the GitHub API request
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

# Function to fetch PRs for a specific user in a specific repository
def fetch_user_prs(user, repo, state='all'):
    prs = []
    page = 1
    while True:
        print(f'Fetching PRs for user: {user}, repo: {repo}, state: {state}, page: {page}...')
        url = f'https://api.github.com/repos/{repo}/pulls?state={state}&per_page=100&page={page}'
        response = requests.get(url, headers=headers)
        page_prs = response.json()
        if not page_prs:
            break
        prs.extend(page_prs)
        page += 1

    user_prs = []
    for pr in prs:
        if pr['user']['login'] in user:
            pr_details = {
                'url': pr['html_url'],
                'title': pr['title'],
                'created_at': pr['created_at'],
                'state': pr['state'],
                'merged_at': pr.get('merged_at'),
                'approved': fetch_pr_approvals(repo, pr['number']),
                'comments': fetch_pr_comments(repo, pr['number']),
                'user_login': pr['user']['login'],
                'user_url': pr['user']['html_url']
            }
            user_prs.append(pr_details)

    return user_prs

# Function to fetch comments for a specific PR
def fetch_pr_comments(repo, pr_number):
    url = f'https://api.github.com/repos/{repo}/issues/{pr_number}/comments'
    response = requests.get(url, headers=headers)
    comments = response.json()
    comment_texts = [comment['body'] for comment in comments]
    return comment_texts

# Function to fetch approvals for a specific PR
def fetch_pr_approvals(repo, pr_number):
    url = f'https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews'
    response = requests.get(url, headers=headers)
    reviews = response.json()
    approvals = [review for review in reviews if review['state'] == 'APPROVED']
    return len(approvals) > 0

# Function to fetch PRs across multiple repositories for multiple users
def fetch_prs_across_repos(users, repos):
    all_prs = []
    for repo in repos:
        print(f'Fetching PRs for repo: {repo}...')
        for user in users:
            print(f'Fetching PRs for user: {user}...')
            all_prs.extend(fetch_user_prs(user, repo, state='all'))
    return all_prs

# List of repositories to check (in the format 'owner/repo')
repositories = [
    'kata-containers/kata-containers',
    'unikraft/unikraft',
    'containerd/containerd'
]

# List of users to track
users_to_track = [
    'ananos',
    'pyrromanis',
    'gntouts'
]

# Fetch PRs
all_prs = fetch_prs_across_repos(users_to_track, repositories)

# Create DataFrame for all PRs
all_prs_df = pd.DataFrame(all_prs)

# Save the results to a CSV file
# all_prs_df.to_csv('all_prs.csv', index=False)
all_prs_df.to_json('docs/all_prs.json', orient='records')

pd.set_option('display.max_columns', None)  # Ensure all columns are displayed
pd.set_option('display.max_colwidth', None)  # Ensure full width of each column is displayed

# Display the results
print("All PRs:")
if all_prs_df.empty:
    print("No PRs found.")
else:
    print(all_prs_df[['url', 'created_at', 'state', 'merged_at', 'approved', 'user_login']])
