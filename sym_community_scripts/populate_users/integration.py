from abc import ABC, abstractmethod
from typing import Dict, List, Type

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
