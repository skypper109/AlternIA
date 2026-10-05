#ifndef LED_MANAGER_H
#define LED_MANAGER_H

#include <Arduino.h>
#include "config.h"

enum AlterniaLedState {
    STATE_DISCONNECTED,     // Déconnecté du serveur (LED éteinte ou rouge doux)
    STATE_CONNECTED_IDLE,   // Connecté au serveur Runpod (VERT ALLUMÉ FIXE)
    STATE_CLASS_10EME,      // Classe 10ème sélectionnée sur device (BLEU FIXE)
    STATE_CLASS_11EME,      // Classe 11ème sélectionnée sur device (ROUGE FIXE)
    STATE_CLASS_12EME,      // Classe 12ème sélectionnée sur device (JAUNE FIXE)
    STATE_TTS_SPEAKING      // Synthèse vocale TTS en cours (BLANC CLIGNOTANT)
};

class LedManager {
public:
    LedManager();
    void begin();
    
    // Actions logiques
    void setServerConnected(bool connected);
    void selectClass(const String& className);
    void setTtsSpeaking(bool speaking);
    void setState(AlterniaLedState newState);

    // Boucle non-bloquante pour gérer le clignotement blanc
    void update();

    AlterniaLedState getCurrentState() const { return _currentState; }
    String getCurrentStateName() const;
    String getCurrentColorName() const;

private:
    AlterniaLedState _currentState;
    AlterniaLedState _savedClassState; // Mémorise la classe active pendant le clignotement blanc
    bool _isServerConnected;
    bool _isTtsSpeaking;

    // Gestion du clignotement non-bloquant
    unsigned long _lastBlinkMillis;
    bool _blinkWhiteState;

    void _applyHardwareOutputs();
    void _setDiscreteLeds(bool green, bool blue, bool red, bool yellow, bool white);
    void _setNeoPixelColor(uint8_t r, uint8_t g, uint8_t b);
};

extern LedManager ledManager;

#endif // LED_MANAGER_H
