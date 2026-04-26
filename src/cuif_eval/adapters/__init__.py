from .base import AdapterResult
from .command import CommandAdapter, build_command_env
from .manual import ManualAdapter
from .mock import MockAdapter

ADAPTERS = {"mock": MockAdapter, "manual": ManualAdapter, "command": CommandAdapter}

__all__ = ["ADAPTERS", "AdapterResult", "CommandAdapter", "ManualAdapter", "MockAdapter", "build_command_env"]
