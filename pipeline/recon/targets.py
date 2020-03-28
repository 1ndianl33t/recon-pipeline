import ipaddress

import luigi
from luigi.contrib.sqla import SQLAlchemyTarget

from .config import defaults
from ..models import Target, DBManager


class TargetList(luigi.ExternalTask):
    """ External task.  ``TARGET_FILE`` is generated manually by the user from target's scope.

    Args:
        results_dir: specifies the directory on disk to which all Task results are written
        db_location: specifies the path to the database used for storing results
    """

    target_file = luigi.Parameter()
    db_location = luigi.Parameter()
    results_dir = luigi.Parameter(default=defaults.get("results-dir"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_mgr = DBManager(db_location=self.db_location)

    def output(self):
        """ Returns the target output for this task. target_file.ips || target_file.domains

        In this case, it expects a file to be present in the local filesystem.
        By convention, TARGET_NAME should be something like tesla or some other
        target identifier.  The returned target output will either be target_file.ips
        or target_file.domains, depending on what is found on the first line of the file.

        Example:  Given a TARGET_FILE of tesla where the first line is tesla.com; tesla.domains
        is written to disk.

        Returns:
            luigi.local_target.LocalTarget
        """
        # normally the call is self.output().touch(), however, that causes recursion here, so we grab the target now
        # in order to call .touch() on it later and eventually return it
        db_target = SQLAlchemyTarget(
            connection_string=self.db_mgr.connection_string, target_table="target", update_id=self.task_id
        )

        with open(self.target_file) as f:
            for line in f.readlines():
                line = line.strip()
                try:
                    ipaddress.ip_interface(line)  # is it a valid ip/network?
                except ValueError:
                    # exception thrown by ip_interface; domain name assumed
                    tgt = self.db_mgr.get_or_create(Target, hostname=line, is_web=True)
                else:
                    # no exception thrown; ip address found
                    tgt = self.db_mgr.get_or_create(Target)

                    tgt = self.db_mgr.add_ipv4_or_v6_address_to_target(tgt, line)

                self.db_mgr.add(tgt)
                db_target.touch()

            self.db_mgr.close()

        return db_target
