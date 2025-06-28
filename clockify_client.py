import requests

class ClockifyClient:
    def __init__(self, api_key, workspace_id):
        self.api_key = api_key
        self.workspace_id = workspace_id
        self.base_url = f"https://api.clockify.me/api/v1/workspaces/{workspace_id}"

    def create_time_entry(self, start, end, description, project_id):
        headers = {"X-Api-Key": self.api_key, "Content-Type": "application/json"}
        payload = {
            "start": start,
            "end": end,
            "description": description,
            "projectId": project_id
        }
        response = requests.post(f"{self.base_url}/time-entries", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
