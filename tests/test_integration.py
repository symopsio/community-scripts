import os

import click
import pytest


class TestEnvOrPrompt:
    @pytest.fixture
    def mock_env(self, monkeypatch):
        envs = {"FOO": "bar"}
        monkeypatch.setattr(os, "environ", envs)

    @pytest.fixture
    def mock_click(self, mocker):
        mocker.patch("click.prompt", return_value="baz")

    def test_env_or_prompt_with_env(self, integration_stub, mock_env):
        assert integration_stub.env_or_prompt("FOO", "Foo") == "bar"

    def test_env_or_prompt_with_click(self, integration_stub, mock_click):
        assert integration_stub.env_or_prompt("FOO", "Foo") == "baz"

    def test_env_or_prompt_with_env_and_click(self, integration_stub, mock_env, mock_click):
        assert click.prompt() == "baz"
        assert integration_stub.env_or_prompt("FOO", "Foo") == "bar"
