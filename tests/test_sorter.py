import unittest
import tempfile
import shutil
from pathlib import Path
from downloads_sorter.sorter import (
    is_ignored_file,
    categorize_file,
    cluster_files,
    resolve_destination_path,
    move_files,
    undo_last_run,
)

class TestDownloadsSorter(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.history_file = self.test_dir / "history.json"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_is_ignored_file(self):
        self.assertTrue(is_ignored_file(Path("something.crdownload")))
        self.assertTrue(is_ignored_file(Path("file.download")))
        self.assertTrue(is_ignored_file(Path("archive.part")))
        self.assertTrue(is_ignored_file(Path(".DS_Store")))
        self.assertTrue(is_ignored_file(Path(".localized")))
        self.assertFalse(is_ignored_file(Path("normal_document.pdf")))

    def test_categorize_by_known_rules(self):
        self.assertEqual(categorize_file(Path("docker-desktop.dmg")), "Installers & Apps")
        self.assertEqual(categorize_file(Path("Screenshot 2026-11-01 at 10.00.png")), "Screenshots")
        self.assertEqual(categorize_file(Path("Invoice_March_2026.pdf")), "Financial & Receipts")
        self.assertEqual(categorize_file(Path("novel.epub")), "Reading & Publications")

    def test_cluster_files_semantic(self):
        files = [
            Path("project_apollo_specs.pdf"),
            Path("project_apollo_architecture.docx"),
            Path("docker.dmg"),
            Path("random_notes.txt"),
        ]
        clusters = cluster_files(files)
        self.assertIn("Project Apollo", clusters)
        self.assertEqual(
            set(clusters["Project Apollo"]),
            {Path("project_apollo_specs.pdf"), Path("project_apollo_architecture.docx")}
        )
        self.assertEqual(clusters["Installers & Apps"], [Path("docker.dmg")])
        self.assertEqual(clusters["Documents"], [Path("random_notes.txt")])

    def test_collision_resolution(self):
        target_folder = self.test_dir / "Documents"
        target_folder.mkdir(parents=True)
        (target_folder / "report.pdf").touch()

        dest = resolve_destination_path(target_folder, "report.pdf")
        self.assertEqual(dest.name, "report (1).pdf")

        # Second collision
        (target_folder / "report (1).pdf").touch()
        dest2 = resolve_destination_path(target_folder, "report.pdf")
        self.assertEqual(dest2.name, "report (2).pdf")

    def test_move_files_and_undo(self):
        f1 = self.test_dir / "test_doc.pdf"
        f1.write_text("hello doc")
        f2 = self.test_dir / "my_app.dmg"
        f2.write_text("hello dmg")

        clusters = {
            "Documents": [f1],
            "Installers & Apps": [f2],
        }

        # Execute move
        moved_records = move_files(clusters, base_dir=self.test_dir, history_file=self.history_file)
        self.assertEqual(len(moved_records), 2)
        self.assertTrue((self.test_dir / "Documents" / "test_doc.pdf").exists())
        self.assertTrue((self.test_dir / "Installers & Apps" / "my_app.dmg").exists())
        self.assertFalse(f1.exists())
        self.assertFalse(f2.exists())

        # Test Undo
        undone_records = undo_last_run(history_file=self.history_file)
        self.assertEqual(len(undone_records), 2)
        self.assertTrue(f1.exists())
        self.assertTrue(f2.exists())
        self.assertFalse((self.test_dir / "Documents" / "test_doc.pdf").exists())

if __name__ == '__main__':
    unittest.main()
