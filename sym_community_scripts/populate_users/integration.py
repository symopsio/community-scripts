from abc import ABC, abstractmethod
from typing import Dict, List, Type

import os

from click import ClickException


class IntegrationException(ClickException):
    pass


class Integration(ABC):
    _registry: Dict[str, Type["Integration"]] = {}

    def __init_subclass__(cls: Type["Integration"], /, slug, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._registry[slug] = cls

    @abstractmethod
    def prompt_for_creds(self) -> None:
        pass

    @abstractmethod
    def fetch(self, emails: List[str]) -> Dict[str, str]:
        pass

    def env_or_prompt(self, env_var: str, label: str) -> str:
        """
        Get a value from the supplied environment variable key or prompt if unspecified
        """
        if env_value := os.environ.get(env_var):
            return env_value
        return click.prompt(f"Enter {label}")
