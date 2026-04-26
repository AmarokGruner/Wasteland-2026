import pytest
from app.database import Base, engine, SessionLocal
from app.models import Province, MarketStand, Resource, ProvinceLager
from app.market_logic import process_market_tick

def get_test_session():
    # Create all tables fresh for each test
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    return session

def test_auto_buy_triggers_and_updates_balances():
    """Test that auto_buy logic runs, reduces lager stock and updates 4‑account balances."""
    sess = get_test_session()

    # --- Setup: create a province, a resource, lager stock and a market stand ---
    province = Province(
        player_id=1,
        name="TestProv",
        population=100,
        marktpunkte=5,
        provinzkonto=1000.0,
        volkskonto=500.0,
        handelskonto=200.0,
    )
    sess.add(province)
    sess.flush()  # get province.id

    resource = Resource(name="Wasser", typ="Getränk", wert=10)
    sess.add(resource)
    sess.flush()

    lager = ProvinceLager(
        provinz_id=province.id,
        ressource_id=resource.id,
        menge=100,
    )
    sess.add(lager)
    sess.flush()

    stand = MarketStand(
        province_id=province.id,
        resource_id=resource.id,
        auto_buy=True,
    )
    sess.add(stand)
    sess.flush()

    # --- Execute the market tick logic ---
    # process_market_tick expects a SQLAlchemy Session, so we pass our test session
    result = process_market_tick(sess, province.id)

    # --- Verify lager stock was reduced ---
    updated_lager = sess.query(ProvinceLager).filter_by(
        provinz_id=province.id, ressource_id=resource.id
    ).first()
    assert updated_lager is not None
    # At least some amount should have been purchased (stock decreases)
    assert updated_lager.menge < 100

    # --- Verify 4‑account balances changed as expected ---
    updated_prov = sess.query(Province).filter_by(id=province.id).first()
    # провинконто should have increased (money earned from sales)
    assert updated_prov.provinzkonto > 1000.0
    # volkskonto should have decreased (population spent money)
    assert updated_prov.volkskonto < 500.0

    sess.close()

def test_market_stand_creation_ui_logic():
    """Test that a MarketStand can be created via UI‑style logic and persists correctly."""
    sess = get_test_session()

    # Create a province and a resource similar to UI workflow
    province = Province(
        player_id=1,
        name="UITestProv",
        population=50,
        marktpunkte=3,
        provinzkonto=500.0,
        volkskonto=250.0,
        handelskonto=100.0,
    )
    sess.add(province)
    sess.flush()

    resource = Resource(name="Holz", typ="Nahrung", wert=5)
    sess.add(resource)
    sess.flush()

    # Simulate UI creating a new market stand (auto_buy can be false for this test)
    stand = MarketStand(
        province_id=province.id,
        resource_id=resource.id,
        auto_buy=False,
    )
    sess.add(stand)
    sess.commit()  # persist to get ID

    # Verify that the stand was created and has an ID
    assert stand.id is not None

    # Verify that the stand is linked to the correct province and resource
    fetched = sess.query(MarketStand).filter_by(id=stand.id).first()
    assert fetched is not None
    assert fetched.province_id == province.id
    assert fetched.resource_id == resource.id

    sess.close()