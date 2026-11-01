package com.luxisoft.realityos

data class LocalizedSpeech(val text: String, val language: String) {
    fun matches(selectedLanguage: String): Boolean = language == selectedLanguage
}
