from flask import Flask, request
from waitress import serve
import lzma
import struct
from base64 import b64encode
from paste.translogger import TransLogger
import os
import sys
import pyjson5

app = Flask(__name__)

directory = 'modules'
modules = []

# to generate a password you can use `openssl rand -hex 32` if you have openssl installed
api_key = os.getenv('STWEAKS_MANAGEMENT_API_KEY') or 'changeme'

if api_key == 'changeme':
    print("[-] La clef d'API ne peut pas être celle par défaut, relancer le programme avec une clef différente en changeant la variable d'envrionnement STWEAKS_MANAGEMENT_API_KEY")
    sys.exit(-1)

# convert to compatible LZMA then encode with base64
# usable with util.Decompress
def encode_lua(s):
    input_bytes = s.encode('utf-8')
    uncompressed_size = len(input_bytes)
    
    lzma_filters = [
        {'id': lzma.FILTER_LZMA1, 'preset': 5, 'dict_size': 1 << 16}
    ]

    compressed_data = lzma.compress(input_bytes, format=lzma.FORMAT_ALONE, filters=lzma_filters)
    lzma_props = compressed_data[:5]
    uncompressed_size = struct.pack('<Q', uncompressed_size)
    compressed_body = compressed_data[13:]
    result = b64encode(lzma_props + uncompressed_size + compressed_body)
    
    return result

# initialize existing modules
def initialize_modules():
    global modules
    with open('config.json', 'r') as f:
        modules = pyjson5.loads(f.read())

    for m in modules:
        f = os.path.join(directory, m['filename'])
        if os.path.isfile(f):
            file = open(f, 'r')
            buffer = file.read()
            m['encoded_code'] = encode_lua(buffer)

@app.route('/')
def index():
    return {'message': 'Stweaks server 1.0'}

@app.route('/mgmt/reload')
def reload_modules():
    key = request.args.get('key')
    if key is None or key != api_key:
        return {'message': '401 Unauthorized'}, 401
    initialize_modules()
    return {'message': 'modules successfully reloaded'}

@app.route('/new')
def get_code():
    name = request.args.get('check')
    if name is None:
        return {'message': '400 Bad Request'}, 400
    for m in modules:
        print(m)
        if m['name'] == name:
            return m['encoded_code'], 200, {'Content-Type': 'text/plain; charset=utf8'}
    return {'message': '404 Not Found'}, 404

@app.route('/update')
def list_modules():
    steamid = request.args.get('steamid')
    if steamid is None:
        return {'message':  '400 Bad Request'}, 400
    modules_to_show = [
        {'name': m['name'], 'author': m['author'], 'comments': m['description']} for m in modules if (steamid in m['whitelist']) or len(m['whitelist']) == 0
    ]
    return modules_to_show

if __name__ == '__main__':
    initialize_modules()
    serve(TransLogger(app), listen='*:8080')

