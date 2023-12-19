<template>
    <div class="footer-container" style="transform: scale(0.8);">
        <h3 style="color:#ccc;">Credits</h3>
        <p style="color:#ccc;">
            Book written by <span style="font-weight:700">Susan Ford Collins</span><br />
            AI Coach trained on notes from the book <br />
            Project built by <span style="font-weight:700">Benjamin Klieger</span>
        </p>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

</script>

<style scoped>
.footer-container {
    position: absolute;
    top: 0;
    right: 0;
    text-align: center;
    background-color: #101B2C;
    overflow: hidden;
    padding: 10px;
    margin-top: 250px;
    border-radius: 10px;

}
</style>