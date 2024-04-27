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

load_dotenv()

APP_ID = os.getenv("APP_ID")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

app = Flask(__name__)

model = SentenceTransformer("all-MiniLM-L6-v2")
issues_data = []

SIMILARITY_THRESHOLD = 0.5

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
    repo_full_name = data.get("repository", {}).get("full_name")

    if not installation_id:
        abort(400, "Installation ID is missing")

    if not repo_full_name:
        abort(400, "Repository full name is missing")

    if event_type == 'issues':
        action = data.get('action')
        issue_number = data['issue']['number']
        issue_title = data['issue']['title']
        issue_description = data['issue'].get('body', '')

        if action == 'opened':
            print(f'New issue opened: {issue_number}')
            full_issue = (issue_title or "") + (issue_description or "")

            if issues_data:
                query_embedding = model.encode(full_issue)
                array_embeddings = model.encode([issue['full_text'] for issue in issues_data])

                cosine_similarities = cosine_similarity([query_embedding], array_embeddings)
                max_similarity = max(cosine_similarities[0])
                max_index = cosine_similarities[0].tolist().index(max_similarity)

                if max_similarity > SIMILARITY_THRESHOLD and repo_full_name:
                    close_issue(installation_id, repo_full_name, issue_number)
                    most_similar_issue = issues_data[max_index]
                    print(
                        f"The new issue #{issue_number} with title '{issue_title}' is most similar to existing issue #{most_similar_issue['issue_number']} with title '{most_similar_issue['title']}', with a cosine similarity of {max_similarity:.2f}."
                    )
                else:
                    print(
                        f"The new issue #{issue_number} with title '{issue_title}' is not similar to existing issues or cannot be closed due to missing information."
                    )

            issues_data.append({
                "issue_number": issue_number,
                "title": issue_title,
                "full_text": full_issue
            })

    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run(port=4000)
