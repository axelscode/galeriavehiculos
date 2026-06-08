from flask import Flask, render_template, jsonify, request, send_from_directory
import os
from pathlib import Path
import json
from datetime import datetime

app = Flask(__name__)

# Configuration
BASE_DIR = Path(__file__).parent
FOTOS_DIR = BASE_DIR / 'FOTOS'
DATA_FILE = BASE_DIR / 'data.json'

# Ensure directories exist
FOTOS_DIR.mkdir(exist_ok=True)

# Load or initialize data
def load_data():
    """Load favorites and tags data from JSON file"""
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'favorites': {}, 'tags': {}}

def save_data(data):
    """Save favorites and tags data to JSON file"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Global data
data = load_data()
favorites = data.get('favorites', {})
tags = data.get('tags', {})

def get_vehicles():
    """Scan FOTOS folder and return structured data"""
    vehicles = []
    
    if not FOTOS_DIR.exists():
        return vehicles
    
    for folder in sorted(FOTOS_DIR.iterdir()):
        if folder.is_dir():
            images = []
            for img_file in sorted(folder.iterdir()):
                if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                    stat = img_file.stat()
                    images.append({
                        'nombre': img_file.name,
                        'tamaño': stat.st_size,
                        'fecha_modificacion': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            if images:  # Only add folders that contain images
                vehicles.append({
                    'nombre': folder.name,
                    'total_imagenes': len(images),
                    'imagenes': images
                })
    
    return vehicles

# Routes
@app.route('/')
def index():
    """Main page"""
    vehicles = get_vehicles()
    return render_template('galeria.html', 
                         vehiculos=vehicles,
                         favoritos=favorites,
                         etiquetas=tags)

@app.route('/imagen/<path:ruta>')
def serve_image(ruta):
    """Serve images from FOTOS folder"""
    return send_from_directory(FOTOS_DIR, ruta)

@app.route('/api/favorito', methods=['POST'])
def toggle_favorite():
    """Toggle favorite status for an image"""
    data_req = request.json
    ruta = data_req.get('ruta')
    
    key = ruta
    if key in favorites:
        del favorites[key]
        es_favorito = False
    else:
        favorites[key] = True
        es_favorito = True
    
    # Save to file
    save_data({'favorites': favorites, 'tags': tags})
    
    return jsonify({
        'success': True,
        'es_favorito': es_favorito
    })

@app.route('/api/etiqueta', methods=['POST'])
def add_tag():
    """Add a tag to an image"""
    data_req = request.json
    ruta = data_req.get('ruta')
    etiqueta = data_req.get('etiqueta', '').strip()
    
    if not etiqueta:
        return jsonify({'success': False, 'error': 'Tag cannot be empty'})
    
    key = ruta
    if key not in tags:
        tags[key] = []
    
    if etiqueta not in tags[key]:
        tags[key].append(etiqueta)
    
    # Save to file
    save_data({'favorites': favorites, 'tags': tags})
    
    return jsonify({
        'success': True,
        'etiquetas': tags[key]
    })

@app.route('/api/eliminar', methods=['DELETE'])
def delete_image():
    """Delete an image file"""
    data_req = request.json
    ruta = data_req.get('ruta')
    
    if not ruta:
        return jsonify({'success': False, 'error': 'No route specified'})
    
    file_path = FOTOS_DIR / ruta
    
    if not file_path.exists():
        return jsonify({'success': False, 'error': 'File not found'})
    
    try:
        # Delete the file
        os.remove(file_path)
        
        # Remove from favorites and tags
        key = ruta
        if key in favorites:
            del favorites[key]
        if key in tags:
            del tags[key]
        
        # Save data
        save_data({'favorites': favorites, 'tags': tags})
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/vehiculos', methods=['GET'])
def get_vehicles_api():
    """API endpoint to get vehicles data"""
    vehicles = get_vehicles()
    return jsonify({
        'vehiculos': vehicles,
        'favoritos': favorites,
        'etiquetas': tags
    })

if __name__ == '__main__':
    print(f"📁 FOTOS directory: {FOTOS_DIR.absolute()}")
    print(f"📊 Data file: {DATA_FILE.absolute()}")
    print("\n🚀 Starting Flask server...")
    print("🌐 Open http://localhost:5000 in your browser\n")
    app.run(debug=True, host='0.0.0.0', port=5000)