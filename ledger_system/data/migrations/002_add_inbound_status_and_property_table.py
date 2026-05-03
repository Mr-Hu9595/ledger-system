"""Migration: 添加 inbound_status, planned_inbound_date 字段和 ledger_property 表"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ledger_system.data.database import get_session
from sqlalchemy import text


def migrate():
    with get_session() as session:
        # 1. 添加 Ledger 表新字段
        session.execute(text("""
            ALTER TABLE ledger
            ADD COLUMN IF NOT EXISTS inbound_status VARCHAR(20) DEFAULT '待入库',
            ADD COLUMN IF NOT EXISTS planned_inbound_date DATE;
        """))

        # 2. 创建 ledger_property 表
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS ledger_property (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ledger_id UUID NOT NULL REFERENCES ledger(id),
                property_key VARCHAR(50) NOT NULL,
                property_value VARCHAR(500) DEFAULT '',
                property_category VARCHAR(20) DEFAULT ''
            );
        """))

        # 3. 创建索引
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ledger_property_ledger_id ON ledger_property(ledger_id);
            CREATE INDEX IF NOT EXISTS idx_ledger_property_key ON ledger_property(property_key);
        """))

        session.commit()
        print("Migration completed: ledger.inbound_status, ledger.planned_inbound_date, ledger_property table")


if __name__ == "__main__":
    migrate()