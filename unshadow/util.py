

class MetricClient(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server = "http://{}:{}".format(self.host, self.port)
        self.send_metrics_url = "{}/metric/add_data".format(self.server)
        self.declare_metric_url = "{}/metric/declare".format(self.server)
        self.opener = build_opener()
        self.opener.addheaders = [
            ("Content-Type", "application/json")        
        ]

    def send_metrics(self, metrics):
        self.opener.open()

    def declare_metric(self):
        pass
