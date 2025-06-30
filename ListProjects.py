from clockify_client import ClockifyClient
import os
from dotenv import load_dotenv

load_dotenv()

clockify = ClockifyClient(
    api_key=os.getenv("CLOCKIFY_API_KEY"),
    workspace_id=os.getenv("CLOCKIFY_WORKSPACE_ID")
)

# Use the method on ClockifyClient to print all projects
clockify.list_all_projects()
# This script lists all projects in the Clockify workspace.
# It initializes the Clockify client with the API key and workspace ID from environment variables,