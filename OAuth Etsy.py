# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
from requests_oauthlib import OAuth1Session, OAuth1
from urllib.parse import urlencode


key = 'ETSY_KEY'
secret = 'ETSY_SECRET'
scope = urlencode({'scope': 'transactions_r transactions_w'})
request_token_url = f'https://openapi.etsy.com/v2/oauth/request_token?{scope}'
access_token_url = 'https://openapi.etsy.com/v2/oauth/access_token'

etsy = OAuth1Session(key, client_secret=secret)

resp = etsy.fetch_request_token(request_token_url)


print('Click to this URL for allow access:')
print(resp['login_url'])

verifier = input('Paste confirm code:')

etsy = OAuth1Session(key, client_secret=secret, resource_owner_key=resp['oauth_token'], resource_owner_secret=resp['oauth_token_secret'])
acc_token = etsy.fetch_access_token(access_token_url, verifier=verifier)
print(acc_token)


