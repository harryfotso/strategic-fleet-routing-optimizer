# Strategic Fleet Routing Optimizer

Multi-year fleet sizing and vehicle routing optimization for chemical logistics using MILP.

## Problem

A chemical transport company operating from Liège must deliver acid to five Belgian cities and transport base from Antwerp back to Liège.

The objective is to minimize total operating cost over a 5-year horizon while satisfying demand and operational constraints.

## Features

- Multi-year fleet planning
- Vehicle routing
- Mixed-Integer Linear Programming
- Automatic route generation
- Vehicle capacity constraints
- Driver availability constraints
- Fleet purchase and resale decisions
- ADR-related operational constraints
- Sensitivity analysis across 13 scenarios

## Technologies

- Python
- PuLP
- CBC Solver
- NumPy / Pandas

## Model size

- 5,495 variables
- 1,170 binary variables
- 5,298 constraints

## Main result

The optimized strategy reduces the initial fleet from 10 vehicles to 7 vehicles while satisfying all demand requirements.

## Run

```bash
pip install -r requirements.txt
python src/main.py
