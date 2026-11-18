import os, re, subprocess, tempfile, logging
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.get('/')
def home():
    return send_file('index.html')

@app.post('/download')
def download():
    data = request.get_json(silent=True) or {}
    url = str(data.get('url', '')).strip()
    if not re.match(r'^https://', url, re.I) or '.m3u8' not in url.lower():
        return jsonify(error='Introduce una URL HTTPS de un manifiesto M3U8 válido.'), 400
    if any(x in url.lower() for x in ['localhost','127.0.0.1','0.0.0.0','[::1]']):
        return jsonify(error='URL no permitida.'), 400
    output = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            output = f.name
        logging.info('Inicio de procesamiento de manifiesto.')
        result = subprocess.run(
            ['ffmpeg','-nostdin','-y','-i',url,'-c','copy','-bsf:a','aac_adtstoasc','-movflags','+faststart',output],
            capture_output=True, text=True, timeout=900
        )
        if result.returncode != 0 or not os.path.exists(output) or os.path.getsize(output) == 0:
            logging.error('FFmpeg fallo: %s', (result.stderr or '')[-1800:])
            return jsonify(error='FFmpeg no pudo procesar el enlace. Revisa que el stream sea accesible y permitido; detalles registrados en el servidor.'), 400
        logging.info('Procesamiento completado. Archivo listo.')
        return send_file(output, mimetype='video/mp4', as_attachment=True, download_name='video_hd.mp4')
    except subprocess.TimeoutExpired:
        logging.error('Procesamiento excedio el tiempo limite de 15 minutos.')
        return jsonify(error='El procesamiento excedió el límite de 15 minutos. Prueba con un fragmento más corto.'), 408
    except Exception:
        logging.exception('Error inesperado en /download')
        return jsonify(error='Error interno del servidor al procesar la solicitud.'), 500
    finally:
        pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    
