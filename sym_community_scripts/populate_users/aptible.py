from typing import Any, Dict, Generator, Set, Tuple

import click
import inquirer
import requests
from requests.exceptions import InvalidJSONError

from .integration import Integration, IntegrationException


class Aptible(Integration, slug="aptible"):
    def __init__(self) -> None:
        self.token = None

    def _create_access_token(self, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        r = requests.post("https://auth.aptible.com/tokens", json=payload)
        try:
            return r.status_code, r.json()
        except InvalidJSONError as e:
            raise IntegrationException(
                f"Unexpected response from Aptible! Invalid JSON: {e} ({r.status_code})"
            )

    def prompt_for_creds(self) -> None:
        aptible_email = self.env_or_prompt("APTIBLE_EMAIL", "Aptible Email")
        aptible_password = self.env_or_prompt("APTIBLE_PASSWORD", "Aptible Password")

        payload = {
            "expires_in": 43200,
            "grant_type": "password",
            "username": aptible_email,
            "password": aptible_password,
            "scope": "manage",
            "_source": "dashboard",
        }

        status_code, json = self._create_access_token(payload)

        if status_code == 401 and json.get("error") == "otp_token_required":
            payload["otp_token"] = click.prompt("Enter 2FA Token")
            status_code, json = self._create_access_token(payload)

        if status_code != 201:
            message = json.get("message", "")
            raise IntegrationException(f"Invalid credentials! {message} ({status_code})")

        try:
            self.token = json["access_token"]
        except KeyError:
            raise IntegrationException("Invalid credentials! Missing access_token.")

    def prompt_for_external_id(self) -> str:
        question = inquirer.Text("organization_id", message="What is your Aptible Organization ID?")
        return inquirer.prompt([question])["organization_id"]

    def _fetch_aptible_resource(self, path: str) -> Dict[str, Any]:
        r = requests.get(
            f"https://auth.aptible.com/{path}",
            headers={
                "Authorization": f"Bearer {self.token}",
            },
        )

        if r.status_code != 200:
            json = {}
            try:
                json = r.json()
            except InvalidJSONError as e:
                pass

            message = json.get("message", "")
            raise IntegrationException(f"Aptible connection issue! {message} ({r.status_code})")

        try:
            return r.json()
        except InvalidJSONError as e:
            raise IntegrationException(f"Unexpected response from Aptible! Invalid JSON: {e}")

    def _fetch_org_id(self) -> str:
        orgs = self._fetch_aptible_resource("organizations")
        try:
            return orgs["_embedded"]["organizations"][0]["id"]
        except (KeyError, IndexError) as e:
            raise IntegrationException(f"Unexpected response from Aptible! Missing org key: {e}")

    def _fetch_all_users(self) -> Generator[Tuple[str, str], None, None]:
        org_id = self._fetch_org_id()
        users = self._fetch_aptible_resource(f"organizations/{org_id}/users")
        try:
            for user in users["_embedded"]["users"]:
                yield user["email"], user["id"]
        except KeyError as e:
            raise IntegrationException(f"Unexpected response from Aptible! Missing user key: {e}")

    def fetch(self, emails: Set[str]) -> Dict[str, str]:
        results = {}
        for (email, id) in self._fetch_all_users():
            if email in emails:
                results[email] = id
        return results
