from src.github_api import close_issue, leave_comment
from src.vector_db import add_issue_to_chroma, query_similar_issue
from config import SIMILARITY_THRESHOLD

def handle_new_issue(installation_id, repo_full_name, issue_number, issue_title, issue_body):
    print(f'New issue opened: {issue_number} in {repo_full_name}')
    full_issue = f"{issue_title} {issue_body}"

    similar_issue = query_similar_issue(full_issue)

    if similar_issue and similar_issue['distance'] < 1 - SIMILARITY_THRESHOLD:
        comment_text = f"Closed due to high similarity with issue #{similar_issue['issue_number']} with title '{similar_issue['title']}'"
        leave_comment(installation_id, repo_full_name, issue_number, comment_text)
        close_issue(installation_id, repo_full_name, issue_number)
        print(
            f"The new issue #{issue_number} with title '{issue_title}' is most similar to existing issue #{similar_issue['issue_number']} with title '{similar_issue['title']}', with a cosine similarity of {1 - similar_issue['distance']:.2f}."
        )
    else:
        print(
            f"The new issue #{issue_number} with title '{issue_title}' is not similar to existing issues or cannot be closed due to missing information."
        )

    add_issue_to_chroma(full_issue, issue_number, issue_title, repo_full_name)