# ESP8266 LED Spotify Sync

This project synchronizes WS2812 LEDs connected to an ESP8266 with the BPM of the track currently playing on Spotify. The Python script (`spotify_to_esp.py`) detects the song being played, estimates its BPM, and sends it to the ESP, which then adjusts the LED effects to match the rhythm.

## How it works

* The Python script uses the Spotify API to identify the currently playing track.
* It tries to estimate the BPM using the track’s preview (with `librosa`). If that fails, it falls back to querying the GetSongBPM API.
* The BPM value is sent via HTTP to the ESP8266, which controls the LEDs using the FastLED library.

## Prerequisites

* Python 3.x with the libraries: `spotipy`, `librosa`, `requests`
* An ESP8266 flashed with compatible firmware and the FastLED-based code (see [src/main.cpp](src/main.cpp))
* A `credentials.py` file configured with your Spotify credentials, the ESP’s IP address, and your GetSongBPM key.

## How to use

1. Install the Python dependencies:

   ```sh
   pip install spotipy librosa requests
   ```

2. Configure the `credentials.py` file:

   ```python
   ESP_IP         = "http://<ESP_IP>:80/"
   CLIENT_ID      = "<your_client_id>"
   CLIENT_SECRET  = "<your_client_secret>"
   REDIRECT_URI   = "<your_redirect_uri>"
   GETSONGBPM_KEY = "<your_api_key>"
   REFERER        = "<required_referer>"
   ```

3. Upload the code to the ESP8266 (`src/main.cpp`).

4. Run the Python script:

   ```sh
   python spotify_to_esp.py
   ```

5. Play a song on Spotify and watch the LEDs react to the detected BPM.

## Notes

* The Python script must remain running for continuous synchronization.
* Ensure the ESP8266 is on the same local network as the machine running the script.
* BPM may not be detected for every track (especially if no preview is available).
