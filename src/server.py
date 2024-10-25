#!/usr/bin/env python3
from flask import Flask, Response, stream_with_context, request, send_from_directory
from multiprocessing import Queue
import subprocess, queue, subprocess, threading, sys, os

app = Flask('terminal')
shell = None
threads = []
out_q = None

report_path = '/tmp/report'

sessions = {}

def stream_output(stream, q):
  while True:
    try: q.put(stream.read(1))
    except ValueError: break

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
    self.shell = subprocess.Popen(['bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    self.out_q = None
  
  def subscribe(self):
    if self.out_q: self.out_q.close()
    self.out_q = Queue()
    self.threads = [threading.Thread(target=stream_output, args=(pipe, self.out_q)) for pipe in [self.shell.stdout, self.shell.stderr]]
    for t in self.threads: t.start()
    def generate():
      while True:
        try: yield self.out_q.get(timeout=1)
        except queue.Empty: pass
        except OSError: break
    return Response(stream_with_context(generate()), content_type='text/plain')
  
  def command(self):
    if os.path.exists(report_path+self.id): os.remove(report_path+self.id)
    os.mkfifo(report_path+self.id)
    self.shell.stdin.write(f'{request.get_json()["command"]} > {report_path+self.id}\n')
    self.shell.stdin.flush()
    with open(report_path+self.id) as f: return f.read()
  
  def run(self):
    command = request.get_json()['command']
    self.shell.stdin.write(command + '\n')
    self.shell.stdin.flush()
    return 'ok'

for fname in TerminalSession.__dict__:
  if fname.startswith('_'): continue
  def handler():
    name = fname
    return lambda : getattr(request_session(), name)()
  app.route('/'+fname, methods=['POST'], endpoint = '/'+fname)(handler())

app.route('/')(lambda: send_from_directory('static', 'index.html'))

if __name__ == '__main__':

  if os.environ.get('dev'):
    app.run(debug = True, port=1358)
  else:
    # os.system('open http://localhost:1358')
    app.run(port=1358)
