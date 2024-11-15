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
