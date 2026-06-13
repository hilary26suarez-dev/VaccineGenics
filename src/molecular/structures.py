"""
PDB structure metadata for VaccineGenics 3D visualization.

Structures used:
  6M0J — SARS-CoV-2 Spike RBD bound to human ACE2 receptor (2.45 Å)
  6VSB — Full-length Spike trimer, prefusion conformation (3.46 Å)
"""

PDB_METADATA = {
    "6M0J": {
        "title": "Structure of SARS-CoV-2 spike receptor-binding domain bound to ACE2",
        "chains": {
            "A": "Human ACE2 receptor",
            "E": "SARS-CoV-2 Spike RBD",
        },
        "resolution_ang": 2.45,
        "pmid": "32241718",
        "authors": "Lan et al.",
        "year": 2020,
        "journal": "Nature",
        "rbd_residues": list(range(333, 527)),  # Spike RBD domain, chain E
        "interface_residues": [417, 446, 449, 453, 455, 456, 475, 476, 484, 485, 486, 487, 489, 490, 493, 494, 496, 498, 500, 501, 502, 505],
        "default_focus_chain": "E",
    },
    "6VSB": {
        "title": "Prefusion 2P Spike trimer from SARS-CoV-2",
        "chains": {
            "A": "Spike protomer 1",
            "B": "Spike protomer 2",
            "C": "Spike protomer 3",
        },
        "resolution_ang": 3.46,
        "pmid": "32075877",
        "authors": "Wrapp et al.",
        "year": 2020,
        "journal": "Science",
        "rbd_residues": list(range(333, 527)),
        "default_focus_chain": "A",
    },
}

# Vaccine platform — relevant structural regions
VACCINE_PLATFORM_CONTEXT = {
    "mRNA": {
        "pdb_id": "6VSB",
        "note": "mRNA-LNP vaccines encode full-length Spike (2P stabilized prefusion). LNP delivery affected by APOE genotype.",
        "highlight_chains": ["A"],
    },
    "adenoviral_vector": {
        "pdb_id": "6M0J",
        "note": "Adenoviral vector encodes Spike; RBD epitopes critical for T-cell response. HLA-DRB1*11:04 VITT risk.",
        "highlight_chains": ["E", "A"],
    },
    "protein_subunit": {
        "pdb_id": "6M0J",
        "note": "Protein subunit vaccines present purified Spike RBD or nanoparticle. Lower VITT risk.",
        "highlight_chains": ["E"],
    },
}
