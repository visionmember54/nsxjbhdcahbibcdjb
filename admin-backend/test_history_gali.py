from datetime import date
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, sessionmaker, Mapped, mapped_column

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)

class MarketCategory(Base):
    __tablename__ = 'market_categories'
    id = Column(Integer, primary_key=True)
    slug = Column(String)

class Market(Base):
    __tablename__ = 'markets'
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('market_categories.id'))

class SimulationEntry(Base):
    __tablename__ = 'simulation_entries'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    market_id = Column(Integer, ForeignKey('markets.id'))
    created_at = Column(DateTime)
    status = Column(String)

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

db.add(User(id=1))
db.add(MarketCategory(id=1, slug="GALI_DISAWAR"))
db.add(Market(id=1, category_id=1))
from datetime import datetime
db.add(SimulationEntry(id=1, user_id=1, market_id=1, created_at=datetime(2026, 9, 21, 10, 0), status="Pending"))
db.commit()

# The query in app_api.py
query = db.query(SimulationEntry).filter(SimulationEntry.user_id == 1)
on_date = date(2026, 9, 21)
query = query.filter(func.date(SimulationEntry.created_at) == on_date)
query = query.join(Market, Market.id == SimulationEntry.market_id).join(MarketCategory, MarketCategory.id == Market.category_id).filter(MarketCategory.slug == "GALI_DISAWAR")

entries = query.all()
print("Entries count:", len(entries))

