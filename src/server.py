#!/usr/bin/env python3
from flask import Flask, Response, stream_with_context, request, send_from_directory
from multiprocessing import Queue

import functools, subprocess, queue, subprocess, threading, sys, os, time

app = Flask('terminal', static_folder='static')
shell = None
threads = []
out_q = None
report_path = '/tmp/report'
sessions = {}

default_shell = os.environ.get('SHELL')

sess_counter = 0
def request_session(): return sessions.get(int(request.get_json()['session']), None)

@app.route('/newsession')
def newsession():
  global sess_counter
  sess_counter += 1
  sessions[sess_counter] = TerminalSession(sess_counter)
  return str(sess_counter)

class TerminalSession:
  def __init__(self, id):
    self.id = str(id)
    self.shell = subprocess.Popen([default_shell], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    self.out_q = None
  
  def subscribe(self):
    if self.out_q: self.out_q.close()
    self.out_q = Queue()

    def stream_output(stream, q):
      while True:
        try:
          c=stream.read(1)
          if c: q.put(c)
          else: time.sleep(0.1)
        except ValueError:
          print('ValueError, thread exiting')
          break

    self.threads = [threading.Thread(target=stream_output, args=(pipe, self.out_q)) for pipe in [self.shell.stdout, self.shell.stderr]]
    for t in self.threads: t.start()
    def generate():
      while True:
        try: yield self.out_q.get(timeout=1)
        except queue.Empty: pass
        except OSError as e: break
    return Response(stream_with_context(generate()), content_type='text/plain')
  
  def command(self):
    if os.path.exists(report_path+self.id): os.remove(report_path+self.id)
    os.mkfifo(report_path+self.id)
    self._command(f'{request.get_json()["command"]} > {report_path+self.id}\n')
    with open(report_path+self.id) as f: return f.read()
  
  def run(self):
    self._command(request.get_json()['command'])
    return 'ok'
  
  def _command(self, command):
    self.shell.stdin.write(command + '\n')
    self.shell.stdin.flush()

def handler(name): return lambda : getattr(request_session(), name)()
for fname in dir(TerminalSession):
  if not fname.startswith('_'): app.route('/'+fname, methods=['POST'], endpoint = '/'+fname)(handler(fname))

# @functools.lru_cache()
# def getstatic(path):
#   with open(app.static_folder + '/' + path) as f: return f.read()

@app.route('/')
def index(): 
  # return getstatic('index.html')
  return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def logo(path):
  # return getstatic(path)
  return send_from_directory(app.static_folder, path)

@app.route('/get_file/<path:path>')
def get_file(path): return send_from_directory('/', path)

if __name__ == '__main__':
  dev = os.environ.get('dev')
  app.run(debug=os.environ.get('dev'), port=1358)
  if not dev: os.system('open http://localhost:1358')
