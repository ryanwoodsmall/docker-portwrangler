#
# ahh,
#

import docker
from flask import Flask
from flask import request
import json
import re

app = Flask(__name__)
whoami = __name__

hheader = """
<html>
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
  </tr>
"""

tfooter = """
</table>
<br>
"""

h1o = '<h1>'
h1c = '</h1>'
tro = '<tr>'
trc = '</tr>'
tdo = '<td>'
tdc = '</td>'

dclient = docker.from_env()

def get_docker_container_ids():
    cids = []
    for container in dclient.containers.list():
        cids.append(container.short_id)
    return cids

def get_docker_container_info(cid):
    c = dclient.containers.get(cid)
    cname = re.sub('^/', '', c.attrs['Name'])
    cinfo = { 'Id': cid, 'Name': cname, 'Ports': c.attrs['NetworkSettings']['Ports'] }
    return cinfo

@app.route('/')
def docker_portwrangler():
    page = ''
    cids = get_docker_container_ids()
    cps = []
    for cid in cids:
        cps.append(get_docker_container_info(cid))
    cpj = json.dumps([cps])
    if request.args.get('format') == 'json':
        page += cpj
    else:
        page += hheader
        page += h1o + dclient.info()['Name'] + h1c
        page += theader
        for cp in cps:
            commontd = ''
            emptytd = ''
            for a in 'Name','Id':
                commontd += tdo + cp[a] + tdc
            for i in range(0, 5, 1):
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
                page += trc
        page += tfooter
        page += dclient.info()['SystemTime']
        page += hfooter
    return page
