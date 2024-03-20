<template>
  <div>
    <div class="b-alert-parent">
      <b-alert variant="danger" dismissible fade :show="dismissCountDown" @dismissed="alertDismissed" @dismiss-count-down="countDownChanged">
        <strong class="alert-heading" style="display:inline">{{error.error_type}} </strong>
        <span>{{error ? error.error_message : ''}}</span> 
      </b-alert>
    </div>
  </div>
</template>

<script>

export default {
  props: {
    type: Object,
    //error: Object,
    default: () => ({ error_type: '', error_message: '' })
  },
  watch: {
  error: {
    handler(newValue) {
      if (newValue === null) {
        // Handle the case where error is explicitly set to null.
        this.alertDismissed();
      } else {
        this.showAlert();
      }
    }
  }
},
  data() {
    return {
      dismissSecs: 16,
      dismissCountDown: 0
    };
  },
  methods: {
    countDownChanged(dismissCountDown) {
      this.dismissCountDown = dismissCountDown;
    },
    showAlert() {
      this.dismissCountDown = this.dismissSecs;
    },
    alertDismissed() {
      this.dismissCountDown = 0;
      this.$emit('error_alert_dismissed');
    }
  }
};
</script>

<style scoped>
.b-alert-parent {
  width: 90vw;
  margin: auto;
}
</style>