import watchtower


class LoggerNameAsStreamHandler(watchtower.CloudWatchLogHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def emit(self, record):
        logger_name = record.name
        self.log_stream_name = logger_name
        super().emit(record)