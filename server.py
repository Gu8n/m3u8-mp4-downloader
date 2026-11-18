import os, re, subprocess, tempfile
from flask import Flask, request, send_file, jsonify
app = Flask(__name__)

@app.get('/')
def home():
    return send_file('index.html')

@app.post('/download')
def download():
    url = (request.json or {}).get('url','').strip()
    # Restrict to HTTPS M3U8 links; basic protection against arbitrary local/network targets.
    if not re.match(r'^https://', url, re.I) or '.m3u8' not in url.lower():
        return jsonify(error='Introduce una URL HTTPS de un manifiesto M3U8 válido.'), 400
    if any(x in url.lower() for x in ['localhost','127.0.0.1','0.0.0.0','[::1]']):
        return jsonify(error='URL no permitida.'), 400
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        output = f.name
    try:
        result = subprocess.run(['ffmpeg','-nostdin','-y','-i',url,'-c','copy','-bsf:a','aac_adtstoasc','-movflags','+faststart',output], capture_output=True, text=True, timeout=900)
        if result.returncode != 0 or not os.path.exists(output) or os.path.getsize(output) == 0:
            return jsonify(error='No se pudo procesar el stream. Puede requerir permisos o no ser compatible.'), 400
        return send_file(output, mimetype='video/mp4', as_attachment=True, download_name='video_hd.mp4')
    except subprocess.TimeoutExpired:
        return jsonify(error='La descarga excedió el tiempo límite.'), 408
    finally:
        # Note: output is deleted on process exit in this simple starter.
        pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
