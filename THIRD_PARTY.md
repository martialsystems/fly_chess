# Third-party materials

Original `fly_chess` code is MIT (see `LICENSE`). That license does not relicense research data.

## MaleCNS v1.0

Credit: FlyEM at HHMI Janelia, the University of Cambridge Department of Zoology, the MRC Laboratory of Molecular Biology, and Google Research, with the authors of Berg et al., *Cell* 2026.

- Dataset: https://male-cns.janelia.org/download/
- License: Creative Commons Attribution 4.0 International (https://creativecommons.org/licenses/by/4.0/)
- This slice ships a synthetic fixture graph for tests. It is not the MaleCNS reconstruction. If you later fetch the official tables, keep them CC BY and hash-lock them under `data-provenance/`.

## python-chess

Used for boards, legal moves, and PGN-free FEN handling. GPL-3.0 with a linking exception as published by the python-chess project. See the installed package license.

## MaleCNS file hashes

`data-provenance/malecns_v1/source.lock.json` copies the sha256/size/URL triple published by doomfly for the same three Janelia GCS objects. Re-hash after fetch. The graph itself remains CC BY 4.0.

## Named circuit literature (aliases only)

Descending and feeding names in `config/type_aliases.json` follow published Drosophila types (Namiki DN catalog; MN9 / sugar GRNs; LPLC2; MDN; DNa02 / DNg13; BB / FG halt). They are aliases until neuPrint resolves bodyIds on a live MaleCNS import.
