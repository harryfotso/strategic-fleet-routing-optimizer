# src/main.py

from data import (
    ANNEES,
    TYPES,
)

from routes import (
    NR,
    ROUTE_VILLE,
)

from sensitivity import (
    run_sensitivity_analysis,
    print_full_report,
)


def main():

    number_binary_variables = (
        len(ROUTE_VILLE)
        * len(TYPES)
        * len(ANNEES)
    )

    print(
        f"Routes: {NR}"
    )

    print(
        "Binaires par scenario: "
        f"{number_binary_variables}"
    )

    results = run_sensitivity_analysis(
        time_limit=600
    )

    print_full_report(results)


if __name__ == "__main__":
    main()