import ast
import os
from typing import List, Dict, Any
import re
import chromadb
from sentence_transformers import SentenceTransformer
from config import ROOT_DIR

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


def add_issues_to_chroma(issues, repo_id):
    for issue in issues:
        issue_number = issue["number"]
        issue_title = issue["title"]
        issue_body = issue.get("body", "")
        full_issue = f"{issue_title} {issue_body}"
        repo_id = issue["repository"]["id"]

        add_issue_to_chroma(full_issue, issue_number, issue_title, repo_id)


def get_collection_for_repo_branch(repo_id: int, branch: str = "main"):
    return chroma_client.get_or_create_collection(f"github_code_{repo_id}_{branch}")


def _extract_function_info(file_path: str) -> List[Dict[str, Any]]:
    """
    Extract function information from a Python file

    :param file_path: Path to the Python source file
    :return: List of function information dictionaries
    """
    with open(file_path, "r") as f:
        try:
            tree = ast.parse(f.read(), filename=file_path)
        except SyntaxError:
            return []  # Skip files with syntax errors

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_name = node.name
            func_path = f"{file_path}:{func_name}"
            code = ast.get_source_segment(open(file_path).read(), node)
            if code:
                functions.append(
                    {
                        "function_path": func_path,
                        "file_path": file_path,
                        "function_name": func_name,
                        "source_code": code,
                    }
                )
    return functions


def _format_function_path(function_path: str, file_extensions: List[str]) -> str:
    relative_path = os.path.relpath(function_path, ROOT_DIR)
    formatted_func_path = relative_path.replace("\\", "/")
    pattern = r"(" + "|".join(re.escape(ext) for ext in file_extensions) + r"):"
    formatted_func_path = re.sub(pattern, "/", formatted_func_path)
    return formatted_func_path


def embed_code_base(
    repo_id: int, base_path: str, file_extensions: List[str] = [".py"]
) -> None:
    """
    Recursively embed all functions in a code base

    :param repo_id: Repository ID of code base
    :param base_path: Root directory of the code base
    :param file_extensions: List of file extensions to process
    """

    # Add or update code files in the collection
    collection = get_collection_for_repo_branch(repo_id)

    # Walk through the directory
    for root, _, files in os.walk(base_path):
        for file in files:
            # Check file extension
            if any(file.endswith(ext) for ext in file_extensions):
                file_path = os.path.join(root, file)

                # Extract function information
                functions = _extract_function_info(file_path)

                # Embed and store functions
                for func in functions:

                    func["function_path"] = _format_function_path(
                        func["function_path"], file_extensions
                    )

                    # Create embedding
                    embedding = model.encode(f"{func['source_code']}").tolist()

                    # Add to ChromaDB
                    collection.add(
                        ids=[func["function_path"]],
                        embeddings=[embedding],
                        documents=[func["source_code"]],
                        metadatas=[
                            {
                                "function_path": func[
                                    "function_path"
                                ],  # sample: src/vector_db/add_issue_to_chroma
                                "file_path": func[
                                    "file_path"
                                ],  # sample: '<absolutute path to doppelganger>\\src\\vector_db.py'
                                "function_name": func[
                                    "function_name"
                                ],  # sample: add_issue_to_chroma
                            }
                        ],
                    )


def query_by_function_names(function_paths, repo_id):
    collection = get_collection_for_repo_branch(repo_id)
    """
    Retrieve full code and metadata for a list of specific function name paths.
    
    :param functions: List of full function name paths to retrieve
    :return: List of dictionaries containing function details
    """
    # Validate input
    if not function_paths:
        return []

    # Retrieve functions from ChromaDB
    results = collection.get(where={"function_path": {"$in": function_paths}})

    # Process and format results
    function_details = []

    for i in range(len(results["ids"])):
        function_info = {
            "source_code": results["documents"][i] if results["documents"] else None,
            "metadata": results["metadatas"][i] if results["metadatas"] else None,
        }

        function_details.append(function_info)

    return function_details
