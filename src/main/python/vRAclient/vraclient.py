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


class ResourceNotFound(Exception):
    """ ResourceNotFound
    """
    pass


class MultipleResourcesFound(Exception):
    """ MultipleResourcesFound
    """
    pass


class RequestFailed(Exception):
    """ RequestFailed
    """
    pass


class WaitTimeExceeded(Exception):
    """ WaitTimeExceeded
    """
    pass


class NoPermission(Exception):
    """ OperationsNotFound
    """
    pass


def get_bearer_token(hostname, username, password, tenant):
    """ return bearer token for vRA
    """
    endpoint = 'https://{}/iaas/api/login'.format(hostname)
    logger.debug('obtaining bearer token from {}'.format(endpoint))

    try:
        response = requests.post(
            endpoint,
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            json={
                'username': username,
                'password': password,
                'tenant': tenant
            },
            verify=RESTclient.cabundle)

        refreshtoken = response.json()['refreshToken']
        endpoint2 =  'https://{}/iaas/api/login'.format(hostname)
        data = {
               "refreshToken": refreshtoken }
        
        response1 = requests.post(
            endpoint2,
            data =json.dumps( data )  ,
            headers={
                  'Content-Type': 'application/json'
                 },
            verify= '/etc/ssl/certs/cabundle.pem')
        access_token =  "Bearer " + response1.json()['token']
        return   access_token


    except Exception as exception:
        logger.error('error occurred obtaining bearer token from {} - {}'.format(endpoint, str(exception)))
        raise


def get_id(items, name):
    """ return id of matching item with name
    """
    for item in items:
        if item['name'] == name:
            return item['id']


def get_endpoint_resource_name(endpoint):
    """ return endpoint resource name
    """
    endpoint_split = endpoint.split('/')
    resource = endpoint_split[-1]
    resource_split = resource.split('?')
    return resource_split[0]


def validate_lease_days(days):
    """ validate lease days
    """
    if not days:
        return 180
    if days < 0:
        raise ValueError('lease days must be integer value greater than 0')
    if days > 180:
        raise ValueError('lease days must be integer value less than 180')
    return days


class vRAclient(RESTclient):

    def __init__(self, hostname, **kwargs):
        """ class constructor

            Args:
                hostname (str): hostname of API server
                kwargs (dict): arbritrary number of key word arguments

            Returns:
                vRAclient: instance of vRAclient
        """
        logger.debug('executing vRAclient constructor')

        if 'bearer_token' not in kwargs:
            raise ValueError('a bearer_token must be provided to vRAclient')

        if 'username' not in kwargs:
            raise ValueError('a username must be provided to vRAclient')

        super(vRAclient, self).__init__(hostname, **kwargs)

    def get_endpoint_resource(self, endpoint=None, with_filter=None):
        """ return resource from endpoint using with_filter
        """
        resource_name = get_endpoint_resource_name(endpoint)
        logger.debug('getting "{}" with filter "{}"'.format(resource_name, with_filter))

        filter_p = 'filter={}'.format(with_filter)

        separator = '?'
        if '?' in endpoint:
            separator = '&'

        resource = self.get(
            '{}{}${}'.format(endpoint, separator, filter_p))

        if not resource['content']:
            raise ResourceNotFound(
                'unable to locate "{}" with filter "{}"'.format(resource_name, with_filter))

        if len(resource['content']) > 1:
            raise MultipleResourcesFound(
                'found multiple "{}" with filter "{}"'.format(resource_name, with_filter))

        return resource['content'][0]

    def wait_for_request(self, request_id=None, status='successful', delay=10, timeout=120):
        """ wait for request with request_id to reach state of status

            Arguments:
                request_id (str) - id of the request
                status (str) - state of the request that will result in execution returning to caller
                    default is 'successful'
                delay (int) - number of seconds to wait between checks, default is 10
                timeout (int) - total number of seconds to wait before raising exception, default is 120
            Raises:
                WaitTimeExceeded - if request state doesn't reach status before waiting timeout seconds
                RequestFailed - if request state failed
            Returns:
                request_id (str)
        """
        logger.debug("waiting for status to be '{}' for request id '{}'".format(status, request_id))

        if not request_id:
            return request_id

        total_wait_time = 0
        while True:
            if total_wait_time >= timeout:
                raise WaitTimeExceeded("request id '{}' exceeded timeout of '{}' seconds".format(request_id, timeout))

            request = self.get('/catalog-service/api/consumer/requests/{}'.format(request_id))
            request_state = request['state'].lower()
            logger.debug("state for request id '{}' is '{}'".format(request_id, request_state))

            if request_state == status:
                return request_id
            elif 'failed' in request_state:
                raise RequestFailed("request id '{}' failed with status '{}'".format(request_id, request_state))
            else:
                sleep(delay)
                total_wait_time += delay

    def get_next_page_href(self, links):
        """ get next page href from links
        """
        logger.debug('getting next page href')
        for link in links:
            if link['rel'] == 'next':
                href = link['href']
                href_split = href.split(self.hostname)
                if len(href_split) > 1:
                    return href_split[1]
        else:
            logger.debug('unable to find next page href')

    def get_page(self, endpoint):
        """ get page from endpoint
        """
        while True:
            logger.debug('retrieving page from "{}"'.format(endpoint))
            page = self.get(endpoint)
            if page and page['content']:
                if isinstance(page['content'], list):
                    logger.debug('retrieved {} items from "{}"'.format(len(page['content']), endpoint))
                yield page['content']
                endpoint = self.get_next_page_href(page['links'])
                if not endpoint:
                    logger.debug('no more pages to retrieve - exiting')
                    break
            else:
                logger.debug('no page content detected - exiting')
                break

    def get_resources(self, page_size=None, filter=None):
        """ get resources
        """
        endpoint = "/catalog-service/api/consumer/resources"
        orderby_p = "orderby=dateCreated"
        limit_p = "limit={}".format(page_size if page_size else 1000)
        api_endpoint = "{}?{}&${}".format(endpoint, limit_p, orderby_p)
        if filter:
            filter_p = 'filter={}'.format(filter)
            api_endpoint = "{}&${}".format(api_endpoint, filter_p)

        if page_size:
            logger.debug('retrieving paged resources from "{}"'.format(api_endpoint))
            return self.get_page(api_endpoint)

        logger.debug('retrieving all resources from "{}"'.format(api_endpoint))
        result = []
        for data in self.get_page(api_endpoint):
            result.extend(data)
        logger.debug('retrieved total of {} resources from "{}"'.format(len(result), api_endpoint))
        return result

    def get_reservations(self, page_size=None, filter=None):
        """ get reservations
        """
        endpoint = '/reservation-service/api/reservations'
        orderby_p = 'orderby=id'
        limit_p = "limit={}".format(page_size if page_size else 1000)
        api_endpoint = "{}?{}&${}".format(endpoint, limit_p, orderby_p)
        if filter:
            filter_p = 'filter={}'.format(filter)
            api_endpoint = "{}&${}".format(api_endpoint, filter_p)

        if page_size:
            logger.debug('retrieving paged reservations from "{}"'.format(api_endpoint))
            return self.get_page(api_endpoint)

        logger.debug('retrieving all reservations from "{}"'.format(api_endpoint))
        result = []
        for data in self.get_page(api_endpoint):
            result.extend(data)
        logger.debug('retrieved total of {} reservations from "{}"'.format(len(result), api_endpoint))
        return result

    def get_subtenants(self):
        """ get subtenants

            NOTE: As of release 7.2 use Identity Service https://{{hostname}}/identity/api/tenants/{tenantId}/subtenants
            The endpoint below has been deprecated. However, currently don't have access to consume the identity endpoint above.
        """
        endpoint = '/reservation-service/api/reservations/subtenants'
        orderby = 'orderby=id'
        # NOTE: paging is not supported for this endpoint for some reason
        # only way to get all data is set a large limit
        limit = 1000000
        api_endpoint = '{}?limit={}&${}'.format(endpoint, limit, orderby)

        logger.debug('retrieving all subtenants from "{}"'.format(api_endpoint))
        result = []
        for data in self.get_page(api_endpoint):
            result.extend(data)
        logger.debug('retrieved total of {} subtenants from "{}"'.format(len(result), api_endpoint))
        return result

    def extend_lease_action(self, server_name=None, days=180, wait_for_request=True):
        """ extend lease by days for server_name

            submit CatalogResourceRequest action to Renew Lease

            Arguments:
                server_name (list) - list of server names to renew lease for
                days (int) - amount of days for lease renewal, default is 180
                wait_for_request (bool) - wait for request to succeed, default is True
            Raises:
                ResourceNotFound - if resource with server_name is not found
                MultipleResourcesFound - if multiple resources with name were found
                NoPermission - user does not have permission to execute action against server_name
            Returns:
                -
        """
        lease_days = validate_lease_days(days)

        resource = self.get_endpoint_resource(
            endpoint='/catalog-service/api/consumer/resources?withOperations=true',
            with_filter="tolower(name) eq '{}'".format(server_name.lower()))

        resource_id = resource['id']
        action_id = get_id(resource['operations'], 'Renew Lease')
        if not action_id:
            raise NoPermission(
                'user "{}" does not have permission to execute operation on server "{}"'.format(
                    self.username, server_name))

        template = self.get(
            '/catalog-service/api/consumer/resources/{}/actions/{}/requests/template'.format(
                resource_id, action_id))
        current_time = datetime.utcnow().replace(microsecond=0)
        new_lease_date = (current_time + timedelta(days=days)).isoformat() + '.000Z'

        logger.debug('submitting request to set new lease date of {} for server {}'.format(new_lease_date, server_name))
        template['data']['provider-NewLease'] = new_lease_date
        template['data']['provider-VirtualMachineName'] = server_name
        template['data']['provider-numIncrement'] = lease_days

        response = self.post(
            '/catalog-service/api/consumer/resources/{}/actions/{}/requests'.format(
                resource_id, action_id),
            json=template)

        request = self.get_endpoint_resource(
            endpoint='/catalog-service/api/consumer/requests',
            with_filter="startswith(requestedBy, '{}') and dateCreated gt '{}'".format(
                self.username, current_time.isoformat()))

        request_id = request['id']

        if not wait_for_request:
            return request_id

        return self.wait_for_request(request_id=request_id)

    def extend_lease(self, server_names=None, days=180, wait_for_request=True):
        """ extend lease by days for all server_names

            submit CatalogItemProvisioningRequest to Renew Multiple Leases

            Arguments:
                server_names (list) - list of server names to renew lease for
                days (int) - amount of days for lease renewal, default is 180
                wait_for_request (bool) - wait for request to succeed, default is True
            Raises:
                RequestFailed - if wait_for_request is True and request fails
                WaitTimeExceeded - if wait_for_request is True and wait time for request execeeds timeout
            Returns:
                request id
        """
        lease_days = validate_lease_days(days)

        catalog_item = self.get_endpoint_resource(
            endpoint='/catalog-service/api/consumer/entitledCatalogItems',
            with_filter="tolower(name) eq 'renew multiple leases'")
        catalog_id = catalog_item['catalogItem']['id']

        template = self.get(
            '/catalog-service/api/consumer/entitledCatalogItems/{}/requests/template'.format(catalog_id))
        template['data']['numIncrement'] = lease_days
        template['data']['vmNames'] = server_names

        response = self.post(
            '/catalog-service/api/consumer/entitledCatalogItems/{}/requests'.format(catalog_id),
            json=template)
        request_id = response['id']

        if not wait_for_request:
            return request_id

        return self.wait_for_request(request_id=request_id)

    @classmethod
    def get_vRAclient(cls, hostname=None, username=None, password=None, tenant=None):
        """ return instance of vRAclient

            Args:
                hostname (str): the host for the vRA REST API
                username (str): username
                password (str): password
                tenant (str): tenant

            Returns:
                vRAclient: instance of vRAclient
        """
        if not hostname:
            hostname = os.environ.get('VRA_H')
            if not hostname:
                hostname = VRA_HOST

        if not username:
            username = os.environ.get('VRA_U')
            if not username:
                raise ValueError('username must be specified or set in VRA_U environment variable')

        if not password:
            password = os.environ.get('VRA_P')
            if not password:
                raise ValueError('password must be specified or set in VRA_P environment variable')

        if not tenant:
            tenant = os.environ.get('VRA_T')
            if not tenant:
                tenant = VRA_TENANT

        bearer_token = get_bearer_token(hostname, username, password, tenant)
        return vRAclient(hostname, bearer_token=bearer_token, username=username)
