# This script parses out unique API calls from the monitored traffic and provides example bodies
# Eventually it will likely support identifying new/removed/changed calls and content
import os
import json
from urllib.parse import urlparse

root = ''

unique_urls = {}

for path, dirs, files in os.walk(root):
    for file in files:
        if file == 'request.json':
            with open(os.path.join(path, file)) as f:
                request = json.load(f)
            method = request['method']
            url = urlparse(request['url'])
            key = f'{method} {url.path}'
            if url.path == '/AppAPI':
                # this is actually a bunch of methods
                apiMethod = url.query.split('&', 1)[0]
                key = f'{key}/{apiMethod}'
            if key not in unique_urls:
                
                sample = {
                    'url': url.geturl()
                }
                if 'request_body.txt' in files:
                    with open(os.path.join(path, 'request_body.txt')) as b:
                        try:
                            sample['body'] = json.load(b)
                        except:
                            sample['body'] = b.read()
                if 'response_body.json' in files:
                    with open(os.path.join(path, 'response_body.json')) as b:
                        sample['response'] = json.load(b)
                unique_urls[key] = sample

# dump = json.dumps(unique_urls, indent=2)
with open('api_data.json', 'w') as f:
    json.dump(unique_urls, f, indent=2)