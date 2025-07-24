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
  }>
}

export const useTranslationStore = defineStore('translation', {
  state: () => ({
    isLoading: false,
    isProcessing: false,
    error: null as string | null,
    uploadStatus: null,
    processId: null,
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

        this.processId = response.data.process_id
        return response.data
      } catch (error: any) {
        throw new Error(error.response?.data?.error || 'File upload failed')
      }
    },

    async checkUploadStatus(processId: string) {
      try {
        const response = await axios.post(
          `${config.baseURL}/translations/check-upload-status/`,
          { process_id: processId }
        )
        this.uploadStatus = response.data.status
        return response.data
      } catch (error: any) {
        throw new Error(error.response?.data?.error || 'Status check failed')
      }
    },

    async checkQuality(sourceText: string, translatedText: string, targetLanguage: string) {
      try {
        const response = await axios.post(`${config.baseURL}/translations/check_quality/`, {
          source_text: sourceText,
          translated_text: translatedText,
          target_language: targetLanguage
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
    }
  }
}) 