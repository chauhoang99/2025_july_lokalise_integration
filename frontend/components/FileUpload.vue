<template>
  <div class="bg-white shadow rounded-lg p-6">
    <h2 class="text-xl font-semibold mb-4">Upload Translation File</h2>

    <!-- Upload Form -->
    <div class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">Translation File</label>
        <div class="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
          <div class="space-y-1 text-center">
            <svg
              class="mx-auto h-12 w-12 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
              aria-hidden="true"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            <div class="flex text-sm text-gray-600">
              <label
                for="file-upload"
                class="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500"
              >
                <span>Upload a file</span>
                <input 
                  id="file-upload" 
                  name="file-upload" 
                  type="file" 
                  class="sr-only"
                  @change="handleFileChange"
                >
              </label>
              <p class="pl-1">or drag and drop</p>
            </div>
            <p class="text-xs text-gray-500">
              JSON, YAML, or other translation files up to 10MB
            </p>
          </div>
        </div>
        <div v-if="selectedFile" class="mt-2 text-sm text-gray-500">
          Selected file: {{ selectedFile.name }}
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">Target Language</label>
        <select
          v-model="targetLanguage"
          class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        >
          <option value="">Select a language</option>
          <option v-for="(name, code) in supportedLanguages" :key="code" :value="code">
            {{ name }}
          </option>
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">Tags (optional)</label>
        <input
          v-model="tags"
          type="text"
          placeholder="Enter tags separated by commas"
          class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
      </div>

      <button
        @click="uploadFile"
        :disabled="!canUpload || isLoading"
        class="w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
      >
        <svg
          v-if="isLoading"
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
        {{ isLoading ? 'Uploading...' : 'Upload File' }}
      </button>
    </div>

    <!-- Upload Status -->
    <div v-if="uploadResult" class="mt-6 space-y-4">
      <h3 class="text-lg font-medium">Upload Status</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-gray-50 p-4 rounded-md">
          <div class="text-sm text-gray-500">Status</div>
          <div class="text-xl font-semibold" :class="{
            'text-green-600': uploadResult.status === 'success',
            'text-yellow-600': uploadResult.status === 'processing',
            'text-red-600': uploadResult.status === 'error'
          }">
            {{ uploadResult.status }}
          </div>
        </div>
        <div v-if="uploadResult.stats" class="bg-gray-50 p-4 rounded-md">
          <div class="text-sm text-gray-500">Keys Added/Updated</div>
          <div class="text-xl font-semibold">
            {{ uploadResult.stats.keys_added + uploadResult.stats.keys_updated }}
          </div>
          <div class="text-sm text-gray-500">
            Added: {{ uploadResult.stats.keys_added }} / Updated: {{ uploadResult.stats.keys_updated }}
          </div>
        </div>
        <div v-if="uploadResult.stats" class="bg-gray-50 p-4 rounded-md">
          <div class="text-sm text-gray-500">Keys Skipped</div>
          <div class="text-xl font-semibold">{{ uploadResult.stats.keys_skipped }}</div>
        </div>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="mt-4 p-4 bg-red-50 text-red-700 rounded-md">
      {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useTranslationStore } from '~/stores/translation'
import { supportedLanguages } from '~/constants/languages'

const translationStore = useTranslationStore()

const selectedFile = ref<File | null>(null)
const targetLanguage = ref('')
const tags = ref('')
const isLoading = ref(false)
const error = ref<string | null>(null)
const uploadResult = ref<any>(null)

const canUpload = computed(() => {
  return selectedFile.value && targetLanguage.value !== ''
})

const handleFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    selectedFile.value = input.files[0]
  }
}

const uploadFile = async () => {
  if (!selectedFile.value) return

  try {
    isLoading.value = true
    error.value = null
    
    // Convert tags string to array
    const tagArray = tags.value
      ? tags.value.split(',').map(tag => tag.trim()).filter(Boolean)
      : []

    const result = await translationStore.uploadFile(
      selectedFile.value,
      targetLanguage.value,
      tagArray
    )
    
    uploadResult.value = result

    // Start polling for status if we have a process ID
    if (result.process_id) {
      pollUploadStatus(result.process_id)
    }

  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Upload failed'
  } finally {
    isLoading.value = false
  }
}

const pollUploadStatus = async (processId: string) => {
  try {
    const result = await translationStore.checkUploadStatus(processId)
    
    if (result.status === 'processing') {
      // Poll again in 2 seconds
      setTimeout(() => pollUploadStatus(processId), 2000)
    }
    
    uploadResult.value = {
      ...uploadResult.value,
      status: result.status
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Status check failed'
  }
}
</script> 