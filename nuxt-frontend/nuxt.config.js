export default defineNuxtConfig({
  serverMiddleware: [
    '~/server/api/joycoach.ts'
  ],
  app: {
    head: {
      title: "Nuxt App",
      link: [{ rel: "icon", type: "image/x-icon", href: "/favicon.ico" }],
    }
  },
  css: [
    "@/assets/main.css",
    '@/assets/global-styles.css',
    "primeicons/primeicons.css",
    'primevue/resources/themes/bootstrap4-light-blue/theme.css',
    'primevue/resources/primevue.min.css',
  ],
  modules: ['nuxt-primevue'],
  primevue: {
    ripple: true,
    components: {
      include: ['Textarea', 'Button', 'Fieldset','Divider','Toast'],
    },
  },
  runtimeConfig: {
    private: {
      BACKEND_API_KEY: process.env.NUXT_BACKEND_API_KEY,
      BACKEND_URL: process.env.NUXT_BACKEND_URL
    },
  },
  nitro: {  
    vercel: {  
      functions: {  
        maxDuration: 30,  
      },  
    },  
  },
});
