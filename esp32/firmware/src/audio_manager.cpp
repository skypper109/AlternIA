#include "audio_manager.h"

AudioManager audioManager;

AudioManager::AudioManager()
    : _micInitialized(false),
      _spkInitialized(false),
      _isRecording(false),
      _volume(0.85f) {}

bool AudioManager::begin() {
    Serial.println(F("🎙️ [Audio Manager] Initialisation des périphériques I2S..."));
    bool micOk = initMicrophone();
    bool spkOk = initSpeaker();
    return micOk || spkOk;
}

bool AudioManager::initMicrophone() {
    i2s_config_t i2s_mic_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = AUDIO_SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT, // La plupart des INMP441 transmettent sur 32-bit (24-bit réels)
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = i2s_comm_format_t(I2S_COMM_FORMAT_STAND_I2S),
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 4,
        .dma_buf_len = 512,
        .use_apll = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk = 0
    };

    i2s_pin_config_t mic_pin_config = {
        .bck_io_num = I2S_MIC_SCK,
        .ws_io_num = I2S_MIC_WS,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_MIC_SD
    };

    esp_err_t err = i2s_driver_install(I2S_MIC_PORT, &i2s_mic_config, 0, NULL);
    if (err != ESP_OK) {
        Serial.printf("❌ [Audio] Échec driver I2S Microphone (err: %d)\n", err);
        return false;
    }

    err = i2s_set_pin(I2S_MIC_PORT, &mic_pin_config);
    if (err != ESP_OK) {
        Serial.printf("❌ [Audio] Échec brochage I2S Microphone (err: %d)\n", err);
        return false;
    }

    _micInitialized = true;
    Serial.println(F("✅ [Audio] Microphone I2S (INMP441) configuré sur GPIO 14 (SCK), 15 (WS), 32 (SD)"));
    return true;
}

bool AudioManager::initSpeaker() {
    i2s_config_t i2s_spk_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
        .sample_rate = 22050, // Fréquence de restitution vocale TTS
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,
        .communication_format = i2s_comm_format_t(I2S_COMM_FORMAT_STAND_I2S),
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 6,
        .dma_buf_len = 512,
        .use_apll = false,
        .tx_desc_auto_clear = true,
        .fixed_mclk = 0
    };

    i2s_pin_config_t spk_pin_config = {
        .bck_io_num = I2S_SPK_BCLK,
        .ws_io_num = I2S_SPK_LRC,
        .data_out_num = I2S_SPK_DIN,
        .data_in_num = I2S_PIN_NO_CHANGE
    };

    esp_err_t err = i2s_driver_install(I2S_SPK_PORT, &i2s_spk_config, 0, NULL);
    if (err != ESP_OK) {
        Serial.printf("❌ [Audio] Échec driver I2S Haut-Parleur (err: %d)\n", err);
        return false;
    }

    err = i2s_set_pin(I2S_SPK_PORT, &spk_pin_config);
    if (err != ESP_OK) {
        Serial.printf("❌ [Audio] Échec brochage I2S Haut-Parleur (err: %d)\n", err);
        return false;
    }

    _spkInitialized = true;
    Serial.println(F("✅ [Audio] Haut-Parleur I2S (MAX98357A) configuré sur GPIO 26 (BCLK), 25 (LRC), 22 (DIN)"));
    return true;
}

void AudioManager::startRecording() {
    if (!_micInitialized) return;
    _isRecording = true;
    Serial.println(F("🎙️ [Audio] Début de capture microphone I2S"));
}

void AudioManager::stopRecording() {
    _isRecording = false;
    Serial.println(F("⏹️ [Audio] Fin de capture microphone I2S"));
}

size_t AudioManager::recordPcmData(uint8_t* outputBuffer, size_t bufferSize) {
    if (!_micInitialized || !_isRecording) return 0;

    size_t bytesRead = 0;
    // Lecture directe par accès DMA
    esp_err_t result = i2s_read(I2S_MIC_PORT, outputBuffer, bufferSize, &bytesRead, portMAX_DELAY);
    if (result == ESP_OK) {
        return bytesRead;
    }
    return 0;
}

size_t AudioManager::playPcmData(const uint8_t* audioData, size_t dataSize) {
    if (!_spkInitialized) return 0;

    size_t bytesWritten = 0;
    esp_err_t result = i2s_write(I2S_SPK_PORT, audioData, dataSize, &bytesWritten, portMAX_DELAY);
    if (result == ESP_OK) {
        return bytesWritten;
    }
    return 0;
}

void AudioManager::stopPlayback() {
    if (_spkInitialized) {
        i2s_zero_dma_buffer(I2S_SPK_PORT);
    }
}

void AudioManager::setVolume(float volumePercent) {
    _volume = constrain(volumePercent, 0.0f, 1.0f);
}
