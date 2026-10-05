#ifndef AUDIO_MANAGER_H
#define AUDIO_MANAGER_H

#include <Arduino.h>
#include "driver/i2s.h"
#include "config.h"

class AudioManager {
public:
    AudioManager();
    
    // Initialisation matérielle
    bool begin();

    // ── GESTION DU MICROPHONE (INMP441) ──────────────────────────────────────
    bool initMicrophone();
    size_t recordPcmData(uint8_t* outputBuffer, size_t bufferSize);
    bool isRecording() const { return _isRecording; }
    void startRecording();
    void stopRecording();

    // ── GESTION DU HAUT-PARLEUR (MAX98357A / I2S DAC) ───────────────────────
    bool initSpeaker();
    size_t playPcmData(const uint8_t* audioData, size_t dataSize);
    void stopPlayback();

    // Utilitaires de volume et monitoring
    void setVolume(float volumePercent); // 0.0 à 1.0
    float getVolume() const { return _volume; }

private:
    bool _micInitialized;
    bool _spkInitialized;
    bool _isRecording;
    float _volume;
};

extern AudioManager audioManager;

#endif // AUDIO_MANAGER_H
