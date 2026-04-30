"""Migration script to add sequence and property fields"""
import sys
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ledger_system.data.database import get_session, init_database
from ledger_system.data.repository import LedgerRepository
from ledger_system.data.models import Ledger, Inbound, Outbound


def migrate_inbound_sequence():
    """Migrate existing inbound records with sequence numbers"""
    print("迁移入库记录序号...")

    with get_session() as session:
        repo = LedgerRepository(session)

        # Get all inbounds grouped by ledger
        inbounds = session.query(Inbound).order_by(
            Inbound.ledger_id, Inbound.inbound_date, Inbound.inbound_time
        ).all()

        current_ledger_id = None
        sequence = 0
        cumulative = Decimal(0)

        for ib in inbounds:
            if ib.ledger_id != current_ledger_id:
                current_ledger_id = ib.ledger_id
                sequence = 0
                cumulative = Decimal(0)

            sequence += 1
            cumulative += ib.quantity

            ib.inbound_sequence = sequence
            ib.cumulative_in = cumulative

        session.commit()
        print(f"完成: 迁移了 {len(inbounds)} 条入库记录")


def migrate_outbound_sequence():
    """Migrate existing outbound records with sequence numbers"""
    print("迁移出库记录序号...")

    with get_session() as session:
        repo = LedgerRepository(session)

        # Get all outbounds grouped by ledger
        outbounds = session.query(Outbound).order_by(
            Outbound.ledger_id, Outbound.outbound_date, Outbound.outbound_time
        ).all()

        current_ledger_id = None
        sequence = 0
        cumulative = Decimal(0)

        for ob in outbounds:
            if ob.ledger_id != current_ledger_id:
                current_ledger_id = ob.ledger_id
                sequence = 0
                cumulative = Decimal(0)

            sequence += 1
            cumulative += ob.quantity

            ob.outbound_sequence = sequence
            ob.cumulative_out = cumulative

        session.commit()
        print(f"完成: 迁移了 {len(outbounds)} 条出库记录")


def migrate_material_properties():
    """Migrate material-specific properties from ledger to material_property table"""
    print("迁移物料属性...")

    from ledger_system.data.models import MaterialProperty

    # Property keys that belong to materials
    material_keys = ["medium", "material_type", "execution_standard",
                     "surface_treatment", "origin", "brand"]

    with get_session() as session:
        ledgers = session.query(Ledger).filter(Ledger.category == "material").all()

        count = 0
        for ledger in ledgers:
            for key in material_keys:
                value = getattr(ledger, key, None) or ""
                if value and value != "" and value != "0":
                    prop = MaterialProperty(
                        ledger_id=ledger.id,
                        property_key=key,
                        property_value=str(value),
                        property_type="material"
                    )
                    session.add(prop)
                    count += 1

        session.commit()
        print(f"完成: 迁移了 {count} 条物料属性")


def migrate_equipment_properties():
    """Migrate equipment-specific properties from ledger to equipment_property table"""
    print("迁移设备属性...")

    from ledger_system.data.models import EquipmentProperty

    # Property keys that belong to equipment
    equipment_keys = ["drive_type", "nominal_diameter", "valve_position",
                      "design_pressure", "design_temperature", "manufacturer"]

    with get_session() as session:
        ledgers = session.query(Ledger).filter(Ledger.category == "equipment").all()

        count = 0
        for ledger in ledgers:
            for key in equipment_keys:
                value = getattr(ledger, key, None) or ""
                if value and value != "" and value != "0":
                    prop = EquipmentProperty(
                        ledger_id=ledger.id,
                        property_key=key,
                        property_value=str(value),
                        property_type="mechanical"
                    )
                    session.add(prop)
                    count += 1

        session.commit()
        print(f"完成: 迁移了 {count} 条设备属性")


def remove_old_columns():
    """Remove old mixed columns from ledger table (requires DB migration)"""
    print("注意: 需要手动执行数据库迁移移除以下旧字段:")
    print("  - ledger.meduem, ledger.design_pressure, ledger.material_type")
    print("  - ledger.design_temperature, ledger.manufacturer, ledger.drive_type")
    print("  - ledger.nominal_diameter, ledger.valve_position")
    print("  请执行: ALTER TABLE ledger DROP COLUMN IF EXISTS <column_name>;")


if __name__ == "__main__":
    print("开始数据迁移...")
    migrate_inbound_sequence()
    migrate_outbound_sequence()
    migrate_material_properties()
    migrate_equipment_properties()
    remove_old_columns()
    print("迁移完成!")
