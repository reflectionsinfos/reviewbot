"""
Services package.

Keep this module side-effect free so importing submodules does not eagerly pull
in optional providers or heavyweight integrations.
"""

__all__ = [
    "checklist_parser",
    "report_generator",
    "voice_interface",
    "checklist_optimizer",
]
