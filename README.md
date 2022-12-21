![alt text](https://ubit-teamcity-iag.intel.com/app/rest/builds/buildType:%28id:HostingSDI_CloudInfrastructureProvisioning_vRAclient%29/statusIcon "TC Build Status Icon")


## vRAclient
A Python client for vRA REST API

Tested with vRA 7.4, API reference:
https://code.vmware.com/apis/370/vra-catalog?p=vrealize-automation#


#### Usage
```bash
export VRA_U="<USER>"
export VRA_P="<PASSWORD>"

python
>>> from vRAclient import vRAclient
>>> client = vRAclient.get_vRAclient()
>>>
>>> resources = client.get_resources()
>>> print(len(resources))
>>>
>>> reservations = client.get_reservations()
>>> print(len(reservations))
>>>
>>> subtenants = client.get_subtenants()
>>> print(len(subtenants))
>>>
>>> # extend virutal machine leases for all server names by 180 days and wait for request to complete successfully
>>> client.extend_lease(server_names=['devicmhf01', 'prdicmhf01', 'prdicmfm01'])
>>>
>>> # extend virtual machine lease by 180 days and wait for request to complete successfully
>>> client.extend_lease_action(server_name='ubt1404vm201')
>>>
>>> # extend virtual machine lease by 30 days and wait for request to complete successfully
>>> client.extend_lease_action(server_name='ubt1404vm201', days=30)
>>>
>>> # extend virtual machine lease by 30 days and do not wait for request to complete successfully
>>> client.extend_lease_action(server_name='ubt1404vm201', days=30, wait_for_request=False)
>>>
>>> # wait for request state to be successful, wait 10s between checks but no more than 300s before raising WaitTimeExceeded error
>>> client.wait_for_request(request_id='ac4ff95f-b0c9-4a52-9911-dccb749edac4', delay=10, timeout=300)
>>>
>>> # return resource with name
>>> client.get_endpoint_resource(
        endpoint='/catalog-service/api/consumer/resources?withOperations=true',
        with_filter="tolower(name) eq 'ubt1404vm201'")
>>>
>>> # return all requests submitted by 'ad_lereyes1' that have failed
>>> client.get("/catalog-service/api/consumer/requests?$filter=startswith(requestedBy, 'ad_lereyes1') and substringof('FAILED', state)")
>>>
>>> # return all requests requested by 'ad_lereyes1@amr.corp.intel.com' that were created after 2019-04-29
>>> client.get("/catalog-service/api/consumer/requests?$filter=requestedBy eq 'ad_lereyes1@amr.corp.intel.com' and dateCreated gt '2019-04-29T00:00:00'")
```


### Development using Docker ###

For instructions on installing Docker:
https://github.intel.com/EnterpriseDocker/docker-auto-install-scripts

Clone the repository to a directory on your development server:
```bash
cd
git clone https://github.intel.com/HostingSDI/vRAclient.git
cd vRAclient
```

Build the Docker image
```bash
docker build -t vraclient:latest  .
```

Run the Docker image
```bash
docker run \
--rm \
-v $HOME/vRAclient:/vRAclient \
-it vraclient:latest \
/bin/bash
```
Note: Run the image with the source directory mounted as a volume within the container; this will allow changes to be made to the source code and have those changes reflected inside the container where they can be tested using pybuilder

Execute the build
```bash
pyb -X
```
