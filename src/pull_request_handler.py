import logging

from src.github_api import leave_comment

logger = logging.getLogger(__name__)


def handle_new_pull_request(
    installation_id, repo_full_name, pull_request_number, pull_request_title, pull_request_body
):
    logger.info("inside handle enw pull reqeust")
    context = "I am coding with the Python programming language and I plan to merge in a pull request.\
     Given the title and description of my pull request, succinctly identify any potential issues or downsides"
    prompt = f"{context} \n Title: {pull_request_title} \n Description: {pull_request_body}"
    logging.info(prompt)
    # comment_text = "sample response from llm"
    # leave_comment(installation_id, repo_full_name, issue_number, comment_text)

