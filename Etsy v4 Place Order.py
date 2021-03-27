# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%


import sys
import requests
import json
from requests_oauthlib import OAuth1
import pandas as pd
from pandas.io.json import json_normalize

def placeOrder(order_num,endpoint):
    link_excel = pd.read_excel (r'/Users/jamesmbp/Google Drive/Sports Chord/Etsy/Automation/Print IDs.xlsx',sheet_name='Gdrive Links')
    size_excel = pd.read_excel (r'/Users/jamesmbp/Google Drive/Sports Chord/Etsy/Automation/Print IDs.xlsx',sheet_name='Sizes')
    countries = json.load(open('/Users/jamesmbp/Google Drive/Sports Chord/Etsy/Automation/Countries.json'))

    #order_num=1

    #endpoint='sandbox'

    if endpoint=='sandbox':
        url_start="https://api.sandbox.prodigi.com/v4.0/Orders"
        pwinty_headers = {
        'X-API-Key': 'SANDBOX_API_KEY',
        'Content-Type': 'application/json'
    }    
    elif endpoint=='pwinty':
        url_start="https://api.prodigi.com/v4.0/Orders"
        pwinty_headers = {
        'X-API-Key': 'PRODIGI_API_KEY',
        'Content-Type': 'application/json'
    } 

    orders_url = "https://openapi.etsy.com/v2/shops/YOUR_SHOP_HERE/receipts/open?limit=10"

    ## headers for Etsy authentication

    key = 'ETSY_API_KEY'
    secret = 'ETSY_API_SECRET'
    oauth_token = "ETSY_OAUTH_TOKEN"
    oauth_token_secret = 'ETSY_TOKEN_SECRET'

    etsy_oauth = OAuth1(key, secret,
                            oauth_token, oauth_token_secret,
                            signature_type='auth_header')

    response = requests.get(orders_url, auth=etsy_oauth)
    orders=response.json()

    #Gathering data from most recent order

    order_detail=orders['results']

    name=order_detail[order_num]['name']
    firstline=order_detail[order_num]['first_line']
    secondline=order_detail[order_num]['second_line']
    city=order_detail[order_num]['city']
    state=order_detail[order_num]['state']
    zipcode=order_detail[order_num]['zip']
    country_id=order_detail[order_num]['country_id']
    total=order_detail[order_num]['grandtotal']
    receipt_id=order_detail[order_num]['receipt_id']
    shipping_method=order_detail[order_num]['shipping_details']['shipping_method']
    order_date=order_detail[order_num]['creation_tsz']

    #country lookup
    country_df = pd.DataFrame(countries["results"])
    country_row=country_df.loc[country_df['country_id']==country_id].index[0]
    country_code=country_df['iso_country_code'][country_row]

    #GB Express Shipping
    if country_code=='GB':
        shipping_method='Express'
    elif country_code in ['BE','AT','FR','DE','PT','ES','IT','NL','SE','US','CA']:
        shipping_method='Standard'
    else: 
        shipping_method

    #call the Etsy Receipt based on transaction data

    receipt_url = ("https://openapi.etsy.com/v2/receipts/"+str(receipt_id)+"/transactions")
    response = requests.get(receipt_url, auth=etsy_oauth)
    receipts=response.json()

    ##check if order is a digital file
    digital=receipts['results'][0]['is_digital']


    #if not digital then store the listing details
    if digital == False:

        ##Place Pwinty Order
        

        for i in range(0,len(receipts['results'])):
                listing_id=receipts['results'][i]['listing_id'] #required for excel look ups
                size=receipts['results'][i]['variations'][0]['formatted_value']
                framed=receipts['results'][i]['variations'][1]['formatted_value']
                quant=receipts['results'][i]['quantity']
                print_size=size[1:3] #extracts A2 from (A2) 16.5 x 23.4 inches
                print_frame=size_excel.loc[size_excel['Framed'].str.contains(framed)&size_excel['Etsy'].str.contains(print_size)].index[0]
                sku=size_excel['Pwinty'][print_frame]
                link_row=link_excel.loc[link_excel['EtsyID'] == listing_id].index[0]
                link=link_excel['Link'][link_row]
                viz_title=link_excel['Viz'][link_row]

        
        payload = {
                'merchantReference': receipt_id,
                'shippingMethod': shipping_method,
                'recipient': 
                        {
                        'name': name,
                        'address': {
                            'line1': firstline,
                            'postalOrZipCode': zipcode,
                            'countryCode': country_code,
                            },
                        },
                'items':[
                    {
                        "merchantReference": "item "+str(i+1), 
                        "sku": sku, 
                        "copies": quant, 
                        "sizing": "fillPrintArea", 
                        'recipientCost':
                        { 
                            "amount": total, 
                            "currency": "GBP" 
                        }, 
                        "assets": [ 
                            { 
                            "printArea": "default", 
                            "url": link
                            } 
                            ]
                    }],
                "packingslip":
                    {
                    'url':'PACKING_SLIP_URL'
                    }
                    
                }
        if secondline is not '':
            payload['recipient']['address']['line2']=secondline
        if state is not '':
            payload['recipient']['address']['stateOrCounty']=state
        if city is not '':
            payload['recipient']['address']['townOrCity']=city
        if framed=='Framed':
            payload['items'][i]['attributes']={'color':'black'}


        response = requests.post(url_start, headers=pwinty_headers, json = payload)

        status=response.json()['outcome']

        print('Order for '+name
            +'\nAddress: '+firstline,secondline,city,state,zipcode,country_code
            +'\nPrint: '+viz_title
            +'\nItem Details: '+ size,framed 
            +'\nRevenue: £'+total
            +'\nItem Cost : £'
            +'\nShipping Cost : £'
            +'\nProfit before Etsy Fees: £'
            +'\nShipping Method : '+shipping_method
            +'\nStatus: '+status)

    if status=='Created' and endpoint=='pwinty':
        order_df = pd.read_excel (r'/Users/jamesmbp/Google Drive/Sports Chord/Etsy/Automation/Orders.xlsx',sheet_name='Orders')
        i=len(order_df)
        row=list((10000+i,order_date,receipt_id,999,name,viz_title,size,framed,total))
        order_df.loc[i] = row
        order_df.to_excel(r'/Users/jamesmbp/Google Drive/Sports Chord/Etsy/Automation/Orders.xlsx',sheet_name='Orders',index=False)  


# %%


placeOrder(int(sys.argv[1]),sys.argv[2])


