import time
import re
import tempfile
import requests
import spotipy
import librosa
from spotipy.oauth2 import SpotifyOAuth
import credentials
import threading

# CONFIGURAÇÕES
ESP_IP = credentials.ESP_IP
CLIENT_ID = credentials.CLIENT_ID
CLIENT_SECRET = credentials.CLIENT_SECRET
REDIRECT_URI = credentials.REDIRECT_URI
GETSONGBPM_KEY = credentials.GETSONGBPM_KEY
REFERER = credentials.REFERER

# Inicializa Spotipy
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="user-read-playback-state user-read-currently-playing",
    show_dialog=True
))

last_track_id = None
last_bpm = 300
bpm = 0
bpm_lock = threading.Lock()
bpm_search_thread = None
searching_bpm = False
search_track_id = None


def get_bpm_from_preview(track_id: str) -> int | None:
    """Tenta baixar o preview e estimar o BPM com librosa."""
    preview_url = sp.track(track_id).get("preview_url")
    if not preview_url:
        print("[DEBUG] Sem preview disponível.")
        return None

    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as tmp:
            resp = requests.get(preview_url, stream=True, timeout=10)
            resp.raise_for_status()
            for chunk in resp.iter_content(1024):
                tmp.write(chunk)
            tmp.flush()

            y, sr = librosa.load(tmp.name, sr=None)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            return round(tempo)
    except Exception as e:
        print(f"[DEBUG] Erro ao processar preview: {e}")
        return None

def get_bpm_from_getsongbpm(title: str, artist: str) -> int | None:
    """Fallback: consulta API GetSongBPM (.co) com referer correto."""
    lookup = f"song:{title} artist:{artist}"
    url = "https://api.getsong.co/search/"
    params = {
        "api_key": GETSONGBPM_KEY,
        "type": "both",
        "lookup": lookup
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": REFERER
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=0.5)  
        print("[DEBUG] GETSongBPM URL:", resp.url)
        data = resp.json()
        tracks = data.get("search") or []
        if not tracks:
            return None
        tempo = tracks[0].get("tempo")
        return int(float(tempo)) if tempo else None
    except Exception as e:
        print(f"[DEBUG] Erro GetSongBPM: {e}")
        return None

def get_bpm(track_id: str, title: str, artist: str) -> int:
    """Tenta preview, senão GetSongBPM, senão último BPM."""
    bpm = get_bpm_from_preview(track_id)
    if bpm:
        print(f"[DEBUG] BPM via preview: {bpm}")
        return bpm

    print("[DEBUG] Fallback para GetSongBPM...")
    bpm = get_bpm_from_getsongbpm(title, artist)
    if bpm:
        print(f"[DEBUG] BPM via GetSongBPM: {bpm}")
        return bpm

    print("[DEBUG] Não achou BPM — deixando a LED apagada.")
    return 0

def send_to_esp(bpm: int):
    try:
        requests.get(ESP_IP, params={"bpm": bpm}, timeout=5)
    except Exception as e:
        print(f"[DEBUG] Erro ao enviar para ESP: {e}")

def bpm_search_worker(track_id, title, artist):
    global bpm, last_bpm, last_track_id, searching_bpm, search_track_id
    with bpm_lock:
        searching_bpm = True
        search_track_id = track_id
    found_bpm = get_bpm(track_id, title, artist)
    with bpm_lock:
        # Só atualiza se ainda for a música atual
        if search_track_id == track_id:
            bpm = found_bpm
            last_bpm, last_track_id = bpm, track_id
            searching_bpm = False

# Loop principal
while True:
    playback = sp.current_playback()
    if playback and playback.get("is_playing") and playback.get("item"):
        item = playback["item"]
        tid = item["id"]
        title = item["name"]
        artist = item["artists"][0]["name"]
        print(f"Tocando agora: {title} - {artist}")

        with bpm_lock:
            # Se mudou de música ou está buscando, inicia nova busca
            if tid != last_track_id or searching_bpm:
                bpm = 0
                send_to_esp(0)
                print("Buscando BPM...")
                if bpm_search_thread and bpm_search_thread.is_alive():
                    search_track_id = tid
                bpm_search_thread = threading.Thread(target=bpm_search_worker, args=(tid, title, artist))
                bpm_search_thread.start()
            else:
                # Se BPM está 0 mas já temos last_bpm, envia last_bpm
                if bpm == 0 and last_bpm and tid == last_track_id:
                    send_to_esp(last_bpm)
                    print(f"BPM enviado (retomado): {last_bpm}")
                else:
                    send_to_esp(bpm)
                    print(f"BPM enviado: {bpm}")
    else:
        print("Nada tocando.")
        with bpm_lock:
            bpm = 0
        send_to_esp(0)
        print(f"BPM enviado: 0")

    time.sleep(0.5)
