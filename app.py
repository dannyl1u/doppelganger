from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

app = Flask(__name__)

model = SentenceTransformer("all-MiniLM-L6-v2")
issues_data = []

SIMILARITY_THRESHOLD = 0.5

@app.route('/webhook', methods=['POST'])
def github_webhook():
    print('Received webhook')
    data = request.json
    event_type = request.headers.get('X-GitHub-Event', 'ping')

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

                if max_similarity > SIMILARITY_THRESHOLD:
                    most_similar_issue = issues_data[max_index]
                    print(
                        f"The new issue #{issue_number} with title '{issue_title}' is most similar to existing issue #{most_similar_issue['issue_number']} with title '{most_similar_issue['title']}', having a cosine similarity of {max_similarity:.2f}."
                    )
                else:
                    print(f"The new issue #{issue_number} with title '{issue_title}' is not similar to any existing issue.")

            issues_data.append({
                "issue_number": issue_number,
                "title": issue_title,
                "full_text": full_issue
            })

    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run(port=4000)
