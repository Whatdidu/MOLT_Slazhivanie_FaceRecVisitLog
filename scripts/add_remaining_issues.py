#!/usr/bin/env python3
"""
Add remaining issues that failed due to connection errors
"""
import os
import requests
import json
import time
from typing import Dict, List, Optional

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "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")
REPO_OWNER = "Whatdidu"
REPO_NAME = "MOLT_Slazhivanie_FaceRecVisitLog"
PROJECT_ID = "PVT_kwHOAYsxQs4BNHMM"
STATUS_FIELD_ID = "PVTSSF_lAHOAYsxQs4BNHMMzg8M6Z0"

GRAPHQL_URL = "https://api.github.com/graphql"
HEADERS = {
    "Authorization": f"bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}


def run_graphql_query(query: str, variables: Optional[Dict] = None, retry=3) -> Dict:
    """Execute GraphQL query with retry"""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    for attempt in range(retry):
        try:
            response = requests.post(GRAPHQL_URL, json=payload, headers=HEADERS, timeout=30)
            response.raise_for_status()
            result = response.json()

            if "errors" in result:
                print(f"GraphQL errors: {json.dumps(result['errors'], indent=2)}")
                raise Exception(f"GraphQL query failed: {result['errors']}")

            return result["data"]
        except Exception as e:
            if attempt < retry - 1:
                print(f"   Attempt {attempt + 1} failed, retrying in 2 seconds...")
                time.sleep(2)
            else:
                raise


def get_issue_node_id(issue_number: int) -> str:
    """Get GraphQL node ID for an issue"""
    query = """
    query($owner: String!, $repo: String!, $number: Int!) {
      repository(owner: $owner, name: $repo) {
        issue(number: $number) {
          id
        }
      }
    }
    """

    variables = {
        "owner": REPO_OWNER,
        "repo": REPO_NAME,
        "number": issue_number
    }

    data = run_graphql_query(query, variables)
    return data["repository"]["issue"]["id"]


def add_issue_to_project(project_id: str, issue_id: str) -> str:
    """Add an issue to the project"""
    query = """
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
        item {
          id
        }
      }
    }
    """

    variables = {
        "projectId": project_id,
        "contentId": issue_id
    }

    data = run_graphql_query(query, variables)
    return data["addProjectV2ItemById"]["item"]["id"]


def update_project_item_status(project_id: str, item_id: str, field_id: str, option_id: str):
    """Update the status of a project item"""
    query = """
    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: ProjectV2FieldValue!) {
      updateProjectV2ItemFieldValue(
        input: {
          projectId: $projectId
          itemId: $itemId
          fieldId: $fieldId
          value: $value
        }
      ) {
        projectV2Item {
          id
        }
      }
    }
    """

    variables = {
        "projectId": project_id,
        "itemId": item_id,
        "fieldId": field_id,
        "value": {"singleSelectOptionId": option_id}
    }

    run_graphql_query(query, variables)


def main():
    print("Adding remaining issues...")

    # Status option IDs (from previous run)
    # These can be obtained from the project, but we already know them
    STATUS_TODO = None
    STATUS_DONE = None

    # Get status options
    query = """
    query {
      node(id: "PVT_kwHOAYsxQs4BNHMM") {
        ... on ProjectV2 {
          field(name: "Status") {
            ... on ProjectV2SingleSelectField {
              options {
                id
                name
              }
            }
          }
        }
      }
    }
    """

    result = run_graphql_query(query)
    for opt in result["node"]["field"]["options"]:
        if opt["name"] == "Done":
            STATUS_DONE = opt["id"]
        elif opt["name"] == "Todo":
            STATUS_TODO = opt["id"]

    print(f"Status Done ID: {STATUS_DONE}")
    print(f"Status Todo ID: {STATUS_TODO}")

    # Remaining completed issues
    completed_remaining = [55, 57, 61, 62]

    # Remaining pending issues
    pending_remaining = [66]

    # Add completed issues
    print(f"\nAdding {len(completed_remaining)} completed issues...")
    for issue_num in completed_remaining:
        try:
            print(f"   Processing issue #{issue_num}...")
            issue_node_id = get_issue_node_id(issue_num)
            item_id = add_issue_to_project(PROJECT_ID, issue_node_id)
            update_project_item_status(PROJECT_ID, item_id, STATUS_FIELD_ID, STATUS_DONE)
            print(f"   OK: Issue #{issue_num} added to 'Done'")
            time.sleep(1)  # Rate limiting
        except Exception as e:
            print(f"   ERROR: Failed to add issue #{issue_num}: {e}")

    # Add pending issues
    print(f"\nAdding {len(pending_remaining)} pending issues...")
    for issue_num in pending_remaining:
        try:
            print(f"   Processing issue #{issue_num}...")
            issue_node_id = get_issue_node_id(issue_num)
            item_id = add_issue_to_project(PROJECT_ID, issue_node_id)
            update_project_item_status(PROJECT_ID, item_id, STATUS_FIELD_ID, STATUS_TODO)
            print(f"   OK: Issue #{issue_num} added to 'Todo'")
            time.sleep(1)  # Rate limiting
        except Exception as e:
            print(f"   ERROR: Failed to add issue #{issue_num}: {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()
