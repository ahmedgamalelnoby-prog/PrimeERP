from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from app.database.base import Base


class HelpdeskTeam(Base):
    __tablename__ = "helpdesk_teams"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(160), nullable=False)
    description = Column(Text)
    active = Column(Boolean, nullable=False, server_default="true")


class HelpdeskStage(Base):
    __tablename__ = "helpdesk_stages"
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("helpdesk_teams.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    sequence = Column(Integer, nullable=False, server_default="10")
    is_closed = Column(Boolean, nullable=False, server_default="false")
    folded = Column(Boolean, nullable=False, server_default="false")


class HelpdeskTicket(Base):
    __tablename__ = "helpdesk_tickets"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("helpdesk_teams.id", ondelete="RESTRICT"), nullable=False, index=True)
    stage_id = Column(Integer, ForeignKey("helpdesk_stages.id", ondelete="RESTRICT"), nullable=False, index=True)
    ticket_no = Column(String(50), nullable=False)
    subject = Column(String(240), nullable=False)
    description = Column(Text)
    priority = Column(String(20), nullable=False, server_default="normal")
    status = Column(String(20), nullable=False, server_default="open")
    customer_ref = Column(String(120))
    assignee_ref = Column(String(120))
    sla_due_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")


class HelpdeskFollower(Base):
    __tablename__ = "helpdesk_followers"
    ticket_id = Column(Integer, ForeignKey("helpdesk_tickets.id", ondelete="CASCADE"), primary_key=True)
    follower_ref = Column(String(120), primary_key=True)


class HelpdeskTeamMember(Base):
    __tablename__ = "helpdesk_team_members"
    team_id = Column(Integer, ForeignKey("helpdesk_teams.id", ondelete="CASCADE"), primary_key=True)
    member_ref = Column(String(120), primary_key=True)
    active = Column(Boolean, nullable=False, server_default="true")
