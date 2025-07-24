import { defineStore } from 'pinia'
import axios from 'axios'

const config = {
  baseURL: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/api'
}

export const useTranslationStore = defineStore('translation', {
  state: () => ({
    isLoading: false,
    error: null,
    uploadStatus: null,
    processId: null
  }),

  actions: {
    async uploadFile(file: File, targetLanguage: string, tags?: string[]) {
      try {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('lang_iso', targetLanguage)
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
    }
  }
}) 