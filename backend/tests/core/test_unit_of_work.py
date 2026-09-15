from unittest.mock import MagicMock

import pytest

from app.core.database.unit_of_work import UnitOfWork


def test_unit_of_work_commits_and_closes_owned_session() -> None:
    session = MagicMock()
    uow = UnitOfWork(session_factory=lambda: session)

    with uow as active:
        assert active.session is session
        active.commit()

    session.commit.assert_called_once()
    session.rollback.assert_not_called()
    session.close.assert_called_once()
    assert uow.session is None


def test_unit_of_work_rolls_back_when_exception_escapes() -> None:
    session = MagicMock()
    uow = UnitOfWork(session_factory=lambda: session)

    with pytest.raises(ValueError):
        with uow:
            raise ValueError("boom")

    session.rollback.assert_called_once()
    session.commit.assert_not_called()
    session.close.assert_called_once()


def test_unit_of_work_rolls_back_uncommitted_successful_block() -> None:
    session = MagicMock()
    uow = UnitOfWork(session_factory=lambda: session)

    with uow:
        pass

    session.rollback.assert_called_once()
    session.commit.assert_not_called()
    session.close.assert_called_once()


def test_unit_of_work_does_not_close_provided_session() -> None:
    session = MagicMock()
    uow = UnitOfWork(session=session)

    with uow:
        uow.commit()

    session.commit.assert_called_once()
    session.close.assert_not_called()


def test_unit_of_work_guards_operations_outside_context() -> None:
    uow = UnitOfWork(session_factory=lambda: MagicMock())

    with pytest.raises(RuntimeError, match="session has not been started"):
        uow.commit()
