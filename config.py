"""Configuration module for the AI Coding Agent."""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class Config:
    """Agent runtime configuration settings."""

    # LLM Settings
    llm_provider: str = field(
        default_factory=lambda: os.getenv("LLM_PROVIDER", "openai").lower()
    )
    llm_model: str = field(
        default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini")
    )
    llm_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("LLM_API_KEY")
    )
    llm_base_url: Optional[str] = field(
        default_factory=lambda: os.getenv("LLM_BASE_URL")
    )

    # Agent Limits & Flags
    max_debug_iterations: int = field(
        default_factory=lambda: int(os.getenv("MAX_DEBUG_ITERATIONS", "3"))
    )
    command_timeout: int = field(
        default_factory=lambda: int(os.getenv("COMMAND_TIMEOUT", "120"))
    )
    auto_approve: bool = field(
        default_factory=lambda: os.getenv("AUTO_APPROVE", "false").lower() in ("true", "1", "yes")
    )

    # Workspace directory
    workspace_dir: Path = field(
        default_factory=lambda: Path(os.getenv("WORKSPACE_DIR", "./workspace/repositories")).resolve()
    )

    # Default ignored directories for file crawlers and search
    ignore_dirs: List[str] = field(
        default_factory=lambda: [
            ".git",
            "node_modules",
            "venv",
            ".venv",
            "env",
            ".env",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            "target",
            "build",
            "dist",
            ".idea",
            ".vscode",
            "bin",
            "obj",
            ".gradle",
        ]
    )


# Singleton default config instance
default_config = Config()
