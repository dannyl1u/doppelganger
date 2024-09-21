import jwt
import time
import requests
from config import APP_ID, PRIVATE_KEY

def generate_jwt():
    current_time = int(time.time())
    payload = {
        "iat": current_time,
        "exp": current_time + 600,
        "iss": APP_ID
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")

def get_access_token(installation_id):
    jwt_token = generate_jwt()
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        headers=headers
    )
    response.raise_for_status()
    return response.json()["token"]

def close_issue(installation_id, repo_full_name, issue_number):
    access_token = get_access_token(installation_id)
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {"state": "closed"}
    response = requests.patch(
        f"https://api.github.com/repos/{repo_full_name}/issues/{issue_number}",
        json=payload,
        headers=headers
    )
    response.raise_for_status()

def leave_comment(installation_id, repo_full_name, issue_number, comment_text):
    access_token = get_access_token(installation_id)
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "body": comment_text
    }
    response = requests.post(
        f"https://api.github.com/repos/{repo_full_name}/issues/{issue_number}/comments",
        json=payload,
        headers=headers
    )
    response.raise_for_status()

def fetch_existing_issues(installation_id, repo_full_name):
    access_token = get_access_token(installation_id)
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    issues = []
    page = 1
    while True:
        response = requests.get(
            f"https://api.github.com/repos/{repo_full_name}/issues",
            headers=headers,
            params={"state": "all", "per_page": 100, "page": page}
        )
        response.raise_for_status()
        page_issues = response.json()
        if not page_issues:
            break
        issues.extend(page_issues)
        page += 1
    return issues