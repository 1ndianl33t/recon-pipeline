import subprocess
from pathlib import Path

import luigi
from luigi.util import inherits

from .targets import GatherWebTargets
from ..config import tool_paths, defaults


@inherits(GatherWebTargets)
class AquatoneScan(luigi.Task):
    """ Screenshot all web targets and generate HTML report.

    Install:
        .. code-block:: console

            mkdir /tmp/aquatone
            wget -q https://github.com/michenriksen/aquatone/releases/download/v1.7.0/aquatone_linux_amd64_1.7.0.zip -O /tmp/aquatone/aquatone.zip
            unzip /tmp/aquatone/aquatone.zip -d /tmp/aquatone
            sudo mv /tmp/aquatone/aquatone /usr/local/bin/aquatone
            rm -rf /tmp/aquatone

    Basic Example:
        ``aquatone`` commands are structured like the example below.

        ``cat webtargets.tesla.txt | /opt/aquatone -scan-timeout 900 -threads 20``

    Luigi Example:
        .. code-block:: python

            PYTHONPATH=$(pwd) luigi --local-scheduler --module recon.web.aquatone AquatoneScan --target-file tesla --top-ports 1000

    Args:
        threads: number of threads for parallel aquatone command execution
        scan_timeout: timeout in miliseconds for aquatone port scans
        exempt_list: Path to a file providing blacklisted subdomains, one per line. *Optional by upstream Task*
        top_ports: Scan top N most popular ports *Required by upstream Task*
        ports: specifies the port(s) to be scanned *Required by upstream Task*
        interface: use the named raw network interface, such as "eth0" *Required by upstream Task*
        rate: desired rate for transmitting packets (packets per second) *Required by upstream Task*
        target_file: specifies the file on disk containing a list of ips or domains *Required by upstream Task*
        results_dir: specifes the directory on disk to which all Task results are written *Required by upstream Task*
    """

    threads = luigi.Parameter(default=defaults.get("threads", ""))
    scan_timeout = luigi.Parameter(default=defaults.get("aquatone-scan-timeout", ""))

    def requires(self):
        """ AquatoneScan depends on GatherWebTargets to run.

        GatherWebTargets accepts exempt_list and expects rate, target_file, interface,
                         and either ports or top_ports as parameters

        Returns:
            luigi.Task - GatherWebTargets
        """
        args = {
            "results_dir": self.results_dir,
            "rate": self.rate,
            "target_file": self.target_file,
            "top_ports": self.top_ports,
            "interface": self.interface,
            "ports": self.ports,
            "exempt_list": self.exempt_list,
        }
        return GatherWebTargets(**args)

    def output(self):
        """ Returns the target output for this task.

        Naming convention for the output file is amass.TARGET_FILE.json.

        Returns:
            luigi.local_target.LocalTarget
        """
        results_subfolder = Path(self.results_dir) / "aquatone-results"

        return luigi.LocalTarget(results_subfolder.resolve())

    def run(self):
        """ Defines the options/arguments sent to aquatone after processing.

        cat webtargets.tesla.txt | /opt/aquatone -scan-timeout 900 -threads 20

        Returns:
            list: list of options/arguments, beginning with the name of the executable to run
        """
        Path(self.output().path).mkdir(parents=True, exist_ok=True)

        command = [
            tool_paths.get("aquatone"),
            "-scan-timeout",
            self.scan_timeout,
            "-threads",
            self.threads,
            "-silent",
            "-out",
            self.output().path,
        ]

        with self.input().open() as target_list:
            subprocess.run(command, stdin=target_list)
