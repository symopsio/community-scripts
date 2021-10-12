import os
from typing import Dict, Set

import click
import pytest

from sym_community_scripts.populate_users.integration import Integration


class TestIntegration(Integration, slug="test"):
    def prompt_for_creds(self) -> None:
        pass

    def fetch(self, emails: Set[str]) -> Dict[str, str]:
        pass


@pytest.fixture
def integration():
    return TestIntegration()


@pytest.fixture
def mock_env(monkeypatch):
    envs = {"FOO": "bar"}
    monkeypatch.setattr(os, "environ", envs)


@pytest.fixture
def mock_click(mocker):
    mocker.patch("click.prompt", return_value="baz")


def test_env_or_prompt_with_env(integration, mock_env):
    assert integration.env_or_prompt("FOO", "Foo") == "bar"


def test_env_or_prompt_with_click(integration, mock_click):
    assert integration.env_or_prompt("FOO", "Foo") == "baz"


def test_env_or_prompt_with_env_and_click(integration, mock_env, mock_click):
    assert click.prompt() == "baz"
    assert integration.env_or_prompt("FOO", "Foo") == "bar"
