<template>
  <div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold mb-8">Lokalise Integration</h1>
    
    <!-- File Upload Section -->
    <FileUpload />
    
    <!-- Translation Pipeline Section -->
    <TranslationPipeline />
  </div>
</template>

<script setup lang="ts">
import FileUpload from '~/components/FileUpload.vue'
import TranslationPipeline from '~/components/TranslationPipeline.vue'
</script> 