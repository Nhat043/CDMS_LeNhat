import pytest
from sqlalchemy.orm import Session

from app.core.db import cdms_engine


@pytest.fixture
def db():
    """A session whose work is always rolled back.

    process() commits, so the session joins the outer transaction through
    a savepoint: its commits release the savepoint, and the rollback at
    the end still undoes everything.
    """
    connection = cdms_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
