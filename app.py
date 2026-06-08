from flask import Flask, render_template, send_file, request, jsonify
import os
from pathlib import Path
import json
from datetime import datetime

app = Flask(__name__)

# Configuración
CARPETA_PRINCIPAL = Path(r"C:\MAMP\htdocs\galeria_vehiculos\FOTOS")
EXTENSIONES_PERMITIDAS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
ARCHIVO_FAVORITOS = "favoritos.json"
ARCHIVO_ETIQUETAS = "etiquetas.json"

# Cargar favoritos y etiquetas
def cargar_favoritos():
    if os.path.exists(ARCHIVO_FAVORITOS):
        with open(ARCHIVO_FAVORITOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def guardar_favoritos(favoritos):
    with open(ARCHIVO_FAVORITOS, 'w', encoding='utf-8') as f:
        json.dump(favoritos, f, ensure_ascii=False, indent=2)

def cargar_etiquetas():
    if os.path.exists(ARCHIVO_ETIQUETAS):
        with open(ARCHIVO_ETIQUETAS, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def guardar_etiquetas(etiquetas):
    with open(ARCHIVO_ETIQUETAS, 'w', encoding='utf-8') as f:
        json.dump(etiquetas, f, ensure_ascii=False, indent=2)

@app.route('/')
def galeria():
    """Lee todas las carpetas y muestra la galería"""
    vehiculos = []
    
    if CARPETA_PRINCIPAL.exists():
        for carpeta in CARPETA_PRINCIPAL.iterdir():
            if carpeta.is_dir():
                imagenes = []
                for archivo in carpeta.iterdir():
                    if archivo.suffix.lower() in EXTENSIONES_PERMITIDAS:
                        # Obtener metadatos de la imagen
                        stat = archivo.stat()
                        imagenes.append({
                            'nombre': archivo.name,
                            'tamaño': stat.st_size,
                            'fecha_modificacion': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        })
                
                imagenes.sort(key=lambda x: x['nombre'])
                
                if imagenes:
                    vehiculos.append({
                        'nombre': carpeta.name,
                        'imagenes': imagenes,
                        'ruta': str(carpeta),
                        'total_imagenes': len(imagenes)
                    })
    
    vehiculos.sort(key=lambda x: x['nombre'])
    
    favoritos = cargar_favoritos()
    etiquetas = cargar_etiquetas()
    
    print(f"📁 Encontradas {len(vehiculos)} carpetas con imágenes")
    
    return render_template('galeria.html', vehiculos=vehiculos, favoritos=favoritos, etiquetas=etiquetas)

@app.route('/imagen/<path:ruta_imagen>')
def servir_imagen(ruta_imagen):
    """Sirve las imágenes usando Path de Python"""
    try:
        ruta_completa = CARPETA_PRINCIPAL / ruta_imagen
        
        if ruta_completa.exists() and ruta_completa.suffix.lower() in EXTENSIONES_PERMITIDAS:
            return send_file(ruta_completa)
        else:
            return "Imagen no encontrada", 404
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return "Error al cargar la imagen", 500

# API para favoritos
@app.route('/api/favorito', methods=['POST'])
def toggle_favorito():
    data = request.json
    ruta_imagen = data.get('ruta')
    favoritos = cargar_favoritos()
    
    if ruta_imagen in favoritos:
        del favoritos[ruta_imagen]
        es_favorito = False
    else:
        favoritos[ruta_imagen] = True
        es_favorito = True
    
    guardar_favoritos(favoritos)
    return jsonify({'success': True, 'es_favorito': es_favorito})

# API para etiquetas
@app.route('/api/etiqueta', methods=['POST'])
def guardar_etiqueta():
    data = request.json
    ruta_imagen = data.get('ruta')
    etiqueta = data.get('etiqueta')
    etiquetas = cargar_etiquetas()
    
    if ruta_imagen not in etiquetas:
        etiquetas[ruta_imagen] = []
    
    if etiqueta in etiquetas[ruta_imagen]:
        etiquetas[ruta_imagen].remove(etiqueta)
    else:
        etiquetas[ruta_imagen].append(etiqueta)
    
    guardar_etiquetas(etiquetas)
    return jsonify({'success': True, 'etiquetas': etiquetas[ruta_imagen]})

# API para eliminar imagen
@app.route('/api/eliminar', methods=['DELETE'])
def eliminar_imagen():
    data = request.json
    ruta_imagen = data.get('ruta')
    ruta_completa = CARPETA_PRINCIPAL / ruta_imagen
    
    try:
        if ruta_completa.exists():
            ruta_completa.unlink()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'No existe'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)