from flask import Flask, render_template, url_for, request
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
import concurrent.futures
import boto3
import uuid
from rjecnik import webshop_dict

clientDynamo = boto3.client('dynamodb')
resourceSNS = boto3.resource('sns')
clientSNS = boto3.client('sns')

app = Flask(__name__)
@app.route('/')
def index():
    print('test1')
    return render_template('index.html')


@app.route('/pretraga')
def pretraga():
    if 'item' in request.args:
        item = request.args['item']
        
    rezultati_proizvod = []
    rezultati_cijena = []
    rezultati_linkovi = []
    svi_proizvodi = []
    
    headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36"}
    def scrape_ws(shop):
        stranica = requests.get(url=shop['url'] + item, headers = headers)
        soup = BeautifulSoup(stranica.content,'html5lib')
        
        tagovi = ['a', 'p', 'span', 'h1', 'h2', 'h3','h3 title', 'div', 'ul', 'ol','ins', 'li','section','table','th', 'tb', 'label']
        
        for naziv in soup.find_all (tagovi, class_ = shop['naziv_pr']):
            nazivS = naziv.get_text()
            nazivSS = nazivS.strip()
            rezultati_proizvod.append(nazivSS)
        
        for link in soup.find_all (shop['link_tag'], class_ = shop['link_class']):
            domain = urlparse(shop['url']).netloc
            #print(link.find('a')['href'])
            linkovi=str(link.find('a')['href'])
            if 'http' not in linkovi:
                linkovi = 'https://' + domain + linkovi
            rezultati_linkovi.append(linkovi)
            
                    
        for cijena in soup.find_all (tagovi, class_ = shop['cijena_pr']):
            cijenaS = cijena.get_text()
            cijenaSS = cijenaS.strip()
            cijenaSS = str(cijenaSS).replace('\xa0Kn', '').replace(' kn', '').replace('Kn','').replace('.', '').replace(',','')
            lipe = cijenaSS[-2:]
            if shop['ime'] != 'Mall.hr':
                cijenaSS = cijenaSS[:-2]
                cijenaSS = cijenaSS + '.' + lipe
            cijenaSS = float(cijenaSS)
            rezultati_cijena.append(cijenaSS)
            
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(scrape_ws, webshop_dict) 
        
    try:              
        for i, proizvod in enumerate(rezultati_proizvod):
            svi_proizvodi.append({
                'Naziv': proizvod,
                'Cijena(HRK)': rezultati_cijena[i],
                'Link': rezultati_linkovi[i]
                })         
        print(svi_proizvodi)
        return render_template('pretraga.html', svi_proizvodi = svi_proizvodi)
    
    except IndexError:
        return render_template('pretraga2.html')
    
@app.route('/obavijesti', methods = ['POST'])
def obavijesti():
    if request.method == 'POST':
        output = request.form
    
    return render_template('obavijesti.html', url = output['link'])


@app.route('/pretplata', methods=['POST'])
def pretplata():
    if request.method == 'POST':
        email = request.form['email']
        zeljenaCijena = request.form['zeljenaCijena']
        link = request.form['link']
        
        response = clientSNS.create_topic(
            Name=str(uuid.uuid4()),
        )
    
        clientDynamo.put_item(
            TableName='obavijesti',
            Item={
                'id': {
                    'S': str(uuid.uuid4())
                },
                'email': {
                    'S': email
                    },
                'link': {
                    'S': link
                    },
                'zeljenaCijena': {
                    'S': str(zeljenaCijena)
                    },
                'emailPoslan': {
                    'BOOL': False
                    },
                'TopicArn': {
                    'S': response['TopicArn']
                    }
                })
        
        
        topic = resourceSNS.Topic(response['TopicArn'])
       
        topic.subscribe(
            Protocol='email',
            Endpoint=email,
            )
        
        return render_template('index.html')
        
@app.errorhandler(404)
def page_not_found(error):
    return render_template('not_found.html'), 404

if __name__ == "__main__":
    app.run(debug=True)
    