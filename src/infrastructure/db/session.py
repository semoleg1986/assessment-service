from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy.orm.scoping import scoped_session

SessionLike = Session | scoped_session[Session]
