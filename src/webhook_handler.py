from flask import Blueprint, request, jsonify, abort
import hmac
import hashlib
from config import WEBHOOK_SECRET
from src.github_api import fetch_existing_issues
from src.vector_db import add_issues_to_chroma, remove_issues_from_chroma
from src.issue_handler import handle_new_issue

import logging

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

    return jsonify({"status": "success"}), 200


def handle_installation_repositories(data, installation_id):
    action = data.get("action")

    if action == "added":
        repositories_added = data.get("repositories_added", [])
        for repo in repositories_added:
            repo_full_name = repo.get("full_name")
            if repo_full_name:
                logger.info(f"Repository added to installation: {repo_full_name}")
                existing_issues = fetch_existing_issues(installation_id, repo_full_name)
                add_issues_to_chroma(existing_issues)
                logger.info(
                    f"Loaded {len(existing_issues)} existing issues into the database for {repo_full_name}"
                )

    elif action == "removed":
        repositories_removed = data.get("repositories_removed", [])
        for repo in repositories_removed:
            repo_full_name = repo.get("full_name")
            if repo_full_name:
                logger.info(f"Repository removed from installation: {repo_full_name}")
                remove_issues_from_chroma(repo_full_name)
                logger.info(f"Removed issues for {repo_full_name} from the database")

    else:
        logger.info(f"Unhandled action for installation_repositories event: {action}")


def handle_installation(data, installation_id):
    if data["action"] == "created":
        repositories = data.get("repositories", [])
        for repo in repositories:
            repo_full_name = repo.get("full_name")
            if repo_full_name:
                logger.info(f"App installed on repository: {repo_full_name}")
                existing_issues = fetch_existing_issues(installation_id, repo_full_name)
                add_issues_to_chroma(existing_issues)
                logger.info(
                    f"Loaded {len(existing_issues)} existing issues into the database for {repo_full_name}"
                )


def handle_issues(data, installation_id):
    action = data.get("action")
    issue = data["issue"]
    repo_full_name = data.get("repository", {}).get("full_name")

    if not repo_full_name:
        abort(400, "Repository full name is missing")

    if action == "opened":
        handle_new_issue(
            installation_id,
            repo_full_name,
            issue["number"],
            issue["title"],
            issue.get("body", ""),
        )
