"""
Core recipes for Lennard-Jones Potential

NOTE: This set of minimal recipes is mainly for demonstration purposes
"""
from __future__ import annotations

from typing import Literal

import covalent as ct
from ase import Atoms
from ase.calculators.lj import LennardJones
from ase.optimize import FIRE

from quacc.schemas.ase import (
    OptSchema,
    RunSchema,
    ThermoSchema,
    VibSchema,
    summarize_opt_run,
    summarize_run,
    summarize_thermo_run,
    summarize_vib_run,
)
from quacc.util.calc import run_ase_opt, run_ase_vib, run_calc
from quacc.util.thermo import ideal_gas


@ct.electron
def static_job(
    atoms: Atoms | dict,
    calc_kwargs: dict | None = None,
) -> RunSchema:
    """
    Function to carry out a static calculation.

    Parameters
    ----------
    atoms
        Atoms object or a dictionary with the key "atoms" and an Atoms object as the value
    calc_kwargs
        Dictionary of custom kwargs for the LJ calculator

    Returns
    -------
    RunSchema
        Dictionary of results from `quacc.schemas.ase.summarize_run`
    """
    atoms = atoms if isinstance(atoms, Atoms) else atoms["atoms"]
    calc_kwargs = calc_kwargs or {}

    atoms.calc = LennardJones(**calc_kwargs)
    final_atoms = run_calc(atoms)

    return summarize_run(
        final_atoms, input_atoms=atoms, additional_fields={"name": "LJ Static"}
    )


@ct.electron
def relax_job(
    atoms: Atoms | dict,
    calc_kwargs: dict | None = None,
    opt_swaps: dict | None = None,
) -> OptSchema:
    """
    Function to carry out a geometry optimization

    Parameters
    ----------
    atoms
        Atoms object
    calc_kwargs
        Dictionary of custom kwargs for the LJ calculator.
    opt_swaps
        Dictionary of swaps for run_ase_opt

    Returns
    -------
    OptSchema
        Dictionary of results from `quacc.schemas.ase.summarize_opt_run`
    """
    atoms = atoms if isinstance(atoms, Atoms) else atoms["atoms"]
    calc_kwargs = calc_kwargs or {}
    opt_swaps = opt_swaps or {}

    opt_defaults = {"fmax": 0.01, "max_steps": 1000, "optimizer": FIRE}

    opt_flags = opt_defaults | opt_swaps

    atoms.calc = LennardJones(**calc_kwargs)
    dyn = run_ase_opt(atoms, **opt_flags)

    return summarize_opt_run(dyn, additional_fields={"name": "LJ Relax"})


@ct.electron
def freq_job(
    atoms: Atoms | dict,
    energy: float = 0.0,
    temperature: float = 298.15,
    pressure: float = 1.0,
    calc_kwargs: dict | None = None,
    vib_kwargs: dict | None = None,
) -> dict[Literal["vib", "thermo"], VibSchema | ThermoSchema]:
    """
    Run a frequency job and calculate thermochemistry.

    Parameters
    ----------
    atoms
        Atoms object or a dictionary with the key "atoms" and an Atoms object as the value
    energy
        Potential energy in eV. If 0, then the output is just the correction.
    temperature
        Temperature in Kelvins.
    pressure
        Pressure in bar.
    calc_kwargs
        dictionary of custom kwargs for the LJ calculator.
    vib_kwargs
        dictionary of custom kwargs for the Vibrations object

    Returns
    -------
    dict
        Dictionary of results from quacc.schemas.ase.summarize_vib_run and
        quacc.schemas.ase.summarize_thermo_run
    """
    atoms = atoms if isinstance(atoms, Atoms) else atoms["atoms"]
    calc_kwargs = calc_kwargs or {}
    vib_kwargs = vib_kwargs or {}

    atoms.calc = LennardJones(**calc_kwargs)
    vibrations = run_ase_vib(atoms, vib_kwargs=vib_kwargs)

    igt = ideal_gas(atoms, vibrations.get_frequencies(), energy=energy)

    return {
        "vib": summarize_vib_run(
            vibrations, additional_fields={"name": "LJ Vibrations"}
        ),
        "thermo": summarize_thermo_run(
            igt,
            temperature=temperature,
            pressure=pressure,
            additional_fields={"name": "LJ Thermo"},
        ),
    }