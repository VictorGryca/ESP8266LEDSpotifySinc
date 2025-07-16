#include <ESP8266WiFi.h> // Use <WiFi.h> para ESP32
#include <ESP8266WebServer.h> // Use <WebServer.h> para ESP32
#include <FastLED.h>

#define LED_PIN 5
#define NUM_LEDS 30
CRGB leds[NUM_LEDS];
#define BRIGHTNESS 50 

const char* ssid = "R2D2_2G";
const char* password = "9090909090";

ESP8266WebServer server(80); // Use WebServer para ESP32
int bpm = 300;
unsigned long lastBeat = 0;

void handleBPM() {
  if (server.hasArg("bpm")) {
      bpm = server.arg("bpm").toInt();
      Serial.print("BPM atualizado: ");
      Serial.println(bpm);
      server.send(200, "text/plain", "OK");
  }
  else {
    server.send(400, "text/plain", "Missing bpm");
  }
}

void setup() {
  Serial.begin(9600);
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness( BRIGHTNESS );
  fill_solid(leds, NUM_LEDS, CRGB::Black); // Inicializa todos os LEDs apagados
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

bool ledOn = false;
unsigned long pulseStart = 0;

void loop() {
  server.handleClient();

  if (bpm > 0) {
    unsigned long interval = 60000 / bpm;
    unsigned long pulseDuration = 50; // ms

    if (!ledOn && millis() - lastBeat > interval) {
      FastLED.clear();
      fill_solid(leds, NUM_LEDS, CRGB::White);
      FastLED.show();
      ledOn = true;
      pulseStart = millis();
      lastBeat = millis();
    }

    if (ledOn && millis() - pulseStart > pulseDuration) {
      FastLED.clear();
      FastLED.show();
      ledOn = false;
    }
  } else {
    FastLED.clear();
    FastLED.show();
    ledOn = false;
  }
}