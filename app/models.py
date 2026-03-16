from sqlalchemy import Column, Integer, Float, String, ForeignKey, JSON, DateTime, func, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
import json

Base = declarative_base()

class TerrainType(Base):
    __tablename__ = 'terrain_typen'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    playable = Column(Integer, default=1)
    color = Column(String)
    icon = Column(String)
    beschreibung = Column(String)
    bild_url = Column(String)
    gif_filename = Column(String)
    
    # Costs
    mips_kosten = Column(Integer, default=0)
    
    # Bonuses
    holz_yield = Column(Float, default=1.0)
    stein_yield = Column(Float, default=1.0)
    eisen_yield = Column(Float, default=1.0)
    
    def get_probability(self, terrain_name: str) -> float:
        """Helper to get probability of a resource occurring on this terrain"""
        # This logic is usually on the resource/vorkommen, but let's see
        return 0.0

class MapCell(Base):
    __tablename__ = 'world_map_cells'
    id = Column(Integer, primary_key=True, autoincrement=True)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    terrain_id = Column(Integer, ForeignKey('terrain_typen.id'), nullable=False)
    owner_id = Column(Integer, ForeignKey('players.id'), nullable=True)
    is_ruin_province = Column(Integer, default=0)
    has_ocean_border = Column(Integer, default=0)
    
    terrain = relationship("TerrainType")
    owner = relationship("Player")
    
    __table_args__ = (UniqueConstraint('x', 'y', name='_x_y_uc'),)

class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    time_credit = Column(Float, default=240.0)
    tech_level = Column(Integer, default=0)
    regierungsform_id = Column(Integer, ForeignKey('regierungsformen.id'), default=1)
    regierungsform_transition_ticks_remaining = Column(Integer, default=0)  # 0=done
    provinces = relationship("Province", back_populates="player")
    
    # State finance account
    staatskonto = Column(Float, default=0.0)
    
    # Trading
    karren_count = Column(Integer, default=2)  # Start with 2 Handelskarren
    
    regierungsform = relationship("Regierungsform")

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
    kultureinfluss_total = Column(Float, default=0.0)  # Accumulates for field annexation
    kultureinfluss_owner_id = Column(Integer, ForeignKey('players.id'), nullable=True)  # Owner of culture influence
    tech_production = Column(Integer, default=0)  # Daily tech production points
    size_level = Column(Integer, default=1) # 1-7 (Camp to Metropole)
    fields_total = Column(Integer, default=40)
    fields_city = Column(Integer, default=5)
    arbeitspunkte_current = Column(Integer, default=100)
    arbeitspunkte_max = Column(Integer, default=100)
    terrain_yield_malus = Column(Float, default=0.0)
    
    player = relationship("Player", back_populates="provinces")
    kultureinfluss_owner = relationship("Player", foreign_keys=[kultureinfluss_owner_id])
    buildings = relationship("BuildingInstance", back_populates="province")
    roads = relationship("RoadInstance", back_populates="province")
    lager = relationship("ProvinceLager", back_populates="province")
    market_stands = relationship("MarketStand", back_populates="province")
    trade_routes = relationship("TradeRoute", foreign_keys="TradeRoute.origin_province_id", back_populates="origin_province")
    kontor_prices = relationship("KontorPrice", back_populates="province")
    units = relationship("Unit", back_populates="province")
    
    # Add new relationship for animals
    animals = relationship("ProvinceAnimal", back_populates="province")
    
    # Finance accounts (4 accounts system)
    provinzkonto = Column(Float, default=0.0)
    volkskonto = Column(Float, default=0.0)
    handelskonto = Column(Float, default=0.0)
    
    # Coast & Sea access
    sea_access = Column(String, default=None)  # None, "boats", "ships"
    
    # Military
    min_soldiers = Column(Integer, default=20)
    security_bonus = Column(Integer, default=0)
    
    # Bunker
    has_bunker = Column(Integer, default=0) # 1=True, 0=False
    is_bunker_province = Column(Integer, default=0) # 1=True, 0=False (for start province)
    bunker_defense_bonus = Column(Float, default=1.3) # 30% bonus
    
    stationed_armies = relationship("Army", back_populates="province")

class Army(Base):
    __tablename__ = 'armies'
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    
    # units: List of {einheiten_typ_id, count, training, fitness}
    units_json = Column(String, default="[]") 
    
    status = Column(String, default="stationed") # stationed/marching/besieging/in_combat
    
    # Movement data
    target_province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=True)
    travel_ticks_remaining = Column(Integer, default=0)
    
    owner = relationship("Player")
    province = relationship("Province", foreign_keys=[province_id], back_populates="stationed_armies")
    target_province = relationship("Province", foreign_keys=[target_province_id])

class CombatLog(Base):
    __tablename__ = 'combat_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    attacker_army_id = Column(Integer, ForeignKey('armies.id'), nullable=False)
    defender_army_id = Column(Integer, ForeignKey('armies.id'), nullable=True) # Can be Null if only garrison? 
    # Better: province_id for defensive garrison/buildings
    province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    
    rounds_json = Column(String, default="[]") # JSON list of round details
    attacker_losses = Column(Integer, default=0)
    defender_losses = Column(Integer, default=0)
    outcome = Column(String, default="ongoing") # attacker_wins/defender_wins/ongoing
    resolved_at = Column(DateTime, nullable=True)
    
    attacker_army = relationship("Army", foreign_keys=[attacker_army_id])
    defender_army = relationship("Army", foreign_keys=[defender_army_id])
    province = relationship("Province")

class Unit(Base):
    __tablename__ = 'units'
    id = Column(Integer, primary_key=True, autoincrement=True)
    province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    count = Column(Integer, default=0)
    training = Column(Float, default=0.0) # 0-100
    fitness = Column(Float, default=100.0) # 0-100
    type = Column(String, default="soldier") # "soldier"/"settler"
    
    province = relationship("Province", back_populates="units")

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
    vorkommen_id = Column(Integer, ForeignKey('vorkommen.id'), nullable=False)
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

class TaxSettings(Base):
    __tablename__ = 'steuer_einstellungen'
    id = Column(Integer, primary_key=True, autoincrement=True)
    province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False, unique=True)
    
    tax_rate = Column(Integer, default=10)      # 0-100
    lohn_rate = Column(Float, default=1.0)       # Lohn per worker
    sold_rate = Column(Float, default=1.0)       # Military pay per unit
    rente_rate = Column(Float, default=0.5)      # Renten rate
    state_transfer_pct = Column(Integer, default=0)  # % transfer to Staatskonto
    kindergeld_rate = Column(Float, default=0.5)  # Kindergeld rate per child
    
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

class MarketStand(Base):
    __tablename__ = 'markt_staende'
    id = Column(Integer, primary_key=True, autoincrement=True)
    province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    resource_id = Column(Integer, ForeignKey('ressourcen.id'), nullable=False)
    auto_buy = Column(Integer, default=1) # 1=True, 0=False

    province = relationship("Province", back_populates="market_stands")
    resource = relationship("Resource")

class TradeRoute(Base):
    __tablename__ = 'handelsrouten'
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    origin_province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    destination_province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    cargo_json = Column(String, default="{}") # {resource_id: amount}
    settlers_count = Column(Integer, default=0)
    status = Column(String, default="traveling") # traveling/arrived/returning
    
    owner = relationship("Player")
    origin_province = relationship("Province", foreign_keys=[origin_province_id], back_populates="trade_routes")
    destination_province = relationship("Province", foreign_keys=[destination_province_id])


class SiedlerExpedition(Base):
    __tablename__ = 'siedler_expeditionen'
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    origin_province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    destination_province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    settler_count = Column(Integer, default=0)
    karren_count = Column(Integer, default=0)
    cargo_json = Column(String, default="{}")  # {resource_id: amount}
    status = Column(String, default="preparing")  # preparing/traveling/arrived/colonizing
    travel_ticks_remaining = Column(Integer, default=0)
    total_travel_ticks = Column(Integer, default=0)
    settler_tick_age = Column(Integer, default=4)  # tick_age of settlers (4-5)
    
    owner = relationship("Player")
    origin_province = relationship("Province", foreign_keys=[origin_province_id])
    destination_province = relationship("Province", foreign_keys=[destination_province_id])


class ProvinceTransfer(Base):
    __tablename__ = 'provinz_transfers'
    id = Column(Integer, primary_key=True)
    province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    from_player_id = Column(Integer, ForeignKey('players.id'), nullable=True)  # NULL for unowned
    to_player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    status = Column(String, default="pending")  # pending/accepted/rejected
    created_at = Column(DateTime, server_default=func.now())
    
    province = relationship("Province")
    from_player = relationship("Player", foreign_keys=[from_player_id])
    to_player = relationship("Player", foreign_keys=[to_player_id])

class KontorPrice(Base):
    __tablename__ = 'kontor_preise'
    id = Column(Integer, primary_key=True, autoincrement=True)
    province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    resource_id = Column(Integer, ForeignKey('ressourcen.id'), nullable=False)
    mode = Column(String, nullable=False) # "buy" (kontor buys from visitor) or "sell" (kontor sells to visitor)
    price = Column(Float, nullable=False)
    friends_only = Column(Integer, default=0)
    verbündete_only = Column(Integer, default=0)
    active = Column(Integer, default=1)

    province = relationship("Province", back_populates="kontor_prices")
    resource = relationship("Resource")

class UnitType(Base):
    __tablename__ = 'einheiten_typen'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    geschwindigkeit = Column(Float, default=1.0)
    transport_land = Column(Integer, default=1)
    einheitengroesse = Column(Integer, default=1)
    module_json = Column(String, default="[]")  # JSON array of modules

class ProvinceUnit(Base):
    __tablename__ = 'provinz_einheiten'
    id = Column(Integer, primary_key=True, autoincrement=True)
    province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    einheiten_typ_id = Column(Integer, ForeignKey('einheiten_typen.id'), nullable=False)
    count = Column(Integer, default=1)
    status = Column(String, default="idle")  # idle/marching/trading
    cargo_json = Column(String, default="{}")  # JSON {resource_id: amount}
    
    unit_type = relationship("UnitType")
    province = relationship("Province")

class PopulationCohort(Base):
    __tablename__ = 'population_cohorts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    tick_age = Column(Integer, default=0)  # 0-15 (each tick = 5 years: 0-75+)
    age_group = Column(String, default="kind")  # "kind" (0-14), "arbeiter" (15-64), "rentner" (65+)
    count = Column(Integer, default=0)

    province = relationship("Province")

class GameLog(Base):
    __tablename__ = 'game_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    province_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    timestamp = Column(DateTime, server_default=func.now())
    event_type = Column(String, nullable=False)  # ROUTE_CREATED, ROUTE_ARRIVED, ROUTE_RETURNED, etc.
    message = Column(String, nullable=False)
    details_json = Column(String, default="{}")  # JSON for additional data

    province = relationship("Province")

class DiplomacyRelation(Base):
    __tablename__ = 'diplomatie'
    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    target_player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    status = Column(String, nullable=False)  # verbündet/freund/neutral/unerwünscht/feind
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('player_id', 'target_player_id', name='uq_diplomatie_player_target'),
    )


class Regierungsform(Base):
    __tablename__ = 'regierungsformen'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    formtyp = Column(String, default='')
    techlevel = Column(Integer, default=0)
    ausbauwert_regierungssitz = Column(Integer, default=None)  # Required government seat level
    kulturverbreitung = Column(Float, default=1.0)
    grundmoral = Column(Integer, default=50)
    forschungsfortschritt = Column(Float, default=1.0)
    produktivitaet = Column(Float, default=1.0)
    wachstum = Column(Float, default=1.0)
    finanzen = Column(Float, default=1.0)
    sicherheit = Column(Float, default=1.0)
    moralmalus_armee_aussen = Column(Integer, default=10)
    entfernungsmalus = Column(Float, default=1.0)
    lebensmittelbedarf = Column(Float, default=1.0)
    verbrauchsgutbedarf = Column(Float, default=1.0)
    streikbereitschaft = Column(Float, default=0.0)
    auswanderbereitschaft = Column(Float, default=0.0)
    milizen = Column(Float, default=0.0)
    fremdkultur_verlust = Column(Integer, default=0)
    aufstand = Column(Integer, default=0)
    krieg_moeglich = Column(Integer, default=0)
    provinzanzahl_bis_malus = Column(Integer, default=2)
    malus_beschreibung = Column(String, default='')

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
