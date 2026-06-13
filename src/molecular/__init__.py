"""
VaccineGenics Molecular Module — 3D structure visualization and variant mapping.
"""
from .pdb_loader import (
    get_variants_to_highlight,
    generate_3d_visualization_script,
    GENETIC_VARIANT_TO_PDB_RESIDUES,
)

__all__ = [
    "get_variants_to_highlight",
    "generate_3d_visualization_script",
    "GENETIC_VARIANT_TO_PDB_RESIDUES",
]
