"""
Backup and Restore Service
"""
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from loguru import logger

from ..config import settings


class BackupService:
    """
    Service for backing up and restoring data
    """

    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, include_files: bool = True) -> Dict:
        """
        Create full backup

        Args:
            include_files: Include knowledge base files

        Returns:
            Backup info
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)

        try:
            # Backup database
            db_backup = self._backup_database(backup_path)

            # Backup knowledge base files
            if include_files:
                files_backup = self._backup_files(backup_path)
            else:
                files_backup = {'status': 'skipped'}

            backup_info = {
                'backup_name': backup_name,
                'timestamp': timestamp,
                'path': str(backup_path),
                'database': db_backup,
                'files': files_backup,
                'size_mb': self._get_dir_size(backup_path) / (1024 * 1024)
            }

            # Save backup metadata
            import json
            metadata_file = backup_path / 'metadata.json'
            metadata_file.write_text(json.dumps(backup_info, indent=2))

            logger.success(f"Backup created: {backup_name}")
            return backup_info

        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            return {'success': False, 'error': str(e)}

    def list_backups(self) -> List[Dict]:
        """
        List all backups

        Returns:
            List of backup info
        """
        backups = []

        for backup_dir in self.backup_dir.glob('backup_*'):
            if backup_dir.is_dir():
                metadata_file = backup_dir / 'metadata.json'

                if metadata_file.exists():
                    import json
                    try:
                        metadata = json.loads(metadata_file.read_text())
                        backups.append(metadata)
                    except:
                        backups.append({
                            'backup_name': backup_dir.name,
                            'path': str(backup_dir),
                            'size_mb': self._get_dir_size(backup_dir) / (1024 * 1024)
                        })

        return sorted(backups, key=lambda x: x.get('timestamp', ''), reverse=True)

    def restore_backup(self, backup_name: str) -> Dict:
        """
        Restore from backup

        Args:
            backup_name: Backup name

        Returns:
            Restore result
        """
        backup_path = self.backup_dir / backup_name

        if not backup_path.exists():
            return {'success': False, 'error': 'Backup not found'}

        try:
            logger.info(f"Restoring from backup: {backup_name}")

            # Restore database
            db_result = self._restore_database(backup_path)

            # Restore files
            files_result = self._restore_files(backup_path)

            logger.success("Backup restored successfully")

            return {
                'success': True,
                'backup_name': backup_name,
                'database': db_result,
                'files': files_result
            }

        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            return {'success': False, 'error': str(e)}

    def delete_backup(self, backup_name: str) -> bool:
        """
        Delete a backup

        Args:
            backup_name: Backup name

        Returns:
            True if successful
        """
        backup_path = self.backup_dir / backup_name

        if not backup_path.exists():
            return False

        try:
            shutil.rmtree(backup_path)
            logger.success(f"Deleted backup: {backup_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting backup: {str(e)}")
            return False

    def _backup_database(self, backup_path: Path) -> Dict:
        """Backup SQLite database"""
        db_file = Path("coupang_cs.db")

        if db_file.exists():
            backup_db = backup_path / "database.db"
            shutil.copy2(db_file, backup_db)
            return {'status': 'success', 'size': backup_db.stat().st_size}

        return {'status': 'no_database'}

    def _backup_files(self, backup_path: Path) -> Dict:
        """Backup knowledge base files"""
        kb_backup = backup_path / "knowledge_base"

        if settings.KNOWLEDGE_BASE_DIR.exists():
            shutil.copytree(settings.KNOWLEDGE_BASE_DIR, kb_backup)
            return {'status': 'success', 'files': len(list(kb_backup.rglob('*')))}

        return {'status': 'no_files'}

    def _restore_database(self, backup_path: Path) -> Dict:
        """Restore database from backup"""
        backup_db = backup_path / "database.db"

        if backup_db.exists():
            db_file = Path("coupang_cs.db")

            # Backup current database
            if db_file.exists():
                shutil.copy2(db_file, f"{db_file}.pre_restore")

            shutil.copy2(backup_db, db_file)
            return {'status': 'restored'}

        return {'status': 'no_database_in_backup'}

    def _restore_files(self, backup_path: Path) -> Dict:
        """Restore knowledge base files from backup"""
        kb_backup = backup_path / "knowledge_base"

        if kb_backup.exists():
            if settings.KNOWLEDGE_BASE_DIR.exists():
                shutil.rmtree(settings.KNOWLEDGE_BASE_DIR)

            shutil.copytree(kb_backup, settings.KNOWLEDGE_BASE_DIR)
            return {'status': 'restored'}

        return {'status': 'no_files_in_backup'}

    def _get_dir_size(self, path: Path) -> int:
        """Get directory size in bytes"""
        return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
