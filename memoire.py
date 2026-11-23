"""
Memoire de l'agent e-commerce, construite avec Relate (Neo4j).

Ce fichier contient les outils de base :
- se connecter a la memoire (un seul fichier : memoire.rl)
- normaliser un numero de telephone marocain
- retrouver des clients a partir d'un numero ou d'un nom
"""

import re

import relate

# Mode Relate choisi : fichier unique, pour que les juges puissent l'inspecter.
STORE = "memoire.rl"


def connecter(chemin=STORE):
    """Ouvre la memoire (le fichier est cree s'il n'existe pas)."""
    return relate.connect(chemin)


def normaliser_numero(numero):
    """
    Ecrit tous les numeros marocains au meme format : +2126XXXXXXXX.
    Exemples : "06 00 00 00 02", "+212600000002", "00212600000002"
    donnent tous "+212600000002".
    """
    chiffres = re.sub(r"\D", "", numero or "")  # on garde seulement les chiffres
    if chiffres.startswith("00212"):
        chiffres = chiffres[5:]
    elif chiffres.startswith("212"):
        chiffres = chiffres[3:]
    elif chiffres.startswith("0"):
        chiffres = chiffres[1:]
    if len(chiffres) != 9:
        raise ValueError(f"Numero marocain invalide : {numero!r}")
    return "+212" + chiffres


def clients_par_numero(conn, numero):
    """Tous les clients lies a ce numero (il peut y en avoir plusieurs : une famille)."""
    cursor = conn.execute(
        "MATCH (c:Customer)-[:HAS_PHONE]->(p:Phone {e164: $phone}) "
        "RETURN c.id AS id, c.name AS nom, c.city AS ville",
        {"phone": normaliser_numero(numero)},
    )
    return [dict(row) for row in cursor]


def clients_par_nom(conn, nom):
    """Tous les clients qui portent ce nom (il peut y avoir des homonymes)."""
    cursor = conn.execute(
        "MATCH (c:Customer {name: $nom}) RETURN c.id AS id, c.name AS nom, c.city AS ville",
        {"nom": nom},
    )
    return [dict(row) for row in cursor]
