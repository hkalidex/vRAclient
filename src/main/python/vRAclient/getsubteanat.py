import os
import json
from time import sleep
from datetime import datetime
from datetime import timedelta
import requests
from retrying import retry
from RESTclient import RESTclient

import logging
logger = logging.getLogger(__name__)

logging.getLogger('urllib3.connectionpool').setLevel(logging.CRITICAL)


VRA_HOST = 'vradev.fms07vraapp101.fm.intel.com'
VRA_TENANT = 'VRADEV'

def get_subtenants_new(access_token):
url = 'https://{}/iaas/api/projects'.format(hostname)


headers = {
       'accept': "application/json",
       'authorization': access_token
       }
api_output = requests.request("GET",url, headers=headers,  verify=RESTclient.cabundle').json()['content']
return api_output
