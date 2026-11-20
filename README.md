# RecoBundles X

(describe what this app does here)

## Inputs

- `track` (neuro/track/trk)
- `anat` (neuro/anat/t1w)

## Outputs

- `wmc` (neuro/wmc) -- White matter classification: recognized bundle assignments for each streamline.
- `tcks` (neuro/tcks) -- Recognized bundles as a collection of MRtrix (.tck) files, one per bundle.

## Usage

Brainlife.io: run via `faber-app-run`/`faber-app-pipeline` (once registered
with `faber-app-create`), or the web UI.

Locally (outside brainlife): copy `config.json.example` to `config.json`,
fill in real file paths, then run `./main` from this directory. `main` pulls
its own container (`singularity exec docker://...`) -- no local install of
the underlying tool needed, only Singularity itself.

Entrypoint: `main.py`

## Authors

- Gabriele Amorosino <gabriele.amorosino@utexas.edu>

#### MIT Copyright (c) 2026 Gabriele Amorosino
