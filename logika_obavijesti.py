import boto3
from bs4 import BeautifulSoup
import requests

headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36"}
    
client = boto3.client('dynamodb')
clientSNS = boto3.client('sns')
def lambda_handler(event, context):
                
    response = client.scan(TableName = 'obavijesti')
    items = response.get('Items')
    for item in items:
        link = item ['link']['S']
        cijena = item ['zeljenaCijena']['S']
        itemID = item ['id']['S']
        email = item ['email']['S']
        emailPoslan = item ['emailPoslan']['BOOL']
        topicArn = item['TopicArn']['S']
        #print(link)
        
        #pretraživanje trenutne cijene za svaki link iz DynamoDB-a
        #pretraživanje trenutne cijene za Links
        try:
            if 'links.hr' in link:
                stranica = requests.get(url = link, headers = headers)
                soup = BeautifulSoup(stranica.content,'lxml')
                #cijena2 = soup.find('div', class_='product-price discounted-price').span.text
                #cijena2 = soup.find('div', class_='prices').span.text
                cijena2 = soup.find('meta', itemprop = 'price')
                cijena2 = cijena2['content']
                cijenaS = cijena2.strip()
                """
                cijenaSS = str(cijenaS).replace(' kn', '').replace('.','')
                lipe = cijenaSS[-2:]
                cijenaSS = cijenaSS[:-2]
                cijenaSS = cijenaSS + '.' + lipe
                cijenaSS = cijenaSS.replace(',', '.').replace(',','')
                cijena2 = float(cijenaSS)
                """
                cijena2 = float(cijenaS)
        except:
            continue
        
        #pretraživanje trenutne cijene za MALL.hr
        try:
            if 'mall.hr' in link:
                stranica = requests.get(url = link, headers = headers)
                soup = BeautifulSoup(stranica.content,'lxml')
                cijena2 = soup.find(class_ = 'price__wrap__box__final').text
                cijenaS = cijena2.strip()
                cijena2 = float(cijenaS.split()[0].replace(".", "").replace(",", "."))
        except:
            continue
        
        #pretraživanje trenutne cijene za Instar
        try:
            if 'instar-informatika' in link:
                stranica = requests.get(url = link, headers = headers)
                soup = BeautifulSoup(stranica.content,'lxml')
                cijena2 = soup.find('span', class_ = 'success').text
                cijenaS = cijena2.strip()
                cijena2 = float(cijenaS.split()[0].replace(".", "").replace(",", "."))
        except:
            continue
        
        
        #pretraživanje trenutne cijene za H2 shop
        try:
            if 'h2-shop.com' in link:
                stranica = requests.get(url = link, headers = headers)
                soup = BeautifulSoup(stranica.content,'lxml')
                cijena2 = soup.find('div', class_='product-price').text
                cijenaS = cijena2.strip()
                cijena2 = float(cijenaS.split()[0].replace(".", "").replace(",", "."))
        except:
            continue
          
        #pretraživanje trenutne cijene za PC shop
        try:
            if 'pcshop.hr' in link:
                stranica = requests.get(url = link, headers = headers)
                soup = BeautifulSoup(stranica.content,'lxml')
                cijena2 = soup.find('div', style='color: #F00; font-size: 16px; font-weight: 700;').span.text
                cijena2 = float(cijena2.split()[0].replace(".", "").replace(",", "."))
        except:
            continue
        
        #pretraživanje trenutne cijene za Tia mobiteli
        try:
            if 'tia-mobiteli' in link:
                stranica = requests.get(url = link, headers = headers)
                soup = BeautifulSoup(stranica.content,'lxml')
                cijena2 = soup.find('div', class_='widget widget-info widget-price').b.text
                cijena2 = float(cijena2.split()[0].replace(".", "").replace(",", "."))
        except:
            continue
        
        #uspoređivanje trenutne cijene sa željenom cijenom
        #ako je trenutna cijena <= željenoj cijeni šalje se email obavijest i postavlja 'emailPoslan' na True
        if cijena2 <= float(cijena) and emailPoslan == False:
            clientSNS.publish(
                TopicArn=topicArn,
                Message=f'Dobra vijest! Trenutna cijena Vašeg željenog proizvoda je pala! Sada iznosi {cijena2} kuna.\nPosjetite poveznicu: {link}',
                Subject='Pad cijene proizvoda!',
            )
            
            response = client.put_item(
                TableName='obavijesti',
                Item={
                    'id': {
                        'S': str(itemID)
                    },
                    'email': {
                        'S': str(email)
                        },
                    'link': {
                        'S': str(link)
                        },
                    'zeljenaCijena': {
                        'S': str(cijena)
                        },
                    'emailPoslan': {
                        'BOOL': True
                        },
                    'TopicArn': {
                        'S': str(topicArn)
                        }
                    })