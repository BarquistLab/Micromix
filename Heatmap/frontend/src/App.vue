<template>
  <div id="app">
    <loadingOverlay v-if="this.longLoading" />
    <deckglCanvas @long-loading-finished="longLoading = false" />
    <router-view />
  </div>
</template>

<script>
// @ is an alias to /src

// The Heatmap canvas
import deckglCanvas from './components/deckglCanvas.vue';
// The loading screen
import loadingOverlay from './components/loadingOverlay.vue';

export default {
  components: {
    deckglCanvas,
    loadingOverlay,
  },
  data() {
    return {
      longLoading: true,
    };
  },
};
</script>

<style scoped>
#app {
  font-family: "Space Grotesk", -apple-system, BlinkMacSystemFont, "Segoe UI",
    Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

#nav {
  padding: 30px;
}

#nav a {
  font-weight: bold;
  color: #2c3e50;
}

#nav a.router-link-exact-active {
  color: #42b983;
}
</style>
