from satellite.benchmark.chron_benchmark import ChronosBenchmarkBase

class NasaBenchmark(ChronosBenchmarkBase):
    def __init__(self, predictions_csv, channel=None, timestamp_col="timestamp", source_file=None):
        super().__init__(predictions_csv, channel, timestamp_col)
        if source_file:
            self.source_file = source_file  # Sovrascrive se fornito esplicitamente
