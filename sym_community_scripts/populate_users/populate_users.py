# Author: Yasyf Mohamedali <yasyf@symops.io>
# Author: Joshua Timberman <joshua@symops.io>
# Author: Adam Buggia <adam@symops.io>
#
# Copyright: (c) SymOps, Inc.
# License: BSD-3-Clause

import csv
from pathlib import Path
from typing import Dict, List, Set

import click
import inquirer

from ..script import Script
from .integration import Integration, IntegrationException


class PopulateUsers(Script):
    INQUIRER_SKIP_OPTION = "SELECT TO SKIP"
    SERVICE_KEY_DELIMITER = ":"

    def __init__(
        self,
        csv_path: Path,
        integrations: List[str],
        *,
        import_new: bool,
    ) -> None:
        self.csv_path = csv_path
        self.db = self._parse_csv(csv_path)
        self.integrations = set(integrations) or self._default_integrations()
        self.import_new = import_new

    @classmethod
    def _parse_csv(cls, csv_path: Path) -> Dict[str, Dict[str, str]]:
        all_user_data = {}
        with csv_path.open() as f:
            for user_data in csv.DictReader(f):
                email = user_data.get(f"sym{cls.SERVICE_KEY_DELIMITER}cloud") or user_data.get(
                    "email"
                )
                all_user_data[email] = user_data
        return all_user_data

    def _missing_emails(self, integration) -> List[str]:
        return [e for e, d in self.db.items() if not d.get(integration)]

    def _integrations(self) -> List[str]:
        return list(next(iter(self.db.values())).keys())

    def _default_integrations(self) -> Set[str]:
        return set(self._integrations()) - {
            "email",
            f"sym{self.SERVICE_KEY_DELIMITER}cloud",
            "User ID",
        }

    def _integration_type(self, integration: str) -> str:
        if integration in Integration._registry.keys():
            return integration

        return inquirer.list_input(
            f"Select Service for Integration '{integration}'",
            choices=list(Integration._registry.keys()) + [self.INQUIRER_SKIP_OPTION],
        )

    def _ensure_integration(self, integration: str):
        if integration not in self._integrations():
            for row in self.db.values():
                row[integration] = ""

    def _parse_integration_type_from_key(self, key: str) -> str:
        """From a key such as ``slack:T12345`` or ``google:symops.io``,
        parse out the integration type. If there is no separator, assumes
        the entire key represents the integration type.
        """
        try:
            return key.split(":")[0]
        except IndexError:
            return key

    def write_db(self):
        with self.csv_path.open("w") as f:
            writer = csv.DictWriter(f, fieldnames=self._integrations())
            writer.writeheader()
            for row in self.db.values():
                writer.writerow(row)

    def run(self):
        for integration in self.integrations:
            click.secho(f"\nIntegration: {integration}", bold=True)

            integration_type = self._parse_integration_type_from_key(integration)
            if not integration_type or not Integration.is_supported(integration_type):
                integration_type = self._integration_type(integration)

            if integration_type == self.INQUIRER_SKIP_OPTION:
                continue

            klass = Integration._registry[integration_type]()
            click.secho(f"Service: {integration_type}")
            integration_header = integration
            if self.SERVICE_KEY_DELIMITER not in integration_header:
                external_id = klass.prompt_for_external_id()
                integration_header = f"{integration}:{external_id}"

            self._ensure_integration(integration_header)

            if self.import_new and klass.supports_importing_new():
                emails = None
            else:
                emails = self._missing_emails(integration_header)
                if not emails:
                    continue

            try:
                klass.prompt_for_creds()
                results = klass.fetch(emails)
            except IntegrationException as e:
                click.secho(f"Error: {e.format_message()}", fg="red")
                continue

            for email, value in results.items():
                self.db[email][integration_header] = value
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
@click.option("--import-new/--no-import-new", default=False)
@click.option("-i", "--integration", multiple=True, type=str)
def populate_users(csv_path: str, import_new: bool, integration: List[str]):
    s = PopulateUsers(Path(csv_path), integration, import_new=import_new)
    s.run()
