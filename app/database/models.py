from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(100), nullable=True) # Mock authentication
    role = Column(String(20), nullable=False) # 'worker', 'assessor', 'admin'
    
    worker_profile = relationship("Worker", back_populates="user", uselist=False)

class Worker(Base):
    __tablename__ = 'workers'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    full_name = Column(String(100))
    phone = Column(String(20))
    preferred_language = Column(String(20), default='English')
    
    user = relationship("User", back_populates="worker_profile")
    assessments = relationship("Assessment", back_populates="worker")

class Assessment(Base):
    __tablename__ = 'assessments'
    id = Column(Integer, primary_key=True)
    worker_id = Column(Integer, ForeignKey('workers.id'))
    assessor_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    status = Column(String(50), default='CREATED') # CREATED, QP_MAPPED, IN_PROGRESS, REVIEW, COMPLETED
    
    # Worker's initial self declaration
    trade_selected = Column(String(100))
    experience_years = Column(Integer)
    self_declaration_text = Column(Text)
    
    # Mapped QP
    qp_id = Column(String(50), nullable=True) # Reference to YAML QP ID
    qp_name = Column(String(200), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    worker = relationship("Worker", back_populates="assessments")
    assessor = relationship("User", foreign_keys=[assessor_id])
    tasks = relationship("AssessmentTask", back_populates="assessment")

class AssessmentTask(Base):
    __tablename__ = 'assessment_tasks'
    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey('assessments.id'))
    task_id = Column(String(50)) # ID from QP YAML
    name = Column(String(200))
    description = Column(Text)
    
    status = Column(String(50), default='PENDING') # PENDING, EVIDENCE_SUBMITTED, AI_REVIEWED, ASSESSOR_REVIEWED, COMPLETED
    requires_in_person = Column(Boolean, default=False)
    in_person_reason = Column(Text, nullable=True)
    
    assessment = relationship("Assessment", back_populates="tasks")
    evidence = relationship("Evidence", back_populates="task")
    ai_suggestion = relationship("AISuggestion", back_populates="task", uselist=False)
    assessor_decision = relationship("AssessorDecision", back_populates="task", uselist=False)

class Evidence(Base):
    __tablename__ = 'evidence'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('assessment_tasks.id'))
    evidence_type = Column(String(50)) # 'image', 'video', 'audio', 'document', 'text'
    file_path = Column(String(255), nullable=True)
    text_content = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    task = relationship("AssessmentTask", back_populates="evidence")

class AISuggestion(Base):
    __tablename__ = 'ai_suggestions'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('assessment_tasks.id'))
    
    suggested_score = Column(Integer, nullable=True)
    observation = Column(Text)
    confidence = Column(Float)
    requires_human = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    task = relationship("AssessmentTask", back_populates="ai_suggestion")

class AssessorDecision(Base):
    __tablename__ = 'assessor_decisions'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('assessment_tasks.id'))
    assessor_id = Column(Integer, ForeignKey('users.id'))
    
    final_score = Column(Integer) # 1-4
    override_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    task = relationship("AssessmentTask", back_populates="assessor_decision")
    assessor = relationship("User", foreign_keys=[assessor_id])

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    entity_type = Column(String(50)) # Assessment, AssessmentTask
    entity_id = Column(Integer)
    action = Column(String(50))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    previous_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SyncQueue(Base):
    __tablename__ = 'sync_queue'
    id = Column(Integer, primary_key=True)
    operation = Column(String(50)) # CREATE, UPDATE, DELETE
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    payload = Column(JSON)
    status = Column(String(50), default='PENDING') # PENDING, SYNCED, ERROR
    created_at = Column(DateTime, default=datetime.utcnow)
