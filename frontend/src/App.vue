<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="wrapper">
    <RouterView />
  </div>
</template>

<style scoped>
.wrapper {
  display: flex;
  place-items: flex-start;
  flex-wrap: wrap;
  height: 100vh;
}
</style>
