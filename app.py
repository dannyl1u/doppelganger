from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import chromadb

app = Flask(__name__)

chroma_client = chromadb.Client()

collection_name = "github_issues"

model = SentenceTransformer("all-MiniLM-L6-v2")
texts = []

SIMILARITY_THRESHOLD = 0.7

@app.route('/webhook', methods=['POST'])
def github_webhook():
    print('Received webhook')
    data = request.json
    event_type = request.headers.get('X-GitHub-Event', 'ping')

    if event_type == 'pull_request':
        action = data.get('action')
        pr_number = data['pull_request']['number']
        if action == 'opened':
            print(f'New PR opened: {pr_number}')

    elif event_type == 'issues':
        action = data.get('action')
        issue_number = data['issue']['number']
        issue_title = data['issue']['title']
        issue_description = data['issue'].get('body', '')

        if action == 'opened':
            print(f'New issue opened: {issue_number}')
            issue_title = issue_title or ""
            issue_description = issue_description or ""
            full_issue = issue_title + issue_description

            if texts:
                query_embedding = model.encode(full_issue)
                array_embeddings = model.encode(texts)

                cosine_similarities = cosine_similarity(
                    [query_embedding], array_embeddings
                )

                max_similarity = max(cosine_similarities[0])
                max_index = cosine_similarities[0].tolist().index(max_similarity)

                if max_similarity > SIMILARITY_THRESHOLD:
                    print(
                        f"New issue {issue_number} is most similar to existing issue at index {max_index} with a similarity score of {max_similarity:.2f}"
                    )
                else:
                    print(f"New issue {issue_number} is not similar to any existing issues")

            texts.append(full_issue)

    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run(port=4000)
