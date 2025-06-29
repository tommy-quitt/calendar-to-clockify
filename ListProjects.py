from clockify_client import ClockifyClient
import os
from dotenv import load_dotenv

load_dotenv()

clockify = ClockifyClient(
    api_key=os.getenv("CLOCKIFY_API_KEY"),
    workspace_id=os.getenv("CLOCKIFY_WORKSPACE_ID")
)

def list_all_projects(clockify_client):
    projects = clockify_client.get_projects()
    for project in projects:
        print(f"Project: {project['name']} (ID: {project['id']})")

list_all_projects(clockify)
# This script lists all projects in the Clockify workspace.
# It initializes the Clockify client with the API key and workspace ID from environment variables,