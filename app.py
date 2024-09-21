from flask import Flask, request, jsonify, abort
import jwt
import time
import hmac
import hashlib
import requests
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
import os
import chromadb

load_dotenv()

APP_ID = os.getenv("APP_ID")
PRIVATE_KEY = open('rsa.pem', 'r').read()
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

app = Flask(__name__)

model = SentenceTransformer("all-MiniLM-L6-v2")
issues_data = []

SIMILARITY_THRESHOLD = 0.5

chroma_client = chromadb.PersistentClient(path="./chroma")
collection = chroma_client.get_or_create_collection("github_issues")

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

def add_issues_to_chroma(issues):
    for issue in issues:
        issue_number = issue['number']
        issue_title = issue['title']
        issue_body = issue.get('body', '')
        full_issue = f"{issue_title} {issue_body}"
        
        embedding = model.encode(full_issue).tolist()
        
        collection.add(
            documents=[full_issue],
            metadatas=[{"issue_number": str(issue_number), "title": issue_title}],
            ids=[f"issue_{issue_number}"]
        )

@app.before_request
def verify_github_signature():
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        abort(400, "Signature is missing")

    calculated_signature = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        request.data,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, calculated_signature):
        abort(400, "Invalid signature")

@app.route('/webhook', methods=['POST'])
def github_webhook():
    print('Received webhook')
    data = request.json
    event_type = request.headers.get('X-GitHub-Event', 'ping')

    installation_id = data.get("installation", {}).get("id")

    if not installation_id:
        abort(400, "Installation ID is missing")

    print(f"Received webhook with event_type {event_type}")
    print(f"installation_id: {installation_id}")

    if event_type == 'installation_repositories':
        action = data.get('action')
        
        if action == 'added':
            repositories_added = data.get('repositories_added', [])
            for repo in repositories_added:
                repo_full_name = repo.get('full_name')
                if repo_full_name:
                    print(f"Repository added to installation: {repo_full_name}")
                    existing_issues = fetch_existing_issues(installation_id, repo_full_name)
                    add_issues_to_chroma(existing_issues)
                    print(f"Loaded {len(existing_issues)} existing issues into the database for {repo_full_name}")
        
        elif action == 'removed':
            repositories_removed = data.get('repositories_removed', [])
            for repo in repositories_removed:
                repo_full_name = repo.get('full_name')
                if repo_full_name:
                    print(f"Repository removed from installation: {repo_full_name}")
                    remove_issues_from_chroma(repo_full_name)
                    print(f"Removed issues for {repo_full_name} from the database")
        
        else:
            print(f"Unhandled action for installation_repositories event: {action}")

    elif event_type == 'installation':
        if data['action'] == 'created':
            repositories = data.get('repositories', [])
            for repo in repositories:
                repo_full_name = repo.get('full_name')
                if repo_full_name:
                    print(f"App installed on repository: {repo_full_name}")
                    existing_issues = fetch_existing_issues(installation_id, repo_full_name)
                    add_issues_to_chroma(existing_issues)
                    print(f"Loaded {len(existing_issues)} existing issues into the database for {repo_full_name}")

    elif event_type == 'issues':
        action = data.get('action')
        issue_number = data['issue']['number']
        issue_title = data['issue']['title']
        issue_body = data['issue'].get('body', '')
        repo_full_name = data.get('repository', {}).get('full_name')

        if not repo_full_name:
            abort(400, "Repository full name is missing")

        if action == 'opened':
            print(f'New issue opened: {issue_number} in {repo_full_name}')
            full_issue = f"{issue_title} {issue_body}"

            embedding = model.encode(full_issue).tolist()
            results = collection.query(
                query_embeddings=[embedding],
                n_results=1
            )

            if results['distances'][0] and results['distances'][0][0] < 1 - SIMILARITY_THRESHOLD:
                similar_issue = results['metadatas'][0][0]
                comment_text = f"Closed due to high similarity with issue #{similar_issue['issue_number']} with title '{similar_issue['title']}'"
                leave_comment(installation_id, repo_full_name, issue_number, comment_text)
                close_issue(installation_id, repo_full_name, issue_number)
                print(
                    f"The new issue #{issue_number} with title '{issue_title}' is most similar to existing issue #{similar_issue['issue_number']} with title '{similar_issue['title']}', with a cosine similarity of {1 - results['distances'][0][0]:.2f}."
                )
            else:
                print(
                    f"The new issue #{issue_number} with title '{issue_title}' is not similar to existing issues or cannot be closed due to missing information."
                )

            collection.add(
                documents=[full_issue],
                metadatas=[{"issue_number": str(issue_number), "title": issue_title, "repo_full_name": repo_full_name}],
                ids=[f"{repo_full_name}_{issue_number}"]
            )

    return jsonify({'status': 'success'}), 200

def remove_issues_from_chroma(repo_full_name):
    results = collection.get(where={"repo_full_name": repo_full_name})
    
    if results and results['ids']:
        collection.delete(ids=results['ids'])

if __name__ == '__main__':
    app.run(port=4000)