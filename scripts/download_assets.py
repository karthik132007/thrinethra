"""Download publisher-provided real videos, ground truth and pretrained models.

Assets stay under ignored runtime/. SHA-256 is checked against the committed manifest.
No generated tracks, repeated photographs or synthetic counts are used here.
"""

import argparse
import hashlib
import json
import shutil
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def download(asset):
    path = ROOT / asset["path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    expected = asset.get("sha256")
    if path.exists() and (not expected or digest(path) == expected):
        print(f"Verified {asset['id']}", flush=True)
        return
    temporary = path.with_suffix(path.suffix + ".part")
    for attempt in range(3):
        try:
            if asset.get("bytes",0)>64*1024*1024 or asset.get("range_download"):
                total=asset['bytes']
                if total>300*1024*1024:raise ValueError('Asset exceeds download limit')
                offset=temporary.stat().st_size if temporary.exists() else 0
                with temporary.open('ab') as output:
                    while offset<total:
                        end=min(total-1,offset+3*1024*1024-1)
                        request=urllib.request.Request(asset['url'],headers={'Range':f'bytes={offset}-{end}'})
                        with urllib.request.urlopen(request,timeout=60) as response:
                            if response.status!=206:raise ValueError('Server did not honor resumable download')
                            block=response.read(end-offset+1)
                        if len(block)!=end-offset+1:raise ValueError('Short range response')
                        output.write(block);output.flush();offset+=len(block)
            else:
                request=urllib.request.Request(asset['url'],headers={'User-Agent':'Trinethra research asset downloader/0.2'})
                with urllib.request.urlopen(request,timeout=60) as response,temporary.open('wb') as output:
                    size=0
                    while chunk:=response.read(1024*1024):
                        size+=len(chunk)
                        if size>300*1024*1024:raise ValueError('Asset exceeds download limit')
                        output.write(chunk)
            if expected and digest(temporary) != expected:
                raise ValueError(f"Checksum mismatch for {asset['id']}")
            temporary.replace(path)
            print(f"Downloaded {asset['id']}: {path.stat().st_size} bytes", flush=True)
            return
        except Exception:
            temporary.unlink(missing_ok=True)
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models-only", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "configs/assets.json").read_text())
    for asset in manifest["assets"]:
        if not args.models_only or asset["kind"] == "model":
            download(asset)
    if not args.models_only:
        import zipfile
        with zipfile.ZipFile(ROOT/'runtime/datasets/MOT17Labels.zip') as archive:
            for sequence in ('MOT17-04-FRCNN','MOT17-09-FRCNN'):
                for suffix in ('gt/gt.txt','seqinfo.ini'):
                    member=f'train/{sequence}/{suffix}'
                    destination=ROOT/'runtime/datasets'/member
                    destination.parent.mkdir(parents=True,exist_ok=True)
                    destination.write_bytes(archive.read(member))
        import sys

        sys.path.insert(0, str(ROOT / "apps/backend"))
        from trinethra.media import ensure_preview

        for asset in manifest["assets"]:
            if asset["kind"] == "video":
                print("Preparing browser preview: " + asset["id"], flush=True)
                ensure_preview(ROOT / asset["path"])
    print("Ready. Run make real-demo to configure real recording sources.")


if __name__ == "__main__":
    main()
