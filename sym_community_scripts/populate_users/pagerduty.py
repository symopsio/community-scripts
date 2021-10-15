from typing import Dict, Generator, Set, Tuple

import click
import pdpyras
import inquirer

from .integration import Integration, IntegrationException


class PagerDuty(Integration, slug="pagerduty"):
    def __init__(self) -> None:
        self.session = None

    def prompt_for_creds(self) -> None:
        api_key = self.env_or_prompt("PAGERDUTY_API_KEY", "PagerDuty API Key")
        self.session = pdpyras.APISession(api_key)
        try:
            self.session.get("users")
        except pdpyras.PDClientError:
            raise IntegrationException("Invalid API Key")

    def prompt_for_external_id(self) -> str:
        question = inquirer.Text("domain", message="What is your PagerDuty account domain?")
        return inquirer.prompt([question])["domain"]

    def _fetch_all_users(self) -> Generator[Tuple[str, str], None, None]:
        for user in self.session.iter_all("users"):
            yield user["email"], user["id"]

    def fetch(self, emails: Set[str]) -> Dict[str, str]:
        results = {}
        for (email, id) in self._fetch_all_users():
            if email in emails:
                results[email] = id
        return results
