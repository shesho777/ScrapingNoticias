from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import threading

app = Flask(__name__)

# Cache para noticias
news_cache = {
    'eltiempo': {'data': None, 'last_update': None},
    'lanacion': {'data': None, 'last_update': None}
}

def scrape_eltiempo():
    """Scraping de noticias médicas de El Tiempo"""
    url = "https://www.eltiempo.com/noticias/medicina"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        seccion = soup.find('section', class_='u-estructura-home__seccion')
        if not seccion:
            return None
        
        noticias = []
        for articulo in seccion.find_all('div', class_='c-landing-tema__articulo'):
            titulo = articulo.find('h3', class_='c-articulo__titulo').get_text(strip=True)
            enlace = "https://www.eltiempo.com" + articulo.find('a')['href']
            imagen = articulo.find('img')
            
            noticia = {
                'titulo': titulo,
                'enlace': enlace,
                'imagen': imagen['src'] if imagen else None,
                'fecha': articulo.find('span', class_='c-articulo__fecha').get_text(strip=True),
                'fuente': 'El Tiempo'
            }
            
            print("[El Tiempo] 📌", noticia)  # 👈 imprime cada noticia
            noticias.append(noticia)
        
        return noticias
    except Exception as e:
        print(f"Error scraping El Tiempo: {str(e)}")
        return None

def scrape_lanacion():
    """Scraping de noticias médicas de La Nación"""
    url = "https://www.lanacion.com.ar/tema/medicina/"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        seccion = soup.find('div', class_='row-gap-tablet-3')
        if not seccion:
            return None
        
        noticias = []
        for articulo in seccion.find_all('article', class_='mod-article'):
            titulo = articulo.find('h2', class_='com-title').get_text(strip=True)
            enlace = "https://www.lanacion.com.ar" + articulo.find('a')['href']
            imagen = articulo.find('img')
            
            noticia = {
                'titulo': titulo,
                'enlace': enlace,
                'imagen': imagen.get('src') if imagen else None,
                'autor': articulo.find('strong', class_='mod-marquee').get_text(strip=True) if articulo.find('strong', class_='mod-marquee') else None,
                'fecha': articulo.find('time', class_='com-date').get_text(strip=True),
                'fuente': 'La Nación'
            }
            
            print("[La Nación] 📰", noticia)  # 👈 imprime cada noticia
            noticias.append(noticia)
        
        return noticias
    except Exception as e:
        print(f"Error scraping La Nación: {str(e)}")
        return None

def update_cache():
    """Actualiza el cache de noticias periódicamente"""
    while True:
        print("\n🔄 Actualizando cache de noticias...\n")
        news_cache['eltiempo']['data'] = scrape_eltiempo()
        news_cache['lanacion']['data'] = scrape_lanacion()
        news_cache['eltiempo']['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        news_cache['lanacion']['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("\n✅ Cache actualizado\n")
        threading.Event().wait(3600)  # Actualizar cada hora

# Iniciar hilo de actualización de cache
threading.Thread(target=update_cache, daemon=True).start()

@app.route('/')
def home():
    return """
    <h1>API de Noticias Médicas</h1>
    <p>Endpoints disponibles:</p>
    <ul>
        <li><a href="/eltiempo">/eltiempo</a> - Noticias de El Tiempo</li>
        <li><a href="/lanacion">/lanacion</a> - Noticias de La Nación</li>
    </ul>
    """

@app.route('/eltiempo', methods=['GET'])
def get_eltiempo():
    """Endpoint para obtener noticias de El Tiempo"""
    noticias = news_cache['eltiempo']['data']
    if not noticias:
        return jsonify({'error': 'No se pudieron obtener noticias de El Tiempo'}), 500
    
    return jsonify({
        'noticias': noticias,
        'total': len(noticias),
        'ultima_actualizacion': news_cache['eltiempo']['last_update']
    })

@app.route('/lanacion', methods=['GET'])
def get_lanacion():
    """Endpoint para obtener noticias de La Nación"""
    noticias = news_cache['lanacion']['data']
    if not noticias:
        return jsonify({'error': 'No se pudieron obtener noticias de La Nación'}), 500
    
    return jsonify({
        'noticias': noticias,
        'total': len(noticias),
        'ultima_actualizacion': news_cache['lanacion']['last_update']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
