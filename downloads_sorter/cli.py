import argparse
import sys
from pathlib import Path

# Support running directly as a script without PYTHONPATH setup
try:
    from downloads_sorter.sorter import (
        is_ignored_file,
        cluster_files,
        move_files,
        undo_last_run,
        DEFAULT_HISTORY_FILE
    )
except ImportError:
    from sorter import (
        is_ignored_file,
        cluster_files,
        move_files,
        undo_last_run,
        DEFAULT_HISTORY_FILE
    )

def scan_unfoldered_files(directory: Path) -> list[Path]:
    if not directory.exists() or not directory.is_dir():
        return []
    # Only pick files directly in root directory (unfoldered)
    files = [p for p in directory.iterdir() if p.is_file() and not is_ignored_file(p)]
    return sorted(files)

def main():
    parser = argparse.ArgumentParser(
        description="Intelligent Downloads Organizer: Sort unfoldered files into semantic/topic folders."
    )
    parser.add_argument(
        "--target",
        "-t",
        type=Path,
        default=Path.home() / "Downloads",
        help="Target downloads folder (default: ~/Downloads)"
    )
    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Simulate the sorting plan without moving any files."
    )
    parser.add_argument(
        "--undo",
        "-u",
        action="store_true",
        help="Undo the most recent sorting run."
    )

    args = parser.parse_args()

    if args.undo:
        print("Reverting previous sorting run...")
        undone = undo_last_run()
        if not undone:
            print("No previous sort history found to undo.")
            return
        print(f"Successfully restored {len(undone)} file(s):")
        for u in undone:
            print(f"  ↩ {Path(u['from']).name} -> {u['to']}")
        return

    target_dir = args.target.expanduser().resolve()
    if not target_dir.exists():
        print(f"Target directory '{target_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning unfoldered files in: {target_dir}")
    files = scan_unfoldered_files(target_dir)

    if not files:
        print("No unfoldered files found to sort.")
        return

    print(f"Found {len(files)} unfoldered file(s). Clustering into topic/category folders...")
    clusters = cluster_files(files)

    if args.dry_run:
        print("\n[DRY RUN PREVIEW] No files will be moved:")
        for folder, group in clusters.items():
            print(f"\n📂 {folder}/ ({len(group)} file{'s' if len(group) > 1 else ''}):")
            for f in group:
                print(f"   • {f.name}")
        print("\nTo apply these changes, run without --dry-run.")
        return

    # Execute moves
    records = move_files(clusters, base_dir=target_dir)
    print(f"\nSuccessfully organized {len(records)} file(s) into {len(clusters)} folder(s):")
    for folder, group in clusters.items():
        print(f"📂 {folder}/: {len(group)} file(s)")

if __name__ == "__main__":
    main()
