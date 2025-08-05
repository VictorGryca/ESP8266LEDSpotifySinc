# ESP8266 LED Spotify Sync

Este projeto sincroniza LEDs WS2812 conectados a um ESP8266 com o BPM da música atualmente tocando no Spotify. O script Python (`spotify_to_esp.py`) detecta a música em reprodução, estima o BPM e envia para o ESP, que ajusta os efeitos dos LEDs conforme o ritmo.

## Como funciona

- O script Python usa a API do Spotify para identificar a música tocando.
- Tenta estimar o BPM usando o preview da faixa (com `librosa`). Se não conseguir, consulta a API do GetSongBPM.
- O BPM é enviado via HTTP para o ESP8266, que controla os LEDs com a biblioteca FastLED.

## Pré-requisitos

- Python 3.x com as bibliotecas: `spotipy`, `librosa`, `requests`
- ESP8266 com firmware compatível e código FastLED (ver [src/main.cpp](src/main.cpp))
- Configurar o arquivo `credentials.py` com suas credenciais do Spotify, IP do ESP e chave do GetSongBPM.

## Como usar

1. Instale as dependências Python:
   ```sh
   pip install spotipy librosa requests
   
2. Configure o arquivo credentials.py:
```python
ESP_IP = "http://<IP_DO_ESP>:80/"
CLIENT_ID = "<seu_client_id>"
CLIENT_SECRET = "<seu_client_secret>"
REDIRECT_URI = "<seu_redirect_uri>"
GETSONGBPM_KEY = "<sua_api_key>"
REFERER = "<referer_necessario>"
```

4. Faça upload do código para o ESP8266 (src/main.cpp).
5. Execute o script Python:
python spotify_to_esp.py

6. Toque uma música no Spotify e veja os LEDs reagirem ao BPM detectado.
## Observações
- O script precisa estar rodando enquanto quiser sincronizar os LEDs.
- O ESP8266 deve estar na mesma rede do computador rodando o script.
- O BPM pode não ser detectado para todas as músicas (especialmente sem preview).
