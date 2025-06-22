#include <ESP8266WiFi.h> // Use <WiFi.h> para ESP32
#include <ESP8266WebServer.h> // Use <WebServer.h> para ESP32
#include <FastLED.h>

#define LED_PIN 5
#define NUM_LEDS 30
CRGB leds[NUM_LEDS];
#define BRIGHTNESS 50 

const char* ssid = "Gryca";
const char* password = "r2d29090909090";

ESP8266WebServer server(80); // Use WebServer para ESP32
int bpm = 120;
unsigned long lastBeat = 0;
unsigned long lastBpmUpdate = 0; // Novo: controla quando o BPM foi atualizado
const unsigned long bpmTimeout = 10000; // 10 segundos sem BPM = para de piscar
bool bpmActive = false;

void handleBPM() {
  if (server.hasArg("bpm")) {
    bpm = server.arg("bpm").toInt();
    lastBpmUpdate = millis();
    bpmActive = true;
    server.send(200, "text/plain", "OK");
  } else {
    server.send(400, "text/plain", "Missing bpm");
  }
}

void setup() {
  Serial.begin(9600);
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness( BRIGHTNESS );
  FastLED.clear();
  FastLED.show();

  WiFi.begin(ssid, password);
  Serial.print("Conectando WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi conectado!");
  Serial.println(WiFi.localIP());

  server.on("/bpm", handleBPM);
  server.begin();
}

void loop() {
  server.handleClient();
  // Se não receber BPM por 10s, para de piscar
  if (bpmActive && (millis() - lastBpmUpdate > bpmTimeout)) {
    bpmActive = false;
    FastLED.clear();
    FastLED.show();
  }
  if (bpmActive) {
    unsigned long interval = 60000 / bpm;
    if (millis() - lastBeat > interval) {
      for (int i = 0; i < NUM_LEDS; i++) leds[i] = CRGB::White;
      FastLED.show();
      delay(50);
      for (int i = 0; i < NUM_LEDS; i++) leds[i] = CRGB::Black;
      FastLED.show();
      lastBeat = millis();
    }
  }
}