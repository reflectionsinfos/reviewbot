"""
Template Manager
Manages checklist templates and project-specific files
"""
from pathlib import Path
from typing import List, Optional
from app.core.config import settings


class TemplateManager:
    """Manage checklist templates"""
    
    def __init__(self):
        self.templates_dir = Path(settings.TEMPLATES_DIR)
        self.projects_dir = Path(settings.PROJECTS_DATA_DIR)
        
        # Ensure directories exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.projects_dir.mkdir(parents=True, exist_ok=True)
    
    def list_templates(self) -> List[Path]:
        """List all available templates"""
        return list(self.templates_dir.glob("*.xlsx"))
    
    def get_template(self, name: str) -> Optional[Path]:
        """Get template by name"""
        template_path = self.templates_dir / name
        return template_path if template_path.exists() else None
    
    def get_project_checklist(self, project_name: str, checklist_type: str) -> Optional[Path]:
        """Get project-specific checklist"""
        project_dir = self.projects_dir / project_name.lower()
        checklist_path = project_dir / f"{checklist_type}.xlsx"
        return checklist_path if checklist_path.exists() else None
    
    def save_project_checklist(
        self,
        project_name: str,
        checklist_type: str,
        file_content: bytes
    ) -> Path:
        """Save project-specific checklist"""
        project_dir = self.projects_dir / project_name.lower()
        project_dir.mkdir(parents=True, exist_ok=True)
        
        checklist_path = project_dir / f"{checklist_type}.xlsx"
        
        with open(checklist_path, 'wb') as f:
            f.write(file_content)
        
        return checklist_path


# Global instance
_template_manager: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """Get or create template manager instance"""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager