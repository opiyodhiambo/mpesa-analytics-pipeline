import logging
import pykka
from service.etl.transform import TransactionTransformer
from service.models.commands import Command

import os
import pandas as pd

from .transformers.temporal_analyzer_actor import TemporalAnalyzerActor
from .transformers.summary_calculator_actor import SummaryCalculatorActor
from .transformers.customer_analyser_actor import CustomerAnalyserActor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class TransformerActor(pykka.ThreadingActor):
    def __init__(self):
        super().__init__()
        self.transaction_transformer = TransactionTransformer()

        logging.info("TransformerActor Spawing child actors ")
        self.temporal_analyzer_actor = TemporalAnalyzerActor.start()
        self.summary_calculator_actor = SummaryCalculatorActor.start()
        self.customer_analyser_actor = CustomerAnalyserActor.start()

    def on_receive(self, message):
        logging.info(f"TransformerActor received command :: {message['command']}")
        try:
            if message.get("command") == Command.TRANSFORM:
                raw_data = message["data"]

                # Parse time
                parsed_data = self.transaction_transformer.parse_time(raw_data)

                logging.info("TransformerActor Sending messages to child actors")
                total_transactions = self.summary_calculator_actor.ask({"command": Command.GET_TOTAL_TRANSACTIONS, "data": parsed_data})
                transaction_volume = self.summary_calculator_actor.ask({"command": Command.COMPUTE_TRANSACTION_VOLUME, "data": parsed_data})
                repeat_customers = self.customer_analyser_actor.ask({"command": Command.GET_REPEAT_CUSTOMERS, "data": parsed_data})
                cltv = self.customer_analyser_actor.ask({"command": Command.COMPUTE_CLTV, "data": repeat_customers})
                clustered_customers = self.customer_analyser_actor.ask({"command": Command.CLUSTER_CUSTOMERS_FCM, "data": cltv})
                timeseries_trends = self.temporal_analyzer_actor.ask({"command": Command.COMPUTE_TIMESERIES, "data": parsed_data})
                activity_heatmap = self.temporal_analyzer_actor.ask({"command": Command.GET_ACTIVITY_HEATMAP, "data": parsed_data})

                return {
                    "total_transactions": total_transactions,
                    "transaction_volume": transaction_volume,
                    "customers": clustered_customers,
                    "timeseries_trends": timeseries_trends,
                    "activity_heatmap": activity_heatmap
                }
        except Exception as e:
            logging.error(f"Error in on_receive: {e}", exc_info=True)
            return {"error": str(e)}
       


