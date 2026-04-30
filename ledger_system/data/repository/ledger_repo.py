"""Ledger repository for data access"""
from datetime import date, time
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from ledger_system.data.models.ledger import Ledger
from ledger_system.data.models.inbound import Inbound
from ledger_system.data.models.outbound import Outbound


class LedgerRepository:
    """Repository for ledger operations"""

    def __init__(self, session: Session):
        self.session = session

    def create_ledger(self, category: str, name: str, specification: str = "",
                      unit: str = "", min_stock: Decimal = Decimal(0)) -> Ledger:
        """Create new ledger entry"""
        ledger = Ledger(
            category=category,
            name=name,
            specification=specification,
            unit=unit,
            current_stock=Decimal(0),
            min_stock=min_stock
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

    def add_inbound(self, ledger_id: UUID, quantity: Decimal, supplier: str = "",
                    inbound_date: date = None, inbound_time: time = None,
                    inbound_operator: str = "", document_source: str = "",
                    notes: str = "") -> Inbound:
        """Add inbound record and update stock"""
        if inbound_date is None:
            inbound_date = date.today()
        if inbound_time is None:
            inbound_time = time(8, 0)  # 默认早上8点

        inbound = Inbound(
            ledger_id=ledger_id,
            quantity=quantity,
            supplier=supplier,
            inbound_date=inbound_date,
            inbound_time=inbound_time,
            inbound_operator=inbound_operator,
            document_source=document_source,
            notes=notes
        )
        self.session.add(inbound)

        # Update stock
        self.update_stock(ledger_id, quantity)

        return inbound

    def add_outbound(self, ledger_id: UUID, quantity: Decimal, usage: str = "",
                     outbound_date: date = None, outbound_time: time = None,
                     receiver: str = "", outbound_operator: str = "",
                     notes: str = "") -> Optional[Outbound]:
        """Add outbound record and update stock (only if sufficient stock)"""
        if outbound_date is None:
            outbound_date = date.today()
        if outbound_time is None:
            outbound_time = time(8, 0)  # 默认早上8点

        ledger = self.get_ledger_by_id(ledger_id)
        if not ledger or ledger.current_stock < quantity:
            return None

        outbound = Outbound(
            ledger_id=ledger_id,
            quantity=quantity,
            usage=usage,
            outbound_date=outbound_date,
            outbound_time=outbound_time,
            receiver=receiver,
            outbound_operator=outbound_operator,
            notes=notes
        )
        self.session.add(outbound)

        # Update stock
        self.update_stock(ledger_id, -quantity)

        return outbound

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