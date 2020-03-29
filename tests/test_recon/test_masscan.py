import tempfile
from pathlib import Path

import luigi

from pipeline.recon import MasscanScan, ParseMasscanOutput

masscan_results = Path(__file__).parent.parent / "data" / "recon-results" / "masscan-results" / "masscan.json"


class TestMasscanScan:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = MasscanScan(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )

    def test_scan_creates_results_dir(self):
        assert self.scan.results_subfolder == self.tmp_path / "masscan-results"

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location

    def test_scan_output_location(self):
        assert self.scan.output().path == str(self.scan.results_subfolder / "masscan.json")


class TestParseMasscanOutput:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = ParseMasscanOutput(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )
        self.scan.input = lambda: luigi.LocalTarget(masscan_results)

    def test_scan_creates_results_dir(self):
        assert self.scan.results_subfolder == self.tmp_path / "masscan-results"

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location

    def test_scan_creates_results(self):
        self.scan.run()
        assert self.scan.output().exists()
