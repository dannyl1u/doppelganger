import logging
import ollama
from typing import List, Dict

from config import OLLAMA_MODEL
from src.vector_db import query_similar_code
from src.github_api import leave_comment

logger = logging.getLogger(__name__)


def generate_pr_feedback(
    similar_code: List[Dict], pr_title: str, pr_body: str, pr_diff: str
) -> str:
    """Generate feedback using Ollama"""
    context = "\n".join(
        [f"File: {code['file_path']}\n{code['content']}\n---" for code in similar_code]
    )

    prompt = f"""
    
    You are to provide feedback on a code base pull request. Follow the Instructions to provide your feedback on the Context below.
    
    Start of Instructions:
    
    1. Review the pull request's title, description, code diff, and relevant context from the codebase.
    2. Using point-form, succinctly identify potential issues, code smells, code duplication, or downsides of 
    the pull request. 
    3. Consider interactions with the codebase and architectural design. 
    4. Remember that in the code diff, '+' is code addition and '-' is code subtraction.
    5. Do not provide refactored code as part of your feedback. 
    6. End your response with the sentence "Has the PR author considered these points?"
   
    End of Instructions.
      
    Start of Context:
    
    Pull Request:
    Title: {pr_title}
    Description: {pr_body}

    Relevant context from codebase:
    {context}

    Changes in PR:
    {pr_diff}
    
    End of Context.
    """
    logging.info("generating feedback...")
    response = ollama.chat(
        model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]


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
        # Query similar code from main branch
        similar_code = query_similar_code(
            changed_files, f"{pr_title} {pr_body} {pr_diff}", repo_id
        )

        # Generate feedback
        feedback = generate_pr_feedback(similar_code, pr_title, pr_body, pr_diff)

        # Post comment
        leave_comment(installation_id, repo_full_name, pr_number, feedback)

        logger.info(f"Posted feedback for PR #{pr_number} in {repo_full_name}")

    except Exception as e:
        logger.error(f"Error handling PR #{pr_number}: {str(e)}")
        raise
