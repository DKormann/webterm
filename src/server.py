#!/usr/bin/env python3
from flask import Flask, Response, stream_with_context, request, send_from_directory
from multiprocessing import Queue
import subprocess, queue, subprocess, threading, sys, os, time

app = Flask('terminal')
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

app.route('/')(lambda: send_from_directory('static', 'index.html'))
app.route('/<path:path>', endpoint='logo')(lambda path: send_from_directory('static', path))

if __name__ == '__main__':
  app.run(debug=os.environ.get('dev'), port=1358)
