"""Ledger repository for data access"""
from datetime import date, time
from decimal import Decimal
from typing import List, Optional, Dict
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session
from ledger_system.data.models.ledger import Ledger
from ledger_system.data.models.inbound import Inbound
from ledger_system.data.models.outbound import Outbound
from ledger_system.data.models.material_property import MaterialProperty
from ledger_system.data.models.equipment_property import EquipmentProperty


class LedgerRepository:
    """Repository for ledger operations"""

    def __init__(self, session: Session):
        self.session = session

    def create_ledger(
        self,
        category: str,
        name: str,
        specification: str = "",
        unit: str = "",
        min_stock: Decimal = Decimal(0),
        material_code: str = None,
        purchase_date: date = None
    ) -> Ledger:
        """Create new ledger entry"""
        ledger = Ledger(
            category=category,
            name=name,
            specification=specification,
            unit=unit,
            current_stock=Decimal(0),
            min_stock=min_stock,
            material_code=material_code,
            purchase_date=purchase_date
        )
        self.session.add(ledger)
        self.session.flush()
        return ledger

    def get_ledger_by_id(self, ledger_id: UUID) -> Optional[Ledger]:
        """Get ledger by ID"""
        return self.session.query(Ledger).filter(Ledger.id == ledger_id).first()

    def get_ledger_by_name(self, name: str) -> Optional[Ledger]:
        """Get ledger by name (case-insensitive)"""
        return self.session.query(Ledger).filter(
            Ledger.name.ilike(f"%{name}%")
        ).first()

    def get_all_ledgers(self) -> List[Ledger]:
        """Get all ledgers"""
        return self.session.query(Ledger).order_by(Ledger.name).all()

    def get_ledgers_by_category(self, category: str) -> List[Ledger]:
        """Get ledgers by category"""
        return self.session.query(Ledger).filter(
            Ledger.category == category
        ).order_by(Ledger.name).all()

    def update_stock(self, ledger_id: UUID, quantity_change: Decimal) -> bool:
        """Update ledger stock (positive for add, negative for subtract)"""
        ledger = self.get_ledger_by_id(ledger_id)
        if not ledger:
            return False
        ledger.current_stock = ledger.current_stock + quantity_change
        self.session.flush()
        return True

    def _get_next_inbound_sequence(self, ledger_id: UUID) -> int:
        """Get next inbound sequence number for ledger (requires ledger lock held)"""
        # Lock ledger row to prevent race conditions on sequence generation
        self.session.query(Ledger).filter(
            Ledger.id == ledger_id
        ).with_for_update().first()
        max_seq = self.session.query(func.max(Inbound.inbound_sequence)).filter(
            Inbound.ledger_id == ledger_id
        ).scalar()
        return (max_seq or 0) + 1

    def _get_cumulative_in(self, ledger_id: UUID) -> Decimal:
        """Get current cumulative inbound for ledger"""
        total = self.session.query(func.sum(Inbound.quantity)).filter(
            Inbound.ledger_id == ledger_id
        ).scalar()
        return total or Decimal(0)

    def _get_next_outbound_sequence(self, ledger_id: UUID) -> int:
        """Get next outbound sequence number for ledger (requires ledger lock held)"""
        # Lock ledger row to prevent race conditions on sequence generation
        self.session.query(Ledger).filter(
            Ledger.id == ledger_id
        ).with_for_update().first()
        max_seq = self.session.query(func.max(Outbound.outbound_sequence)).filter(
            Outbound.ledger_id == ledger_id
        ).scalar()
        return (max_seq or 0) + 1

    def _get_cumulative_out(self, ledger_id: UUID) -> Decimal:
        """Get current cumulative outbound for ledger"""
        total = self.session.query(func.sum(Outbound.quantity)).filter(
            Outbound.ledger_id == ledger_id
        ).scalar()
        return total or Decimal(0)

    def add_inbound(self, ledger_id: UUID, quantity: Decimal, supplier: str = "",
                    inbound_date: date = None, inbound_time: time = None,
                    inbound_operator: str = "", document_source: str = "",
                    original_document_path: str = "",
                    notes: str = "") -> Inbound:
        """Add inbound record and update stock with sequence and cumulative"""
        if inbound_date is None:
            inbound_date = date.today()
        if inbound_time is None:
            inbound_time = time(8, 0)

        # Calculate sequence and cumulative BEFORE adding
        inbound_sequence = self._get_next_inbound_sequence(ledger_id)
        cumulative_in = self._get_cumulative_in(ledger_id) + quantity

        inbound = Inbound(
            ledger_id=ledger_id,
            quantity=quantity,
            inbound_sequence=inbound_sequence,
            cumulative_in=cumulative_in,
            supplier=supplier,
            inbound_date=inbound_date,
            inbound_time=inbound_time,
            inbound_operator=inbound_operator,
            document_source=document_source,
            original_document_path=original_document_path,
            notes=notes
        )
        self.session.add(inbound)

        # Update stock
        self.update_stock(ledger_id, quantity)

        return inbound

    def add_outbound(self, ledger_id: UUID, quantity: Decimal, usage: str = "",
                     outbound_date: date = None, outbound_time: time = None,
                     receiver: str = "", outbound_operator: str = "",
                     original_document_path: str = "",
                     notes: str = "") -> Optional[Outbound]:
        """Add outbound record and update stock with sequence and cumulative"""
        if outbound_date is None:
            outbound_date = date.today()
        if outbound_time is None:
            outbound_time = time(8, 0)

        ledger = self.get_ledger_by_id(ledger_id)
        if not ledger or ledger.current_stock < quantity:
            return None

        # Calculate sequence and cumulative BEFORE adding
        outbound_sequence = self._get_next_outbound_sequence(ledger_id)
        cumulative_out = self._get_cumulative_out(ledger_id) + quantity

        outbound = Outbound(
            ledger_id=ledger_id,
            quantity=quantity,
            outbound_sequence=outbound_sequence,
            cumulative_out=cumulative_out,
            usage=usage,
            outbound_date=outbound_date,
            outbound_time=outbound_time,
            receiver=receiver,
            outbound_operator=outbound_operator,
            original_document_path=original_document_path,
            notes=notes
        )
        self.session.add(outbound)

        # Update stock
        self.update_stock(ledger_id, -quantity)

        return outbound

    def get_all_inbounds(self, days: int = 99999) -> List[Inbound]:
        """Get all inbound records"""
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        return self.session.query(Inbound).filter(
            Inbound.inbound_date >= start_date
        ).order_by(Inbound.inbound_date.desc(), Inbound.inbound_time.desc()).all()

    def get_all_outbounds(self, days: int = 99999) -> List[Outbound]:
        """Get all outbound records"""
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        return self.session.query(Outbound).filter(
            Outbound.outbound_date >= start_date
        ).order_by(Outbound.outbound_date.desc(), Outbound.outbound_time.desc()).all()

    def get_inbound_history(self, ledger_id: UUID, days: int = 30) -> List[Inbound]:
        """Get inbound history for ledger"""
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        return self.session.query(Inbound).filter(
            Inbound.ledger_id == ledger_id,
            Inbound.inbound_date >= start_date
        ).order_by(Inbound.inbound_date.desc(), Inbound.inbound_time.desc()).all()

    def get_outbound_history(self, ledger_id: UUID, days: int = 30) -> List[Outbound]:
        """Get outbound history for ledger"""
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        return self.session.query(Outbound).filter(
            Outbound.ledger_id == ledger_id,
            Outbound.outbound_date >= start_date
        ).order_by(Outbound.outbound_date.desc(), Outbound.outbound_time.desc()).all()

    def get_low_stock_items(self) -> List[Ledger]:
        """Get items at or below min_stock"""
        return self.session.query(Ledger).filter(
            Ledger.current_stock <= Ledger.min_stock
        ).all()

    # ========== Property Management ==========

    def add_material_property(self, ledger_id: UUID, property_key: str,
                               property_value: str, property_type: str = "") -> MaterialProperty:
        """Add a property to a material ledger entry"""
        prop = MaterialProperty(
            ledger_id=ledger_id,
            property_key=property_key,
            property_value=property_value,
            property_type=property_type
        )
        self.session.add(prop)
        self.session.flush()
        return prop

    def add_equipment_property(self, ledger_id: UUID, property_key: str,
                               property_value: str, property_type: str = "") -> EquipmentProperty:
        """Add a property to an equipment ledger entry"""
        prop = EquipmentProperty(
            ledger_id=ledger_id,
            property_key=property_key,
            property_value=property_value,
            property_type=property_type
        )
        self.session.add(prop)
        self.session.flush()
        return prop

    def get_material_properties(self, ledger_id: UUID) -> List[MaterialProperty]:
        """Get all properties for a material ledger entry"""
        return self.session.query(MaterialProperty).filter(
            MaterialProperty.ledger_id == ledger_id
        ).all()

    def get_equipment_properties(self, ledger_id: UUID) -> List[EquipmentProperty]:
        """Get all properties for an equipment ledger entry"""
        return self.session.query(EquipmentProperty).filter(
            EquipmentProperty.ledger_id == ledger_id
        ).all()

    def get_ledger_with_properties(self, ledger_id: UUID) -> Optional[Dict]:
        """Get ledger entry with all its properties"""
        ledger = self.get_ledger_by_id(ledger_id)
        if not ledger:
            return None

        result = {
            "ledger": ledger,
            "properties": {}
        }

        if ledger.category == "material":
            props = self.get_material_properties(ledger_id)
            result["properties"] = {p.property_key: p.property_value for p in props}
        elif ledger.category == "equipment":
            props = self.get_equipment_properties(ledger_id)
            result["properties"] = {p.property_key: p.property_value for p in props}

        return result

    def verify_stock(self, ledger_id: UUID) -> Dict[str, Decimal]:
        """Verify current_stock by calculating from records"""
        ledger = self.get_ledger_by_id(ledger_id)
        if not ledger:
            return {"error": "Ledger not found"}

        cumulative_in = self._get_cumulative_in(ledger_id)
        cumulative_out = self._get_cumulative_out(ledger_id)
        calculated_stock = cumulative_in - cumulative_out

        return {
            "ledger_id": str(ledger_id),
            "current_stock_recorded": ledger.current_stock,
            "current_stock_calculated": calculated_stock,
            "cumulative_in": cumulative_in,
            "cumulative_out": cumulative_out,
            "is_match": ledger.current_stock == calculated_stock
        }
