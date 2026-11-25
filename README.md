# RecoBundles X

<!-- brainlife-app:begin (generated from the App manifest; edit the manifest, not this block) -->

> **Recognizes white matter bundles in a whole-brain .trk tractogram with scilpy BundleSeg (RecoBundlesX) against a population atlas downloaded from Zenodo, and outputs a WMC classification and per-bundle .tck files.**

Downloads the selected RecobundlesX/BundleSeg atlas from Zenodo, filters streamlines by length (minL-maxL), registers the atlas T1 to the subject T1 with an ANTs affine (antsRegistrationSyNQuick), and runs scil_tractogram_segment_with_bundleseg with multi-parameter voting. Use it for atlas-based bundle extraction from whole-brain tractograms. It needs internet access; the WMC index covers only recognized streamlines, not the full input tractogram.

| | |
|---|---|
| 📥 **Inputs** | `neuro/track/trk` · `neuro/anat/t1w` |
| 📤 **Outputs** | `neuro/wmc` · `neuro/tcks` |
| 🐳 **Container** | `scilus/scilus:2.3.0` |
| 🔗 **Run it** | [doi.org/10.25663/brainlife.app.1000](https://doi.org/10.25663/brainlife.app.1000) |

#### 📥 Inputs

| Input | Datatype | Required | Description |
|---|---|---|---|
| `track` | `neuro/track/trk` | yes | Whole-brain tractogram in TrackVis (.trk) format. |
| `anat` | `neuro/anat/t1w` | yes | Subject T1-weighted anatomy used for ANTs affine registration to the atlas space. |

#### 📤 Outputs

| Output | Datatype | Description |
|---|---|---|
| `wmc` | `neuro/wmc` | White matter classification: recognized bundle assignments for each streamline. |
| `tcks` | `neuro/tcks` | Recognized bundles as a collection of MRtrix (.tck) files, one per bundle. |

<details>
<summary><b>⚙️ Parameters</b> (6)</summary>

| Parameter | Type | Default | Description |
|---|---|---|---|
| `atlas` | enum | `v3.0` | Atlas version to download from Zenodo at runtime. v3.0 = Zenodo 7950602 (RecobundlesX → BundleSeg transition); v2.2 = Zenodo 7729059; v2.0 = Zenodo 7562635. Options: `v3.0`, `v2.2`, `v2.0`. |
| `minL` | number | `20` | Minimum streamline length (mm). Streamlines shorter than this are discarded before bundle recognition. |
| `maxL` | number | `200` | Maximum streamline length (mm). Streamlines longer than this are discarded before bundle recognition. |
| `seeds` | number | `0` | Random number generator seed for reproducibility. |
| `minimal_vote_ratio` | number | `0.5` | Minimum fraction of multi-parameter runs in which a streamline must be recognized to be kept in the final bundle. |
| `processes` | number | `1` | Number of parallel threads. |

</details>

<!-- brainlife-app:end -->

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
