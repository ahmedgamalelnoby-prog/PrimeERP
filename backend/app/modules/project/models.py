from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from app.database.base import Base


class ProjectMilestone(Base):
    __tablename__ = "project_milestones"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(180), nullable=False)
    sequence = Column(Integer, nullable=False, server_default="10")
    due_date = Column(Date)
    completed_at = Column(DateTime(timezone=True))


class ProjectTask(Base):
    __tablename__ = "project_tasks"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_task_id = Column(Integer, ForeignKey("project_tasks.id", ondelete="SET NULL"))
    milestone_id = Column(Integer, ForeignKey("project_milestones.id", ondelete="SET NULL"))
    code = Column(String(50), nullable=False)
    name = Column(String(240), nullable=False)
    description = Column(Text)
    status = Column(String(30), nullable=False, server_default="todo")
    priority = Column(String(20), nullable=False, server_default="normal")
    assignee_ref = Column(String(120))
    customer_ref = Column(String(120))
    planned_hours = Column(Numeric(12, 2), nullable=False, server_default="0")
    deadline = Column(Date)
    recurrence_rule = Column(String(160))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))


class ProjectTaskDependency(Base):
    __tablename__ = "project_task_dependencies"
    predecessor_task_id = Column(Integer, ForeignKey("project_tasks.id", ondelete="CASCADE"), primary_key=True)
    successor_task_id = Column(Integer, ForeignKey("project_tasks.id", ondelete="CASCADE"), primary_key=True)
