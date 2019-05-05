from ansible.plugins.callback import CallbackBase
from collections import defaultdict
class PlaybookResultsCollector(CallbackBase):
    # CALLBACK_VERSION = 2.0
    """A callback plugin used for performing an action as results come in
    """
    def __init__(self, **meta):
        """Constructor of `PlaybookResultsCollector` class.
        Args:
            **meta: metadata information as keyword arguments.

        Returns:
            None
        """
        super(PlaybookResultsCollector, self).__init__()

        self.task_ok = defaultdict(list)
        self.task_skipped = defaultdict(list)
        self.task_failed = defaultdict(list)
        self.task_status = defaultdict(list)
        self.task_unreachable = defaultdict(list)
        self.task_changed = defaultdict(list)

    def v2_runner_on_ok(self, result, *args, **kwargs):
        """this method gets called when a task is `succeeded`"""
        self.task_ok[result._host.get_name()].append(result)

    def v2_runner_on_failed(self, result, *args, **kwargs):
        """this method gets called when a task is `failed`"""
        self.task_failed[result._host.get_name()].append(result)

    def v2_runner_on_unreachable(self, result):
        """this method gets called when a host is `unreachable`"""
        self.task_unreachable[result._host.get_name()].append(result)

    def v2_runner_on_skipped(self, result):
        """this method gets called when a task is `skipped`"""
        self.task_skipped[result._host.get_name()].append(result)

    def v2_runner_on_changed(self, result):
        """this method gets called when a task has done some `changes`
        to the device.
        """
        self.task_changed[result._host.get_name()].append(result)

    def v2_playbook_on_stats(self, stats):
        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)
            self.task_status[h] = {
                "ok": t["ok"],
                "changed": t["changed"],
                "unreachable": t["unreachable"],
                "skipped": t["skipped"],
                "failed": t["failures"],
            }

