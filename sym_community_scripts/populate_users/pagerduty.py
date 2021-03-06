from typing import Dict, Generator, Set, Tuple

import click
import pdpyras

from .integration import Integration, IntegrationException


class PagerDuty(Integration, slug="pagerduty"):
    def __init__(self) -> None:
        self.session = None

    def prompt_for_creds(self) -> None:
        api_key = click.prompt("Enter PagerDuty API Key")
        self.session = pdpyras.APISession(api_key)
        try:
            self.session.get("users")
        except pdpyras.PDClientError:
            raise IntegrationException("Invalid API Key")

    def _fetch_all_users(self) -> Generator[Tuple[str, str], None, None]:
        for user in self.session.iter_all("users"):
            yield user["email"], user["id"]

    def fetch(self, emails: Set[str]) -> Dict[str, str]:
        results = {}
        for (email, id) in self._fetch_all_users():
            if email in emails:
                results[email] = id
        return results
