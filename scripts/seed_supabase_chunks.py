"""Backward-compatible entrypoint; use sync_supabase_chunks for new workflows."""

from scripts.sync_supabase_chunks import main


if __name__ == "__main__":
    main()
