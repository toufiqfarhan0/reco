"""Database session and repository provider factory."""

from typing import Union
from reco.config import Settings, get_settings
from reco.db.memory import InMemoryDatabase
from reco.db.supabase import SupabaseDatabase

# Global in-memory database singleton for local offline runs
_in_memory_db_instance = InMemoryDatabase()


def get_db(settings: Settings | None = None) -> Union[SupabaseDatabase, InMemoryDatabase]:
    """Return configured database provider.

    Returns SupabaseDatabase if SUPABASE_URL and SUPABASE_KEY are provided.
    Otherwise, returns a local InMemoryDatabase instance for zero-dependency operation.
    """
    cfg = settings or get_settings()
    if cfg.supabase_url and cfg.supabase_key:
        return SupabaseDatabase()
    return _in_memory_db_instance
