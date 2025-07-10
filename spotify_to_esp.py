# Salve como spotify_to_esp.py

# ===========================
# Importa credenciais sigilosas
# ===========================
import time
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Credenciais e IP do ESP ficam em credentials.py (fora do controle de versão)
try:
    from credentials import (
        ESP_IP,
        CLIENT_ID,
        CLIENT_SECRET,
        REDIRECT_URI,
        GETSONGBPM_KEY,
    )
except ImportError as cred_err:
    raise SystemExit(
        "Não foi possível importar credentials.py.\n"
        "Crie um arquivo credentials.py na raiz do projeto com as variáveis:\n"
        "ESP_IP, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, GETSONGBPM_KEY"
    ) from cred_err

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="user-read-playback-state user-read-currently-playing user-library-read user-read-private",
    show_dialog=True
))

last_track_id = None
last_bpm = 120

def get_bpm_from_third_party(title: str, artist: str) -> int | None:
    """Tenta obter o BPM usando a API pública do getsongbpm.
    Retorna int(BPM) ou None se não encontrar."""
    try:
        resp = requests.get(
            "https://api.getsongbpm.com/",
            params={
                "api_key": GETSONGBPM_KEY,
                "type": "single",
                "title": title,
                "artist": artist,
            },
            timeout=3,
        )
        data = resp.json()
        # Estrutura esperada: { "tempo": "123.45", ... }
        tempo = (
            float(data.get("tempo"))
            if isinstance(data, dict) and data.get("tempo")
            else None
        )
        if tempo:
            return int(round(tempo))
    except Exception as api_err:
        print("Erro na API externa de BPM:", api_err)
    return None

while True:
    try:
        playback = sp.current_playback()
        if playback and playback['is_playing']:
            track_id = playback['item']['id']
            if track_id != last_track_id:
                try:
                    # Usar serviço externo, pois o endpoint de audio-features do spotify foi descontinuado
                    title = playback['item']['name']
                    artist = playback['item']['artists'][0]['name']
                    bpm_ext = get_bpm_from_third_party(title, artist)
                    if bpm_ext is None:
                        raise ValueError("BPM não encontrado em serviço externo")
                    bpm = bpm_ext
                    last_bpm = bpm
                    last_track_id = track_id
                    print(f"Nova música: {title} | BPM: {bpm}")
                except Exception as e:
                    print("Erro ao obter BPM de serviço externo:", e)
                    bpm = last_bpm
            else:
                bpm = last_bpm
            # Envia BPM para o ESP
            requests.get(f"{ESP_IP}?bpm={bpm}", timeout=1)
        else:
            print("Nada tocando no Spotify.")
        time.sleep(5)
    except Exception as e:
        print("Erro:", e)
        time.sleep(5)