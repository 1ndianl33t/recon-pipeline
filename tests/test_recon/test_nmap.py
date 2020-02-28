from pathlib import Path

from pipeline.recon import ThreadedNmapScan, SearchsploitScan

import luigi

from ..utils import is_kali

tfp = "../data/bitdiscovery"
tf = Path(tfp).stem
el = "../data/blacklist"
rd = "../data/recon-results"

nmap_results = Path(__file__).parent.parent / "data" / "recon-results" / "nmap-results"


def test_nmap_output_location(tmp_path):
    tns = ThreadedNmapScan(
        target_file=tf,
        exempt_list=el,
        results_dir=str(tmp_path),
        top_ports=100,
        db_location=str(Path(tmp_path) / "testing.sqlite"),
    )

    assert tns.output().path == str(Path(tmp_path) / "nmap-results")


def test_searchsploit_output_location(tmp_path):
    sss = SearchsploitScan(
        target_file=tf,
        exempt_list=el,
        results_dir=str(tmp_path),
        top_ports=100,
        db_location=str(Path(tmp_path) / "testing.sqlite"),
    )

    assert sss.output().path == str(tmp_path / "testing.sqlite")


def test_searchsploit_produces_results(tmp_path):
    sss = SearchsploitScan(
        target_file=tf,
        exempt_list=el,
        results_dir=str(tmp_path),
        top_ports=100,
        db_location=str(Path(tmp_path) / "testing.sqlite"),
    )

    sss.input = lambda: luigi.LocalTarget(nmap_results)

    if not is_kali():
        return True

    sss.run()

    assert len([x for x in Path(sss.output().path).glob("searchsploit*.txt")]) > 0
