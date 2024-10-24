#!/usr/bin/env python3
from flask import Flask, Response, stream_with_context, request, send_from_directory
from multiprocessing import Queue
import subprocess, queue, subprocess, threading, sys, os

app = Flask('terminal')
shell = None
threads = []

def stream_output(stream, q):
  while True:
    try: q.put(stream.read(1))
    except ValueError: break

@app.route('/run', methods=['POST'])
def run():
  shell.stdin.write(request.json['command'] + '\n')
  shell.stdin.flush()
  return 'ok'

@app.route('/subscribe')
def subscribe():
  global shell, threads, out_q
  if shell:
    shell.terminate()
    out_q.close()

  out_q = Queue()
  shell = subprocess.Popen(['bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

  threads = [threading.Thread(target=stream_output, args=(pipe, out_q)) for pipe in [shell.stdout, shell.stderr]]
  for t in threads: t.start()
  def generate():
    while True:
      try: yield out_q.get(timeout=1)
      except queue.Empty:pass
      except OSError:break
  return Response(stream_with_context(generate()))
  
app.route('/')(lambda: send_from_directory('static', 'index.html'))

if __name__ == '__main__':

  if os.environ.get('dev'): app.run(debug = True, port=1358)
  else:
    threading.Thread(target=lambda: os.system('sleep .5 && open http://localhost:1358')).start()
    app.run(port=1358)

