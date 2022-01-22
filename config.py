"""
Mercedes Me APIs

Author: G. Ravera

For more details about this component, please refer to the documentation at
https://github.com/xraver/mercedes_me_api/
"""
import logging
import os

from const import *
from oauth import MercedesMeOauth
from environs import Env

# Logger
_LOGGER = logging.getLogger(__name__)


class MercedesMeConfig:

    ########################
    # Init
    ########################
    def __init__(self):
        self.env = Env()
        self.config_file = self.env("CONFIG_FILE",default=CONFIG_FILE)
        self.env.read_env(self.config_file, recurse=False)
    
    ########################
    # Read Configuration
    ########################
    def ReadConfig(self):
        # Read Config from file
        if not os.path.isfile(self.config_file):
            _LOGGER.warn(f"Credential File {self.config_file} not found, using environment vars instead")

        # Client ID
        self.client_id = self.env(CONF_CLIENT_ID)
        if not self.client_id:
            _LOGGER.error(f"No {CONF_CLIENT_ID} found in the configuration")
            return False
        
        # Client Secret
        self.client_secret = self.env(CONF_CLIENT_SECRET)
        if not self.client_secret:
            _LOGGER.error(f"No {CONF_CLIENT_SECRET} found in the configuration")
            return False
        
        # Vehicle ID
        self.vin = self.env(CONF_VEHICLE_ID)
        if not self.vin:
            _LOGGER.error(f"No {CONF_VEHICLE_ID} found in the configuration")
            return False
        
        # Enable Resources File (optional)
        self.enable_resources_file = self.env.bool(CONF_ENABLE_RESOURCES_FILE, False)
        
        # Read Token
        self.token = MercedesMeOauth(self.client_id, self.client_secret)
        if not self.token.ReadToken():
            return False
        
        return True
