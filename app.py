from flask import Flask, render_template, url_for, request, make_response, jsonify
import os, socket, sys, random, time, math, functools, requests, json, redis

from werkzeug.wsgi import DispatcherMiddleware
from prometheus_client import make_wsgi_app
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY

#Cabeceras http modificadas para algunas respuestas en JSON...
headers={'mimetype':'application/json','Content-Type':'application/json','Server':'Who cares'}
redis_server = 'redis-server'

#Conectamos a ver si hay Redis...
try:
  dstore = redis.Redis(redis_server)
  dstore.ping()
  REDIS_UP=True
except redis.ConnectionError:
  print('{"redis":"Redis no esta disponible"}')
  REDIS_UP=False

#Funcion para adivinar la direccion IP del servidor...
def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

app = Flask(__name__)

@app.route('/')
def hello():
  params={}
  if request.headers.getlist("X-Forwarded-For"):
    params['ip'] = request.headers.getlist("X-Forwarded-For")[0]
  else:
   params['ip'] = request.remote_addr
  
  datos_ip=requests.get('http://ip-api.com/json/'+params['ip'])
  
  if len(set(['country','region','isp']).intersection(datos_ip.json().keys())) == 3:
    params['country']=datos_ip.json()['country']
    params['region']=datos_ip.json()['regionName']
    params['isp']=datos_ip.json()['isp']

  else:
    params['country']='desconocido'
    params['region']='desconocido'
    params['isp']='desconocido'

  params['cont_ip']=get_ip_address()
  params['pub_cont_ip']=requests.get('http://ident.me').text
  params['hostname']=socket.gethostname()
  return render_template('hello.html', params=params)

@app.route('/healthz')
def healthz():
  body={'status':208,'todo':'bien'}
  status=body['status']
  headers={'mimetype':'application/json','Content-Type':'application/json'}

  resp=make_response((jsonify(body), status, headers))
  return resp

@app.route('/redis')
def redis():
  if REDIS_UP:
    dstore.incr('conexiones',1)
    dato=dstore.get('conexiones').decode('utf-8')
    resp=make_response('{"conexiones":'+str(dato)+',"Servidor":"'+socket.gethostname()+'"}')
  else:
    resp=make_response('{"redis":"Error"}')
    
  return resp

@app.route('/cabeceras')
def cabeceras():
  status=200

  resp_dict={}
  for elemento in request.headers.keys():
    resp_dict[str(elemento)]=request.headers.getlist(elemento)[0]
  
  resp=make_response((jsonify(resp_dict), status, headers))
  return resp

@app.route('/particulas')
def particulas():
  return render_template('particulas.html')

@app.route('/particularandom')
def particularandom():
  with open('static/particulas/particulas.json') as particulas_data:
    particulas=json.load(particulas_data)
  
  particula=random.choice(list(particulas.keys()))
  props=particulas[particula]

  if REDIS_UP:
    dstore.incr(particula,1)
    props['vistas']=dstore.get(particula).decode('utf-8')
  else:
    props['vistas']=0 
  
  return render_template('particularandom.html', params=props)

@app.route('/particulasvisitadas')
def particulasvisitadas():
  resp_dict={}
  
  with open('static/particulas/particulas.json') as particulas_data:
    particulas=json.load(particulas_data)

  if REDIS_UP:
    for particula in particulas:
      if dstore.get(particula) is not None:
        resp_dict[particula]=dstore.get(particula).decode('utf-8')
      else:
        resp_dict[particula]=0
  else:
    resp_dict={"redis":"Error"}

  resp=make_response(jsonify(resp_dict),headers)
  return resp

@app.route('/elementos')
def elementos():
  return render_template('elementos.html')

@app.route('/elementorandom')
def elementorandom():
  with open('static/elementos/TablaPeriodica.json') as elementos_data:
    elementos=json.load(elementos_data)

  elemento=random.choice(list(elementos.keys()))
  props=elementos[elemento]
  if REDIS_UP:
    dstore.incr(elemento,1)
    props['vistas']=dstore.get(elemento).decode('utf-8')
  else:
    props['vistas']=0

  return render_template('elementorandom.html', params=props)


@app.route('/elementosvisitados')
def elementosvisitados():
  resp_dict={}
  
  with open('static/elementos/TablaPeriodica.json') as elementos_data:
    elementos=json.load(elementos_data)

  if REDIS_UP:
    for elemento in elementos:
      if dstore.get(elemento) is not None:
        resp_dict[elemento]=dstore.get(elemento).decode('utf-8')
      else:
        resp_dict[elemento]=0
  else:
    resp_dict={"redis":"Error"}

  resp=make_response(jsonify(resp_dict),headers)
  return resp

@app.route('/prueba')
def prueba():
  return('# HELP tonterias_varias_total las tonterias\n\
# TYPE tonterias_varias_total counter\n\
tonterias_varias_total 28.1\n\
# HELP tonterias_varias_otras las tonterias\n\
# TYPE tonterias_otras_total counter\n\
tonterias_otras_total 43.34\n')

#Instrumentacion con Prometheus
class CustomCollector(object):
    def collect(self):
        c=CounterMetricFamily('redis_con', 'las conexiones de redis', value=float(dstore.get('conexiones').decode('utf-8')))
        yield c

REGISTRY.register(CustomCollector())
app_dispatch = DispatcherMiddleware(app, {'/metrics': make_wsgi_app()})
#/Instrumentacion con Prometheus
#Para que funcione, arrancar con 
#uwsgi --http 192.168.56.1:5000 --wsgi-file app.py --callable app_dispatch

if __name__ == '__main__':
  app.run()


