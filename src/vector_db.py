from typing import List, Dict

import chromadb
from sentence_transformers import SentenceTransformer

chroma_client = chromadb.PersistentClient(path="./chroma")
model = SentenceTransformer("all-MiniLM-L6-v2")


def get_collection_for_repo(repo_id):
    return chroma_client.get_or_create_collection(f"github_issues_{repo_id}")


def add_issue_to_chroma(full_issue, issue_number, issue_title, repo_id):
    embedding = model.encode(full_issue).tolist()
    collection = get_collection_for_repo(repo_id)

    collection.add(
        documents=[full_issue],
        metadatas=[
            {
                "issue_number": str(issue_number),
                "title": issue_title,
                "repo_id": repo_id,
            }
        ],
        embeddings=[embedding],
        ids=[f"{repo_id}_{issue_number}"],
    )


def query_similar_issue(full_issue, repo_id):
    embedding = model.encode(full_issue).tolist()
    collection = get_collection_for_repo(repo_id)
    results = collection.query(query_embeddings=[embedding], n_results=1)

    if results["distances"][0]:
        return {
            "issue_number": results["metadatas"][0][0]["issue_number"],
            "title": results["metadatas"][0][0]["title"],
            "distance": results["distances"][0][0],
        }
    return None


def remove_issues_from_chroma(repo_id):
    collection = get_collection_for_repo(repo_id)
    results = collection.get(where={"repo_id": repo_id})

    if results and results["ids"]:
        collection.delete(ids=results["ids"])


def add_issues_to_chroma(issues):
    for issue in issues:
        issue_number = issue["number"]
        issue_title = issue["title"]
        issue_body = issue.get("body", "")
        full_issue = f"{issue_title} {issue_body}"
        repo_id = issue["repository"]["id"]

        add_issue_to_chroma(full_issue, issue_number, issue_title, repo_id)


def get_collection_for_repo_branch(repo_id: int, branch: str = "main"):
    return chroma_client.get_or_create_collection(f"github_code_{repo_id}_{branch}")


def add_code_to_chroma(
    code_files: List[Dict[str, str]], repo_id: int, branch: str = "main"
):
    """Add or update code files in the collection"""
    collection = get_collection_for_repo_branch(repo_id, branch)

    # Prepare all documents for batch processing
    documents = []
    metadatas = []
    ids = []
    embeddings = []

    for file in code_files:
        file_id = f"{repo_id}_{branch}_{file['path']}"
        embedding = model.encode(file["content"]).tolist()

        documents.append(file["content"])
        metadatas.append(
            {"file_path": file["path"], "repo_id": repo_id, "branch": branch}
        )
        embeddings.append(embedding)
        ids.append(file_id)

    # Get existing IDs in the collection
    existing_ids = set()
    try:
        existing = collection.get()
        if existing and existing["ids"]:
            existing_ids = set(existing["ids"])
    except Exception:
        pass  # Collection might be empty

    # Split into new and existing documents
    new_indices = []
    update_indices = []

    for i, doc_id in enumerate(ids):
        if doc_id in existing_ids:
            update_indices.append(i)
        else:
            new_indices.append(i)

    # Add new documents
    if new_indices:
        collection.add(
            documents=[documents[i] for i in new_indices],
            metadatas=[metadatas[i] for i in new_indices],
            embeddings=[embeddings[i] for i in new_indices],
            ids=[ids[i] for i in new_indices],
        )

    # Update existing documents
    if update_indices:
        collection.update(
            documents=[documents[i] for i in update_indices],
            metadatas=[metadatas[i] for i in update_indices],
            embeddings=[embeddings[i] for i in update_indices],
            ids=[ids[i] for i in update_indices],
        )


def query_similar_code(
    changed_files: List[str], pr_content: str, repo_id: int
) -> List[Dict]:
    collection = get_collection_for_repo_branch(repo_id)
    embedding = model.encode(pr_content).tolist()

    results = collection.query(
        query_embeddings=[embedding],
        n_results=5,
        where={"file_path": {"$in": changed_files}},
    )

    return [
        {"file_path": meta["file_path"], "content": doc, "distance": dist}
        for meta, doc, dist in zip(
            results["metadatas"][0], results["documents"][0], results["distances"][0]
        )
    ]
