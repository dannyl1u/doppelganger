from flask import Flask, request, jsonify
from transformers import AutoTokenizer, AutoModel
import torch
import chromadb
import numpy as np

app = Flask(__name__)

chroma_client = chromadb.Client()

collection_name = "github_issues"

existing_collections = chroma_client.list_collections()
if collection_name in existing_collections:
    chroma_client.delete_collection(collection_name)

collection = chroma_client.create_collection(name=collection_name)

tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
        embedding = outputs.last_hidden_state.mean(dim=1).numpy().flatten().tolist()

    if not all(isinstance(x, float) for x in embedding):
        raise ValueError("Embedding should be a flat list of floats.")

    return embedding

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
            issue_title = issue_title or "No title provided."
            issue_description = issue_description or "No description provided."

            new_embedding = get_embedding(issue_title + " " + issue_description)

            try:
                results = collection.query(
                    query_embeddings=[new_embedding],
                    n_results=5
                )

                found_similar = False

                if "documents" in results and isinstance(results["documents"], list):
                    for document in results["documents"]:
                        if "distance" in document and "id" in document:
                            if document["distance"] < 0.9:
                                print(f"New issue {issue_number} is similar to existing issue with ID {document['id']} and similarity score {document['distance']:.2f}")
                                found_similar = True

                if not found_similar:
                    print(f"New issue {issue_number} has no similar existing issues.")

                collection.add(
                    embeddings=[new_embedding],
                    documents=[f"{issue_title} {issue_description}"],
                    metadatas=[{"issue_number": issue_number, "title": issue_title, "description": issue_description}],
                    ids=[str(issue_number)]
                )

            except Exception as e:
                print("Error during Chroma query:", e)
                return jsonify({"status": "error", "message": "Failed to query embeddings"}), 500

    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run(port=4000)