
url = 'https://{}/iaas/api/projects'.format(hostname)
data1 = {
        " Token" : raiserer_token }
data1 =  json.dumps ( data1 )
print ( data1 )
headers = {
       'accept': "application/json",
       'authorization': raiserer_token
       }
api_output = requests.request("GET",url, headers=headers, verify='/etc/ssl/certs/cabundle.pem').json()['content']
return api_output
