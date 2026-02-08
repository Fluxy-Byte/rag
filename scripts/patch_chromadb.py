"""
Hotfix para chromadb em Python 3.14 (pydantic v2).

O que faz:
- Usa pydantic_settings.BaseSettings quando disponível.
- Ajusta os validators para pydantic v2.
- Define extra="ignore" para campos não mapeados.
- Adiciona type hints em chroma_coordinator_host/logservice_*.

Execução:
  python scripts/patch_chromadb.py

Idempotente: pode rodar de novo sem quebrar.
"""

from __future__ import annotations

import re
from pathlib import Path

import chromadb  # type: ignore


def apply_patch(config_path: Path) -> None:
    original = config_path.read_text(encoding="utf-8")
    updated = original

    # 1) Inject compatibility header (pydantic_settings + field_validator)
    pattern_header = r"""
import importlib
import inspect
import logging
from abc import ABC
from enum import Enum
from graphlib import TopologicalSorter
from typing import Optional, List, Any, Dict, Set, Iterable, Union
from typing import Type, TypeVar, cast

from overrides import EnforceOverrides
from overrides import override
from typing_extensions import Literal
import platform

in_pydantic_v2 = False
try:
    from pydantic import BaseSettings
except ImportError:
    in_pydantic_v2 = True
    from pydantic.v1 import BaseSettings
    from pydantic.v1 import validator

if not in_pydantic_v2:
    from pydantic import validator  # type: ignore # noqa
"""
    replacement_header = """
import importlib
import inspect
import logging
from abc import ABC
from enum import Enum
from graphlib import TopologicalSorter
from typing import Optional, List, Any, Dict, Set, Iterable, Union
from typing import Type, TypeVar, cast

from overrides import EnforceOverrides
from overrides import override
from typing_extensions import Literal
import platform

# --- Pydantic compatibility (Python 3.14) ---
USING_PYDANTIC_V2 = False
try:
    from pydantic_settings import BaseSettings  # type: ignore
    from pydantic import field_validator  # type: ignore
    USING_PYDANTIC_V2 = True
except ImportError:  # fallback
    try:
        from pydantic import BaseSettings  # type: ignore
        from pydantic import validator as field_validator  # type: ignore
    except ImportError:
        from pydantic.v1 import BaseSettings  # type: ignore
        from pydantic.v1 import validator as field_validator  # type: ignore
"""
    updated = re.sub(pattern_header.strip(), replacement_header.strip(), updated, count=1, flags=re.S)

    # 2) Fix chroma_coordinator_host/logservice types
    updated = re.sub(r"\n    chroma_coordinator_host\s*=\s*\"localhost\"",
                     '\n    chroma_coordinator_host: str = "localhost"', updated, count=1)
    updated = re.sub(r"\n    chroma_logservice_host\s*=\s*\"localhost\"",
                     '\n    chroma_logservice_host: str = "localhost"', updated, count=1)
    updated = re.sub(r"\n    chroma_logservice_port\s*=\s*50052",
                     "\n    chroma_logservice_port: int = 50052", updated, count=1)

    # 3) Replace validator definition with v2-friendly version
    validator_pattern = r"""
    @validator\("chroma_server_nofile", pre=True, always=True, allow_reuse=True\)
    def empty_str_to_none\(cls, v: str\) -> Optional\[str\]:
        if type\(v\) is str and v.strip\(\) == "":
            return None
        return v
"""
    validator_repl = """
    if USING_PYDANTIC_V2:
        @field_validator("chroma_server_nofile", mode="before")
        def empty_str_to_none(cls, v: str):  # type: ignore
            if type(v) is str and v.strip() == "":
                return None
            return v
    else:
        @field_validator("chroma_server_nofile", pre=True, always=True, allow_reuse=True)  # type: ignore
        def empty_str_to_none(cls, v: str):
            if type(v) is str and v.strip() == "":
                return None
            return v
"""
    updated = re.sub(validator_pattern.strip(), validator_repl.strip(), updated, count=1, flags=re.S)

    # 4) Allow extra env vars (extra = ignore) and env_file support
    # Remove any existing Config/model_config block and replace with unified one
    updated = re.sub(r"\n\s*class Config:\n\s*extra = \"ignore\"\n", "", updated, count=1)
    updated = re.sub(r"\n\s*class Config:\n\s*env_file = \".env\"\n\s*env_file_encoding = \"utf-8\"\n", "", updated, count=1)
    model_cfg_pattern = r"\nclass Settings\(BaseSettings\):\s+# type: ignore\n"
    model_cfg_repl = (
        "\nclass Settings(BaseSettings):  # type: ignore\n"
        "    # extra env vars won't break validation\n"
        "    model_config = {\n"
        "        \"extra\": \"ignore\",\n"
        "        \"env_file\": \".env\",\n"
        "        \"env_file_encoding\": \"utf-8\",\n"
        "    }\n"
    )
    updated = re.sub(model_cfg_pattern, model_cfg_repl, updated, count=1)

    if updated != original:
        config_path.write_text(updated, encoding="utf-8")
        print(f"[ok] Patched {config_path}")
    else:
        print(f"[skip] Already patched {config_path}")


def main():
    config_path = Path(chromadb.__file__).resolve().parent / "config.py"
    apply_patch(config_path)


if __name__ == "__main__":
    main()
