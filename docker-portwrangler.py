#
# ahh,
#

from bs4 import BeautifulSoup
import dicttoxml
import docker
from flask import Flask
from flask import request
import json
import re

app = Flask(__name__)
whoami = __name__

hheader = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html lang="en" xml:lang="en" xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>""" + whoami + """</title>
    <style>
     body { background-color: linen; }
     tr:nth-child(even) { background: #CCC; }
     tr:nth-child(odd)  { background: #FFF; }
    </style>
  </head>
  <body>
"""

hfooter = """
  <br>
  <a href="/json">json</a>
  <br>
  <a href="/xml">xml</a>
  </body>
</html>
"""

theader = """
<table>
   <tr>
    <th>Name</th>
    <th>Id</th>
    <th>PortBinding</th>
    <th>Protocol</th>
    <th>ExposedPort</th>
    <th>HostIp</th>
    <th>HostPort</th>
    <th>Link</th>
  </tr>
"""

tfooter = """
</table>
<br>
"""

ahlo = '<a href="'
ahlc = '">'
ahtc = '</a>'
h1o = '<h1>'
h1c = '</h1>'
tro = '<tr>'
trc = '</tr>'
tdo = '<td>'
tdc = '</td>'

dclient = docker.from_env()
dockerhost= dclient.info()['Name']

def get_docker_container_ids():
    cids = []
    for container in dclient.containers.list():
        cids.append(container.short_id)
    return cids

def get_docker_container_info(cid):
    c = dclient.containers.get(cid)
    cname = re.sub('^/', '', c.attrs['Name'])
    if 'ExposedPorts' in c.attrs['Config'].keys():
        ep = c.attrs['Config']['ExposedPorts']
    else:
        ep = {}
    cinfo = { 'Id': cid, 'Name': cname, 'ExposedPorts': ep, 'Ports': c.attrs['NetworkSettings']['Ports'] }
    return cinfo

def get_docker_port_info():
    cps = []
    cids = get_docker_container_ids()
    for cid in cids:
        cps.append(get_docker_container_info(cid))
    return cps

@app.route('/')
def docker_portwrangler():
    page = ''
    cps = get_docker_port_info()
    if request.args.get('format') == 'json':
        page = docker_portwrangler_json()
    elif request.args.get('format') == 'xml':
        page = docker_portwrangler_xml()
    else:
        page += hheader
        page += h1o + dockerhost + h1c
        page += theader
        for cp in cps:
            commontd = ''
            emptytd = ''
            for a in 'Name','Id':
                commontd += tdo + cp[a] + tdc
            for i in range(0, 6, 1):
                emptytd += tdo + '&nbsp;' + tdc
            if not bool(dclient.containers.get(cp['Id']).attrs['NetworkSettings']['Ports']):
                page += tro + commontd + emptytd + trc
                continue
            for pn in cp['Ports'].keys():
                if cp['Ports'][pn] == None:
                    page += tro + commontd + emptytd + trc
                    continue
                page += tro
                page += commontd
                for p in cp['Ports'][pn]:
                    page += tdo + pn + tdc
                    ep,prot = pn.split('/')
                    page += tdo + prot + tdc + tdo + ep + tdc
                    for k in 'HostIp','HostPort':
                        page += tdo + p[k] + tdc
                    plink = ''
                    if prot == 'tcp':
                        if p['HostIp'] == '0.0.0.0':
                            pd = dockerhost
                        else:
                            pd = p['HostIp']
                        pd += ':' + p['HostPort']
                        plink = ahlo + '//' + pd + ahlc + pd + ahtc
                    page += tdo + plink + tdc
                page += trc
        page += tfooter
        page += dclient.info()['SystemTime']
        page += hfooter
        page = BeautifulSoup(page, 'html.parser').prettify()
    return page

@app.route('/json')
def docker_portwrangler_json():
    return json.dumps(get_docker_port_info())

@app.route('/xml')
def docker_portwrangler_xml():
    return dicttoxml.dicttoxml(get_docker_port_info())
