import logging
import ollama

from config import OLLAMA_MODEL
from src.github_api import leave_comment

logger = logging.getLogger(__name__)


def handle_new_pull_request(
    installation_id,
    repo_full_name,
    pull_request_number,
    pull_request_title,
    pull_request_body,
):
    context = "I am programming and I plan to merge in a pull request.\
     Given the title and description of my pull request, succinctly identify any potential issues or downsides. \
     End your response by asking if the PR author has considered these points"

    prompt = (
        f"{context} \n Title: {pull_request_title} \n Description: {pull_request_body}"
    )

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
    comment_text = response["message"]["content"]

    leave_comment(installation_id, repo_full_name, pull_request_number, comment_text)
