# src/routes.py

from itertools import permutations

from data import (
    VILLES,
    NV,
    DIST,
)


def make_routes():
    routes = []

    for nb in range(1, 5):

        for perm in permutations(VILLES, nb):

            etapes = (
                ["Liege"]
                + list(perm)
                + ["Liege"]
            )

            km = sum(
                DIST[
                    (
                        etapes[i],
                        etapes[i + 1],
                    )
                ]
                for i in range(
                    len(etapes) - 1
                )
            )

            driving_time = km / 70

            # Maximum 9 h de conduite
            if driving_time > 9:
                continue

            villes_route = list(perm)

            route = {
                "v": villes_route,
                "km": km,
                "tc": driving_time,

                "d": {
                    ville: (
                        1
                        if ville in villes_route
                        else 0
                    )
                    for ville in VILLES
                },

                # Peut ramener de la base
                "b": (
                    1
                    if villes_route[-1] == "Anvers"
                    else 0
                ),

                # Nombre max de trajets / jour
                "j": (
                    2
                    if 2 * driving_time <= 9
                    else 1
                ),
            }

            routes.append(route)

    # -----------------------------------------------------
    # SUPPRESSION DES ROUTES DOMINEES
    # -----------------------------------------------------

    best = {}

    for route in routes:

        key = (
            frozenset(route["v"]),
            route["b"],
        )

        if (
            key not in best
            or route["km"] < best[key]["km"]
        ):
            best[key] = route

    return list(best.values())


ROUTES = make_routes()
NR = len(ROUTES)


# Couples route-ville réellement possibles
ROUTE_VILLE = []

for ri in range(NR):

    for vi in range(NV):

        ville = VILLES[vi]

        if ROUTES[ri]["d"][ville] == 1:

            ROUTE_VILLE.append(
                (ri, vi)
            )