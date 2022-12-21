
import unittest
from mock import patch
# from mock import mock_open
from mock import call
from mock import Mock

from vRAclient import vRAclient
from vRAclient.vraclient import get_bearer_token
from vRAclient.vraclient import get_id
from vRAclient.vraclient import get_endpoint_resource_name
from vRAclient.vraclient import validate_lease_days
from vRAclient.vraclient import ResourceNotFound
from vRAclient.vraclient import MultipleResourcesFound
from vRAclient.vraclient import WaitTimeExceeded
from vRAclient.vraclient import RequestFailed
from vRAclient.vraclient import NoPermission
from vRAclient.vraclient import VRA_HOST
from vRAclient.vraclient import VRA_TENANT

import sys
import logging
logger = logging.getLogger(__name__)

consoleHandler = logging.StreamHandler(sys.stdout)
logFormatter = logging.Formatter("%(asctime)s %(threadName)s %(name)s [%(funcName)s] %(levelname)s %(message)s")
consoleHandler.setFormatter(logFormatter)
rootLogger = logging.getLogger()
rootLogger.addHandler(consoleHandler)
rootLogger.setLevel(logging.DEBUG)


class TestVraClient(unittest.TestCase):

    def setUp(self):

        pass

    def tearDown(self):

        pass

    @patch('vRAclient.vraclient.requests.post')
    def test__get_bearer_token_ShouldRaiseException_When_RequestsPostException(self, post_patch, *patches):
        post_patch.side_effect = [Exception('some exception during post')]
        with self.assertRaises(Exception):
            get_bearer_token('hostname', 'username', 'password', 'tenant')

    @patch('vRAclient.vraclient.requests.post')
    def test__get_bearer_token_ShouldReturnExpected_When_Called(self, post_patch, *patches):
        response_mock = Mock()
        response_mock.json.return_value = {
            'id': '<bearer token>'
        }
        post_patch.return_value = response_mock
        result = get_bearer_token('hostname', 'username', 'password', 'tenant')
        expected_result = response_mock.json.return_value['id']
        self.assertEqual(result, expected_result)

    @patch('vRAclient.vraclient.os.environ.get', return_value=None)
    @patch('vRAclient.vraclient.get_bearer_token', return_value='--token--')
    @patch('vRAclient.vraclient.vRAclient')
    def test__get_vRAclient_Should_SetDefaultHostname_When_HostnameNotSpecifiedAndNotInEnvironment(self, vraclient_patch, *patches):
        vRAclient.get_vRAclient(username='username', password='password', tenant='tenant')
        self.assertTrue(call(VRA_HOST, bearer_token='--token--', username='username') in vraclient_patch.mock_calls)

    @patch('vRAclient.vraclient.os.environ.get', return_value='value')
    @patch('vRAclient.vraclient.vRAclient')
    @patch('vRAclient.vraclient.get_bearer_token')
    def test__get_vRAclient_Should_GetUsernameFromEnvironment_When_UsernameNotSpecified(self, get_bearer_token_patch, *patches):
        vRAclient.get_vRAclient(hostname='hostname', password='password', tenant='tenant')
        self.assertTrue(call('hostname', 'value', 'password', 'tenant') in get_bearer_token_patch.mock_calls)

    @patch('vRAclient.vraclient.os.environ.get', return_value='value')
    @patch('vRAclient.vraclient.vRAclient')
    @patch('vRAclient.vraclient.get_bearer_token')
    def test__get_vRAclient_Should_GetPasswordFromEnvironment_When_PasswordNotSpecified(self, get_bearer_token_patch, *patches):
        vRAclient.get_vRAclient(hostname='hostname', username='username', tenant='tenant')
        self.assertTrue(call('hostname', 'username', 'value', 'tenant') in get_bearer_token_patch.mock_calls)

    @patch('vRAclient.vraclient.os.environ.get', return_value='value')
    @patch('vRAclient.vraclient.vRAclient')
    @patch('vRAclient.vraclient.get_bearer_token')
    def test__get_vRAclient_Should_GetTenantFromEnvironment_When_TenantNotSpecified(self, get_bearer_token_patch, *patches):
        vRAclient.get_vRAclient(hostname='hostname', username='username', password='password')
        self.assertTrue(call('hostname', 'username', 'password', 'value') in get_bearer_token_patch.mock_calls)

    @patch('vRAclient.vraclient.os.environ.get', return_value=None)
    def test__get_vRAclient_Should_RaiseValueError_When_UsernameNotSpecifiedAndNotInEnvironment(self, *patches):
        with self.assertRaises(ValueError):
            vRAclient.get_vRAclient(hostname='hostname', password='password', tenant='tenant')

    @patch('vRAclient.vraclient.os.environ.get', return_value=None)
    def test__get_vRAclient_Should_RaiseValueError_When_PasswordNotSpecifiedAndNotInEnvironment(self, *patches):
        with self.assertRaises(ValueError):
            vRAclient.get_vRAclient(hostname='hostname', username='username', tenant='tenant')

    @patch('vRAclient.vraclient.os.environ.get', return_value=None)
    @patch('vRAclient.vraclient.get_bearer_token')
    def test__get_vRAclient_Should_SetDefaultTenant_When_TenantNotSpecifiedAndNotInEnvironment(self, get_bearer_token_patch, *patches):
        vRAclient.get_vRAclient(hostname='hostname', username='username', password='password')
        self.assertTrue(call('hostname', 'username', 'password', VRA_TENANT) in get_bearer_token_patch.mock_calls)

    def test__init_Should_RaiseValueError_When_BearerTokenNotSpecified(self, *patches):
        with self.assertRaises(ValueError):
            vRAclient('hostname')

    def test__init_Should_RaiseValueError_When_UsernameNotSpecified(self, *patches):
        with self.assertRaises(ValueError):
            vRAclient('hostname', bearer_token='--token--')

    def test__get_next_page_href_Should_ReturnNextHref_When_NextHrefInLinks(self, *patches):
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        links = [{'@type': 'link', 'rel': 'next', 'href': 'https://enterprisecloud.intel.com/catalog-service/api/consumer/resources?page=2&limit=20&$orderby=dateCreated'}]
        result = client.get_next_page_href(links)
        expected_result = '/catalog-service/api/consumer/resources?page=2&limit=20&$orderby=dateCreated'
        self.assertEqual(result, expected_result)

    def test__get_next_page_href_Should_ReturnNone_When_Called(self, *patches):
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        links = [{'@type': 'link', 'rel': 'prev', 'href': 'https://enterprisecloud.intel.com/catalog-service/api/consumer/resources?page=2&limit=20&$orderby=dateCreated'}]
        result = client.get_next_page_href(links)
        self.assertIsNone(result)

    @patch('vRAclient.vRAclient.get')
    @patch('vRAclient.vRAclient.get_next_page_href')
    def test__get_page_Should_ReturnGenerator_When_Called(self, get_next_page_href_patch, get_patch, *patches):
        get_next_page_href_patch.side_effect = [
            'link-page2',
            'link-page3',
            None
        ]
        get_patch.side_effect = [
            {'content': ['content-page1'], 'links': []},
            {'content': ['content-page2'], 'links': []},
            {'content': ['content-page3'], 'links': []},
            {'content': [], 'links': []}
        ]

        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        result = client.get_page('page1')
        self.assertEqual(next(result), (['content-page1']))
        self.assertEqual(next(result), (['content-page2']))
        self.assertEqual(next(result), (['content-page3']))
        with self.assertRaises(StopIteration):
            next(result)

    @patch('vRAclient.vRAclient.get')
    def test__get_page_Should_Return_When_NoPageContent(self, get_patch, *patches):
        get_patch.return_value = {'content': [], 'links': []}

        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        result = client.get_page('page1')
        with self.assertRaises(StopIteration):
            next(result)

    @patch('vRAclient.vRAclient.get_page')
    def test__get_resources_Should_ReturnExpected_When_Called(self, get_page_patch, *patches):
        get_page_patch.return_value = [
            ['p1', 'p2'],
            ['p3', 'p4'],
            ['p5']
        ]
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        result = client.get_resources()
        expected_result = ['p1', 'p2', 'p3', 'p4', 'p5']
        self.assertEqual(result, expected_result)

    @patch('vRAclient.vRAclient.get_page')
    def test__get_resources_Should_CallGetPage_When_FilterSpecified(self, get_page_patch, *patches):
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        client.get_resources(filter="resourceType/id eq 'Infrastructure.Virtual'")
        self.assertTrue(call("/catalog-service/api/consumer/resources?limit=1000&$orderby=dateCreated&$filter=resourceType/id eq 'Infrastructure.Virtual'") in get_page_patch.mock_calls)

    @patch('vRAclient.vRAclient.get_page')
    def test__get_resources_Should_ReturnPage_When_PageSizeSpecified(self, get_page_patch, *patches):
        get_page_patch.return_value = [['p1', 'p2']]
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        result = client.get_resources(page_size=10)
        expected_result = get_page_patch.return_value
        self.assertEqual(result, expected_result)

    @patch('vRAclient.vRAclient.get_page')
    def test__get_resources_Should_CallGetPage_When_PageSizeSpecified(self, get_page_patch, *patches):
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        client.get_resources(page_size=10)
        self.assertTrue(call("/catalog-service/api/consumer/resources?limit=10&$orderby=dateCreated") in get_page_patch.mock_calls)

    @patch('vRAclient.vRAclient.get_page')
    def test__get_reservations_Should_ReturnExpected_When_Called(self, get_page_patch, *patches):
        get_page_patch.return_value = [
            ['p1', 'p2'],
            ['p3', 'p4'],
            ['p5']
        ]
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        result = client.get_reservations(filter='enabled eq true')
        expected_result = ['p1', 'p2', 'p3', 'p4', 'p5']
        self.assertEqual(result, expected_result)

    @patch('vRAclient.vRAclient.get_page')
    def test__get_reservations_Should_CallGetPage_When_FilterSpecified(self, get_page_patch, *patches):
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        client.get_reservations(filter='enabled eq true')
        self.assertTrue(call('/reservation-service/api/reservations?limit=1000&$orderby=id&$filter=enabled eq true') in get_page_patch.mock_calls)

    @patch('vRAclient.vRAclient.get_page')
    def test__get_reservations_Should_ReturnPage_When_PageSizeSpecified(self, get_page_patch, *patches):
        get_page_patch.return_value = [['p1', 'p2']]
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        result = client.get_reservations(page_size=10)
        expected_result = get_page_patch.return_value
        self.assertEqual(result, expected_result)

    @patch('vRAclient.vRAclient.get_page')
    def test__get_reservations_Should_CallGetPage_When_PageSizeSpecified(self, get_page_patch, *patches):
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        client.get_reservations(page_size=10)
        self.assertTrue(call('/reservation-service/api/reservations?limit=10&$orderby=id') in get_page_patch.mock_calls)

    @patch('vRAclient.vRAclient.get_page')
    def test__get_subtenants_Should_ReturnExpected_When_Called(self, get_page_patch, *patches):
        get_page_patch.return_value = [
            ['p1', 'p2'],
            ['p3', 'p4'],
            ['p5']
        ]
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        result = client.get_subtenants()
        expected_result = ['p1', 'p2', 'p3', 'p4', 'p5']
        self.assertEqual(result, expected_result)

    def test__get_id_Should_ReturnExpected_When_Match(self, *patches):
        items = [
            {
                'id': '123',
                'name': 'Heroes'
            }, {
                'id': '234',
                'name': 'Caifanes'
            }, {
                'id': '345',
                'name': 'Fobia'
            }
        ]
        result = get_id(items, 'Fobia')
        expected_result = '345'
        self.assertEqual(result, expected_result)

    def test__get_id_Should_ReturnNone_When_Match(self, *patches):
        items = [
            {
                'id': '123',
                'name': 'Heroes'
            }, {
                'id': '234',
                'name': 'Caifanes'
            }, {
                'id': '345',
                'name': 'Fobia'
            }
        ]
        result = get_id(items, 'Zoe')
        self.assertIsNone(result)

    def test__get_endpoint_resource_name_Should_ReturnExpected_When_Argument(self, *patches):
        result = get_endpoint_resource_name('/catalog-service/api/consumer/resources?withOperations=true')
        expected_result = 'resources'
        self.assertEqual(result, expected_result)

    def test__get_endpoint_resource_name_Should_ReturnExpected_When_NoArgument(self, *patches):
        result = get_endpoint_resource_name('/catalog-service/api/consumer/entitledCatalogItems')
        expected_result = 'entitledCatalogItems'
        self.assertEqual(result, expected_result)

    def test__validate_lease_days_Should_ReturnExpected_When_NoDays(self, *patches):

        self.assertEqual(validate_lease_days(None), 180)

    def test__validate_lease_days_Should_RaiseValueError_When_DaysLessThanZero(self, *patches):

        with self.assertRaises(ValueError):
            validate_lease_days(-1)

    def test__validate_lease_days_Should_RaiseValueError_When_DaysGreaterThan181(self, *patches):

        with self.assertRaises(ValueError):
            validate_lease_days(181)

    def test__validate_lease_days_Should_ReturnExpected_When_DaysValid(self, *patches):

        self.assertEqual(validate_lease_days(30), 30)

    @patch('vRAclient.vraclient.get_endpoint_resource_name', return_value='resources')
    @patch('vRAclient.vRAclient.get')
    def test__get_endpoint_resource_Should_RaiseResourceNotFound_When_NoResourcesFound(self, get_patch, *patches):
        get_patch.return_value = {
            'content': []
        }
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        with self.assertRaises(ResourceNotFound):
            client.get_endpoint_resource(
                endpoint='/catalog-service/api/consumer/resources?withOperations=true',
                with_filter="tolower(name) eq 'server123'")

    @patch('vRAclient.vraclient.get_endpoint_resource_name', return_value='resources')
    @patch('vRAclient.vRAclient.get')
    def test__get_endpoint_resource_Should_RaiseMultipleResourcesFound_When_MultipleResourcesFound(self, get_patch, *patches):
        get_patch.return_value = {
            'content': [
                {'id': '123'},
                {'id': '234'}
            ]
        }
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        with self.assertRaises(MultipleResourcesFound):
            client.get_endpoint_resource(
                endpoint='/catalog-service/api/consumer/resources?withOperations=true',
                with_filter="tolower(name) eq 'server123'")

    @patch('vRAclient.vraclient.get_endpoint_resource_name', return_value='resources')
    @patch('vRAclient.vRAclient.get')
    def test__get_endpoint_resources_Should_ReturnExpected_When_Called(self, get_patch, *patches):
        get_patch.return_value = {
            'content': [
                {'id': '123', 'name': 'Caifanes'}
            ]
        }
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        result = client.get_endpoint_resource(
            endpoint='/catalog-service/api/consumer/resources?withOperations=true',
            with_filter="tolower(name) eq 'server123'")
        expected_result = {'id': '123', 'name': 'Caifanes'}
        self.assertEqual(result, expected_result)
        get_patch.assert_called_once_with("/catalog-service/api/consumer/resources?withOperations=true&$filter=tolower(name) eq 'server123'")

    def test__wait_for_request_Should_ReturnNone_When_RequestIdNone(self, *patches):
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        result = client.wait_for_request(request_id=None)
        self.assertIsNone(result)

    @patch('vRAclient.vraclient.sleep')
    @patch('vRAclient.vRAclient.get')
    def test__wait_for_request_Should_RaiseWaitTimeExceeded_When_WaitTimeExceeded(self, get_patch, *patches):
        get_patch.side_effect = [
            {'state': 'submitted'},
            {'state': 'pre_approved'},
            {'state': 'pending'},
            {'state': 'running'},
            {'state': 'running'},
            {'state': 'running'},
            {'state': 'running'},
            {'state': 'running'},
        ]
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        with self.assertRaises(WaitTimeExceeded):
            client.wait_for_request(request_id='123', delay=10, timeout=60)

    @patch('vRAclient.vraclient.sleep')
    @patch('vRAclient.vRAclient.get')
    def test__wait_for_request_Should_RaiseRequestFailed_When_RequestStateFailed(self, get_patch, *patches):
        get_patch.side_effect = [
            {'state': 'submitted'},
            {'state': 'pre_approved'},
            {'state': 'pending'},
            {'state': 'running'},
            {'state': 'running'},
            {'state': 'running'},
            {'state': 'running'},
            {'state': 'failed'},
        ]
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        with self.assertRaises(RequestFailed):
            client.wait_for_request(request_id='123')

    @patch('vRAclient.vraclient.sleep')
    @patch('vRAclient.vRAclient.get')
    def test__wait_for_request_Should_ReturnRequestId_When_RequestStateSuccessful(self, get_patch, *patches):
        get_patch.side_effect = [
            {'state': 'submitted'},
            {'state': 'pre_approved'},
            {'state': 'pending'},
            {'state': 'running'},
            {'state': 'running'},
            {'state': 'running'},
            {'state': 'running'},
            {'state': 'successful'},
        ]
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        result = client.wait_for_request(request_id='123')
        expected_result = '123'
        self.assertEqual(result, expected_result)

    @patch('vRAclient.vraclient.validate_lease_days', return_value=180)
    @patch('vRAclient.vraclient.get_id', return_value=None)
    @patch('vRAclient.vRAclient.get_endpoint_resource')
    @patch('vRAclient.vraclient.get_id')
    def test__extend_lease_action_Should_RaiseNoPermission_When_ResourceHasNoOperations(self, get_endpoint_resource_patch, *patches):
        get_endpoint_resource_patch.return_value = {
            'id': '123',
            'operations': []
        }
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        with self.assertRaises(NoPermission):
            client.extend_lease_action(server_name='server123')

    @patch('vRAclient.vraclient.validate_lease_days', return_value=180)
    @patch('vRAclient.vraclient.get_id', return_value='001')
    @patch('vRAclient.vRAclient.post')
    @patch('vRAclient.vRAclient.wait_for_request')
    @patch('vRAclient.vRAclient.get')
    @patch('vRAclient.vRAclient.get_endpoint_resource')
    def test__extend_lease_action_Should_CallWaitForRequest_When_WaitForRequestTrue(self, get_endpoint_resource_patch, get_patch, wait_for_request_patch, *patches):
        get_endpoint_resource_patch.side_effect = [
            {
                'id': '123',
                'operations': []
            }, {
                'id': '890'
            }
        ]
        get_patch.return_value = {
            'data': {
                'provider-NewLease': '',
                'provider-VirtualMachinename': '',
                'provider-numIncrement': ''
            }
        }
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        result = client.extend_lease_action(server_name='server123')
        wait_for_request_patch.assert_called_once_with(request_id='890')
        self.assertEqual(result, wait_for_request_patch.return_value)

    @patch('vRAclient.vraclient.validate_lease_days', return_value=180)
    @patch('vRAclient.vraclient.get_id', return_value='001')
    @patch('vRAclient.vRAclient.post')
    @patch('vRAclient.vRAclient.get')
    @patch('vRAclient.vRAclient.get_endpoint_resource')
    def test__extend_lease_action_Should_ReturnRequestId_When_WaitForRequestFalse(self, get_endpoint_resource_patch, get_patch, *patches):
        get_endpoint_resource_patch.side_effect = [
            {
                'id': '123',
                'operations': []
            }, {
                'id': '890'
            }
        ]
        get_patch.return_value = {
            'data': {
                'provider-NewLease': '',
                'provider-VirtualMachinename': '',
                'provider-numIncrement': ''
            }
        }
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        result = client.extend_lease_action(server_name='server123', wait_for_request=False)
        self.assertEqual(result, '890')

    @patch('vRAclient.vraclient.validate_lease_days', return_value=180)
    @patch('vRAclient.vRAclient.wait_for_request')
    @patch('vRAclient.vRAclient.post')
    @patch('vRAclient.vRAclient.get')
    @patch('vRAclient.vRAclient.get_endpoint_resource')
    def test__extend_lease_Should_CallWaitForRequest_When_WaitForRequestTrue(self, get_endpoint_resource_patch, get_patch, post_patch, wait_for_request_patch, *patches):
        get_endpoint_resource_patch.return_value = {
            'catalogItem': {
                'id': '123456'
            }
        }
        get_patch.return_value = {
            'data': {
                'numIncrement': '',
                'vmNames': ''
            }
        }
        post_patch.return_value = {
            'id': '<--request_id-->'
        }
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        result = client.extend_lease(server_names=['server123', 'server234'])
        wait_for_request_patch.assert_called_once_with(request_id='<--request_id-->')
        self.assertEqual(result, wait_for_request_patch.return_value)

    @patch('vRAclient.vraclient.validate_lease_days', return_value=180)
    @patch('vRAclient.vRAclient.post')
    @patch('vRAclient.vRAclient.get')
    @patch('vRAclient.vRAclient.get_endpoint_resource')
    def test__extend_lease_Should_ReturnRequestId_When_WaitForRequestFalse(self, get_endpoint_resource_patch, get_patch, post_patch, *patches):
        get_endpoint_resource_patch.return_value = {
            'catalogItem': {
                'id': '123456'
            }
        }
        get_patch.return_value = {
            'data': {
                'numIncrement': '',
                'vmNames': ''
            }
        }
        post_patch.return_value = {
            'id': '<--request_id-->'
        }
        client = vRAclient('enterprisecloud.intel.com', bearer_token='--token--', username='ad_lereyes1')
        result = client.extend_lease(server_names=['server123', 'server234'], wait_for_request=False)
        self.assertEqual(result, '<--request_id-->')
