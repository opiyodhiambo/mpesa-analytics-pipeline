import logging
import pykka
from service.models.commands import Command
from service.etl.transform import TransactionTransformer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class TemporalAnalyzerActor(pykka.ThreadingActor):
    """
    Handles
    - Peak activity Heatmap 
    - Compute weekly trend
    """
    def __init__(self):
        super().__init__()
        self.transaction_transformer = TransactionTransformer()

    def on_receive(self, message):
        command = message.get("command")
        data = message.get("data")

        logging.info(f"TemporalAnalyzerActor received command: {command}")

        try:
            if command == Command.COMPUTE_TIMESERIES:
                return self.transaction_transformer.compute_timeseries(data)
            elif command == Command.GET_ACTIVITY_HEATMAP:
                return self.transaction_transformer.get_peak_hours(data)
            else:
                logging.warning(f"Unknown command received: {command}")
                return None
        except Exception as e:
            logging.error(f"Error in on_receive: {e}", exc_info=True)
            return {"error": str(e)}

       