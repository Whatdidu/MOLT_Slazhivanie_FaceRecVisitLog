#!/usr/bin/env python3
"""
Script to add issues to GitHub Project board
"""
import os
import requests
import json
from typing import Dict, List, Optional

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "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")
REPO_OWNER = "Whatdidu"
REPO_NAME = "MOLT_Slazhivanie_FaceRecVisitLog"
PROJECT_NUMBER = 2

GRAPHQL_URL = "https://api.github.com/graphql"
HEADERS = {
    "Authorization": f"bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}


def run_graphql_query(query: str, variables: Optional[Dict] = None) -> Dict:
    """Execute GraphQL query"""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    response = requests.post(GRAPHQL_URL, json=payload, headers=HEADERS)
    response.raise_for_status()
    result = response.json()

    if "errors" in result:
        print(f"GraphQL errors: {json.dumps(result['errors'], indent=2)}")
        raise Exception(f"GraphQL query failed: {result['errors']}")

    return result["data"]


def get_project_info() -> Dict:
    """Get project ID and fields"""
    query = """
    query($owner: String!, $number: Int!) {
      user(login: $owner) {
        projectV2(number: $number) {
          id
          title
          fields(first: 20) {
            nodes {
              ... on ProjectV2Field {
                id
                name
              }
              ... on ProjectV2SingleSelectField {
                id
                name
                options {
                  id
                  name
                }
              }
            }
          }
        }
      }
    }
    """

    variables = {
        "owner": REPO_OWNER,
        "number": PROJECT_NUMBER
    }

    data = run_graphql_query(query, variables)
    return data["user"]["projectV2"]


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
    print("Starting to add issues to kanban board...")

    # Get project info
    print("\nGetting project information...")
    project = get_project_info()
    project_id = project["id"]
    print(f"   Project: {project['title']}")
    print(f"   Project ID: {project_id}")

    # Find Status field
    status_field = None
    for field in project["fields"]["nodes"]:
        if field.get("name") == "Status":
            status_field = field
            break

    if not status_field:
        print("ERROR: Status field not found in project!")
        return

    print(f"\n   Status field ID: {status_field['id']}")

    # Map status names to IDs
    status_options = {opt["name"]: opt["id"] for opt in status_field["options"]}
    print(f"   Available statuses: {list(status_options.keys())}")

    # Define issues to add
    # Epic
    epic_issue = 53

    # Completed issues (Phase 1-3)
    completed_issues = [54, 55, 56, 57, 58, 59, 60, 61, 62]

    # Pending issues (Phase 4-6)
    pending_issues = [63, 64, 65, 66, 67, 68, 69]

    # Add epic to "In Progress"
    print(f"\nAdding epic issue #{epic_issue}...")
    epic_node_id = get_issue_node_id(epic_issue)
    epic_item_id = add_issue_to_project(project_id, epic_node_id)

    if "In Progress" in status_options:
        update_project_item_status(project_id, epic_item_id, status_field["id"], status_options["In Progress"])
        print(f"   OK: Epic #{epic_issue} added and set to 'In Progress'")
    else:
        print(f"   WARNING: Epic #{epic_issue} added but 'In Progress' status not found")

    # Add completed issues to "Done"
    print(f"\nAdding {len(completed_issues)} completed issues...")
    for issue_num in completed_issues:
        try:
            issue_node_id = get_issue_node_id(issue_num)
            item_id = add_issue_to_project(project_id, issue_node_id)

            if "Done" in status_options:
                update_project_item_status(project_id, item_id, status_field["id"], status_options["Done"])
                print(f"   OK: Issue #{issue_num} added to 'Done'")
            else:
                print(f"   WARNING: Issue #{issue_num} added but 'Done' status not found")
        except Exception as e:
            print(f"   ERROR: Failed to add issue #{issue_num}: {e}")

    # Add pending issues to "To Do"
    print(f"\nAdding {len(pending_issues)} pending issues...")
    for issue_num in pending_issues:
        try:
            issue_node_id = get_issue_node_id(issue_num)
            item_id = add_issue_to_project(project_id, issue_node_id)

            if "Todo" in status_options:
                update_project_item_status(project_id, item_id, status_field["id"], status_options["Todo"])
                print(f"   OK: Issue #{issue_num} added to 'Todo'")
            elif "To Do" in status_options:
                update_project_item_status(project_id, item_id, status_field["id"], status_options["To Do"])
                print(f"   OK: Issue #{issue_num} added to 'To Do'")
            else:
                print(f"   WARNING: Issue #{issue_num} added but 'Todo'/'To Do' status not found")
        except Exception as e:
            print(f"   ERROR: Failed to add issue #{issue_num}: {e}")

    print("\nDone! All issues have been added to the kanban board.")
    print(f"   View at: https://github.com/users/{REPO_OWNER}/projects/{PROJECT_NUMBER}")


if __name__ == "__main__":
    main()
