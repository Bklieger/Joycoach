<template>
  <div class="header-container">
    <img src="@/assets/bookcover.jpeg" alt="Background Image" class="background-image" />
  </div>
</template>
  
<script setup lang="ts">
</script>
  
<style scoped>
.header-container {
  position: relative;
  text-align: center;
  background-color: #0D1B2C;
  overflow: hidden;
}

.background-image {
  max-height: 400px;
  width: auto;
  height: auto;
  object-fit: contain;
  margin: 0 auto;
}
</style>
  