#!/usr/bin/env python3
"""
Assign issues to user
"""
import os
import requests
import time

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "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")
REPO_OWNER = "Whatdidu"
REPO_NAME = "MOLT_Slazhivanie_FaceRecVisitLog"
ASSIGNEE = "IdiatullinaOlga"

API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


def assign_issue(issue_number: int, assignee: str):
    """Assign an issue to a user"""
    url = f"{API_URL}/{issue_number}"
    data = {"assignees": [assignee]}

    response = requests.patch(url, json=data, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def main():
    print(f"Assigning issues to {ASSIGNEE}...")

    # All issues to assign (epic + all tasks)
    all_issues = list(range(53, 70))  # Issues #53-69

    success_count = 0
    fail_count = 0

    for issue_num in all_issues:
        try:
            print(f"   Assigning issue #{issue_num}...", end=" ")
            assign_issue(issue_num, ASSIGNEE)
            print("OK")
            success_count += 1
            time.sleep(0.5)  # Rate limiting
        except Exception as e:
            print(f"ERROR: {e}")
            fail_count += 1

    print(f"\nDone! Assigned {success_count} issues, {fail_count} failures")


if __name__ == "__main__":
    main()
