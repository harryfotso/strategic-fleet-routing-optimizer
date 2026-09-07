# src/data.py

VILLES = ["Anvers", "Charleroi", "Gand", "Bruxelles", "Hasselt"]
NV = len(VILLES)

ANNEES = [1, 2, 3, 4, 5]
TYPES = [1, 2]
COHORTES = [0, 1, 2, 3, 4, 5]

# ---------------------------------------------------------
# DISTANCES
# ---------------------------------------------------------

DIST = {}

NOMS = ["Anvers", "Charleroi", "Liege", "Gand", "Bruxelles", "Hasselt"]

DISTANCE_MATRIX = [
    [0, 100, 105, 40, 45, 50],
    [100, 0, 100, 100, 60, 80],
    [105, 100, 0, 140, 100, 60],
    [40, 100, 140, 0, 40, 60],
    [45, 60, 100, 40, 0, 50],
    [50, 80, 60, 60, 50, 0],
]

for i in range(len(NOMS)):
    for j in range(len(NOMS)):
        DIST[(NOMS[i], NOMS[j])] = DISTANCE_MATRIX[i][j]


# ---------------------------------------------------------
# FLOTTE / PARAMETRES ECONOMIQUES
# ---------------------------------------------------------

N_INIT = {
    1: 4,
    2: 6,
}

PA_BASE = {
    1: 140_000,
    2: 200_000,
}

C_FIX = 13_300
SALAIRE = 45_000
COUT_LAVAGE = 1_500
CONSEILLER_ADR = 4_000

INFLATION = 0.025

CONSO = 30

CAP_G = 16.5
CAP_P = 5.5

Q_MIN = 5.0

BIG_M = 209 * 2 * CAP_G


# ---------------------------------------------------------
# DEMANDE DE REFERENCE
# ---------------------------------------------------------

D_REF = {
    "Anvers": {
        1: 9000,
        2: 9000,
        3: 9000,
        4: 9000,
        5: 9000,
    },
    "Charleroi": {
        1: 12000,
        2: 12000,
        3: 12000,
        4: 12000,
        5: 12000,
    },
    "Gand": {
        1: 2000,
        2: 2000,
        3: 2000,
        4: 2000,
        5: 2000,
    },
    "Bruxelles": {
        1: 6200,
        2: 6200,
        3: 6200,
        4: 6200,
        5: 6200,
    },
    "Hasselt": {
        1: 350,
        2: 825,
        3: 1300,
        4: 1300,
        5: 1300,
    },
}


def copy_demand(base):
    return {
        city: dict(years)
        for city, years in base.items()
    }


# Hasselt retardé
D_H_RE = copy_demand(D_REF)
D_H_RE["Hasselt"] = {
    1: 350,
    2: 350,
    3: 825,
    4: 1300,
    5: 1300,
}


# Charleroi +1 tonne
D_CHAR_1 = copy_demand(D_REF)

for year in ANNEES:
    D_CHAR_1["Charleroi"][year] = 12001


# Charleroi +1000 tonnes
D_CHAR_1000 = copy_demand(D_REF)

for year in ANNEES:
    D_CHAR_1000["Charleroi"][year] = 13000