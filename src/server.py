#!/usr/bin/env python3
from flask import Flask, Response, stream_with_context, request, send_from_directory
from multiprocessing import Queue
import subprocess, queue, subprocess, threading, sys, os

app = Flask('terminal')
shell = None
threads = []
out_q = None

report_path = '/tmp/report'

def stream_output(stream, q):
  while True:
    try: q.put(stream.read(1))
    except ValueError: break

@app.route('/run', methods=['POST'])
def run():
  shell.stdin.write(request.json['command'] + '\n')
  shell.stdin.flush()
  return 'ok'

@app.route('/command', methods=['POST'])
def command():
  if os.path.exists(report_path): os.remove(report_path)
  pipe = os.mkfifo(report_path)
  shell.stdin.write(f'{request.json["command"]} > {report_path}\n')
  shell.stdin.flush()
  with open(report_path) as f: return f.read()

@app.route('/newsession')
def newsession():
  global shell, out_q
  if shell: shell.terminate()
  shell = subprocess.Popen(['bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
  return 'ok'


@app.route('/subscribe')
def subscribe():
  global out_q, threads
  if out_q: out_q.close()
  out_q = Queue()
  threads = [threading.Thread(target=stream_output, args=(pipe, out_q)) for pipe in [shell.stdout, shell.stderr]]
  for t in threads: t.start()
  def generate():
    while True:
      try: yield out_q.get(timeout=1)
      except queue.Empty: pass
      except OSError: break
  return Response(stream_with_context(generate()))
  
app.route('/')(lambda: send_from_directory('static', 'index.html'))

if __name__ == '__main__':

  if os.environ.get('dev'):
    app.run(debug = True, port=1358)
  else:
    # os.system('open http://localhost:1358')
    app.run(port=1358)

