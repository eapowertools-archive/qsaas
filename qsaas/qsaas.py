import re
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import json
from aiohttp import ClientSession
import asyncio
import warnings
import urllib


class Tenant:
    """
    Description
    --------------------
    An instance of a Tenant object, typically one per
    tenant.

    Mandatory parameters
    --------------------
    Either provide all of the below named parameters:
        api_key: an api key for the tenant
        tenant: the fqdn of the tenant, e.g. test.us.qlikcloud.com
        tenant_id: the tenant id of the tenant, found in "Settings"

    OR provide a path to a config.json file that has the structure:
        {
            "api_key": "<API_KEY>",
            "tenant_fqdn": "<TENANT>.<REGION>.qlikcloud.com",
            "tenant_id": "<TENANT_ID>"
        }

        e.g. config="path/to/config.json"

    Example Usage
    --------------------
        Option 1:
        q = Tenant(config="<file>.json")

        Option 2:
        q = Tenant(api_key=<key>, tenant=<tenant>, tenant_id=<id>)

        Multiple tenants:
        q_us = Tenant(config="us.json")
        q_emea = Tenant(config="emea.json")
        q_apac = Tenant(config="apac.json")
    """

    def __init__(self, api_key=False, tenant=False, tenant_id=False,
                 config=False):
        if all([api_key, tenant, tenant_id]) and not config:
            self.tenant = 'https://' + tenant.replace('https://', '')
            self.tenant_id = tenant_id
            self.auth_header = {'Authorization': 'Bearer ' + api_key}
        elif config:
            try:
                with open(config) as f:
                    config_f = json.load(f)
                self.auth_header = {
                    'Authorization': 'Bearer ' + config_f['api_key']}
                self.tenant = 'https://' + config_f['tenant_fqdn']
                self.tenant_id = config_f['tenant_id']
            except FileNotFoundError:
                raise Exception('Cannot find:', config)
        else:
            response = 'You must provide an api_key, tenant, and tenant_id'
            response += ' OR you can provide a path to a config.json file.'
            raise Exception(response)

        self.limit = 100
        self.suppress_warnings = False

    def get(self, endpoint, params={}, headers={}):
        """
        Description
        --------------------
        GETs and paginates all results. Takes optional params.

        Mandatory parameters
        --------------------
        endpoint (str), exclude api/{version}

        Optional parameters
        --------------------
        params (dict)
        headers (dict)

        Example Usage
        --------------------
        Example 1:
            get('users')

            This will return all users.

        Example 2:
            get('items', params={"resourceType":"app"})

            This will return all apps from items.
        """

        params['limit'] = self.limit
        s = requests.Session()
        s.headers.update(self.auth_header)

        if len(headers) > 0:
            s.headers.update(headers)

        next_re = r'(?<=&next=)(?:(?!&|$).)*'
        next_name = 'next'
        starting_after = None
        result = []
        try:
            r = s.get(self.tenant + '/api/v1/' + endpoint, params=params)
            if r.status_code == 200:
                result = r.json()
                if 'data' in result:
                    result = result['data']
                try:
                    starting_after = re.findall(
                        next_re, r.json()['links']['next']['href'])[0]
                except IndexError:
                    try:
                        next_re = r'(?<=&startingAfter=)(?:(?!&|$).)*'
                        starting_after = re.findall(
                            next_re, r.json()['links']['next']['href'])[0]
                        next_name = 'startingAfter'
                    except IndexError:
                        params.clear()
                        return result
                except KeyError:
                    try:
                        starting_after = re.findall(
                            next_re, r.json()['links']['Next']['Href'])[0]
                    except IndexError:
                        try:
                            next_re = r'(?<=&startingAfter=)(?:(?!&|$).)*'
                            starting_after = re.findall(
                                next_re, r.json()['links']['Next']['Href'])[0]
                            next_name = 'startingAfter'
                        except IndexError:
                            params.clear()
                            return result

            else:
                params.clear()
                raise Exception(r.status_code, r.text)
            while r.status_code == 200 and starting_after:
                params[next_name] = starting_after
                r = s.get(self.tenant + '/api/v1/' + endpoint, params=params)
                result += r.json()['data']
                try:
                    starting_after = re.findall(
                        next_re, r.json()['links']['next']['href'])[0]
                except KeyError:
                    starting_after = re.findall(
                        next_re, r.json()['links']['Next']['Href'])[0]
        except KeyError:
            pass
        except TypeError:
            params.clear()
            return result
        s.close()
        params.clear()
        return result

    def delete(self, endpoint, headers={}):
        """
        Description
        --------------------
        DELETEs an object.

        Mandatory parameters
        --------------------
        endpoint (str), exclude api/{version}

        Optional parameters
        --------------------
        headers (dict)

        Example Usage
        --------------------
        Example:
            delete('items/' + '<ItemId>')

            This deletes an item with the corresponding Id.
        """

        s = requests.Session()
        s.headers.update(self.auth_header)

        if len(headers) > 0:
            s.headers.update(headers)

        r = s.delete(self.tenant + '/api/v1/' + endpoint)
        if r.status_code in range(200, 300):
            try:
                result = r.json()
            except json.decoder.JSONDecodeError:
                result = r
        else:
            raise Exception(r.status_code, r.text)
        s.close()
        return result

    def post(self, endpoint, body, params={}, headers={}):
        """
        Description
        --------------------
        POSTs an object.

        This function attempts to properly format
        the body properly for you. E.g. if the endpoint
        expects [{"key":"value"}] but {"key":"value"} is
        sent, it will try again by wrapping it in an array.
        Similarly, it will try json.dumps(<body>) if
        it isn't already dumped.

        Mandatory parameters
        --------------------
        endpoint (str), exclude api/{version}
        body (dict), occasionally requires manual json.dumps()

        Optional parameters
        --------------------
        params (dict)
        headers (dict)

        Example Usage
        --------------------
        Example:
            post('apps/' + '<AppId>' + '/publish',
                 {"spaceId": '<SpaceId>'})
        """

        return self._generic('post', endpoint, body, params, headers)

    def put(self, endpoint, body, params={}, headers={}):
        """
        Description
        --------------------
        PUTs an object.

        This function attempts to properly format
        the body properly for you. E.g. if the endpoint
        expects [{"key":"value"}] but {"key":"value"} is
        sent, it will try again by wrapping it in an array.
        Similarly, it will try json.dumps(<body>) if
        it isn't already dumped.

        Mandatory parameters
        --------------------
        endpoint (str), exclude api/{version}
        body (dict), occasionally requires manual json.dumps()

        Optional parameters
        --------------------
        params (dict)
        headers (dict)

        Example Usage
        --------------------
        Example:
            put('apps/' + '<AppId>' + '/owner',
                json.dumps({"ownerId": '<UserId>'}))
        """

        return self._generic('put', endpoint, body, params, headers)

    def patch(self, endpoint, body, params={}, headers={}):
        """
        Description
        --------------------
        PATCHs an object.

        This function attempts to properly format
        the body properly for you. E.g. if the endpoint
        expects [{"key":"value"}] but {"key":"value"} is
        sent, it will try again by wrapping it in an array.
        Similarly, it will try json.dumps(<body>) if
        it isn't already dumped.

        Mandatory parameters
        --------------------
        endpoint (str), exclude api/{version}
        body (dict), occasionally requires manual json.dumps()

        Optional parameters
        --------------------
        params (dict)
        headers (dict)
        """

        return self._generic('patch', endpoint, body, params, headers)

    def async_app_copy(self, app_id, copies=1, chunks=10, users=[],
                       headers={}):
        """
        Description
        --------------------
        Asynchronously copies applications, optionally assigning
        the copies to new owners. The default amount of copies
        is 1, and the amount of asynchronous copying is defaulted to 10.

        Mandatory parameters
        --------------------
        app_id (str)

        Optional parameters
        --------------------
        copies (int), keyword param, default 1
        chunks (int), keyword param, default 10
        users (list), keyword param
        headers (dict), keyword param

        Example Usage
        --------------------
        Example 1:
            async_app_copy('<GUID>',users=['<UserId-1>','<UserId-2>'])

            This would copy an app once for each user, assigning the
            new owner as that user.

        Example 2:
            async_app_copy('<GUID>',users=['<UserId-1>','<UserId-2>',
                           '<UserId-3>'], copies=2, chunks=2)

            This would copy an app twice per user two copies at a
            time, assigning both to the new owners.

        Example 3:
            async_app_copy('<GUID>',copies=10)

            This would copy an app 10 times, retaining the original owner.
        """

        async def call(url, session, app_id, user_id, headers):
            async with session.post(url + 'apps/' + app_id + '/copy',
                                    headers=headers) as resp:
                response = await resp.text()
                if resp.status not in range(200, 300):
                    raise Exception(resp.status, response)

                attributes = json.loads(response)['attributes']
                copied_app_id = attributes['id']
                payload = {
                    "name": attributes['name'],
                    "resourceId": attributes['id'],
                    "description": attributes['description'],
                    "resourceType": "app",
                    "resourceAttributes": attributes,
                    "resourceCustomAttributes": {},
                    "resourceCreatedAt": attributes['createdDate'],
                    "resourceCreatedBySubject": attributes['owner']
                }

            async with session.post(url + 'items', data=json.dumps(payload),
                                    headers=headers) as resp:
                response = await resp.text()
                if resp.status not in range(200, 300):
                    raise Exception(resp.status, response)
                return response

            if user_id:
                async with session.put(url + 'apps/' + copied_app_id +
                                       '/owner',
                                       data=json.dumps({"ownerId": user_id}),
                                       headers=headers) as resp:
                    response = await resp.text()
                    if resp.status not in range(200, 300):
                        raise Exception(resp.status, response)
                    return response
            else:
                return copied_app_id

        async def bound_call(sem, url, session, app_id, user_id, headers):
            async with sem:
                return await call(url, session, app_id, user_id, headers)

        async def run(app_id, copies, chunks, users, headers):
            url = self.tenant + '/api/v1/'
            auth_header = self.auth_header
            auth_header.update(headers)
            headers = auth_header

            tasks = []

            sem = asyncio.Semaphore(chunks)

            async with ClientSession() as session:
                if len(users) > 0:
                    for user_id in users:
                        for i in range(copies):
                            task = asyncio.ensure_future(
                                bound_call(sem, url.format(i), session, app_id,
                                           user_id, headers))
                            tasks.append(task)

                    responses = asyncio.gather(*tasks)
                    return await responses
                else:
                    for i in range(copies):
                        task = asyncio.ensure_future(
                            bound_call(sem, url.format(i), session, app_id,
                                       False, headers))
                        tasks.append(task)

                    responses = asyncio.gather(*tasks)
                    return await responses

        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(
            run(app_id, copies, chunks, users, headers))
        loop.run_until_complete(future)

    def async_delete(self, endpoint, ids=[], chunks=10, headers={}):
        """
        Description
        --------------------
        Asynchronously deletes objects with IDs from arbitrary
        endpoints. The default number of asynchronous operations
        is set to 10.

        Mandatory parameters
        --------------------
        endpoint (str), exclude api/{version}

        Optional parameters
        --------------------
        ids (list), keyword param
        chunks (int), keyword param, default 10
        headers (dict), keyword param

        Example Usage
        --------------------
        Example:
            async_delete('users', ids=['<GUID1>','<GUID2>'])
        """

        async def call(url, session, headers):
            async with session.delete(url,
                                      headers=headers) as resp:
                response = await resp.text()
                if resp.status not in range(200, 300):
                    raise Exception(resp.status, response)
                return response

        async def bound_call(sem, url, session, headers):
            async with sem:
                return await call(url, session, headers)

        async def run(endpoint, ids, chunks, headers):
            auth_header = self.auth_header
            auth_header.update(headers)
            headers = auth_header

            if len(ids) > 0:
                url = self.tenant + '/api/v1/' + endpoint + '/'
                tasks = []

                sem = asyncio.Semaphore(chunks)

                async with ClientSession() as session:
                    for element_id in ids:
                        task = asyncio.ensure_future(
                            bound_call(sem, url + element_id, session,
                                       headers))
                        tasks.append(task)

                    responses = asyncio.gather(*tasks)
                    return await responses
            else:
                raise Exception(
                    'No ids were provided, ensure ids=[] is provided')

        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(run(endpoint, ids, chunks, headers))
        loop.run_until_complete(future)

    def async_post(self, endpoint, payloads=[], replace_char='',
                   replace_ids=[], chunks=10, headers={}):
        """
        Description
        --------------------
        POSTs asynchronously

        This function takes a list of payloads to POST to
        an endpoint, and depending on the endpoint, can
        take a list of GUIDs to replace a mid-part of the
        endpoint path. For example, if the goal is to POST
        to "users" to create new users in bulk, there is no
        need to have a GUID as part of the URL, and you can
        simply send along an list of payloads to POST.
        However, if you wanted to bulk publish applications,
        the endpoint would require a GUID as part of the
        URL, e.g. "apps/<GUID>/publish". This function
        allows you to pass in an additional list of GUIDs
        to replace a specific string in the URL. Refer
        to the examples below.

        Mandatory parameters
        --------------------
        endpoint (str), exclude api/{version}
                        if this endpoint has a GUID in it,
                        replace where the GUID would be
                        with a character such as '_' so that
                        it can be programmatically replaced.
        payloads (list), keyword param, occasionally requires
                         manual json.dumps() on the objects
                         within the list.

        Optional parameters
        --------------------
        replace_char (str), keyword param, a character(s) that
                            is to be replaced with GUIDs from
                            the "replace_ids" list.
        replace_ids (list), keyword param, a list of GUIDs
                            that will replace a specific string
                            per-call in the endpoint URL
        chunks (int),   keyword param, default 10
        headers (dict), keyword param

        Example Usage
        --------------------
        Example:
            async_post('apps/_/publish', replace_ids=Ids,
                       replace_char='_', payloads=payloads)

            async_post('users',payloads=payloads)
        """

        return self._async_generic('post', endpoint, payloads, replace_char,
                                   replace_ids, chunks, headers)

    def async_put(self, endpoint, payloads=[], replace_char='',
                  replace_ids=[], chunks=10, headers={}):
        """
        Description
        --------------------
        PUTs asynchronously

        This function takes a list of payloads to PUT to
        an endpoint, and depending on the endpoint, can
        take a list of GUIDs to replace a mid-part of the
        endpoint path.

        Refer to the documentation and examples from async_post
        """

        return self._async_generic('put', endpoint, payloads, replace_char,
                                   replace_ids, chunks, headers)

    def async_patch(self, endpoint, payloads=[], replace_char='',
                    replace_ids=[], chunks=10, headers={}):
        """
        Description
        --------------------
        PATCHs asynchronously

        This function takes a list of payloads to PUT to
        an endpoint, and depending on the endpoint, can
        take a list of GUIDs to replace a mid-part of the
        endpoint path.

        Refer to the documentation and examples from async_post
        """

        return self._async_generic('patch', endpoint, payloads, replace_char,
                                   replace_ids, chunks, headers)

    def _async_generic(self, method, endpoint, payloads, replace_char,
                       replace_ids, chunks, headers):
        """
        Description
        --------------------
        Helper function for async_post, async_patch, async_put
        """

        async def call(method, url, session, payload, headers):
            func = 'session.' + method
            async with eval(func)(url, data=payload,
                                  headers=headers) as resp:
                response = await resp.text()
                if resp.status not in range(200, 300):
                    raise Exception(resp.status, response)
                return response

        async def bound_call(sem, method, url, session, payload, headers):
            async with sem:
                return await call(method, url, session, payload, headers)

        async def run(method, endpoint, payloads, replace_char, replace_ids,
                      chunks, headers):
            if len(payloads) > 0:
                if len(replace_char) > 0 and len(replace_ids) > 0:
                    fill_urls = True
                elif any([len(replace_char) > 0, len(replace_ids) > 0]):
                    raise Exception(
                        'both replace_char and replace_ids must be present')
                else:
                    fill_urls = False

                tasks = []
                sem = asyncio.Semaphore(chunks)

                auth_header = self.auth_header
                auth_header.update(headers)
                headers = auth_header

                async with ClientSession() as session:

                    if fill_urls:
                        if len(replace_ids) == len(payloads):
                            for idx, element_id in enumerate(replace_ids):
                                new_endpoint = endpoint.replace(
                                    replace_char, element_id)
                                url = self.tenant + '/api/v1/' + new_endpoint
                                task = asyncio.ensure_future(
                                    bound_call(sem, method, url, session,
                                               payloads[idx], headers))
                                tasks.append(task)

                            responses = asyncio.gather(*tasks)
                            return await responses
                        else:
                            raise Exception(
                                'len(payloads) != len(replace_ids)')
                    else:
                        url = self.tenant + '/api/v1/' + endpoint
                        for payload in payloads:
                            task = asyncio.ensure_future(
                                bound_call(sem, method, url, session,
                                           payload, headers))
                            tasks.append(task)

                        responses = asyncio.gather(*tasks)
                        return await responses

            else:
                raise Exception(
                    'No payloads were provided, ensure payloads=[]')

        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(run(method, endpoint, payloads,
                                           replace_char, replace_ids, chunks,
                                           headers))
        loop.run_until_complete(future)

    def _generic_request(self, s, method, endpoint, body, params, headers,
                         json=False):
        """
        Description
        --------------------
        Private helper function for _generic.
        """
        func = 's.' + method
        if 'import' in endpoint:
            params = urllib.parse.urlencode(
                params, quote_via=urllib.parse.quote)
        elif 'qix-datafiles' in endpoint and method in ['post', 'put']:
            try:
                body = MultipartEncoder(
                    fields={'Data': (params['name'], body, 'text/plain')}
                )
                s.headers.update({'Content-Type': body.content_type})
            except KeyError:
                raise Exception('Provide the "name" param')
        elif method in ['post', 'put', 'patch']:
            s.headers.update({'Content-Type': 'application/json',
                              'Accept': 'application/json'})

        if len(headers) > 0:
            s.headers.update(headers)

        if not json:
            r = eval(func)(self.tenant + '/api/v1/' + endpoint,
                           params=params, data=body)
        else:
            r = eval(func)(self.tenant + '/api/v1/' +
                           endpoint, params=params, json=body)

        return r

    def _generic(self, method, endpoint, body, params, headers):
        """
        Description
        --------------------
        Private helper function for post, put, patch.
        """
        flag_400 = False
        flag_500 = False
        s = requests.Session()
        s.headers.update(self.auth_header)

        r = self._generic_request(s, method, endpoint, body, params, headers)

        if r.status_code == 400:
            flag_400 = True
            body = [body]

            r = self._generic_request(
                s, method, endpoint, body, params, headers, json=True)

            if r.status_code == 500:
                flag_500 = True
                body = json.dumps(body[0])
                r = self._generic_request(
                    s, method, endpoint, body, params, headers)

            elif r.status_code == 400:
                raise Exception(r.status_code, r.text)

        if r.status_code == 500:
            flag_500 = True
            body = json.dumps(body)
            r = self._generic_request(
                s, method, endpoint, body, params, headers)

        if r.status_code in range(200, 300):
            try:
                result = r.json()
            except json.decoder.JSONDecodeError:
                result = r
        else:
            raise Exception(r.status_code, r.text)
        s.close()
        if any([flag_400, flag_500]) and not self.suppress_warnings:
            if flag_400 and not flag_500:
                wm = 'Payload required being wrapped in an array, '
                wm += 'and then resulted in a successful ' + method
                wm += ' call. To avoid this warning in the future, '
                wm += ' send your payload to "' + endpoint + '" in '
                wm += 'an array, or suppress warnings using '
                wm += 'suppress_warnings = True'
                warnings.warn(wm)
            else:
                wm = 'Payload required being dumped to json using '
                wm += 'json.dumps(), which then resulted in a successful '
                wm += 'call. To avoid this warning in the future, '
                wm += method + ' send your payload to "' + endpoint + '"'
                wm += ' in an array, or suppress warnings using '
                wm += 'suppress_warnings = True'
                warnings.warn(wm)
        return result
