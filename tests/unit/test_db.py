import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Base, User, Worker, Assessment, AssessmentTask

@pytest.fixture(scope="module")
def db_session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_user_worker_creation(db_session):
    u = User(username="test_user", role="worker")
    db_session.add(u)
    db_session.commit()
    
    w = Worker(user_id=u.id, full_name="Test Worker")
    db_session.add(w)
    db_session.commit()
    
    fetched = db_session.query(Worker).filter_by(full_name="Test Worker").first()
    assert fetched is not None
    assert fetched.user.username == "test_user"
