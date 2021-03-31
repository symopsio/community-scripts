# Author: Yasyf Mohamedali <yasyf@symops.io>
# Author: Joshua Timberman <joshua@symops.io>
# Author: Adam Buggia <adam@symops.io>
#
# Copyright: (c) SymOps, Inc.
# License: BSD-3-Clause

import csv
import json
from pathlib import Path
from typing import Dict, List, Set

import click
import inquirer

from ..script import Script
from .integration import Integration, IntegrationException


class PopulateUsers(Script):
    def __init__(self, csv_path: Path, integrations: List[str]) -> None:
        self.csv_path = csv_path
        self.db = self._parse_csv(csv_path)
        self.integrations = set(integrations) or self._default_integrations()

    @classmethod
    def _parse_csv(cls, csv_path: Path) -> Dict[str, Dict[str, str]]:
        with csv_path.open() as f:
            return {x["email"]: x for x in csv.DictReader(f)}

    def _missing_emails(self, integration) -> List[str]:
        return [e for e, d in self.db.items() if not d.get(integration)]

    def _integrations(self) -> List[str]:
        return list(next(iter(self.db.values())).keys())

    def _default_integrations(self) -> Set[str]:
        return set(self._integrations()) - {"email"}

    def _parse_xattrs(self) -> Dict:
        try:
            import xattr

            connectors = xattr.xattr(self.csv_path)["user.sym.connectors"]
            return json.loads(connectors)
        except Exception:
            return {}

    def _integration_type(self, integration: str) -> str:
        if integration in Integration._registry.keys():
            return integration
        if (cached := self._parse_xattrs().get(integration)) :
            return cached
        return inquirer.list_input(
            f"Select Connector for Integration '{integration}'",
            choices=list(Integration._registry.keys()),
        )

    def _ensure_integration(self, integration: str):
        if integration not in self._integrations():
            for row in self.db.values():
                row[integration] = ""

    def write_db(self):
        with self.csv_path.open("w") as f:
            writer = csv.DictWriter(f, fieldnames=self._integrations())
            writer.writeheader()
            for row in self.db.values():
                writer.writerow(row)

    def run(self):
        for integration in self.integrations:
            click.secho(f"\nIntegration: {integration}", bold=True)

            integration_type = self._integration_type(integration)
            klass = Integration._registry[integration_type]()
            click.secho(f"Connector: {integration_type}")

            self._ensure_integration(integration)

            emails = self._missing_emails(integration)
            if not emails:
                continue

            try:
                klass.prompt_for_creds()
                results = klass.fetch(emails)
            except IntegrationException as e:
                click.secho(f"Error: {e.format_message()}", fg="red")
                continue

            for email, value in results.items():
                self.db[email][integration] = value
            click.secho(f"Updated {len(results)} rows!", fg="green")

            remaining = len(emails) - len(results)
            if remaining:
                click.secho(f"There are {remaining} blanks.", fg="yellow")

        self.write_db()


@click.command()
@click.argument(
    "csv_path",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True, writable=True, resolve_path=True
    ),
)
@click.option("-i", "--integration", multiple=True, type=str)
def populate_users(csv_path: str, integration: List[str]):
    s = PopulateUsers(Path(csv_path), integration)
    s.run()
