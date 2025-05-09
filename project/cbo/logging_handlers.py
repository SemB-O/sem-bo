import watchtower

class LoggerNameStreamHandler(watchtower.CloudWatchLogHandler):
    def emit(self, record):
        self.stream_name = record.name 
        super().emit(record)
