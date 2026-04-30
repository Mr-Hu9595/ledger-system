"""Sync command - synchronize database to Excel reports"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ledger_system.business.report.report_sync import ReportSync


class SyncCommand:
    """Sync database to Excel reports"""

    def execute(self, args):
        """Execute sync command"""
        sync = ReportSync()
        sync.sync_all()
        print(f"报表已同步: {sync.REPORT_FILE}")
