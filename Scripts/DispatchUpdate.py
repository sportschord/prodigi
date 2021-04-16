#!/usr/bin/env python
# coding: utf-8

# In[3]:


'''Order Dispatch script.

This script was designed to check pwinty API for updates in status and then update the etsy dispatch status'''

import requests
import json
from requests_oauthlib import OAuth1
import pandas as pd
from pandas.io.json import json_normalize
import yagmail

## Check for status changes

carriers=pd.read_csv('/PATH TO CARRIERS/carriers.csv')
data=pd.read_csv('PATH TO CURRENT STATUS.csv')
newsave='/PATH TO CURRENT STATUS./status.csv'

endpoint='pwinty'

if endpoint=='sandbox':
    url_start="https://sandbox.pwinty.com/v3.0/orders"
    pwinty_headers = {
    'X-Pwinty-MerchantId': 'YOURIDHERE',
    'X-Pwinty-REST-API-Key': 'YOURKEYHERE',
    'Content-Type': 'application/json'
}    
elif endpoint=='pwinty':
    url_start="https://api.pwinty.com/v3.0/orders"
    pwinty_headers = {
    'X-Pwinty-MerchantId': 'YOURIDHERE',
    'X-Pwinty-REST-API-Key': 'YOURKEYHERE',
    'Content-Type': 'application/json'
}     
    

#get 10 most recent orders
get_pwinty_request = requests.get(url_start+"?limit=150&start=0", headers=pwinty_headers)

seq=range(0,150)
ords=[]

#fetch order IDs
for i in seq:
        ord_id=str(get_pwinty_request.json()['data']['content'][i]['id'])
        ords.append(ord_id)

#fetch order status
stats=[]
merchant_ids=[]
buyers=[]
cnt=0
for i in ords:
    #get_pwinty_request = requests.get(url_start+"/"+i, headers=pwinty_headers)
    response=get_pwinty_request.json()['data']['content'][cnt]
    pwinty_status=response['status']
    stats.append(pwinty_status)
    merchant_id=response['merchantOrderId']
    merchant_ids.append(merchant_id)
    name=response['recipientName']
    buyers.append(name)
    cnt=cnt+1


##check which orders have changed from submitted to complete and return index


def shipping(orderid):
    orderid=str(orderid)
    get_pwinty_request = requests.get(url_start+'/'+orderid, headers=pwinty_headers)
    response=get_pwinty_request.json()['data']
    pwinty_status=response['status']
    if pwinty_status =='Complete':
        carrier=response['shippingInfo']['shipments'][0]['carrier']
        is_tracked=response['shippingInfo']['shipments'][0]['isTracked']
        tracking_number=response['shippingInfo']['shipments'][0]['trackingNumber']
        tracking_Url=response['shippingInfo']['shipments'][0]['trackingUrl']
    return is_tracked,carrier,tracking_number,tracking_Url



#creat new df for current pwinty status of orders
ords_df=pd.DataFrame({'id':ords,'new_status':stats})
ords_df['id']=ords_df['id'].astype(int)

#left join this with the existing data
b=pd.merge(data,ords_df,left_on='id',right_on='id')

#loop through orders to find changed status
new_ords=[]
for i in range(0,len(b)):
    a=b['new_status'][i]+'-'+b['status'][i]
    new_ords.append(a)


indices = [i for i, new_ords in enumerate(new_ords) if 'Complete-Submitted' in new_ords]


order_df=pd.DataFrame({'id':ords,'status':stats,'etsyid':merchant_ids,'buyer':buyers})

if len(indices)>0:
    
    key = 'ETSY_API_KEY'
    secret = 'ETSY_API_SECRET'
    oauth_token = "ETSY_OAUTH_TOKEN"
    oauth_token_secret = 'ETSY_TOKEN_SECRET'

    etsy_oauth = OAuth1(key, secret,
                         oauth_token, oauth_token_secret,
                         signature_type='auth_header')
    


    for i in range(0,len(indices)):
        a=indices[i]
        etsy_id_dispatched=int(data['etsyid'][a])
        pwinty_id_dispatched=int(data['id'][a])
        buyer_name=data['buyer'][a]
        
        #update with tracking info
        
        try:
            shipping_details=shipping(pwinty_id_dispatched)
            carrier=carriers.loc[carriers['pwinty_carrier']==shipping_details[1]]['etsy_carrier'].item()
            track_url = ('https://openapi.etsy.com/v2/shops/14868331/receipts/'+str(etsy_id_dispatched)+'/tracking?tracking_code='+shipping_details[2]+'&carrier_name='+carrier+'&send_bcc=1')
            response = requests.post(track_url, auth=etsy_oauth)
            print(response,' tracking was added fine for ',buyer_name)
        except:
            
            #PUT UPDATE ORDER To Dispatched
            receipt_url = ("https://openapi.etsy.com/v2/receipts/"+str(etsy_id_dispatched))+'?was_shipped=1'
            response = requests.put(receipt_url, auth=etsy_oauth)
            receiver = "YOUR_EMAIL_HERE"
            subject = "Order Dispatched - #"+str(etsy_id_dispatched)
            body = ('Pwinty has dispatched order for '+buyer_name+
                    '\nPwintyID:'+str(pwinty_id_dispatched)+
                    '\nEtsyID:'+str(etsy_id_dispatched)+
                    'Great news, \nJames')
            #filename = "document.pdf"

            yag = yagmail.SMTP("YOUR_EMAIL_HERE",'EMAIL_PW_HERE')
            yag.send(
                to=receiver,
                subject=subject,
                contents=body, 
                #attachments=filename,
            )
            print(etsy_id_dispatched,'marked as dispatched')
        
else:
    print('no new orders')

#export to csv file
order_df.to_csv(newsave,index=False,encoding='utf-8') 


# In[ ]:




