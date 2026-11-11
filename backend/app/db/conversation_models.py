"""Business-scoped conversation snapshots. WhatsApp ingestion wiring is separate."""
import uuid
from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.models import Base


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (UniqueConstraint("business_id", "customer_phone", name="uq_conversations_business_customer"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_phone: Mapped[str] = mapped_column(Text, nullable=False)
    last_message: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
