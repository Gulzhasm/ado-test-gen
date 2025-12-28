import requests
from ado.auth import build_auth_header
from config import settings

class ADOClient:
    """
    Reusable Azure DevOps API client using PAT authentication.
    """

    def __init__(self):
        self.base_url = f"https://dev.azure.com/{settings.ado_org}/{settings.ado_project}"
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()

        session.headers.update({
            "Authorization": build_auth_header(settings.ado_pat),
            "Content-Type": "application/json-patch+json",
            "Accept": "application/json"
        })
        return session
    
    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
    
    def get(self, path: str, params: dict | None = None) -> requests.Response:
        response = self.session.get(self._url(path), params=params)
        print("GET:", self._url(path), "params:", params)
        response.raise_for_status()
        return response
    
    def post(self, path: str, json: list | dict | None = None) -> requests.Response:
        response = self.session.post(self._url(path), json=json)
        response.raise_for_status()
        return response
    
    def patch(self, path: str, json: list) -> requests.Response:
        response = self.session.patch(self._url(path), json=json)
        response.raise_for_status()
        return response