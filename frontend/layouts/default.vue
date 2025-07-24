<template>
  <div>
    <header class="bg-white shadow">
      <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex">
            <div class="flex-shrink-0 flex items-center">
              <h1 class="text-xl font-bold text-gray-900">Translation QA</h1>
            </div>
          </div>
        </div>
      </nav>
    </header>

    <main>
      <slot />
    </main>

    <footer class="bg-white mt-8 py-4">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <p class="text-center text-gray-500 text-sm">
          Powered by Lokalise & OpenRouter
        </p>
      </div>
    </footer>
  </div>
</template> 