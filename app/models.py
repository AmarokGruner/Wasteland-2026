from sqlalchemy import Column, Integer, Float, String, ForeignKey, JSON, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
import json

Base = declarative_base()

class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    time_credit = Column(Float, default=240.0)
    tech_level = Column(Integer, default=0)
    provinces = relationship("Province", back_populates="player")

class Province(Base):
    __tablename__ = 'provinzen'
    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    world_x = Column(Integer, nullable=False)
    world_y = Column(Integer, nullable=False)
    name = Column(String, default='')
    terrain = Column(String, default='Grasland')
    population = Column(Integer, default=10)
    mips = Column(Integer, default=0)
    moral = Column(Integer, default=50)
    gesundheit = Column(Integer, default=50)
    marktpunkte = Column(Integer, default=0)
    strassennetz = Column(Integer, default=0)
    einheiten_count = Column(Integer, default=0)
    
    # New columns for building system
    kulturpunkte = Column(Integer, default=0)
    size_level = Column(Integer, default=1) # 1-7 (Camp to Metropole)
    fields_total = Column(Integer, default=40)
    fields_city = Column(Integer, default=5)
    arbeitspunkte_current = Column(Integer, default=100)
    arbeitspunkte_max = Column(Integer, default=100)
    terrain_yield_malus = Column(Float, default=0.0)
    
    player = relationship("Player", back_populates="provinces")
    buildings = relationship("BuildingInstance", back_populates="province")
    roads = relationship("RoadInstance", back_populates="province")
    lager = relationship("ProvinceLager", back_populates="province")
    
    # Add new relationship for animals
    animals = relationship("ProvinceAnimal", back_populates="province")

class BuildingType(Base):
    __tablename__ = 'gebaeude_typen'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    produktion = Column(String, default='[]') # JSON string
    rohstoffverbrauch = Column(String, default='[]') # JSON string
    arbeiter = Column(Integer, default=0)
    wohnraum = Column(Integer, default=0)
    lagerkapazitaet = Column(Integer, default=0)
    terrain_effektivitaet = Column(String, default='{}') # JSON string
    
    # New columns for building system
    kategorie = Column(String)
    bautyp = Column(String) # Land/Stadt/Stadtausbau/Weg/Wegkreuzung
    baubar = Column(Integer, default=1)
    ausbaubar = Column(Integer, default=0)
    unique_gebaeude = Column(Integer, default=0)
    nur_kueste = Column(Integer, default=0)
    ist_feld = Column(Integer, default=0)
    tech_level = Column(Integer, default=0)
    baukosten_mips = Column(Integer, default=0)
    ausbaukosten_mips = Column(Integer, default=0)
    rohstoffbedarf_bau = Column(String, default='[]') # JSON string
    rohstoffgrundbedarf_ausbau = Column(String, default='[]') # JSON string
    spezial_eigenschaften = Column(String, default='{}') # JSON string

class BuildingInstance(Base):
    __tablename__ = 'provinz_gebaeude'
    id = Column(Integer, primary_key=True, autoincrement=True)
    provinz_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    gebaeude_typ_id = Column(Integer, ForeignKey('gebaeude_typen.id'), nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    level = Column(Integer, default=1)
    built_at = Column(DateTime, server_default=func.now())
    
    # Compatibility access
    @property
    def stufe(self):
        return self.level
    
    province = relationship("Province", back_populates="buildings")
    type = relationship("BuildingType")

class RoadInstance(Base):
    __tablename__ = 'provinz_strassen'
    id = Column(Integer, primary_key=True, autoincrement=True)
    provinz_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    gebaeude_typ_id = Column(Integer, ForeignKey('gebaeude_typen.id'), nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    
    province = relationship("Province", back_populates="roads")
    type = relationship("BuildingType")

class Resource(Base):
    __tablename__ = 'ressourcen'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    typ = Column(String, nullable=False) # Getränk, Nahrung, etc.
    wert = Column(Integer, default=0)

class ProvinceLager(Base):
    __tablename__ = 'provinz_lager'
    id = Column(Integer, primary_key=True, autoincrement=True)
    provinz_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    ressource_id = Column(Integer, ForeignKey('ressourcen.id'), nullable=False)
    menge = Column(Integer, default=0)
    
    province = relationship("Province", back_populates="lager")
    resource = relationship("Resource")

class SystemLock(Base):
    __tablename__ = 'system_locks'
    task_name = Column(String, primary_key=True)
    is_running = Column(Integer, default=0)
    last_run = Column(DateTime)
    error_count = Column(Integer, default=0)

class TickLog(Base):
    __tablename__ = 'tick_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, server_default=func.now())
    duration_ms = Column(Integer)
    status = Column(Integer) # 1=Success, 0=Failed
    provinces_processed = Column(Integer)
    details = Column(String)

class QuickBuildSession(Base):
    __tablename__ = 'quick_build_sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False, unique=True)
    template_id = Column(Integer, ForeignKey('gebaeude_typen.id'), nullable=True) # Null for demolish
    mode = Column(String, nullable=False) # 'build' or 'demolish'
    last_activity = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())

class TerrainConfig(Base):
    __tablename__ = 'terrain_configs'
    terrain_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    rain_probability = Column(Float, default=0.3)
    rain_amount = Column(Integer, default=10)
    average_moisture = Column(Float, default=50.0)
    next_terrain_id = Column(Integer, ForeignKey('terrain_configs.terrain_id'), nullable=True)

class ProvinceClimate(Base):
    __tablename__ = 'provinz_klima'
    id = Column(Integer, primary_key=True, autoincrement=True)
    province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False, unique=True)
    bodenfeuchtigkeit = Column(Float, default=50.0)
    grundwasserspiegel = Column(Float, default=50.0)
    last_rained = Column(DateTime, nullable=True)
    is_raining_now = Column(Integer, default=0)
    
    province = relationship("Province")

class ProvinceDeposit(Base):
    __tablename__ = 'provinz_reserven'
    id = Column(Integer, primary_key=True, autoincrement=True)
    province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    vorkommen_id = Column(Integer, nullable=False) # References Vorkommen.id
    deposit_found = Column(Integer, default=0)
    deposit_searched = Column(Integer, default=0)
    quality = Column(Integer, default=2) # 1=50%, 2=100%, 3=150%
    
    province = relationship("Province")
    vorkommen = relationship("Vorkommen")

class Vorkommen(Base):
    __tablename__ = 'vorkommen'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    typ = Column(String) # geologisch/Oberfläche/unt.Seen
    tech = Column(Integer, default=0)
    suchkosten = Column(Integer, default=100)
    findwahrscheinlichkeit = Column(String, default='{}') # JSON {terrain: probability}
    
    def get_probability(self, terrain_name: str) -> float:
        import json
        data = json.loads(self.findwahrscheinlichkeit)
        return data.get(terrain_name, 0)

class ProvinceSettings(Base):
    __tablename__ = 'provinz_settings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False, unique=True)
    worker_mode = Column(String, default="idle") # idle/sammeln/jagen
    feiertag_active = Column(Integer, default=0)
    feiertag_expires_at = Column(DateTime, nullable=True)
    
    province = relationship("Province")

class SammelLoot(Base):
    __tablename__ = 'sammel_loot'
    id = Column(Integer, primary_key=True)
    terrain_id = Column(String) # terrain name
    resource_id = Column(Integer, ForeignKey('ressourcen.id'), nullable=False)
    base_amount = Column(Float, default=0.0)
    random_min = Column(Float, default=0.0)
    random_max = Column(Float, default=1.0)
    weight = Column(Integer, default=100) # for random selection
    loot_category = Column(String) # material/food_farmable/food_forage/genuss
    
    resource = relationship("Resource")

class JagdLoot(Base):
    __tablename__ = 'jagd_loot'
    id = Column(Integer, primary_key=True)
    terrain_id = Column(String) # terrain name
    resource_id = Column(Integer, ForeignKey('ressourcen.id'), nullable=False)
    base_amount = Column(Float, default=0.0)
    random_min = Column(Float, default=0.0)
    random_max = Column(Float, default=1.0)
    is_animal = Column(Integer, default=0) # 1 for live animal capture
    capture_chance = Column(Float, default=0.0)
    
    resource = relationship("Resource")

class ProvinceAnimal(Base):
    __tablename__ = 'provinz_tiere'
    id = Column(Integer, primary_key=True, autoincrement=True)
    province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    animal_resource_id = Column(Integer, ForeignKey('ressourcen.id'), nullable=False)
    count = Column(Integer, default=0)
    is_wild = Column(Integer, default=1) # 1 = wild roaming, 0 = in breeding building
    building_instance_id = Column(Integer, ForeignKey('provinz_gebaeude.id'), nullable=True)
    
    province = relationship("Province")
    animal_resource = relationship("Resource")

class AnimalTemplate(Base):
    __tablename__ = 'tier_vorlagen'
    id = Column(Integer, primary_key=True)
    resource_id = Column(Integer, ForeignKey('ressourcen.id'), nullable=False, unique=True)
    feed_resource_id = Column(Integer, ForeignKey('ressourcen.id'), nullable=False)
    feed_amount_per_24h = Column(Float, default=1.0)
    breed_output_resource_id = Column(Integer, ForeignKey('ressourcen.id'), nullable=True) # e.g. Eier from Hühner
    breed_rate = Column(Float, default=0.1) # 10% growth per day
    is_pflanzenfresser = Column(Integer, default=1)
    
    resource = relationship("Resource", foreign_keys=[resource_id])
    feed_resource = relationship("Resource", foreign_keys=[feed_resource_id])

# Engine setup
engine = create_engine('sqlite:///verbrannte_zone.db')
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
