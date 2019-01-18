from datetime import datetime
from flask import Flask, render_template, url_for, request, make_response, jsonify
import os, socket, sys, random, time, math, functools, requests, json, redis, psutil

#Para trazas con OpenCensus contra Jaeger
from opencensus.trace.tracer import Tracer
from opencensus.trace import time_event as time_event_module
from opencensus.trace import status
from opencensus.trace.exporters.jaeger_exporter import JaegerExporter
from opencensus.trace.exporters import print_exporter
from opencensus.trace.exporters.zipkin_exporter import ZipkinExporter
from opencensus.trace.samplers import always_on
from opencensus.trace.ext.flask.flask_middleware import FlaskMiddleware

#je = JaegerExporter(service_name="flask-app-exporter-service", host_name='jaeger-server')
#tracer=Tracer(exporter=je,sampler=always_on.AlwaysOnSampler())

#exporter = print_exporter.PrintExporter()
#tracer = Tracer(sampler=always_on.AlwaysOnSampler(), exporter=exporter)
headers={'mimetype':'application/json','Content-Type':'application/json','Server':'Who cares'}
redis_server = 'redis-server'
zipkin_server='zipkin-server'

#Conectamos a ver si hay zipkin
try_trazas=False
TRAZAS=False
if try_trazas:
  try:
    zipkin_server='zipkin-server'
    ze = ZipkinExporter(service_name="flask-app",host_name=zipkin_server,port=9411,endpoint='/api/v2/spans')
    tracer = Tracer(exporter=ze, sampler=always_on.AlwaysOnSampler())
    TRAZAS=True
    def traza_main(dict_attr,nombre='ElPadre'):
      with tracer.span(name='ElPadre') as span:
        traza(dict_attr) 

    def traza(dict_attr={}):
      with tracer.span() as span: 
        for elem in dict_attr:
          tracer.add_attribute_to_current_span(attribute_key=elem, attribute_value=dict_attr[elem])

  except Exception:
    print({'Trazas':'No hay backend de trazas'})
    params_trazas={"trazas":"NOT running"}
else:
  print({'Trazas':'No se ponen'})
  params_trazas={"trazas":"NOT Configured"}


#Conectamos a ver si hay Redis...
try_redis=True
REDIS_UP=False
if try_redis:
  try:
    dstore = redis.Redis(redis_server,socket_timeout=2,socket_connect_timeout=3)
    dstore.ping()
    dstore.incr('conexiones',1)
    REDIS_UP=True
    params_redis={"redis":"ready"}
  except Exception:
    print('{"redis":"--Redis no esta disponible--"}')
    params_redis={"redis":"NOT running"}
  if TRAZAS:
    traza_main(params_redis,'RedisConn')
else:
  print('{"redis":"Redis no se intenta"}')
  params_redis={"redis":"NOT configured"}

#Funciones para adivinar la direccion IP del servidor y metadatos sobre la IP
def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

def get_ip_address_data(ip):
  try:
    return requests.get('http://ip-api.com/json/'+ip, timeout=(3,5)).json()
  except Exception:
    return {'country':'Desconocido','regionName':'Desconocido','isp':'Desconocido'}

#Contadores para Prometheus
global hits
hits=0

global redis_con
if REDIS_UP:
  redis_con=dstore.get('conexiones').decode('utf-8')
else:
  redis_con=0

app = Flask(__name__)

if TRAZAS:
  traza_main({'conexiones':str(redis_con)},'RedisCheck')
  middleware = FlaskMiddleware(app,exporter=ze)



@app.route('/')
def home():
  global hits
  hits=hits+1
  params={}
  if request.headers.getlist("X-Forwarded-For"):
    params['ip'] = request.headers.getlist("X-Forwarded-For")[0]
  else:
   params['ip'] = request.remote_addr

  
  datos_ip=get_ip_address_data(params['ip'])
  
  if len(set(['country','region','isp']).intersection(datos_ip.keys())) == 3:
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

#Particulas
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
#/Particulas

#Elementos
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
#/Elementos

@app.route('/hello')
def hello():
  global hits
  hits=hits+1
  params={}
  if request.headers.getlist("X-Forwarded-For"):
    params['ip'] = request.headers.getlist("X-Forwarded-For")[0]
  else:
   params['ip'] = request.remote_addr

  
  datos_ip=get_ip_address_data(params['ip'])
  
  if len(set(['country','region','isp']).intersection(datos_ip.keys())) == 3:
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

@app.route('/fake')
def fake():
  global hits
  hits=hits+1
  
  params={}
  params['ip']          = request.remote_addr
  params['country' ]    = 'loccitan'
  params['region']      = 'zenda'
  params['isp']         = 'Conde Olaf Telecom'
  params['cont_ip']     = '10.1.2.3'
  params['pub_cont_ip'] = '1.2.3.4'
  params['hostname']    = socket.gethostname()
  params['hora']        = str(datetime.now())
  params['random']      = str(random.randrange(1,200))
  params['hora_requ']   = str(request.date)
  params['method']      = request.method
  
  if trazas:
    traza_main(params,"/fake")  
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
    #dstore.incr('conexiones',1)
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

@app.route('/metrics')
def metrics():
  global hits
  global redis_con

  return('# HELP hits_total El total de hits en la raiz\n\
# TYPE hits_total counter\n\
hits_total '+str(hits)+'\n\
# HELP redis_connections_total El total de conexiones que se han hecho a redis\n\
# TYPE redis_connections_total counter\n\
redis_connections_total '+str(redis_con)+'\n\
# HELP uso de CPU \n\
# TYPE cpu_gauge gauge\n\
cpu_gauge '+str(psutil.cpu_percent())+'\n\
# HELP uso de memoria gauge\n\
# TYPE mem_gauge gauge\n\
mem_gauge '+str(psutil.virtual_memory().percent)+'\n')


if __name__ == '__main__':
  app.run(host='0.0.0.0')


