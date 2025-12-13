"""
Template Management Service
"""
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger
import json

from ..config import settings


class TemplateManager:
    """
    Service for managing response templates
    """

    def __init__(self):
        self.templates_dir = settings.TEMPLATES_DIR
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def list_templates(self) -> List[Dict]:
        """
        List all available templates

        Returns:
            List of template info
        """
        templates = []

        for template_file in self.templates_dir.glob('*.txt'):
            stat = template_file.stat()
            templates.append({
                'name': template_file.stem,
                'filename': template_file.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'path': str(template_file)
            })

        return templates

    def get_template(self, template_name: str) -> Optional[str]:
        """
        Get template content

        Args:
            template_name: Template name

        Returns:
            Template content or None
        """
        template_file = self.templates_dir / f"{template_name}.txt"

        if not template_file.exists():
            logger.warning(f"Template not found: {template_name}")
            return None

        try:
            return template_file.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Error reading template: {str(e)}")
            return None

    def create_template(self, template_name: str, content: str) -> bool:
        """
        Create new template

        Args:
            template_name: Template name
            content: Template content

        Returns:
            True if successful
        """
        template_file = self.templates_dir / f"{template_name}.txt"

        if template_file.exists():
            logger.warning(f"Template already exists: {template_name}")
            return False

        try:
            template_file.write_text(content, encoding='utf-8')
            logger.success(f"Created template: {template_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            return False

    def update_template(self, template_name: str, content: str) -> bool:
        """
        Update existing template

        Args:
            template_name: Template name
            content: New content

        Returns:
            True if successful
        """
        template_file = self.templates_dir / f"{template_name}.txt"

        if not template_file.exists():
            logger.warning(f"Template not found: {template_name}")
            return False

        try:
            # Backup old version
            backup_file = template_file.with_suffix('.txt.bak')
            template_file.rename(backup_file)

            # Write new version
            template_file.write_text(content, encoding='utf-8')

            logger.success(f"Updated template: {template_name}")
            return True
        except Exception as e:
            logger.error(f"Error updating template: {str(e)}")
            return False

    def delete_template(self, template_name: str) -> bool:
        """
        Delete template

        Args:
            template_name: Template name

        Returns:
            True if successful
        """
        template_file = self.templates_dir / f"{template_name}.txt"

        if not template_file.exists():
            return False

        try:
            template_file.unlink()
            logger.success(f"Deleted template: {template_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting template: {str(e)}")
            return False
