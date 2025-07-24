// https://nuxt.com/docs/api/configuration/nuxt-config
import { defineNuxtConfig } from 'nuxt/config'

export default defineNuxtConfig({
  devtools: { enabled: true },
  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt'
  ],
  runtimeConfig: {
    public: {
      apiBase: '/api'
    }
  },
  ssr: false,
  app: {
    baseURL: '/',
    buildAssetsDir: '_nuxt/',
    head: {
      title: 'Translation QA',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' }
      ]
    }
  },
  typescript: {
    strict: true,
    typeCheck: false  // Disable type checking during build
  }
})