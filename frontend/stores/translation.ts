import { defineStore } from 'pinia'
import axios from 'axios'

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
    bleu_score?: number
  }>
}

export const useTranslationStore = defineStore('translation', {
  state: () => ({
    isLoading: false,
    isProcessing: false,
    error: null as string | null,
    lastResult: null as TranslationResult | null
  }),

  actions: {
    async uploadFile(file: File, tags?: string[]) {
      try {
        const formData = new FormData()
        formData.append('file', file)
        if (tags && tags.length > 0) {
          tags.forEach(tag => formData.append('tags[]', tag))
        }

        const response = await axios.post(
          `${config.baseURL}/translations/upload-file/`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          }
        )

        return response.data
      } catch (error: any) {
        throw new Error(error.response?.data?.error || 'File upload failed')
      }
    },

    async checkQuality(targetLanguage: string, sourceText: string, referenceTranslation: string, candidateTranslation: string) {
      try {
        const response = await axios.post(`${config.baseURL}/translations/check_quality/`, {
          target_language: targetLanguage,
          existing_translation: referenceTranslation,
          llm_translation: candidateTranslation,
          source_text: sourceText
        })
        return response.data
      } catch (error: any) {
        throw new Error(error.response?.data?.error || 'Quality check failed')
      }
    },

    async processTranslations(targetLanguage: string, sourceLanguage: string = 'en', forceTranslate: boolean = false) {
      this.isProcessing = true
      this.error = null
      
      try {
        // First, get translations
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

        // Store initial results
        const translationResult = await response.json()
        this.lastResult = translationResult

        // Then, compute BLEU scores for successful translations
        if (translationResult?.details) {
          const successfulTranslations = translationResult.details.filter(
            detail => detail.status === 'success' && detail.translated_text && detail.existing_translation
          )

          // Process translations sequentially to avoid overwhelming the API
          for (const detail of successfulTranslations) {
            if (!detail.translated_text || !detail.existing_translation) continue

            try {
              const result = await this.checkQuality(
                targetLanguage,
                detail.source_text || '',
                detail.existing_translation,
                detail.translated_text
              )

              // Create a new details array with the updated BLEU score
              const updatedDetails = this.lastResult!.details.map(d => {
                if (d.key_id === detail.key_id) {
                  return { ...d, bleu_score: result.bleu_score }
                }
                return d
              })

              // Update the store with the new details array
              this.lastResult = {
                ...this.lastResult!,
                details: updatedDetails
              }
            } catch (error) {
              console.error('Failed to compute BLEU score:', error)
            }
          }
        }
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'An error occurred'
      } finally {
        this.isProcessing = false
      }
    },

    clearResults() {
      this.lastResult = null
      this.error = null
    }
  }
}) 