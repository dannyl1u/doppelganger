import json
import logging
import os
from typing import List

import ollama

from config import OLLAMA_MODEL
from src.github_api import leave_comment
from src.vector_db import query_by_function_names

logger = logging.getLogger(__name__)


def generate_pr_feedback(
    used_functions: List, pr_title: str, pr_body: str, pr_diff: str
) -> str:
    """Generate feedback using Ollama"""
    # TODO: refine the prompt
    prompt = f"""
    
    Review the Pull Request and concisely list potential downsides.
    Do not provide refactored code in your response.
    End your response with the sentence "Has the PR author considered these points?"
   
    Pull Request:
    Title: {pr_title}
    Description: {pr_body}

    Relevant context from codebase:
    {used_functions}

    Changes in PR:
    {pr_diff}
    """
    logging.info("generating feedback...")
    response = ollama.chat(
        model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]


def get_function_dependencies(changed_files: List[str]) -> List[str]:
    """Gets all internal functions that are imported into a file"""

    def _replace_dots_with_slash_in_json(json_data):
        if isinstance(json_data, dict):
            return {
                _replace_dots_with_slash_in_json(key): _replace_dots_with_slash_in_json(
                    value
                )
                for key, value in json_data.items()
            }
        elif isinstance(json_data, list):
            return [_replace_dots_with_slash_in_json(element) for element in json_data]
        elif isinstance(json_data, str):
            return json_data.replace(".", "/")
        else:
            return json_data

    function_set = set()

    # remove file extension
    changed_files = [os.path.splitext(x)[0] for x in changed_files]

    with open(
        "dependencies.json"
    ) as f:  # TODO: update dependencies.json when main branch is updated
        dependency_graph = _replace_dots_with_slash_in_json(json.load(f))
        for file in changed_files:
            if file in dependency_graph:
                function_set.update(dependency_graph[file])
    return list(function_set)


def handle_new_pull_request(
    installation_id: str,
    repo_id: int,
    repo_full_name: str,
    pr_number: int,
    pr_title: str,
    pr_body: str,
    pr_diff: str,
    changed_files: List[str],
):
    """Handle new pull request webhook"""
    try:
        dependency_functions = get_function_dependencies(changed_files)
        dependency_function_context = query_by_function_names(
            dependency_functions, repo_id
        )
        # Generate feedback
        feedback = generate_pr_feedback(
            dependency_function_context, pr_title, pr_body, pr_diff
        )

        # Post comment
        leave_comment(installation_id, repo_full_name, pr_number, feedback)

        logger.info(f"Posted feedback for PR #{pr_number} in {repo_full_name}")

    except Exception as e:
        logger.error(f"Error handling PR #{pr_number}: {str(e)}")
        raise
