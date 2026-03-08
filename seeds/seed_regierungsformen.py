from db_config import get_connection, save_entity

REGIERUNGSFORMEN_DATA = [
    {
        "id": 1,
        "name": "Stamm",
        "formtyp": "feste Regierungsform",
        "techlevel": 0,
        "ausbauwert_regierungssitz": 0,
        "kulturverbreitung": 1.0,
        "grundmoral": 50,
        "forschungsfortschritt": 1.0,
        "produktivitaet": 1.0,
        "wachstum": 1.1,
        "finanzen": 1.0,
        "sicherheit": 1.17,
        "moralmalus_armee_aussen": 10,
        "entfernungsmalus": 1.25,
        "lebensmittelbedarf": 0.67,
        "verbrauchsgutbedarf": 0.67,
        "streikbereitschaft": 0.0,
        "auswanderbereitschaft": 1.0,
        "milizen": 0.5,
        "fremdkultur_verlust": 0,
        "aufstand": 0,
        "krieg_moeglich": 0,
        "provinzanzahl_bis_malus": 2,
        "malus_beschreibung": "16 Moral weniger",
        "boni": {},
        "voraussetzungen": {},
        "beschreibung": "Zum ersten mal die Bunker nach der großen Katastrophe verlassen, schließen sich die Überlebenden Menschen in kleinen Stämmen zusammen, um die Welt aufs Neue zu erkunden.\nIn einem Stamm herrschen feste Hierarchien und enge familiäre Bindungen. Man lebt dicht beisammen und obliegt einer militärisch vergleichbaren Befugnis- und Befehlskette.\nAls Vorteile dieser Regierungsform stechen konstantes Wachstum und Gewährleistung der inneren Sicherheit hervor.\nNachteilig hingegen ist die Tatsache, dass ein Stamm eher klein gehalten werden muss, um weiterhin den Überblick zu behalten und nicht die Kontrolle zu verlieren.\n\nNicht alle Menschen sind mit dieser Art von Gebundenheit zufrieden, was zu einer gefährlichen Auswanderbereitschaft führen kann. So sollte diese Art von Regierung doch lediglich dem Neuaufbau einer Zivilisation dienen."
    },
    {
        "id": 2,
        "name": "Anarchie",
        "formtyp": "Übergangsregierung",
        "techlevel": 0,
        "ausbauwert_regierungssitz": 0,
        "kulturverbreitung": 0.0,
        "grundmoral": 30,
        "forschungsfortschritt": 0.0,
        "produktivitaet": 0.9,
        "wachstum": 1.0,
        "finanzen": 0.9,
        "sicherheit": 0.83,
        "moralmalus_armee_aussen": 10,
        "entfernungsmalus": 0.0,
        "lebensmittelbedarf": 0.67,
        "verbrauchsgutbedarf": 0.67,
        "streikbereitschaft": 0.0,
        "auswanderbereitschaft": 0.33,
        "milizen": 0.0,
        "fremdkultur_verlust": 1,
        "aufstand": 1,
        "krieg_moeglich": 0,
        "provinzanzahl_bis_malus": 0,
        "malus_beschreibung": "",
        "boni": {},
        "voraussetzungen": {},
        "beschreibung": "Anarchie ist der Zustand des Chaos zwischen zwei Regierungsformen.\n\n5 Tage dauert die Umstellung auf eine neue Regierungsform. Es gibt viel zu tun, die Arbeit stapelt sich in allen Ecken und das Volk ist mit diesem Aufwand und der Unordnung sehr unzufrieden.\nEs werden 5 harte Tage, sowohl für das Volk als auch für den Herrscher. Bleibt zu hoffen, dass sich die Umstellung auf die neue Regierungsform lohnt.\n\nZu beachten ist, dass es in dieser Zeit keinen Techfortschritt gibt, durch die Unordnung jedoch weiterhin Waren an die Forschungsstätten geliefert wird. Man sollte dies unterbinden, indem man die Forschungsstätten vorsorglich deaktiviert."
    }
]

def seed():
    conn = get_connection()
    c = conn.cursor()
    ins = upd = 0
    print("\n🔹 Regierungsformen:")
    for r in REGIERUNGSFORMEN_DATA:
        if save_entity(c, "regierungsformen", r, id_field="id"):
            print(f"  ✅  Regierungsform: {r['name']} – neu")
            ins += 1
        else:
            upd += 1
    conn.commit()
    conn.close()
    return ins, upd

if __name__ == "__main__":
    seed()
