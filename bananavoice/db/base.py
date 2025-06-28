from sqlalchemy.orm import DeclarativeBase

from bananavoice.db.meta import meta


class Base(DeclarativeBase):
    """Base for all models."""

    metadata = meta
