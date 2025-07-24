import { defineStore } from 'pinia'

const config = {
  baseURL: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/api'
}

interface TranslationResult {
  total_processed: number
  successful: number
  failed: number
  skipped: number
  new_translations: number
  updated_translations: number
  details: Array<{
    key_id: string
    key_name: string
    status: string
    source_text?: string
    translated_text?: string
    existing_translation?: string
    is_new_translation?: boolean
    reason?: string
    error?: string
  }>
}

export const useTranslationPipelineStore = defineStore('translationPipeline', {
  state: () => ({
    isProcessing: false,
    lastResult: null as TranslationResult | null,
    error: null as string | null,
  }),

  actions: {
    async processTranslations(targetLanguage: string, sourceLanguage: string = 'en', forceTranslate: boolean = false) {
      this.isProcessing = true
      this.error = null
      
      try {
        const response = await fetch(`${config.baseURL}/translations/process-translations/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            target_language: targetLanguage,
            source_language: sourceLanguage,
            force_translate: forceTranslate,
          }),
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        this.lastResult = await response.json()
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'An error occurred'
      } finally {
        this.isProcessing = false
      }
    },

    clearResults() {
      this.lastResult = null
      this.error = null
    },
  },
}) 