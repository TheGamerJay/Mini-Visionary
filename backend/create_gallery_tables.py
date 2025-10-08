"""
Create gallery_posts and reactions tables for community gallery feature
"""
from models import Base, get_session, GalleryPost, Reaction
from sqlalchemy import inspect

def create_gallery_tables():
    """Create gallery_posts and reactions tables if they don't exist"""
    with get_session() as db:
        inspector = inspect(db.bind)
        existing_tables = inspector.get_table_names()

        # Create tables if they don't exist
        tables_to_create = []
        if "gallery_posts" not in existing_tables:
            tables_to_create.append(GalleryPost.__table__)
        if "reactions" not in existing_tables:
            tables_to_create.append(Reaction.__table__)

        if tables_to_create:
            Base.metadata.create_all(db.bind, tables=tables_to_create)

if __name__ == "__main__":
    create_gallery_tables()
