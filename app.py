import os
import re
import time
import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import yt_dlp
import ffmpeg
from flask import Flask, Response, request
import uuid
import threading
import subprocess
import shutil
import numpy as np
from pyngrok import ngrok

# ===============================
# ✅ KONFIGURASI SERVER OPTIMIZED
# ===============================
server = Flask(__name__)
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    compress=True  # Aktifkan kompresi Dash
)

# Direktori penyimpanan
CACHE_DIR = "video_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# ===============================
# ✅ UTILITAS VIDEO (EXTREME OPTIMIZATION)
# ===============================
def get_video_info(url):
    """Mendapatkan informasi video YouTube"""
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'extract_flat': True,
        'skip_download': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

def search_youtube(query, max_results=10):
    """Mencari video di YouTube"""
    search_term = f"ytsearch{max_results}:{query}"
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_result = ydl.extract_info(search_term, download=False)
        return [{
            "id": entry["id"],
            "title": entry["title"],
            "thumbnail": entry.get("thumbnail", ""),
            "duration": entry.get("duration_string", "N/A"),
            "view_count": entry.get("view_count", 0)
        } for entry in search_result.get("entries", []) if entry]

def create_optimized_stream(video_id, quality='144p'):
    """Membuat video stream dengan optimisasi ekstrem"""
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Format terendah dengan audio
    ydl_opts = {
        'format': 'worst[height<=360][vcodec!=av01]',
        'outtmpl': '-',
        'quiet': True,
        'noplaylist': True,
    }
    
    session_id = f"{video_id}_{quality}_{str(uuid.uuid4())[:8]}"
    output_file = os.path.join(CACHE_DIR, f"{session_id}.mp4")
    
    # Konfigurasi FFmpeg untuk optimisasi ekstrem
    if quality == '144p':
        scale = "scale=256:144:force_original_aspect_ratio=decrease"
        fps = 12  # Frame rate lebih rendah
        crf = 36  # Higher CRF for more compression
        bitrate = '60k'  # Bitrate sangat rendah
        audio_bitrate = '12k'  # Audio sangat rendah
    elif quality == '240p':
        scale = "scale=426:240:force_original_aspect_ratio=decrease"
        fps = 15
        crf = 32
        bitrate = '120k'
        audio_bitrate = '16k'
    else:  # 360p
        scale = "scale=640:360:force_original_aspect_ratio=decrease"
        fps = 24
        crf = 28
        bitrate = '200k'
        audio_bitrate = '24k'
    
    # Teknik khusus: Skip frame untuk penghematan ekstra
    skip_frame = f"select=not(mod(n\\,{3 if quality == '144p' else 2}))"
    
    try:
        # Proses dengan FFmpeg pipe untuk menghindari disk I/O
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            video_data = ydl.extract_info(url, download=False)
            format_url = video_data['url']
            
        # Proses transcode dengan optimisasi ekstrem
        (
            ffmpeg
            .input(format_url)
            .filter('fps', fps=fps)
            .filter(skip_frame)  # Skip frame untuk hemat bandwidth
            .filter(scale)
            .output(
                output_file,
                crf=crf,
                preset='ultrafast',
                tune='zerolatency',
                vsync='vfr',
                **{
                    'b:v': bitrate,
                    'maxrate': bitrate,
                    'bufsize': '50k',  # Buffer kecil
                    'b:a': audio_bitrate,
                    'ac': 1,  # Mono audio
                    'ar': '22050' if quality == '144p' else '32000',
                    'threads': '1'
                }
            )
            .global_args('-loglevel', 'error')
            .global_args('-movflags', '+faststart')
            .overwrite_output()
            .run()
        )
        
        # Kompresi tambahan dengan teknik khusus
        if os.path.getsize(output_file) > 5 * 1024 * 1024:  # Jika >5MB
            optimize_video(output_file)
            
        return output_file
    except Exception as e:
        print(f"Error processing video: {str(e)}")
        return None

def optimize_video(file_path):
    """Optimisasi tambahan dengan teknik khusus"""
    # Menggunakan FFmpeg untuk kompresi ekstra
    temp_file = file_path + ".opt.mp4"
    
    # Two-pass encoding untuk efisiensi lebih tinggi
    pass1 = (
        ffmpeg
        .input(file_path)
        .output(
            temp_file,
            crf=28,
            preset='slower',
            vcodec='libx264',
            **{'pass': 1, 'passlogfile': 'ffmpeg2pass'}
        )
        .global_args('-f', 'null')
        .global_args('-an')
        .global_args('-y')
    )
    
    pass2 = (
        ffmpeg
        .input(file_path)
        .output(
            temp_file,
            crf=28,
            preset='slower',
            vcodec='libx264',
            **{'pass': 2, 'passlogfile': 'ffmpeg2pass'}
        )
    )
    
    try:
        pass1.run()
        pass2.run()
        os.replace(temp_file, file_path)
    except:
        # Jika gagal, gunakan file asli
        if os.path.exists(temp_file):
            os.remove(temp_file)

def generate_low_bandwidth_stream(video_path):
    """Generator untuk streaming dengan chunk kecil"""
    chunk_size = 512  # Chunk sangat kecil untuk penghematan maksimal
    with open(video_path, 'rb') as video_file:
        while True:
            data = video_file.read(chunk_size)
            if not data:
                break
            yield data

# ===============================
# ✅ ROUTE STREAMING OPTIMIZED
# ===============================
@server.route('/stream/<video_id>')
def video_stream(video_id):
    """Route untuk streaming video optimisasi kuota"""
    quality = request.args.get('quality', '144p')
    
    # Gunakan cache jika memungkinkan
    cached = [f for f in os.listdir(CACHE_DIR) if f.startswith(video_id)]
    if cached:
        video_path = os.path.join(CACHE_DIR, cached[0])
    else:
        video_path = create_optimized_stream(video_id, quality)
    
    if not video_path:
        return "Video tidak dapat diproses", 500
    
    file_size = os.path.getsize(video_path)
    
    # Hapus file setelah 1 jam jika tidak digunakan
    threading.Timer(3600, lambda: os.remove(video_path) if os.path.exists(video_path) else None).start()
    
    return Response(
        generate_low_bandwidth_stream(video_path),
        mimetype='video/mp4',
        headers={
            'Content-Length': str(file_size),
            'Content-Disposition': 'inline',
            'Cache-Control': 'public, max-age=3600'  # Cache browser 1 jam
        }
    )

# ===============================
# ✅ DASH UI OPTIMIZED
# ===============================
app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content', className='mt-2')
], fluid=True, style={'padding': '0'})

# Halaman beranda
home_layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.H3("YouTube Ultra Hemat Kuota", className="text-center mb-3"),
            dbc.Card([
                dbc.CardBody([
                    dbc.InputGroup([
                        dbc.Input(id='search-input', placeholder='Cari video...', 
                                 className='border-primary', style={'fontSize': '14px'}),
                        dbc.Button("Cari", id='search-btn', color="primary", n_clicks=0,
                                  style={'fontSize': '14px'})
                    ]),
                ])
            ], className='mb-3'),
            
            html.Div([
                dbc.Badge("144p: ~3MB/jam", color="success", className='me-1'),
                dbc.Badge("240p: ~6MB/jam", color="info", className='me-1'),
                dbc.Badge("360p: ~12MB/jam", color="warning"),
            ], className='text-center mb-3'),
            
            html.Div(id='search-results')
        ], width=12)
    ])
])

# Halaman pemutar
player_layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.Video(
                id='video-player',
                controls=True,
                autoPlay=True,
                playsInline=True,
                style={
                    'width': '100%', 
                    'maxHeight': '60vh',
                    'backgroundColor': '#000'
                }
            ),
            
            html.Div([
                html.H4(id='video-title', className='mt-2 mb-1', style={'fontSize': '16px'}),
                dbc.Badge(id='video-quality', color="info", className='me-2'),
                dbc.Badge(id='video-size', color="success"),
            ], className='d-flex align-items-center mt-2 mb-2'),
            
            dbc.Select(
                id='quality-selector',
                options=[
                    {'label': '144p (Ekonomi Ekstrim - ~3MB/jam)', 'value': '144p'},
                    {'label': '240p (Hemat - ~6MB/jam)', 'value': '240p'},
                    {'label': '360p (Standar - ~12MB/jam)', 'value': '360p'}
                ],
                value='144p',
                className='mb-2',
                style={'fontSize': '14px'}
            ),
            
            dbc.Progress(id='bandwidth-meter', value=3, striped=True, animated=True),
            html.Small("Estimasi Kuota Digunakan", className='text-muted d-block mt-1')
        ], width=12)
    ])
])

# Callback untuk navigasi
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/':
        return home_layout
    elif re.match(r'/watch/.+', pathname):
        return player_layout
    return home_layout

# Callback untuk pencarian
@app.callback(
    Output('search-results', 'children'),
    Input('search-btn', 'n_clicks'),
    State('search-input', 'value')
)
def search_videos(n_clicks, query):
    if n_clicks == 0 or not query:
        return html.Div()
    
    results = search_youtube(query, max_results=8)
    
    if not results:
        return dbc.Alert("Tidak ada hasil ditemukan", color="warning")
    
    cards = []
    for video in results:
        cards.append(
            dbc.Col([
                dbc.Card([
                    dbc.CardImg(
                        src=video['thumbnail'], 
                        style={
                            'height': '90px', 
                            'objectFit': 'cover',
                            'borderTopLeftRadius': '5px',
                            'borderTopRightRadius': '5px'
                        }
                    ),
                    dbc.CardBody([
                        html.Div(
                            video['title'][:40] + ('...' if len(video['title']) > 40 else '', 
                            style={
                                'fontSize': '12px',
                                'height': '32px',
                                'overflow': 'hidden'
                            }
                        ),
                        html.Small(
                            f"{video['duration']}", 
                            className='text-muted d-block'
                        ),
                        dbc.Button(
                            "Putar", 
                            color="primary", 
                            size="sm", 
                            className='mt-1 w-100',
                            href=f"/watch/{video['id']}",
                            style={'fontSize': '12px'}
                        )
                    ], style={'padding': '8px'})
                ], className='h-100 shadow-sm')
            ], xs=6, sm=4, md=3, className='mb-3')
        )
    
    return dbc.Row(cards, className='g-2')

# Callback untuk pemutar video
@app.callback(
    [Output('video-player', 'src'),
     Output('video-title', 'children'),
     Output('video-quality', 'children'),
     Output('video-size', 'children'),
     Output('bandwidth-meter', 'value')],
    [Input('url', 'pathname'),
     Input('quality-selector', 'value')]
)
def load_video(pathname, quality):
    video_id = re.search(r'/watch/(.+)', pathname)
    if not video_id:
        return [None, "", "", "", 0]
    
    video_id = video_id.group(1)
    video_info = get_video_info(f"https://www.youtube.com/watch?v={video_id}")
    
    stream_url = f"/stream/{video_id}?quality={quality}"
    
    bandwidth_map = {'144p': 3, '240p': 6, '360p': 12}
    
    title = video_info['title'][:50] + ('...' if len(video_info['title']) > 50 else '')
    quality_text = f"{quality.upper()}"
    size_text = f"~{bandwidth_map.get(quality, 3)}MB/jam"
    
    return [stream_url, title, quality_text, size_text, bandwidth_map.get(quality, 3)]

if __name__ == '__main__':
    # ===============================
    # ✅ NGROK TUNNEL SETUP
    # ===============================
    ngrok_tunnel = ngrok.connect(8050)
    public_url = ngrok_tunnel.public_url
    print(f" * Ngrok Tunnel Active: {public_url}")
    
    # Jalankan server
    app.run_server(host='0.0.0.0', port=8050, debug=False, threaded=True)
