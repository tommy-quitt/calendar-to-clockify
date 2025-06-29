import requests

class ClockifyClient:
    def __init__(self, api_key, workspace_id):
        self.api_key = api_key
        self.workspace_id = workspace_id
        self.base_url = f"https://api.clockify.me/api/v1/workspaces/{workspace_id}"
        self._project_cache = None
        self._tag_cache = None
        self._user_id = None

    def get_user_id(self):
        if self._user_id:
            return self._user_id

        headers = {"X-Api-Key": self.api_key}
        response = requests.get("https://api.clockify.me/api/v1/user", headers=headers)
        response.raise_for_status()
        self._user_id = response.json()["id"]
        return self._user_id

    def get_projects(self):
        headers = {"X-Api-Key": self.api_key}
        response = requests.get(f"{self.base_url}/projects", headers=headers)
        response.raise_for_status()
        return response.json()

    def resolve_project_name(self, project_name):
        if self._project_cache is None:
            self._project_cache = self.get_projects()

        for proj in self._project_cache:
            if proj["name"] == project_name:
                return proj["id"]
        return None

    def ensure_tag(self, tag_name="calendar-bot"):
        if self._tag_cache is None:
            headers = {"X-Api-Key": self.api_key}
            response = requests.get(f"{self.base_url}/tags", headers=headers)
            response.raise_for_status()
            self._tag_cache = response.json()

        for tag in self._tag_cache:
            if tag["name"] == tag_name:
                return tag["id"]

        # Create tag if not found
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        tag_data = {"name": tag_name}
        response = requests.post(f"{self.base_url}/tags", headers=headers, json=tag_data)
        response.raise_for_status()
        new_tag = response.json()
        self._tag_cache.append(new_tag)
        return new_tag["id"]

    def get_time_entries(self, start, end):
        """
        Retrieve existing time entries for current user between start and end (ISO strings).
        """
        user_id = self.get_user_id()
        headers = {"X-Api-Key": self.api_key}
        params = {
            "start": start,
            "end": end
        }
        url = f"{self.base_url}/user/{user_id}/time-entries"
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def create_time_entry(self, start, end, description, project_id):
        """
        Create a time entry in Clockify with a 'calendar-bot' tag.
        """
        tag_id = self.ensure_tag()
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "start": start,
            "end": end,
            "description": description,
            "tagIds": [tag_id]
        }
        if project_id:
            payload["projectId"] = project_id

        response = requests.post(f"{self.base_url}/time-entries", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
