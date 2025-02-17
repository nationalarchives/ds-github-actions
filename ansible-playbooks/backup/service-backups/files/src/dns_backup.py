import requests
import os
import json
import tarfile
import boto3
from datetime import datetime
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
from private_tools import get_asm_parameters

def main():
    asm_key = os.environ['ASM_KEY']
    api_url = os.environ['DNS_API_URL']
    access_point = os.environ['S3_ACCESS_POINT']

    data_dir = '/dns-totaluptime-data'
    tar_dir = '/dns-totaluptime-tar'
    ap_dir = 'tna-external-services/dns-totaluptime'

    # read repo credentials from ASM
    secret_values = json.loads(get_asm_parameters(name=asm_key, aws_region='eu-west-2'))
    user = secret_values['user']
    pw = secret_values['pass']

    s3_client = boto3.client("s3")

    domains = list()
    basic = HTTPBasicAuth(user, pw)
    r = requests.get(api_url + "/CloudDNS/Domain/All", auth=basic)
    if r.status_code == 200:
        xml = r.text
        root = ET.fromstring(xml)
        rows = root.find('{http://schemas.datacontract.org/2004/07/Cloud.APIClasses.CloudDNS}rows')
        for domain in rows.findall('{http://schemas.datacontract.org/2004/07/Cloud.APIClasses.CloudDNS}APICloudDNS_Domain'):
            domains.append(domain.find('{http://schemas.datacontract.org/2004/07/Cloud.APIClasses.CloudDNS}domainName').text)

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    if not os.path.exists(tar_dir):
        os.makedirs(tar_dir)

    for domain in domains:
        r = requests.get(api_url + "/CloudDNS/Domain/Export/" + domain, auth=basic)
        if r.status_code == 200:
            root = ET.fromstring(r.text)
            message = root.find('{http://schemas.datacontract.org/2004/07/Cloud.APIClasses}message').text
            if message:
                with open(f'{data_dir}/{domain}.txt', "w") as f:
                    f.write(message)

    tar_name = f'dns_zones_{str(datetime.now()).replace(" ", "_").replace(":", "-")}.tar'
    tar_file = f'{tar_dir}/dns_zones_{str(datetime.now()).replace(" ", "_").replace(":", "-")}.tar'
    with tarfile.open(tar_file, 'w') as tar:
        for entry in os.scandir(data_dir):
            if entry.is_file():
                tar.add(f'{data_dir}/{entry.name}')
                os.remove(f'{data_dir}/{entry.name}')

    s3_client.upload_file(tar_file, access_point , f'{ap_dir}/{tar_name}',
                          ExtraArgs={'Metadata': {'x-amz-meta-legal_hold': 'ON'}}
                          )
    os.remove(f'{tar_dir}/{tar_file}')

if __name__ == "__main__":
    main()
