import Vue from 'vue'
import { BootstrapVue, BootstrapVueIcons } from 'bootstrap-vue'
import App from './App.vue'

import 'mutationobserver-shim'

import './plugins/bootstrap-vue'

import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'
import router from './router'
import VueTypeaheadBootstrap from 'vue-typeahead-bootstrap';

Vue.use(BootstrapVue)
Vue.use(BootstrapVueIcons)
Vue.component('vue-typeahead-bootstrap', VueTypeaheadBootstrap)
Vue.config.productionTip = false

new Vue({
  router,
  render: h => h(App)
}).$mount('#app')