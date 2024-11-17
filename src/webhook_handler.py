import hashlib
import hmac
import logging
import os
import shutil

import requests
from flask import Blueprint, request, jsonify, abort

from config import WEBHOOK_SECRET
from src.code_indexer import clone_repo_branch, index_code_files
from src.github_api import fetch_existing_issues
from src.issue_handler import handle_new_issue
from src.pull_request_handler import handle_new_pull_request
from src.vector_db import (
    add_issues_to_chroma,
    remove_issues_from_chroma,
    add_code_to_chroma,
)

logger = logging.getLogger(__name__)
webhook_blueprint = Blueprint("webhook", __name__)


@webhook_blueprint.before_request
def verify_github_signature():
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        abort(400, "Signature is missing")

    calculated_signature = (
        "sha256="
        + hmac.new(
            WEBHOOK_SECRET.encode("utf-8"), request.data, hashlib.sha256
        ).hexdigest()
    )

    if not hmac.compare_digest(signature, calculated_signature):
        abort(400, "Invalid signature")


@webhook_blueprint.route("/webhook", methods=["POST"])
def github_webhook():
    logger.info("Received webhook")
    data = request.json
    event_type = request.headers.get("X-GitHub-Event", "ping")

    installation_id = data.get("installation", {}).get("id")

    if not installation_id:
        abort(400, "Installation ID is missing")

    logger.info(f"Received webhook with event_type {event_type}")
    logger.info(f"installation_id: {installation_id}")

    if event_type == "installation_repositories":
        handle_installation_repositories(data, installation_id)
    elif event_type == "installation":
        handle_installation(data, installation_id)
    elif event_type == "issues":
        handle_issues(data, installation_id)
    elif event_type == "pull_request":
        handle_pull_requests(data, installation_id)

    return jsonify({"status": "success"}), 200


def handle_installation_repositories(data, installation_id):
    action = data.get("action")

    if action == "added":
        repositories_added = data.get("repositories_added", [])
        for repo in repositories_added:
            repo_full_name = repo.get("full_name")
            repo_id = repo.get("id")
            if repo_full_name and repo_id:
                logger.info(f"Repository added to installation: {repo_full_name}")
                existing_issues = fetch_existing_issues(installation_id, repo_full_name)
                add_issues_to_chroma(existing_issues, repo_id)
                logger.info(
                    f"Loaded {len(existing_issues)} existing issues into the database for {repo_full_name}"
                )

    elif action == "removed":
        repositories_removed = data.get("repositories_removed", [])
        for repo in repositories_removed:
            repo_full_name = repo.get("full_name")
            repo_id = repo.get("id")
            if repo_full_name and repo_id:
                logger.info(f"Repository removed from installation: {repo_full_name}")
                remove_issues_from_chroma(repo_id)
                logger.info(f"Removed issues for {repo_full_name} from the database")

    else:
        logger.info(f"Unhandled action for installation_repositories event: {action}")


def handle_installation(data, installation_id):
    if data["action"] == "created":
        repositories = data.get("repositories", [])
        for repo in repositories:
            repo_full_name = repo.get("full_name")
            repo_id = repo.get("id")
            if repo_full_name and repo_id:
                logger.info(f"App installed on repository: {repo_full_name}")
                existing_issues = fetch_existing_issues(installation_id, repo_full_name)
                add_issues_to_chroma(existing_issues, repo_id)
                logger.info(
                    f"Loaded {len(existing_issues)} existing issues into the database for {repo_full_name}"
                )


def handle_issues(data, installation_id):
    action = data.get("action")
    issue = data["issue"]
    repo_full_name = data.get("repository", {}).get("full_name")
    repo_id = data.get("repository", {}).get("id")

    if not repo_full_name or not repo_id:
        abort(400, "Repository full name or ID is missing")

    if action == "opened":
        handle_new_issue(
            installation_id,
            repo_id,
            repo_full_name,
            issue["number"],
            issue["title"],
            issue.get("body", ""),
        )


def handle_pull_requests(data, installation_id):
    action = data.get("action")
    pull_request = data["pull_request"]
    repo_full_name = data.get("repository", {}).get("full_name")
    repo_id = data.get("repository", {}).get("id")

    if not repo_full_name or not repo_id:
        abort(400, "Repository information missing")

    pr_diff = requests.get(pull_request["diff_url"]).text
    changed_files = [
        f["filename"] for f in requests.get(pull_request["url"] + "/files").json()
    ]

    if action == "opened" or action == "synchronize":
        temp_dir = None
        try:
            # Update main branch collection if needed
            temp_dir = clone_repo_branch(installation_id, repo_full_name, "main")
            code_files = index_code_files(temp_dir)
            add_code_to_chroma(code_files, repo_id, "main")

            # Handle the pull request
            handle_new_pull_request(
                installation_id,
                repo_id,
                repo_full_name,
                pull_request["number"],
                pull_request.get("title", ""),
                pull_request.get("body", ""),
                pr_diff,
                changed_files,
            )
        finally:
            if temp_dir and os.path.exists(temp_dir):
                logging.info(f"removing temp_dir {temp_dir}...")
                shutil.rmtree(temp_dir, ignore_errors=True)
