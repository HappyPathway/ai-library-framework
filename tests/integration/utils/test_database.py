"""Integration tests for database utilities."""
import pytest
from sqlalchemy import Column, Integer, String
from utils.database import Base, get_session, engine, init_db, drop_db

class TestModel(Base):
    """Test model for database integration tests."""
    __tablename__ = 'test_table'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    value = Column(String(100))

@pytest.fixture(scope="function")
def setup_database():
    """Set up test database."""
    drop_db()  # Clean start
    init_db()
    yield
    drop_db()  # Clean up

def test_database_operations(setup_database):
    """Test basic database operations."""
    # Create test record
    with get_session() as session:
        test_record = TestModel(name="test")
        session.add(test_record)
        session.commit()
        
        # Query record
        result = session.query(TestModel).filter_by(name="test").first()
        assert result is not None
        assert result.name == "test"
        
        # Update record
        result.name = "updated"
        session.commit()
        
        # Verify update
        updated = session.query(TestModel).filter_by(name="updated").first()
        assert updated is not None
        assert updated.id == result.id
        
        # Delete record
        session.delete(result)
        session.commit()
        
        # Verify deletion
        deleted = session.query(TestModel).filter_by(id=result.id).first()
        assert deleted is None

def test_session_rollback(setup_database):
    """Test session rollback on error."""
    with pytest.raises(Exception):
        with get_session() as session:
            test_record = TestModel(name="test")
            session.add(test_record)
            raise Exception("Test error")
    
    # Verify record was not persisted
    with get_session() as session:
        result = session.query(TestModel).filter_by(name="test").first()
        assert result is None
