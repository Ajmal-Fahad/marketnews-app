from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from .db import Base, engine

class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, index=True)        # e.g., "NSE", "BSE"
    company = Column(String, index=True)       # company name
    event_type = Column(String, index=True)    # Dividend / Results / BoardMeeting / etc.
    raw_text = Column(Text)                    # original announcement text
    summary = Column(Text, nullable=True)      # short summary (generated later)
    url = Column(String, nullable=True)        # source link
    published_at = Column(DateTime(timezone=False), default=func.now())
    approved = Column(Boolean, default=False)  # whether admin approved the card
    metadata_json = Column("metadata", JSON, nullable=True)  # extra info as JSON (attribute renamed to avoid conflict)

# Create the table in the database
Base.metadata.create_all(bind=engine)