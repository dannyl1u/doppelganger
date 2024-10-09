import requests
import csv
from datetime import datetime

def get_github_issues(owner, repo, token):
    issues = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        params = {
            "state": "all",
            "per_page": 100,
            "page": page
        }
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        new_issues = response.json()
        if not new_issues:
            break
        issues.extend(new_issues)
        page += 1
    return issues

def save_issues_to_csv(issues, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['number', 'title', 'state', 'created_at', 'updated_at', 'closed_at', 'labels', 'assignees', 'comments']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for issue in issues:
            writer.writerow({
                'number': issue['number'],
                'title': issue['title'],
                'state': issue['state'],
                'created_at': issue['created_at'],
                'updated_at': issue['updated_at'],
                'closed_at': issue['closed_at'],
                'labels': ', '.join([label['name'] for label in issue['labels']]),
                'assignees': ', '.join([assignee['login'] for assignee in issue['assignees']]),
                'comments': issue['comments']
            })

if __name__ == "__main__":
    owner = input("Enter the repository owner: ")
    repo = input("Enter the repository name: ")
    token = input("Enter your GitHub personal access token: ")
    
    issues = get_github_issues(owner, repo, token)
    filename = f"{owner}_{repo}_issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    save_issues_to_csv(issues, filename)
    print(f"Issues saved to {filename}")