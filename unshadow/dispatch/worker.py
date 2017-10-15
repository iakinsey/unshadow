from unshadow import config
#from unshadow.metric_client import MetricClient
import datetime
import logging
import json
import os
import random
import shutil
import signal
import sys
import time


class Stage(object):
    ignore_outbox = False
    check_delay = 0
    next_check = 0
    on_check = None
    #metrics = None
    #default_metrics = [
    #    "inbox_size"
    #]

    def __init__(
        self,
        inbox,
        outbox,
        inbox_regex,
        max_iterations,
        death_folder,
        max_sleep_time,
        outbox_max_size,
        metric_args,
        **kwargs
    ):
        signal.signal(signal.SIGTERM, self.handle_sigterm)

        if config.LOG_PATH:
            logging.basicConfig(filename=config.LOG_PATH)
        else:
            logging.basicConfig()

        self.log = logging.getLogger()
        self.log.setLevel(config.LOG_LEVEL)

        self.name = self.__class__.__name__
        self.sequence = 0
        self.inbox = inbox
        self.outbox = outbox
        self.outbox_max_size = outbox_max_size
        self.max_iterations = max_iterations
        self.pid = os.getpid()
        self.tasks = []
        self.pending_metrics = []
        self.death_folder = death_folder
        self.inbox_regex = inbox_regex
        self.sleep_time = random.randint(0, max_sleep_time) / 1000.0
        #self.metric_args = metric_args

        self.create_mailboxes()
        #self.setup_metrics()
        #self.declare_metrics()

        self.init(**kwargs)

    def init(self, **kwargs):
        pass

    def setup_metrics(self):
        self.metric_client = MetricClient(**self.metric_args)
        self.declare_metrics()

    def declare_metrics(self):
        additional_metrics = self.metrics or []
        metrics = self.default_metrics + additional_metrics

        self.metric_map = self.metric_client.declare(self.name, metrics)

    def report_metric(self, name, value):
        pass
        #self.pending_metrics.append((
        #    self.metric_map[name],
        #    datetime.datetime.now(),
        #    value
        #))

    def send_metrics(self):
        # TODO should the array be emptied?
        self.metric_client.send(self.pending_metrics)

    def handle_sigterm(self, signum, frame):
        self.kill_process()

    def kill_process(self, code=0):
        try:
            sys.exit(code)
        finally:
            os._exit(code)

    def create_mailboxes(self):
        self.create_mailbox(self.inbox)
        self.create_mailbox(self.outbox)

    def create_mailbox(self, path):
        try:
            if path:
                os.makedirs(path)
        except FileExistsError:
            pass

    def on_message(self, message):
        raise NotImplementedError

    def event_loop(self):
        self.next_check = int(time.time()) + self.check_delay

        for n in range(self.max_iterations):
            self.find_and_process_work()
            now = int(time.time())

            if self.on_check and now >= self.next_check:
                self.on_check()
                self.next_check = int(time.time()) + self.check_delay

    def find_and_process_work(self):
        path = self.claim_file()

        if path:
            message = self.get_work_from_file(path)
            success = self.process_work(message)

            if success:
                os.remove(path)
        else:
            time.sleep(self.sleep_time)

    def process_work(self, message):
        result = None

        try:
            result = self.on_message(message)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.log.exception(e)
        finally:
            if result is not None and self.outbox:
                self.write_result(result)

        return True

    @property
    def outbox_has_space(self):
        if self.ignore_outbox:
            return True

        if self.outbox and self.outbox_max_size:
            return len(os.listdir(self.outbox)) < self.outbox_max_size
        else:
            return True

    @property
    def outbox_space(self):
        if self.outbox and self.outbox_max_size:
            size = self.outbox_max_size - len(os.listdir(self.outbox))

            if size > 0:
                return size
            else:
                return 0

    def claim_specific_file(self, path):
        new_path = "{}.claimed".format(path)

        try:
            shutil.move(path, new_path)
        except (KeyboardInterrupt, SystemExit):
            self.kill_process()
        except:
            return None
        else:
            return new_path

    def claim_file(self):
        if self.outbox_has_space:
            all_files = os.listdir(self.inbox)
            #self.report_metric("inbox_size",  len(all_files))
            paths = filter(self.inbox_regex.match, all_files)

            for file_name in paths:
                path = os.path.join(self.inbox, file_name)
                new_path = self.claim_specific_file(path)

                if new_path:
                    return new_path

    def generate_unique_name(self, prefix=''):
        self.sequence += 1

        return "{}{}_{}_{}_{}".format(
            prefix,
            self.name,
            self.pid,
            int(time.time()),
            self.sequence
        )

    def write_result(self, message, prefix='', path=None):
        if not path:
            name = self.generate_unique_name(prefix)
            path = os.path.join(self.outbox, name)

        with open(path, 'w') as f:
            f.write(json.dumps(message))

    def get_work_from_file(self, path):
        with open(path, 'r') as f:
            contents = json.loads(f.read())

        return contents

    def die(self, success, message=None):
        death_file_path = os.path.join(self.death_folder, str(self.pid))
        self.log.debug("{} about to die".format(self.name))
        #self.send_metrics()

        death_message = {
            'success': success
        }

        if message:
            death_message['message'] = message

        with open(death_file_path, 'w') as f:
            f.write(json.dumps(death_message))

        self.kill_process()

    def start(self):
        self.event_loop()
        self.die(True)
