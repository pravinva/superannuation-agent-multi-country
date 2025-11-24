"""Configuration package for superannuation agent."""

import importlib.util
from pathlib import Path

# Import and expose everything from the root-level config.py file
# This resolves the naming conflict between config.py file and config/ package
_config_module_path = Path(__file__).parent.parent / 'config.py'
if _config_module_path.exists():
    _spec = importlib.util.spec_from_file_location("_root_config", _config_module_path)
    if _spec and _spec.loader:
        _root_config = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_root_config)

        # Export all public symbols from root config.py
        for _name in dir(_root_config):
            if not _name.startswith('_'):
                globals()[_name] = getattr(_root_config, _name)
