# src/model.py

import time

from pulp import (
    PULP_CBC_CMD,
    LpMinimize,
    LpProblem,
    lpSum,
    LpVariable,
)

from data import (
    VILLES,
    NV,
    ANNEES,
    TYPES,
    COHORTES,
    N_INIT,
    PA_BASE,
    C_FIX,
    SALAIRE,
    COUT_LAVAGE,
    CONSEILLER_ADR,
    CONSO,
    CAP_G,
    CAP_P,
    Q_MIN,
    BIG_M,
)

from routes import (
    ROUTES,
    NR,
    ROUTE_VILLE,
)


def solve(
    diesel,
    alpha,
    dem,
    dem_base,
    j1,
    j2,
    age_init,
    nom,
    time_limit=600,
):
    """
    Solve the multi-year fleet and routing optimization problem.

    Parameters
    ----------
    diesel : float
        Diesel price in EUR/L.

    alpha : float
        Annual depreciation rate.

    dem : dict
        Acid demand by city and year.

    dem_base : float
        Annual base demand.

    j1 : int
        Number of effective operating days for truck type 1.

    j2 : int
        Number of effective operating days for truck type 2.

    age_init : int
        Initial age of the existing fleet.

    nom : str
        Scenario name.

    time_limit : int, optional
        CBC solver time limit in seconds.
        Default is 600 seconds.

    Returns
    -------
    dict
        Dictionary containing:
        - nom
        - cout
        - flotte
        - temps
        - statut
    """

    start_time = time.time()

    # =====================================================
    # ECONOMIC PARAMETERS
    # =====================================================

    # Variable operating cost per km:
    # diesel consumption + Viapass
    cost_per_km = (
        (CONSO / 100) * diesel
        + 0.20
    )

    def purchase_price(k, cohort):
        """
        Purchase/reference price of a truck belonging
        to a given cohort.
        """

        if cohort == 0:
            return PA_BASE[k]

        return (
            PA_BASE[k]
            * 1.025 ** (cohort - 1)
        )

    def resale_price(k, cohort, year):
        """
        Resale value according to age and depreciation rate.
        """

        if cohort == 0:
            age = age_init + year

        else:
            age = year - cohort

        return (
            purchase_price(k, cohort)
            / (1 + alpha) ** age
        )

    # =====================================================
    # MODEL
    # =====================================================

    model = LpProblem(
        nom,
        LpMinimize,
    )

    # =====================================================
    # DECISION VARIABLES
    # =====================================================

    # Routing
    x = {}

    # Type 1 configurations
    za = {}
    zb = {}

    # Type 2 configurations
    c1 = {}
    c2 = {}
    c3 = {}

    # Quantities
    q = {}
    b = {}

    # Binary delivery indicators
    w = {}

    # Fleet variables
    nc = {}
    ac = {}
    sv = {}
    n = {}

    # Drivers
    h = {}

    # -----------------------------------------------------
    # ROUTING AND QUANTITY VARIABLES
    # -----------------------------------------------------

    for r in range(NR):

        for t in ANNEES:

            for k in TYPES:

                x[r, k, t] = LpVariable(
                    f"x_{r}_{k}_{t}",
                    lowBound=0,
                    cat="Integer",
                )

            # Type 1:
            # acid-only or base-only trip
            za[r, t] = LpVariable(
                f"za_{r}_{t}",
                lowBound=0,
                cat="Integer",
            )

            zb[r, t] = LpVariable(
                f"zb_{r}_{t}",
                lowBound=0,
                cat="Integer",
            )

            # Type 2 configurations
            c1[r, t] = LpVariable(
                f"c1_{r}_{t}",
                lowBound=0,
                cat="Integer",
            )

            c2[r, t] = LpVariable(
                f"c2_{r}_{t}",
                lowBound=0,
                cat="Integer",
            )

            c3[r, t] = LpVariable(
                f"c3_{r}_{t}",
                lowBound=0,
                cat="Integer",
            )

            for k in TYPES:

                for vi in range(NV):

                    q[r, k, vi, t] = LpVariable(
                        f"q_{r}_{k}_{vi}_{t}",
                        lowBound=0,
                        cat="Continuous",
                    )

                b[r, k, t] = LpVariable(
                    f"b_{r}_{k}_{t}",
                    lowBound=0,
                    cat="Continuous",
                )

    # -----------------------------------------------------
    # BINARY DELIVERY VARIABLES
    # -----------------------------------------------------

    for ri, vi in ROUTE_VILLE:

        for k in TYPES:

            for t in ANNEES:

                w[ri, k, vi, t] = LpVariable(
                    f"w_{ri}_{k}_{vi}_{t}",
                    cat="Binary",
                )

    # -----------------------------------------------------
    # FLEET VARIABLES
    # -----------------------------------------------------

    for k in TYPES:

        for t in ANNEES:

            # Purchases
            ac[k, t] = LpVariable(
                f"ac_{k}_{t}",
                lowBound=0,
                cat="Integer",
            )

            # Total fleet
            n[k, t] = LpVariable(
                f"n_{k}_{t}",
                lowBound=0,
                cat="Integer",
            )

            for tb in COHORTES:

                # Number of trucks from cohort tb
                # still present in year t
                nc[k, tb, t] = LpVariable(
                    f"nc_{k}_{tb}_{t}",
                    lowBound=0,
                    cat="Integer",
                )

                # Number of trucks sold
                sv[k, tb, t] = LpVariable(
                    f"sv_{k}_{tb}_{t}",
                    lowBound=0,
                    cat="Integer",
                )

    # -----------------------------------------------------
    # DRIVER VARIABLES
    # -----------------------------------------------------

    for t in ANNEES:

        h[t] = LpVariable(
            f"h_{t}",
            lowBound=0,
            cat="Integer",
        )

    # =====================================================
    # CONSTRAINT C1
    # ACID DEMAND
    # =====================================================

    for vi in range(NV):

        city = VILLES[vi]

        for t in ANNEES:

            model += (
                lpSum(
                    q[r, k, vi, t]

                    for r in range(NR)

                    if ROUTES[r]["d"][city]

                    for k in TYPES
                )
                >= dem[city][t]
            ), f"C1_acid_demand_{city}_{t}"

    # =====================================================
    # CONSTRAINT C2
    # BASE DEMAND
    # =====================================================

    for t in ANNEES:

        model += (
            lpSum(
                b[r, k, t]

                for r in range(NR)

                if ROUTES[r]["b"]

                for k in TYPES
            )
            >= dem_base
        ), f"C2_base_demand_{t}"

    # =====================================================
    # CONSTRAINT C3
    # TYPE 1 CONFIGURATION
    # =====================================================

    for r in range(NR):

        for t in ANNEES:

            # Every T1 trip is either acid or base
            model += (
                za[r, t] + zb[r, t]
                == x[r, 1, t]
            ), f"C3_T1_split_{r}_{t}"

            # Acid capacity
            model += (
                lpSum(
                    q[r, 1, vi, t]
                    for vi in range(NV)
                )
                <= za[r, t] * CAP_G
            ), f"C3_T1_acid_capacity_{r}_{t}"

            if ROUTES[r]["b"]:

                # Base capacity
                model += (
                    b[r, 1, t]
                    <= zb[r, t] * CAP_G
                ), f"C3_T1_base_capacity_{r}_{t}"

            else:

                # Cannot transport base when
                # Antwerp is not the last stop
                model += (
                    b[r, 1, t] == 0
                ), f"C3_T1_no_base_{r}_{t}"

                model += (
                    zb[r, t] == 0
                ), f"C3_T1_no_base_trip_{r}_{t}"

    # =====================================================
    # CONSTRAINT C4
    # TYPE 2 CONFIGURATIONS
    # =====================================================

    for r in range(NR):

        for t in ANNEES:

            if ROUTES[r]["b"]:

                # Every T2 trip selects exactly one config
                model += (
                    c1[r, t]
                    + c2[r, t]
                    + c3[r, t]
                    == x[r, 2, t]
                ), f"C4_T2_split_{r}_{t}"

                # Acid capacity
                model += (
                    lpSum(
                        q[r, 2, vi, t]
                        for vi in range(NV)
                    )
                    <= (
                        c1[r, t] * CAP_G
                        + c2[r, t] * CAP_P
                        + c3[r, t] * CAP_G
                    )
                ), f"C4_T2_acid_capacity_{r}_{t}"

                # Base capacity
                model += (
                    b[r, 2, t]
                    <= (
                        c1[r, t] * CAP_P
                        + c2[r, t] * CAP_G
                    )
                ), f"C4_T2_base_capacity_{r}_{t}"

            else:

                # Configurations involving base are forbidden
                model += (
                    c1[r, t] == 0
                ), f"C4_T2_no_c1_{r}_{t}"

                model += (
                    c2[r, t] == 0
                ), f"C4_T2_no_c2_{r}_{t}"

                # All T2 trips are config 3
                model += (
                    c3[r, t]
                    == x[r, 2, t]
                ), f"C4_T2_only_c3_{r}_{t}"

                # Acid only
                model += (
                    lpSum(
                        q[r, 2, vi, t]
                        for vi in range(NV)
                    )
                    <= x[r, 2, t] * CAP_G
                ), f"C4_T2_acid_only_capacity_{r}_{t}"

                # No base
                model += (
                    b[r, 2, t] == 0
                ), f"C4_T2_no_base_{r}_{t}"

    # =====================================================
    # CONSTRAINT C5
    # ROUTE-CITY CONSISTENCY
    # =====================================================

    for r in range(NR):

        for vi in range(NV):

            city = VILLES[vi]

            if not ROUTES[r]["d"][city]:

                for k in TYPES:

                    for t in ANNEES:

                        model += (
                            q[r, k, vi, t] == 0
                        ), f"C5_route_city_{r}_{k}_{vi}_{t}"

    # =====================================================
    # CONSTRAINT C5bis
    # MINIMUM DELIVERY = 5 TONNES
    # =====================================================

    for ri, vi in ROUTE_VILLE:

        for k in TYPES:

            for t in ANNEES:

                model += (
                    q[ri, k, vi, t]
                    >= Q_MIN * w[ri, k, vi, t]
                ), f"C5bis_min_{ri}_{k}_{vi}_{t}"

                model += (
                    q[ri, k, vi, t]
                    <= BIG_M * w[ri, k, vi, t]
                ), f"C5bis_max_{ri}_{k}_{vi}_{t}"

    # =====================================================
    # CONSTRAINT C6
    # FLEET CAPACITY
    # =====================================================

    for k in TYPES:

        effective_days = (
            j1
            if k == 1
            else j2
        )

        for t in ANNEES:

            model += (
                lpSum(
                    x[r, k, t]
                    / ROUTES[r]["j"]

                    for r in range(NR)
                )
                <= n[k, t] * effective_days
            ), f"C6_fleet_capacity_{k}_{t}"

    # =====================================================
    # CONSTRAINT C7
    # FLEET EVOLUTION BY COHORT
    # =====================================================

    for k in TYPES:

        # -------------------------------------------------
        # Initial fleet cohort tb = 0
        # -------------------------------------------------

        for t in ANNEES:

            if t == 1:

                model += (
                    nc[k, 0, t]
                    == N_INIT[k]
                    - sv[k, 0, t]
                ), f"C7_initial_fleet_{k}_{t}"

            else:

                model += (
                    nc[k, 0, t]
                    == nc[k, 0, t - 1]
                    - sv[k, 0, t]
                ), f"C7_initial_cohort_evolution_{k}_{t}"

        # -------------------------------------------------
        # New purchase cohorts
        # -------------------------------------------------

        for tb in range(1, 6):

            for t in ANNEES:

                if t == tb:

                    model += (
                        nc[k, tb, t]
                        == ac[k, t]
                        - sv[k, tb, t]
                    ), f"C7_new_cohort_{k}_{tb}_{t}"

                elif t > tb:

                    model += (
                        nc[k, tb, t]
                        == nc[k, tb, t - 1]
                        - sv[k, tb, t]
                    ), f"C7_cohort_evolution_{k}_{tb}_{t}"

                else:

                    model += (
                        nc[k, tb, t] == 0
                    ), f"C7_future_cohort_stock_{k}_{tb}_{t}"

                    model += (
                        sv[k, tb, t] == 0
                    ), f"C7_future_cohort_sale_{k}_{tb}_{t}"

        # -------------------------------------------------
        # Total fleet
        # -------------------------------------------------

        for t in ANNEES:

            model += (
                n[k, t]
                == lpSum(
                    nc[k, tb, t]
                    for tb in COHORTES
                )
            ), f"C7_total_fleet_{k}_{t}"

    # =====================================================
    # CONSTRAINT C7bis
    # MINIMUM HOLDING PERIOD
    # =====================================================

    for k in TYPES:

        for tb in range(1, 6):

            for t in ANNEES:

                if t < tb + 2:

                    model += (
                        sv[k, tb, t] == 0
                    ), f"C7bis_holding_{k}_{tb}_{t}"

    # =====================================================
    # CONSTRAINT C8
    # DRIVERS
    # =====================================================

    for t in ANNEES:

        model += (
            h[t]
            >= lpSum(
                n[k, t]
                for k in TYPES
            )
        ), f"C8_drivers_{t}"

    # =====================================================
    # OBJECTIVE FUNCTION
    # =====================================================

    model += (

        # -------------------------------------------------
        # Fuel + Viapass
        # -------------------------------------------------

        lpSum(
            x[r, k, t]
            * ROUTES[r]["km"]
            * cost_per_km

            for r in range(NR)
            for k in TYPES
            for t in ANNEES
        )

        # -------------------------------------------------
        # T2 washing
        # -------------------------------------------------

        + lpSum(
            n[2, t]
            * COUT_LAVAGE

            for t in ANNEES
        )

        # -------------------------------------------------
        # Fixed vehicle costs
        # -------------------------------------------------

        + lpSum(
            n[k, t]
            * C_FIX

            for k in TYPES
            for t in ANNEES
        )

        # -------------------------------------------------
        # Drivers
        # -------------------------------------------------

        + lpSum(
            h[t]
            * SALAIRE

            for t in ANNEES
        )

        # -------------------------------------------------
        # Purchases
        # -------------------------------------------------

        + lpSum(
            ac[k, t]
            * PA_BASE[k]
            * 1.025 ** (t - 1)

            for k in TYPES
            for t in ANNEES
        )

        # -------------------------------------------------
        # Resale revenues
        # -------------------------------------------------

        - lpSum(
            sv[k, tb, t]
            * resale_price(
                k,
                tb,
                t,
            )

            for k in TYPES
            for tb in COHORTES
            for t in ANNEES

            if tb == 0 or t >= tb
        )

        # -------------------------------------------------
        # ADR safety advisor
        # -------------------------------------------------

        + CONSEILLER_ADR * 5

    ), "total_cost"

    # =====================================================
    # SOLVE
    # =====================================================

    solver = PULP_CBC_CMD(
        msg=0,
        timeLimit=time_limit,
    )

    model.solve(solver)

    elapsed = (
        time.time()
        - start_time
    )

    # =====================================================
    # EXTRACT FLEET RESULTS
    # =====================================================

    fleet = []

    for t in ANNEES:

        t1 = int(
            n[1, t].varValue
            or 0
        )

        t2 = int(
            n[2, t].varValue
            or 0
        )

        purchases_t1 = int(
            ac[1, t].varValue
            or 0
        )

        purchases_t2 = int(
            ac[2, t].varValue
            or 0
        )

        sales_t1 = sum(
            int(
                sv[1, tb, t].varValue
                or 0
            )
            for tb in COHORTES
        )

        sales_t2 = sum(
            int(
                sv[2, tb, t].varValue
                or 0
            )
            for tb in COHORTES
        )

        drivers = int(
            h[t].varValue
            or 0
        )

        fleet.append(
            (
                t,
                t1,
                t2,
                purchases_t1,
                purchases_t2,
                sales_t1,
                sales_t2,
                drivers,
            )
        )

    # =====================================================
    # RETURN RESULTS
    # =====================================================

    return {
        "nom": nom,
        "cout": model.objective.value(),
        "flotte": fleet,
        "temps": elapsed,
        "statut": model.status,
    }