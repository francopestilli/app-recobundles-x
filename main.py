#!/usr/bin/env python3
"""RecoBundles X — brainlife.io app entrypoint.

Reads config.json written by the brainlife.io orchestrator and runs the
BundleSeg multi-bundle recognition pipeline (scilpy 2.3.0 + ANTs).

Outputs:
  wmc/classification.mat  — neuro/wmc white matter classification
  tcks/                   — per-bundle .tck files  (neuro/tcks)
"""

import json
import sys
import subprocess
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import requests
from scipy.io import savemat

CONFIG_FILE = "config.json"

ATLAS_ZENODO = {
    "v3.0": "7950602",   # Population average atlas for RecobundlesX → BundleSeg transition
    "v2.2": "7729059",   # Population average atlas for RecobundlesX
    "v2.0": "7562635",   # Population average atlas for RecobundlesX
}


def run(cmd):
    print(f"+ {cmd}", flush=True)
    subprocess.run(cmd, shell=True, check=True)


def download_zenodo(zenodo_id, dest_dir):
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    base = f"https://zenodo.org/record/{zenodo_id}/files"
    for fname in ("atlas.zip", "config.zip"):
        url = f"{base}/{fname}?download=1"
        dest = dest_dir / fname
        print(f"Downloading {url}", flush=True)
        with requests.get(url, stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
        with zipfile.ZipFile(dest) as z:
            z.extractall(dest_dir)
    return dest_dir


def find_model_t1(atlas_root):
    for pattern in ("**/mni_masked.nii.gz", "**/*.nii.gz"):
        hits = list(Path(atlas_root).rglob(pattern[3:] if pattern.startswith("**/") else pattern))
        # rglob already handles **
        hits = list(Path(atlas_root).rglob(pattern.lstrip("*/")))
        if hits:
            return str(hits[0])
    raise FileNotFoundError(f"No .nii.gz model T1 found under {atlas_root}")


def find_config_json(atlas_root):
    hits = list(Path(atlas_root).rglob("*.json"))
    if not hits:
        raise FileNotFoundError(f"No .json config found under {atlas_root}")
    return str(hits[0])


def find_atlas_bundles_dir(atlas_root):
    # BundleSeg expects a directory whose subdirectories are atlas bundles.
    for d in sorted(Path(atlas_root).rglob("*")):
        if d.is_dir() and (list(d.glob("*.trk")) or list(d.glob("*.tck"))):
            return str(d.parent)
    raise FileNotFoundError(f"No atlas bundle subdirectories found under {atlas_root}")


def trk_to_tck(bundle_dir, out_tcks_dir):
    out = Path(out_tcks_dir)
    out.mkdir(parents=True, exist_ok=True)
    for trk in sorted(Path(bundle_dir).glob("*.trk")):
        tck = out / (trk.stem + ".tck")
        run(f"scil_tractogram_convert.py {trk} {tck} -f")


def bundles_to_wmc(bundle_dir, out_wmc_dir):
    """Build neuro/wmc classification.mat from per-bundle .trk files.

    NOTE: This generates a simplified WMC where the index array covers only
    streamlines that were recognized (not the full original tractogram).
    For a fully index-aligned WMC (required by some downstream tools), you
    should match bundle streamlines back to original tractogram positions
    using scilpy's streamline-matching utilities.
    """
    import nibabel as nib

    bundle_files = sorted(Path(bundle_dir).glob("*.trk"))
    if not bundle_files:
        raise RuntimeError(f"No .trk bundles found in {bundle_dir}")

    names = [f.stem for f in bundle_files]
    indices = []
    for i, bf in enumerate(bundle_files, start=1):
        sft = nib.streamlines.load(str(bf))
        indices.extend([i] * len(sft.streamlines))

    out = Path(out_wmc_dir)
    out.mkdir(parents=True, exist_ok=True)

    # neuro/wmc classification.mat shape expected by brainlife.io
    mat = {
        "classification": {
            "names": np.array(names, dtype=object),
            "index": np.array(indices, dtype=np.int32),
        }
    }
    savemat(str(out / "classification.mat"), mat)


def main():
    with open(CONFIG_FILE) as f:
        cfg = json.load(f)

    track      = cfg["track"]
    t1         = cfg["t1"]
    atlas_ver  = cfg.get("atlas", "v3.0")
    min_l      = cfg.get("minL", 20)
    max_l      = cfg.get("maxL", 200)
    seeds      = cfg.get("seeds", 0)
    vote_ratio = cfg.get("minimal_vote_ratio", 0.5)
    processes  = int(cfg.get("processes", 1))

    zenodo_id = ATLAS_ZENODO.get(atlas_ver)
    if zenodo_id is None:
        print(f"ERROR: unknown atlas version '{atlas_ver}'. "
              f"Valid: {list(ATLAS_ZENODO.keys())}", file=sys.stderr)
        sys.exit(1)

    work = Path(tempfile.mkdtemp(prefix="rbx_"))

    # 1. Download atlas
    print("=== 1/5  Downloading atlas ===", flush=True)
    atlas_root   = download_zenodo(zenodo_id, work / "atlas")
    model_t1     = find_model_t1(atlas_root)
    cfg_json     = find_config_json(atlas_root)
    atlas_dir    = find_atlas_bundles_dir(atlas_root)

    # 2. Filter streamlines by length
    print("=== 2/5  Filtering by length ===", flush=True)
    filtered = work / "filtered.trk"
    run(f"scil_tractogram_filter_by_length.py {track} {filtered} "
        f"--minL {min_l} --maxL {max_l} -f")

    # 3. ANTs: register model T1 → subject T1 (affine)
    print("=== 3/5  ANTs registration ===", flush=True)
    reg_prefix = str(work / "model_to_subj_")
    run(f"antsRegistrationSyNQuick.sh -d 3 "
        f"-f {t1} -m {model_t1} -o {reg_prefix} -t a -n {processes}")
    affine = reg_prefix + "0GenericAffine.mat"

    # 4. BundleSeg multi-bundle recognition
    print("=== 4/5  BundleSeg recognition ===", flush=True)
    bundles_dir = work / "voting_results"
    run(f"scil_tractogram_segment_with_bundleseg.py "
        f"{filtered} {cfg_json} {atlas_dir} {affine} "
        f"--out_dir {bundles_dir} "
        f"--minimal_vote_ratio {vote_ratio} "
        f"--seed {seeds} -f")

    # 5. Build brainlife.io outputs
    print("=== 5/5  Building outputs ===", flush=True)
    trk_to_tck(bundles_dir, "tcks")
    bundles_to_wmc(bundles_dir, "wmc")

    print("=== Done ===", flush=True)


if __name__ == "__main__":
    main()
