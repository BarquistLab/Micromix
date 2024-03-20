<template>
  <div>
    <b-progress
      :value="loading.bar.value"
      :variant="loading.bar.variant"
      :key="loading.bar.variant"
      :max="loading.bar.max" 
      animated
      height="6px"
    ></b-progress>
  </div>
</template>

<script>
export default {
  props: {
    increment: Number,
  },
  data() {
    return {
      loading: {
        state: false,
        bar: {
          variant: "primary",
          value: 0,
          timer: null,
          max: 100
        }
      }
    };
  },
  mounted() {
    //console.log("###########");
    this.loading.bar.timer = setInterval(() => {
      if (this.loading.bar.value >= this.loading.bar.max) {
        clearInterval();
      }
      else {
        this.loading.bar.value = this.loading.bar.value + this.increment;
      }
    }, 500);
  },
  beforeDestroy() {
    //console.log(this.loading.bar.timer);
    clearInterval(this.loading.bar.timer);
    this.loading.bar.timer = null;
  }
};
</script>