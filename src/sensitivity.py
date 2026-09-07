# src/sensitivity.py

from data import (
    D_REF,
    D_H_RE,
    D_CHAR_1,
    D_CHAR_1000,
)

from model import solve


# =========================================================
# SCENARIOS
# =========================================================

SCENARIOS = [

    # diesel, alpha, demand, base demand,
    # effective days T1, effective days T2,
    # initial fleet age, scenario name

    (
        1.90,
        0.15,
        D_REF,
        30000,
        209,
        206,
        3,
        "REFERENCE",
    ),

    (
        1.50,
        0.15,
        D_REF,
        30000,
        209,
        206,
        3,
        "Diesel_1.50",
    ),

    (
        2.50,
        0.15,
        D_REF,
        30000,
        209,
        206,
        3,
        "Diesel_2.50",
    ),

    (
        1.90,
        0.10,
        D_REF,
        30000,
        209,
        206,
        3,
        "Alpha_10pct",
    ),

    (
        1.90,
        0.20,
        D_REF,
        30000,
        209,
        206,
        3,
        "Alpha_20pct",
    ),

    (
        1.90,
        0.15,
        D_H_RE,
        30000,
        209,
        206,
        3,
        "Hasselt_retarde",
    ),

    (
        1.90,
        0.15,
        D_REF,
        30000,
        198,
        195,
        3,
        "Dispo_90pct",
    ),

    (
        1.90,
        0.15,
        D_CHAR_1,
        30000,
        209,
        206,
        3,
        "Charleroi_+1t",
    ),

    (
        1.90,
        0.15,
        D_CHAR_1000,
        30000,
        209,
        206,
        3,
        "Charleroi_+1000t",
    ),

    (
        1.90,
        0.15,
        D_REF,
        30001,
        209,
        206,
        3,
        "Base_+1t",
    ),

    (
        1.90,
        0.15,
        D_REF,
        31000,
        209,
        206,
        3,
        "Base_+1000t",
    ),

    (
        1.90,
        0.15,
        D_REF,
        30000,
        209,
        206,
        1,
        "Age_1an",
    ),

    (
        1.90,
        0.15,
        D_REF,
        30000,
        209,
        206,
        5,
        "Age_5ans",
    ),
]


# =========================================================
# RUN ALL SCENARIOS
# =========================================================

def run_sensitivity_analysis(time_limit=600):
    """
    Run all sensitivity scenarios.

    Parameters
    ----------
    time_limit : int, optional
        CBC time limit for each scenario, in seconds.

    Returns
    -------
    list
        List of dictionaries returned by model.solve().
    """

    print()
    print("=" * 100)
    print(
        f"ANALYSE DE SENSIBILITE — "
        f"{len(SCENARIOS)} SCENARIOS"
    )
    print("=" * 100)
    print()

    results = []

    for index, scenario in enumerate(
        SCENARIOS,
        start=1,
    ):

        (
            diesel,
            alpha,
            demand,
            base_demand,
            j1,
            j2,
            age,
            name,
        ) = scenario

        print(
            f"  [{index}/{len(SCENARIOS)}] "
            f"{name}...",
            end=" ",
            flush=True,
        )

        result = solve(
            diesel=diesel,
            alpha=alpha,
            dem=demand,
            dem_base=base_demand,
            j1=j1,
            j2=j2,
            age_init=age,
            nom=name,
            time_limit=time_limit,
        )

        results.append(result)

        status = (
            "OK"
            if result["statut"] == 1
            else "WARN"
        )

        print(
            f"{status} — "
            f"{result['cout']:,.0f} EUR — "
            f"{result['temps']:.0f}s"
        )

    return results


# =========================================================
# SUMMARY TABLE
# =========================================================

def print_summary(results):
    """
    Print the global sensitivity-analysis summary.
    """

    if not results:
        print("Aucun resultat.")
        return

    reference = results[0]

    ref_t1 = reference["flotte"][0][1]
    ref_t2 = reference["flotte"][0][2]

    print()
    print("=" * 100)

    print(
        f"{'Scenario':<22} "
        f"{'Cout':>12} "
        f"{'T1':>4} "
        f"{'T2':>4} "
        f"{'=ref?':>6} "
        f"{'Stable':>7} "
        f"{'Delta':>12} "
        f"{'Temps':>6}"
    )

    print("-" * 100)

    for result in results:

        fleet = result["flotte"]

        t1 = fleet[0][1]
        t2 = fleet[0][2]

        identical_to_reference = (
            t1 == ref_t1
            and t2 == ref_t2
        )

        stable = all(
            row[1] == fleet[0][1]
            and row[2] == fleet[0][2]
            for row in fleet
        )

        delta = (
            result["cout"]
            - reference["cout"]
        )

        if result["nom"] == "REFERENCE":
            delta_str = "-"
        else:
            delta_str = f"{delta:+,.0f}"

        print(
            f"  {result['nom']:<20} "
            f"{result['cout']:>12,.0f} "
            f"{t1:>4} "
            f"{t2:>4} "
            f"{'OUI' if identical_to_reference else 'NON':>6} "
            f"{'OUI' if stable else 'NON':>7} "
            f"{delta_str:>12} "
            f"{result['temps']:>5.0f}s"
        )


# =========================================================
# DETAILS FOR SCENARIOS DIFFERENT FROM REFERENCE
# =========================================================

def print_different_fleets(results):
    """
    Print detailed fleet evolution for scenarios whose
    first-year fleet differs from the reference scenario.
    """

    if not results:
        return

    reference = results[0]

    ref_t1 = reference["flotte"][0][1]
    ref_t2 = reference["flotte"][0][2]

    different_results = [

        result

        for result in results

        if (
            result["flotte"][0][1] != ref_t1
            or result["flotte"][0][2] != ref_t2
        )
    ]

    if not different_results:
        print()
        print(
            "Tous les scenarios conservent "
            "la meme flotte initiale que la reference."
        )
        return

    print()
    print("=" * 100)
    print(
        "DETAIL DES SCENARIOS "
        "DIFFERENTS DE LA REFERENCE"
    )
    print("=" * 100)

    for result in different_results:

        print()

        print(
            f"  --- {result['nom']} "
            f"({result['cout']:,.0f} EUR) ---"
        )

        print(
            f"  {'An':<4} "
            f"{'T1':<4} "
            f"{'T2':<4} "
            f"{'A.T1':<6} "
            f"{'A.T2':<6} "
            f"{'V.T1':<6} "
            f"{'V.T2':<6} "
            f"{'Ch':<4}"
        )

        for (
            year,
            n1,
            n2,
            purchase_t1,
            purchase_t2,
            sale_t1,
            sale_t2,
            drivers,
        ) in result["flotte"]:

            print(
                f"   {year:<3} "
                f"{n1:<4} "
                f"{n2:<4} "
                f"{purchase_t1:<6} "
                f"{purchase_t2:<6} "
                f"{sale_t1:<6} "
                f"{sale_t2:<6} "
                f"{drivers:<4}"
            )


# =========================================================
# LOCAL STABILITY CHECK
# =========================================================

def verify_local_stability(results):
    """
    Check whether +1 tonne perturbations change
    the reference fleet structure.
    """

    if not results:
        return

    reference = results[0]

    ref_t1 = reference["flotte"][0][1]
    ref_t2 = reference["flotte"][0][2]

    tests = [
        "Charleroi_+1t",
        "Base_+1t",
    ]

    print()
    print("=" * 100)
    print("VERIFICATION STABILITE LOCALE")
    print("=" * 100)

    for test_name in tests:

        result = next(
            (
                r
                for r in results
                if r["nom"] == test_name
            ),
            None,
        )

        if result is None:

            print(
                f"  {test_name}: "
                "scenario introuvable"
            )

            continue

        t1 = result["flotte"][0][1]
        t2 = result["flotte"][0][2]

        stable = (
            t1 == ref_t1
            and t2 == ref_t2
        )

        if stable:

            message = (
                "STABLE "
                "(identique a la reference)"
            )

        else:

            message = (
                "INSTABLE "
                "(composition differente)"
            )

        print(
            f"  {test_name}: "
            f"T1={t1} "
            f"T2={t2} "
            f"— {message}"
        )


# =========================================================
# TOTAL COMPUTATION TIME
# =========================================================

def print_total_time(results):
    """
    Print total solution time across all scenarios.
    """

    total_time = sum(
        result["temps"]
        for result in results
    )

    print(
        f"\n  Temps total: "
        f"{total_time:.0f}s"
    )


# =========================================================
# COMPLETE REPORT
# =========================================================

def print_full_report(results):
    """
    Print all sensitivity-analysis outputs.
    """

    print_summary(results)

    print_different_fleets(results)

    verify_local_stability(results)

    print_total_time(results)