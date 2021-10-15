from typing import Dict, Set

import pytest

from sym_community_scripts.populate_users.integration import Integration


class IntegrationStub(Integration, slug="test"):
    def prompt_for_creds(self) -> None:
        pass

    def fetch(self, emails: Set[str]) -> Dict[str, str]:
        pass


@pytest.fixture
def integration_stub():
    return IntegrationStub()
