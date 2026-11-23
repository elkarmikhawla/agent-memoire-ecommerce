"""
Charge des donnees 100 % FICTIVES dans la memoire, puis verifie quelques cas.
Aucun vrai client, aucun vrai numero, aucune vraie adresse.

Lancer :  python donnees_fictives.py
"""

from memoire import clients_par_nom, clients_par_numero, connecter, normaliser_numero

# --- Les clients fictifs -------------------------------------------------
# Cas pieges voulus :
#   C2 et C3 : mere et fille avec le MEME numero (famille)
#   C4 et C5 : deux "Youssef Alaoui" dans deux villes differentes (homonymes)
CLIENTS = [
    {"id": "C1", "name": "Salma Amrani", "city": "Casablanca", "phone": "0600000001"},
    {"id": "C2", "name": "Nadia Benali", "city": "Rabat", "phone": "0600000002"},
    {"id": "C3", "name": "Imane Benali", "city": "Rabat", "phone": "+212 6 00 00 00 02"},
    {"id": "C4", "name": "Youssef Alaoui", "city": "Fes", "phone": "00212600000004"},
    {"id": "C5", "name": "Youssef Alaoui", "city": "Marrakech", "phone": "0600000005"},
]

# Comptes sur les canaux (identifiants inventes)
COMPTES = [
    {"client": "C1", "channel": "whatsapp", "external_id": "+212600000001"},
    {"client": "C2", "channel": "instagram", "external_id": "@nadia_fictif"},
    {"client": "C4", "channel": "telegram", "external_id": "100000004"},
]

# --- Le catalogue fictif -------------------------------------------------
MODELES = ["iPhone 15 Pro", "iPhone 16 Pro", "Apple Watch 41mm", "Apple Watch 45mm"]

PRODUITS = [
    {"id": "P1", "name": "Coque MagSafe", "price": 149,
     "fits": ["iPhone 15 Pro", "iPhone 16 Pro"],
     "variants": [{"sku": "P1-BOR", "color": "Bordeaux", "stock": 12},
                  {"sku": "P1-NOI", "color": "Noir", "stock": 0}]},
    {"id": "P2", "name": "Bracelet sport", "price": 99,
     "fits": ["Apple Watch 41mm", "Apple Watch 45mm"],
     "variants": [{"sku": "P2-NOI", "color": "Noir", "stock": 20},
                  {"sku": "P2-BLA", "color": "Blanc", "stock": 5}]},
]

# --- Les commandes fictives ----------------------------------------------
# #2283 est un DOUBLON de #2278 (meme cliente, meme article) : piege voulu.
COMMANDES = [
    {"number": "#2278", "client": "C1", "sku": "P1-BOR", "qty": 1, "state": "confirmed"},
    {"number": "#2279", "client": "C2", "sku": "P2-BLA", "qty": 1, "state": "confirmed"},
    {"number": "#2280", "client": "C3", "sku": "P2-NOI", "qty": 2, "state": "packed"},
    {"number": "#2281", "client": "C4", "sku": "P1-BOR", "qty": 1, "state": "confirmed"},
    {"number": "#2282", "client": "C5", "sku": "P2-NOI", "qty": 1, "state": "modified"},
    {"number": "#2283", "client": "C1", "sku": "P1-BOR", "qty": 1, "state": "confirmed"},
]

# --- Les regles du gerant (au depart, l'agent demande toujours) ----------
REGLES = [
    {"action_type": "changement_couleur", "mode": "demander"},
    {"action_type": "changement_taille", "mode": "demander"},
    {"action_type": "changement_quantite", "mode": "demander"},
    {"action_type": "changement_adresse", "mode": "jamais"},
    {"action_type": "annulation", "mode": "jamais"},
    {"action_type": "remboursement", "mode": "jamais"},
]


def charger(conn):
    conn.execute("MATCH (n) DETACH DELETE n")  # on repart de zero

    for c in CLIENTS:
        conn.execute("CREATE (:Customer {id: $id, name: $name, city: $city})", c)
        # MERGE : un seul noeud Phone par numero, meme s'il est ecrit differemment
        conn.execute(
            "MATCH (c:Customer {id: $id}) "
            "MERGE (p:Phone {e164: $phone}) ON CREATE SET p.verified = false "
            "CREATE (c)-[:HAS_PHONE {source: 'commande'}]->(p)",
            {"id": c["id"], "phone": normaliser_numero(c["phone"])},
        )

    for a in COMPTES:
        conn.execute(
            "MATCH (c:Customer {id: $client}) "
            "CREATE (c)-[:HAS_ACCOUNT {identity_level: 0}]->"
            "(:ChannelAccount {channel: $channel, external_id: $external_id})",
            a,
        )

    for m in MODELES:
        conn.execute("CREATE (:PhoneModel {name: $name})", {"name": m})

    for p in PRODUITS:
        conn.execute("CREATE (:Product {id: $id, name: $name, price: $price})", p)
        for v in p["variants"]:
            conn.execute(
                "MATCH (p:Product {id: $pid}) "
                "CREATE (p)-[:HAS_VARIANT]->(:Variant {sku: $sku, color: $color, stock: $stock})",
                {"pid": p["id"], **v},
            )
            for modele in p["fits"]:
                conn.execute(
                    "MATCH (v:Variant {sku: $sku}), (m:PhoneModel {name: $modele}) "
                    "CREATE (v)-[:FITS]->(m)",
                    {"sku": v["sku"], "modele": modele},
                )

    for o in COMMANDES:
        conn.execute(
            "MATCH (c:Customer {id: $client}), (v:Variant {sku: $sku}) "
            "CREATE (c)-[:PLACED]->(o:Order {number: $number, state: $state}) "
            "CREATE (o)-[:CONTAINS {qty: $qty}]->(v)",
            o,
        )

    for r in REGLES:
        conn.execute(
            "CREATE (:Rule {action_type: $action_type, mode: $mode, approvals_in_a_row: 0})", r
        )


def verifier(conn):
    print("\n=== Contenu de la memoire ===")
    for row in conn.execute("MATCH (n) RETURN labels(n)[0] AS type, count(*) AS nombre"):
        print(f"  {row['type']:<15} {row['nombre']}")

    print("\n=== Test : un meme numero ecrit de 3 facons ===")
    for ecrit in ["06 00 00 00 01", "+212600000001", "00212600000001"]:
        print(f"  {ecrit:<18} -> {normaliser_numero(ecrit)}")

    print("\n=== Test : famille avec le meme numero ===")
    trouves = clients_par_numero(conn, "0600000002")
    print(f"  {len(trouves)} client(s) trouve(s) :", [t["nom"] for t in trouves])
    print("  -> AMBIGU : l'agent doit demander lequel, sans rien reveler" if len(trouves) > 1 else "  -> OK")

    print("\n=== Test : homonymes ===")
    trouves = clients_par_nom(conn, "Youssef Alaoui")
    print(f"  {len(trouves)} client(s) :", [f"{t['nom']} ({t['ville']})" for t in trouves])
    print("  -> AMBIGU : pas de fusion automatique" if len(trouves) > 1 else "  -> OK")

    print("\n=== Test : commandes en double ===")
    cursor = conn.execute(
        "MATCH (c:Customer)-[:PLACED]->(o:Order)-[:CONTAINS]->(v:Variant) "
        "WITH c, v, collect(o.number) AS commandes WHERE size(commandes) > 1 "
        "RETURN c.name AS client, v.sku AS article, commandes"
    )
    for row in cursor:
        print(f"  {row['client']} : {row['commandes']} pour {row['article']} -> DOUBLON a signaler")


if __name__ == "__main__":
    conn = connecter()
    charger(conn)
    verifier(conn)
    conn.close()
    print("\nMemoire enregistree dans memoire.rl")
