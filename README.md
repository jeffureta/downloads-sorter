# downloads-sorter

An intelligent, zero-cost, local Python utility that organizes unfoldered files in `~/Downloads` into semantic project/topic folders and general categories with collision avoidance and instant undo capabilities.

## Features

- **Root Unfoldered Targeting**: Scans and organizes only loose files in `~/Downloads`. Leaves existing subdirectories completely intact.
- **Temporary File Protection**: Automatically ignores active browser downloads (`.crdownload`, `.download`, `.part`, `.tmp`).
- **Semantic & Topic Clustering**:
  - Automatically identifies projects by shared prefix tokens (e.g. `Project_X_specs.pdf` and `Project_X_design.png` &rarr; `Project X/`).
  - Signature and extension rules for `Installers & Apps`, `Financial & Receipts`, `Screenshots`, `Reading & Publications`, `Documents`, `Media`, `Code & Data`, etc.
- **Safe Collision Handling**: If a destination file already exists, appends numeric suffixes (`file (1).pdf`) rather than overwriting.
- **Instant Rollback / Undo**: Tracks batch operations in `~/.downloads_sorter_history.json`. Revert the last run at any time.

## Usage

### 1. Preview changes (Dry Run)
```bash
python3 downloads_sorter/cli.py --dry-run
```

### 2. Organize Downloads
```bash
python3 downloads_sorter/cli.py
```

### 3. Revert Last Run
```bash
python3 downloads_sorter/cli.py --undo
```

### 4. Custom Target Directory
```bash
python3 downloads_sorter/cli.py --target /path/to/directory
```

## Running Tests

```bash
python3 -m unittest discover tests
```

## License

MIT
