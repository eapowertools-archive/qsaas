# Status
[![Project Status: Unsupported – The project has reached a stable, usable state but the author(s) have ceased all work on it. A new maintainer may be desired.](https://www.repostatus.org/badges/latest/unsupported.svg)](https://www.repostatus.org/#unsupported)

# qsaas
A wrapper for the Qlik Sense Enterprise SaaS APIs.

### Intended audience
Developers -- familiarity with the [Qlik Sense Enterprise APIs](https://qlik.dev/apis) is required.

### High-level benefits:
1. Automatic pagination on GETs, returning all results.
2. Ability to asynchronously make POSTs, PUTs, and PATCHs, where one can input the amount of threads you'd like (default is 10), dramatically decreasing processing time.
3. Ease of establishing and managing connections to multiple tenants.
4. Ability to connect to any API endpoint.

# Table of Contents
1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Basic Usage](#basic-usage)
4. [Advanced Usage](#advanced-usage)
5. [Complete list of functions](#complete-list-of-functions)
6. [Additional Notes](#additional-notes)

# Installation
```
pip install qsaas
```

#### Dependencies (auto-installed by pip):
```
requests
requests_toolbelt
aiohttp
asyncio
```
# Configuration
To import qsaas, as qsaas only currently has one class, `Tenant`, the simplest way is:
```python
from qsaas.qsaas import Tenant
```

From there, one can instantiate a new `Tenant` object by executing
```python
q = Tenant(<args>)
```

### Option A
If connecting locally, the simplest way can be to use a json file for each tenant, as these files can be securely stored locally. The file must be a valid json file with the following structure:
```json
{
    "api_key": "<API_KEY>",
    "tenant_fqdn": "<TENANT>.<REGION>.qlikcloud.com",
    "tenant_id": "<TENANT_ID>"
}
```
When creating a new `Tenant` object then, the named param `config` can be used as follows (in this case, the file name is "config.json":
```python
q = Tenant(config="config.json")
```

### Option B
If it's preferred to feed in the api_key, tenant_fqdn, and tenant_id in a different manner, one can instead execute:
```python
q = Tenant(api_key=<API_KEY>, tenant=<TENANT_FQDN>, tenant_id=<TENANT_ID>)
```

# Basic Usage
#### Get all users from a tenant and print their IDs
```python
users = q.get('users')
for user in users:
    print(user['id'])
```
#### Get a specific user from a tenant
```python
user = q.get('users', params={"subject":"QLIK-POC\dpi"})
```
#### Get all apps from a tenant and print their names
```python
apps = q.get('items', params={"resourceType":"app"})
for app in apps:
    print(app['name'])
```
#### Get all spaces from a tenant
```python
spaces = q.get('spaces')
```
#### Create a new user
```python
body = {
    "tenantId": q.tenant_id,
    "subject": 'WORKSHOP\\Qlik1',
    "name": 'Qlik1',
    "email": 'Qlik1@workshop.com',
    "status": "active"
}
q.post('users', json.dumps(body))
```
#### Reload an application
```python
reload = q.post('reloads', json.dumps({"appId": "<APP_ID>"}))
```
#### Reload an application and wait
```python
reload_id = q.post('reloads', json.dumps({"appId": "<APP_ID>"}))['id']
status = None
while status not in ['SUCCEEDED', 'FAILED']:
    time.sleep(1)
    status = q.get('reloads/' + reload_id)['status']
```
#### Publish an application
```python
app_id = <APP_ID>
space_id = <SPACE_ID>
app = q.post('apps/' + app_id + '/publish', json.dumps({"spaceId": space_id}))
payload = {
    "name": app['attributes']['name'],
    "resourceId": app['attributes']['id'],
    "description": app['attributes']['description'],
    "resourceType": "app",
    "resourceAttributes": app['attributes'],
    "resourceCustomAttributes": {},
    "resourceCreatedAt": app['attributes']['createdDate'],
    "resourceCreatedBySubject": app['attributes']['owner'],
    "spaceId": space_id
}
q.post('items', json.dumps(payload))
```
#### Change the owner of an application
```python
app_id = <APP_ID>
user_id = <USER_ID>
q.put('apps/' + app_id + '/owner', json.dumps({"ownerId": user_id}))
```
#### Import an application
```python
with open('<APP-NAME>.qvf', 'rb') as f:
    data = f.read()
app = q.post('apps/import', data,
             params={"name": "<APP-NAME-NEW>"})
payload = {
    "name": app['attributes']['name'],
    "resourceId": app['attributes']['id'],
    "description": app['attributes']['description'],
    "resourceType": "app",
    "resourceAttributes": app['attributes'],
    "resourceCustomAttributes": {},
    "resourceCreatedAt": app['attributes']['createdDate'],
    "resourceCreatedBySubject": app['attributes']['owner']
}
q.post('items', json.dumps(payload))
```

# Advanced Usage
#### Upload a file to DataFiles
```python
file_path = directory_path + '\\' + file_name
body = open(file_path, 'rb')
q.post('qix-datafiles', body,
        params={"connectionId": conn_id, "name": file_name})
```
#### Asynchronously reload multiple applications
_Note:_ The default threading is 10 at a time--to modify this, add the named param `chunks=x`, where x is an integer. Do not make this integer too high to avoid rate limiting.
```python
app_ids = ['<APP_ID1>','<APP_ID2>','<APP_ID3>']
payloads = [json.dumps({"appId": app_id}) for app_id in app_ids]
q.async_post('reloads', payloads=payloads)
```

#### Asynchronously delete apps that have the name "delete_me"
_Note:_ This process currently requires deleting both from the `apps` and `items` endpoints. The default threading is 10 at a time--to modify this, add the named param `chunks=x`, where x is an integer. Do not make this integer too high to avoid rate limiting.
```python
items = q.get('items', params={"resourceType": "app", "name": "delete_me"})
delete_dict = {}
delete_dict['items'] = [item['id'] for item in items]
delete_dict['apps'] = [item['resourceId'] for item in items]
for e in delete_dict:
    q.async_delete(e, ids=delete_dict[e])
```
#### Asychronously add users
_Note:_ The default threading is 10 at a time--to modify this, add the named param `chunks=x`, where x is an integer. Do not make this integer too high to avoid rate limiting.
```python
payloads = []
for i in range(10):
    user_subject = 'WORKSHOP\\Qlik' + str(i+1)
    user_name = 'Qlik' + str(i+1)
    user_email = 'Qlik' + str(i+1) + '@workshop.com'
    body = {
        "tenantId": q.tenant_id,
        "subject": user_subject,
        "name": user_name,
        "email": user_email,
        "status": "active"
    }
    payloads.append(json.dumps(body))
q.async_post('users', payloads=payloads)
```
#### Asynchronously copy applications and assign them to new owners
_Note:_ This is the only "custom" style function in all of qsaas, due to the fact that it has hardcoded endpoints and has an multi-step process--as it can copy applications and then assign those applications ot new owners in one go. The default threading is 10 at a time--to modify this, add the named param `chunks=x`, where x is an integer. Do not make this integer too high to avoid rate limiting.
**Copy app and assign ownership to new users**
```python
q.async_app_copy('<GUID>',users=['<UserId-1>','<UserId-2>'])
```
**Simply copy an app 10 times, without assigning new ownership**
```python
q.async_app_copy('<GUID>',copies=10)
```

#### Customize Headers
_Note:_ This is available for all functions, but should largely not be needed (most headers are automatically generated by the Python libraries used). If the need arises to pass in custom headers, or to overwrite the existing headers, one can leverage the keyword param `headers` as per below.
**Upload an image to an application**
```python
data = open('your_image.png', 'rb').read()
q.put('apps/<GUID>/media/files/your_image.png',
      data, headers={"Content-Type": "image/png"})
```

# Complete list of functions
- `q.get()`
- `q.post()`
- `q.put()`
- `q.patch()`
- `q.delete()`
- `q.async_post()`
- `q.async_put()`
- `q.async_patch()`
- `q.async_app_copy()` *only custom function

For each function, one can always refer to the docstring for a helpful description, and most provide examples. For instance, `help(q.get)` will output:
```
    Description
    --------------------
    GETs and paginates all results. Takes optional params.

    Mandatory parameters
    --------------------
    endpoint (str), exclude api/{version}

    Optional parameters
    --------------------
    params (dict)

    Example Usage
    --------------------
    Example 1:
        get('users')

        This will return all users.

    Example 2:
        get('items', params={"resourceType":"app"})

        This will return all apps from items.
```

# Additional Notes
#### API Documentation
It is highly encouraged to review the API documentation at [the qlik.dev portal](https://qlik.dev/apis). As this wrapper does not have wrapped Qlik functions (aside from the `async_app_copy` function), it is integral to know the API appropriate endpoints to call.

#### Support
This project is built and maintained by Daniel Pilla, a Principal Analytics Platform Architect at Qlik. This project is however not supported by Qlik, and is only supported through Daniel.
