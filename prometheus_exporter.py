"""
Mercedes Me APIs Promtheus Exporter

Author: Hamidreza Josheghani

For more details about this component, please refer to the documentation at
https://github.com/pyguy/mercedes_me_api/
"""
import argparse
import logging
import os
import sys

from config import MercedesMeConfig
from const import *
from resources import MercedesMeResources

from prometheus_client import start_http_server, Gauge, Enum
import time

# Logger
logging_format = logging.Formatter("[%(levelname)s] [%(asctime)s]: %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging_format)
_LOGGER = logging.getLogger(__name__)
_LOGGER.addHandler(handler)
_LOGGER.setLevel(logging.getLevelName(os.getenv("LOG_LEVEL","INFO")))


class MercedesMeData:
    def __init__(self, polling_interval_seconds=5):
        # Configuration Datas
        self.mercedesConfig = MercedesMeConfig()
        # Resource Data
        self.mercedesResources = MercedesMeResources(self.mercedesConfig)
        self.polling_interval_seconds = polling_interval_seconds

        # Prometheus metrics to collect
        self.metrics = {
            'tanklevelpercent': Gauge('tank_level_percent', 'Liquid fuel tank level (Percent)'),
            'doorstatusfrontleft': Enum('door_status_frontleft', 'Status of the front left door',states=['open','closed']),
            'doorstatusfrontright': Enum('door_status_frontright', 'Status of the front right door',states=['open','closed']),
            'doorstatusrearleft': Enum('door_status_rearleft', 'Status of the rear left door',states=['open','closed']),
            'doorstatusrearright': Enum('door_status_rearright', 'Status of the rear right door',states=['open','closed']),
            'interiorLightsFront': Enum('interior_lights_Front:', 'Status of the interior front light',states=['on','off']),
            'interiorLightsRear': Enum('interior_lights_Rear', 'Status of the interior rear light',states=['on','off']),
            'doorlockstatusvehicle': Gauge('door_lockstatus_vehicle', 'Vehicle lock status'),
            'doorlockstatusdecklid': Enum('door_lockstatus_decklid', 'Lock status of the deck lid',states=['locked','unlocked']),
            'doorlockstatusgas': Enum('door_lockstatus_gas', 'Status of gas tank door lock',states=['locked','unlocked']),
            'positionHeading': Gauge('position_heading', 'Vehicle heading position (Degrees)'),
            'odo': Gauge('odometer', 'Odometer (KM)')
        }
        self.pending_requests = Gauge("app_requests_pending", "Pending requests")
        self.total_uptime = Gauge("app_uptime", "Uptime")
        self.health = Enum("app_health", "Health", states=["healthy", "unhealthy"])

    def run_metrics_loop(self):
        """Metrics fetching loop"""

        while True:
            self.fetch()
            time.sleep(self.polling_interval_seconds)

    def fetch(self):
        """
        Get metrics from application and refresh Prometheus metrics with
        new values.
        """
        self.mercedesResources.ReadResources()
        self.mercedesResources.UpdateResourcesState()
        for res in self.mercedesResources.database:
            if res._valid:
                _LOGGER.debug(f"{res._name}: {res._state}")
                try:
                    if res._state in ['true','false']:
                        if 'lock' in res._name:
                            self.metrics[res._name].state('locked' if res._state == 'false' else 'unlocked')
                        elif 'Light' in res._name:
                            self.metrics[res._name].state('off' if res._state == 'false' else 'on')
                        else:
                            self.metrics[res._name].state('closed' if res._state == 'false' else 'open')
                        continue
                    self.metrics[res._name].set(res._state)
                except KeyError as e:
                    _LOGGER.error(f"Key Error: {e}")
        
########################
# Parse Input
########################
def ParseInput():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--address",
        action="store",
        type=str,
        default=os.getenv("EXPORTER_ADDR", "localhost"),
        help="Prometheus listening address (Default: '' - all interfaces)",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        action="store",
        default=int(os.getenv("EXPORTER_PORT", "8000")),
        help="Prometheus listening port (Default: 8000)",
    )

    return parser.parse_args()


########################
# Main
########################
if __name__ == "__main__":

    # Reading Arguments
    args = ParseInput()

    polling_interval_seconds = int(os.getenv("POLLING_INTERVAL_SECONDS", "5"))

    # Creating Data Structure
    data = MercedesMeData(
        polling_interval_seconds=polling_interval_seconds
    )

    # Reading Configuration
    if not data.mercedesConfig.ReadConfig():
        _LOGGER.error("Error initializing configuration")
        exit(1)

    # Refresh Token
    if not os.path.isfile(TOKEN_FILE) and not data.mercedesConfig.token.RefreshToken():
        _LOGGER.error("Error refreshing token")
        exit(1)

    # Start up the server to expose the metrics.
    _LOGGER.info(f"Starting exporter with address={args.address}:{args.port}")
    start_http_server(port=args.port, addr=args.address)

    data.run_metrics_loop()
