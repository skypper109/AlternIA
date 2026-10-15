#include "led_manager.h"

#if ENABLE_WS2812B
#include <Adafruit_NeoPixel.h>
static Adafruit_NeoPixel strip(NUM_PIXELS, PIN_NEOPIXEL, NEO_GRB + NEO_KHZ800);
#endif

LedManager ledManager;

LedManager::LedManager()
    : _currentState(STATE_DISCONNECTED),
      _savedClassState(STATE_CONNECTED_IDLE),
      _isServerConnected(false),
      _isTtsSpeaking(false),
      _lastBlinkMillis(0),
      _blinkWhiteState(false) {}

void LedManager::begin() {
    // 1. Initialiser les broches des LEDs discrètes
    pinMode(PIN_LED_GREEN, OUTPUT);
    pinMode(PIN_LED_BLUE, OUTPUT);
    pinMode(PIN_LED_RED, OUTPUT);
    pinMode(PIN_LED_YELLOW, OUTPUT);
    pinMode(PIN_LED_WHITE, OUTPUT);

    _setDiscreteLeds(false, false, false, false, false);

#if ENABLE_WS2812B
    strip.begin();
    strip.setBrightness(180);
    strip.show(); // Éteindre au démarrage
#endif

    Serial.println(F("💡 [LED Manager] Initialisé avec succès (Discrètes + NeoPixel WS2812B)"));
    _applyHardwareOutputs();
}

void LedManager::setServerConnected(bool connected) {
    _isServerConnected = connected;
    if (!connected) {
        _currentState = STATE_DISCONNECTED;
    } else {
        // Si aucune classe n'était encore choisie, passer à VERT allumé fixe
        if (_currentState == STATE_DISCONNECTED) {
            _currentState = STATE_CONNECTED_IDLE;
            _savedClassState = STATE_CONNECTED_IDLE;
        }
    }
    _applyHardwareOutputs();
}

void LedManager::selectClass(const String& className) {
    String c = className;
    c.toLowerCase();

    if (c.indexOf("10") >= 0) {
        _currentState = STATE_CLASS_10EME;
        _savedClassState = STATE_CLASS_10EME;
        Serial.println(F("🟦 [LED] Classe 10ème sélectionnée -> LED BLEUE ALLUMÉE FIXE"));
    } else if (c.indexOf("11") >= 0) {
        _currentState = STATE_CLASS_11EME;
        _savedClassState = STATE_CLASS_11EME;
        Serial.println(F("🟥 [LED] Classe 11ème sélectionnée -> LED ROUGE ALLUMÉE FIXE"));
    } else if (c.indexOf("12") >= 0 || c.indexOf("tse") >= 0 || c.indexOf("term") >= 0) {
        _currentState = STATE_CLASS_12EME;
        _savedClassState = STATE_CLASS_12EME;
        Serial.println(F("🟨 [LED] Classe 12ème sélectionnée -> LED JAUNE ALLUMÉE FIXE"));
    } else {
        // Autre classe ou retour accueil
        if (_isServerConnected) {
            _currentState = STATE_CONNECTED_IDLE;
            _savedClassState = STATE_CONNECTED_IDLE;
        }
    }

    _applyHardwareOutputs();
}

void LedManager::setTtsSpeaking(bool speaking) {
    _isTtsSpeaking = speaking;
    if (speaking) {
        _currentState = STATE_TTS_SPEAKING;
        _blinkWhiteState = true;
        _lastBlinkMillis = millis();
        Serial.println(F("⚪ [LED] Synthèse vocale TTS en cours -> LED BLANCHE CLIGNOTANTE"));
    } else {
        // Dès que la parole se termine, restaurer la couleur de la classe active
        _currentState = _savedClassState;
        Serial.printf("✨ [LED] Fin de parole TTS -> Retour à l'état de classe : %s\n", getCurrentColorName().c_str());
    }
    _applyHardwareOutputs();
}

void LedManager::setState(AlterniaLedState newState) {
    _currentState = newState;
    if (newState != STATE_TTS_SPEAKING) {
        _savedClassState = newState;
    }
    _applyHardwareOutputs();
}

void LedManager::update() {
    // Si la synthèse vocale TTS est en train de parler, faire clignoter la LED blanche
    if (_currentState == STATE_TTS_SPEAKING) {
        unsigned long currentMillis = millis();
        if (currentMillis - _lastBlinkMillis >= TTS_BLINK_INTERVAL_MS) {
            _lastBlinkMillis = currentMillis;
            _blinkWhiteState = !_blinkWhiteState;

            // Clignotement LED discrète blanche
            _setDiscreteLeds(false, false, false, false, _blinkWhiteState);

            // Clignotement NeoPixel Blanc
            if (_blinkWhiteState) {
                _setNeoPixelColor(255, 255, 255);
            } else {
                _setNeoPixelColor(0, 0, 0);
            }
        }
    }
}

void LedManager::_applyHardwareOutputs() {
    switch (_currentState) {
        case STATE_CONNECTED_IDLE:
            // VERT allumé fixe
            _setDiscreteLeds(true, false, false, false, false);
            _setNeoPixelColor(0, 255, 0);
            break;

        case STATE_CLASS_10EME:
            // BLEU allumé fixe
            _setDiscreteLeds(false, true, false, false, false);
            _setNeoPixelColor(0, 80, 255);
            break;

        case STATE_CLASS_11EME:
            // ROUGE allumé fixe
            _setDiscreteLeds(false, false, true, false, false);
            _setNeoPixelColor(255, 0, 0);
            break;

        case STATE_CLASS_12EME:
            // JAUNE allumé fixe
            _setDiscreteLeds(false, false, false, true, false);
            _setNeoPixelColor(255, 200, 0);
            break;

        case STATE_TTS_SPEAKING:
            // Clignotement actif géré dans update()
            break;

        case STATE_DISCONNECTED:
        default:
            _setDiscreteLeds(false, false, false, false, false);
            _setNeoPixelColor(0, 0, 0);
            break;
    }
}

void LedManager::_setDiscreteLeds(bool green, bool blue, bool red, bool yellow, bool white) {
    digitalWrite(PIN_LED_GREEN, green ? HIGH : LOW);
    digitalWrite(PIN_LED_BLUE, blue ? HIGH : LOW);
    digitalWrite(PIN_LED_RED, red ? HIGH : LOW);
    digitalWrite(PIN_LED_YELLOW, yellow ? HIGH : LOW);
    digitalWrite(PIN_LED_WHITE, white ? HIGH : LOW);
}

void LedManager::_setNeoPixelColor(uint8_t r, uint8_t g, uint8_t b) {
#if ENABLE_WS2812B
    for (int i = 0; i < NUM_PIXELS; i++) {
        strip.setPixelColor(i, strip.Color(r, g, b));
    }
    strip.show();
#endif
}

String LedManager::getCurrentStateName() const {
    switch (_currentState) {
        case STATE_DISCONNECTED:   return "DISCONNECTED";
        case STATE_CONNECTED_IDLE: return "CONNECTED_IDLE";
        case STATE_CLASS_10EME:    return "CLASS_10EME";
        case STATE_CLASS_11EME:    return "CLASS_11EME";
        case STATE_CLASS_12EME:    return "CLASS_12EME";
        case STATE_TTS_SPEAKING:   return "TTS_SPEAKING";
        default:                   return "UNKNOWN";
    }
}

String LedManager::getCurrentColorName() const {
    switch (_currentState) {
        case STATE_DISCONNECTED:   return "OFF";
        case STATE_CONNECTED_IDLE: return "VERT (Fixe)";
        case STATE_CLASS_10EME:    return "BLEU (10ème)";
        case STATE_CLASS_11EME:    return "ROUGE (11ème)";
        case STATE_CLASS_12EME:    return "JAUNE (12ème)";
        case STATE_TTS_SPEAKING:   return "BLANC (Clignotant TTS)";
        default:                   return "OFF";
    }
}
