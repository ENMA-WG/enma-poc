from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Optional

from .chat_provider import ChatProvider

ENV_VAR = "ENMA_LOCAL_PROVIDER_PATH"


def load_local_dev_provider() -> Optional[ChatProvider]:
    """Load an optional, git-ignored ChatProvider for local-only testing.

    Set ENMA_LOCAL_PROVIDER_PATH to a Python file (kept outside this repo,
    e.g. in the sibling enma-poc-dev folder) that defines create_provider().
    Returns None when the variable is unset, so shipped builds never depend
    on it.
    """
    path_str = os.environ.get(ENV_VAR)
    if not path_str:
        return None

    path = Path(path_str)
    if not path.is_file():
        raise FileNotFoundError(f"{ENV_VAR} points to a missing file: {path}")

    spec = importlib.util.spec_from_file_location("local_dev_provider", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "create_provider"):
        raise AttributeError(
            f"{path} must define a create_provider() function returning a ChatProvider"
        )

    return module.create_provider()
