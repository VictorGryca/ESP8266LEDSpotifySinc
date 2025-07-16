# spotify_to_esp_hybrid_bpm.py

import time
import re
import tempfile
import requests
import spotipy
import librosa
from spotipy.oauth2 import SpotifyOAuth
import credentials

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
        resp = requests.get(url, params=params, headers=headers, timeout=5)
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

    print("[DEBUG] Não achou BPM — usando último.")
    return last_bpm

def send_to_esp(bpm: int):
    try:
        requests.get(ESP_IP, params={"bpm": bpm}, timeout=5)
    except Exception as e:
        print(f"[DEBUG] Erro ao enviar para ESP: {e}")

# Loop principal
while True:
    playback = sp.current_playback()
    if playback and playback.get("is_playing") and playback.get("item"):
        item = playback["item"]
        tid = item["id"]
        title = item["name"]
        artist = item["artists"][0]["name"]
        print(f"Tocando agora: {title} - {artist}")

        if tid != last_track_id:
            bpm = get_bpm(tid, title, artist)
            last_bpm, last_track_id = bpm, tid
        send_to_esp(bpm)
        print(f"BPM enviado: {bpm}")

    else:
        print("Nada tocando.")
        bpm = 0
        send_to_esp(bpm)
        print(f"BPM enviado: {bpm}")

    time.sleep(5)
