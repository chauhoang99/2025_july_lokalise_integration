<template>
  <div class="bg-white shadow rounded-lg p-6 mt-8">
    <h2 class="text-xl font-semibold mb-4">Translation Pipeline</h2>
    
    <!-- Translation Form -->
    <form @submit.prevent="startTranslation" class="space-y-4">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Source Language -->
        <div>
          <label class="block text-sm font-medium text-gray-700">Source Language</label>
          <select
            v-model="sourceLanguage"
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            required
          >
            <option value="">Select Language</option>
            <option v-for="(name, code) in supportedLanguages" :key="code" :value="code">
              {{ name }}
            </option>
          </select>
        </div>

        <!-- Target Language -->
        <div>
          <label class="block text-sm font-medium text-gray-700">Target Language</label>
          <select
            v-model="targetLanguage"
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            required
          >
            <option value="">Select Language</option>
            <option v-for="(name, code) in supportedLanguages" :key="code" :value="code">
              {{ name }}
            </option>
          </select>
        </div>

        <!-- Force Translate -->
        <div class="flex items-center">
          <label class="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              v-model="forceTranslate"
              class="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
            <span class="text-sm font-medium text-gray-700">Force Retranslation</span>
          </label>
        </div>
      </div>

      <!-- Action Button -->
      <div>
        <button
          type="submit"
          :disabled="isProcessing"
          class="w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          <svg
            v-if="isProcessing"
            class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          {{ isProcessing ? 'Processing...' : 'Start Translation' }}
        </button>
      </div>
    </form>

    <!-- Error Message -->
    <div v-if="error" class="mt-4 p-4 bg-red-50 text-red-700 rounded-md">
      {{ error }}
    </div>

    <!-- Translation Results -->
    <div v-if="lastResult" class="mt-6 space-y-4">
      <h3 class="text-lg font-medium">Last Translation Results</h3>
      <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div class="bg-gray-50 p-4 rounded-md">
          <div class="text-sm text-gray-500">Processed</div>
          <div class="text-xl font-semibold">{{ lastResult.total_processed }}</div>
        </div>
        <div class="bg-green-50 p-4 rounded-md">
          <div class="text-sm text-green-700">Successful</div>
          <div class="text-xl font-semibold text-green-700">{{ lastResult.successful }}</div>
          <div class="text-sm text-green-600">
            New: {{ lastResult.new_translations }} / Updated: {{ lastResult.updated_translations }}
          </div>
        </div>
        <div class="bg-yellow-50 p-4 rounded-md">
          <div class="text-sm text-yellow-700">Skipped</div>
          <div class="text-xl font-semibold text-yellow-700">{{ lastResult.skipped }}</div>
        </div>
      </div>

      <!-- Detailed Results -->
      <div class="mt-4">
        <button
          @click="showDetails = !showDetails"
          class="text-sm text-indigo-600 hover:text-indigo-500"
        >
          {{ showDetails ? 'Hide' : 'Show' }} Details
        </button>
        <div v-if="showDetails" class="mt-4">
          <!-- Table Headers -->
          <div class="grid grid-cols-3 gap-4 mb-2 font-medium text-gray-700 bg-gray-50 p-2 rounded-t-md">
            <div>Source Text ({{ sourceLanguage }})</div>
            <div>Existing Translation</div>
            <div>LLM Translation</div>
          </div>
          <!-- Table Content -->
          <div class="space-y-2">
            <div
              v-for="detail in lastResult.details"
              :key="detail.key_id"
              class="grid grid-cols-3 gap-4 p-2 rounded-md"
              :class="{
                'bg-green-50': detail.status === 'success',
                'bg-yellow-50': detail.status === 'skipped',
                'bg-red-50': detail.status === 'error'
              }"
            >
              <!-- Source Text -->
              <div class="text-sm text-gray-700">{{ detail.source_text }}</div>

              <!-- Existing Translation -->
              <div class="text-sm text-gray-700">
                <template v-if="detail.status === 'skipped' && detail.reason === 'Translation already exists'">
                  <div class="font-medium text-yellow-700">Existing Translation</div>
                  <div class="mt-1">{{ detail.existing_translation }}</div>
                </template>
                <template v-else>
                  <div class="font-medium text-gray-500">No existing translation</div>
                </template>
              </div>

              <!-- LLM Translation -->
              <div class="text-sm">
                <template v-if="detail.status === 'success'">
                  <div class="font-medium text-green-700">New Translation</div>
                  <div class="mt-1 text-gray-700">{{ detail.translated_text }}</div>
                  <div class="mt-2 text-xs text-green-600" v-if="detail.is_new_translation">
                    ✨ New Translation
                  </div>
                  <div class="mt-2 text-xs text-blue-600" v-else>
                    🔄 Updated Translation
                  </div>
                </template>
                <template v-else-if="detail.status === 'skipped'">
                  <div class="font-medium text-yellow-700">Skipped</div>
                  <div class="mt-1 text-yellow-600">{{ detail.reason }}</div>
                </template>
                <template v-else>
                  <div class="font-medium text-red-700">Error</div>
                  <div class="mt-1 text-red-600">{{ detail.error }}</div>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useTranslationStore } from '~/stores/translation'
import { supportedLanguages } from '~/constants/languages'

const store = useTranslationStore()

const sourceLanguage = ref('en')
const targetLanguage = ref('')
const forceTranslate = ref(false)
const showDetails = ref(false)

const isProcessing = computed(() => store.isProcessing)
const error = computed(() => store.error)
const lastResult = computed(() => store.lastResult)

async function startTranslation() {
  await store.processTranslations(
    targetLanguage.value,
    sourceLanguage.value,
    forceTranslate.value
  )
}
</script> 