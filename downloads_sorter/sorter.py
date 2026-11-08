import json
import re
import shutil
from pathlib import Path
from collections import defaultdict
from typing import Optional

IGNORED_EXTENSIONS = {".crdownload", ".download", ".part", ".tmp"}
IGNORED_NAMES = {".ds_store", ".localized", "thumbs.db"}

EXTENSION_CATEGORIES = {
    # Installers & Apps
    ".dmg": "Installers & Apps",
    ".pkg": "Installers & Apps",
    ".app": "Installers & Apps",
    ".iso": "Installers & Apps",
    ".exe": "Installers & Apps",
    # Reading & Publications
    ".epub": "Reading & Publications",
    ".mobi": "Reading & Publications",
    # Media
    ".mp4": "Media",
    ".mov": "Media",
    ".mp3": "Media",
    ".wav": "Media",
    ".mkv": "Media",
    # Archives
    ".zip": "Archives",
    ".tar": "Archives",
    ".gz": "Archives",
    ".7z": "Archives",
    ".rar": "Archives",
    # Code & Data
    ".py": "Code & Data",
    ".json": "Code & Data",
    ".csv": "Code & Data",
    ".sql": "Code & Data",
    ".js": "Code & Data",
    ".ts": "Code & Data",
    # Documents
    ".pdf": "Documents",
    ".doc": "Documents",
    ".docx": "Documents",
    ".txt": "Documents",
    ".pptx": "Documents",
    ".xlsx": "Documents",
    # Images
    ".png": "Images",
    ".jpg": "Images",
    ".jpeg": "Images",
    ".gif": "Images",
    ".webp": "Images",
    ".svg": "Images",
}

DEFAULT_HISTORY_FILE = Path.home() / ".downloads_sorter_history.json"

def is_ignored_file(path: Path) -> bool:
    name_lower = path.name.lower()
    if name_lower in IGNORED_NAMES or path.name.startswith("."):
        return True
    if path.suffix.lower() in IGNORED_EXTENSIONS:
        return True
    return False

def categorize_file(path: Path) -> str:
    name_lower = path.name.lower()
    
    # Check rule-based prefixes / keywords first
    if name_lower.startswith(("screenshot", "screen shot", "screen recording")):
        return "Screenshots"
    if any(keyword in name_lower for keyword in ["invoice", "receipt", "statement", "bill", "tax"]):
        return "Financial & Receipts"
        
    ext = path.suffix.lower()
    return EXTENSION_CATEGORIES.get(ext, "Other")

def extract_tokens(stem: str) -> list[str]:
    cleaned = re.sub(r"[_\-\.\s]+", " ", stem).strip()
    tokens = [t.lower() for t in cleaned.split() if len(t) > 2 and not t.isdigit()]
    return tokens

def cluster_files(files: list[Path]) -> dict[str, list[Path]]:
    clusters = defaultdict(list)
    pending_clustering: list[Path] = []
    
    for f in files:
        if is_ignored_file(f):
            continue
        cat = categorize_file(f)
        if cat in {"Installers & Apps", "Screenshots", "Financial & Receipts", "Reading & Publications"}:
            clusters[cat].append(f)
        else:
            pending_clustering.append(f)
            
    # Semantic token clustering on pending files
    prefix_groups = defaultdict(list)
    for f in pending_clustering:
        tokens = extract_tokens(f.stem)
        if len(tokens) >= 2:
            prefix_key = " ".join(tokens[:2]).title()
            prefix_groups[prefix_key].append(f)
            
    assigned = set()
    for prefix_key, group in prefix_groups.items():
        if len(group) >= 2:
            clusters[prefix_key].extend(group)
            assigned.update(group)
            
    for f in pending_clustering:
        if f not in assigned:
            cat = categorize_file(f)
            clusters[cat].append(f)
            
    return dict(clusters)

def resolve_destination_path(folder: Path, filename: str) -> Path:
    target = folder / filename
    if not target.exists():
        return target
        
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while True:
        candidate = folder / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1

def move_files(
    clusters: dict[str, list[Path]],
    base_dir: Path,
    history_file: Optional[Path] = None,
    dry_run: bool = False
) -> list[dict[str, str]]:
    history_path = history_file or DEFAULT_HISTORY_FILE
    move_records: list[dict[str, str]] = []

    for folder_name, file_list in clusters.items():
        dest_folder = base_dir / folder_name
        for src_file in file_list:
            if not src_file.exists():
                continue
            dest_file = resolve_destination_path(dest_folder, src_file.name)
            move_records.append({
                "source": str(src_file.resolve()),
                "destination": str(dest_file.resolve()),
                "folder": folder_name
            })
            if not dry_run:
                dest_folder.mkdir(parents=True, exist_ok=True)
                shutil.move(src_file, dest_file)

    if not dry_run and move_records:
        history: list[list[dict[str, str]]] = []
        if history_path.exists():
            try:
                history = json.loads(history_path.read_text(encoding="utf-8"))
            except Exception:
                history = []
        history.append(move_records)
        history_path.write_text(json.dumps(history, indent=2), encoding="utf-8")

    return move_records

def undo_last_run(history_file: Optional[Path] = None) -> list[dict[str, str]]:
    history_path = history_file or DEFAULT_HISTORY_FILE
    if not history_path.exists():
        return []

    try:
        history = json.loads(history_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    if not history:
        return []

    last_run = history.pop()
    undone_records: list[dict[str, str]] = []

    for record in reversed(last_run):
        dest_path = Path(record["destination"])
        src_path = Path(record["source"])
        if dest_path.exists():
            src_path.parent.mkdir(parents=True, exist_ok=True)
            # Safe collision check for return path
            return_dest = src_path
            if return_dest.exists() and return_dest != dest_path:
                return_dest = resolve_destination_path(src_path.parent, src_path.name)
            shutil.move(dest_path, return_dest)
            undone_records.append({
                "from": str(dest_path),
                "to": str(return_dest)
            })

    history_path.write_text(json.dumps(history, indent=2), encoding="utf-8")
    return undone_records
