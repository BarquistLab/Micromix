<template>
  <div id="app">
    <!-- <div class="draggableRegion"></div> -->
    <error_alert
      :error="error"
      @error_alert_dismissed="error = null"
      style="position:fixed;top:10px;width:100vw;z-index:1100;"
    />
    <loading
      v-if="this.loading.state"
      :increment="this.loading.increment"
      style="position: fixed;z-index: 1900;top: 0;left: 0;width: 100vw;"
    />
    <div v-if="this.initializing" class="initial_load">
      <img src="./assets/hzi-logo.svg" alt="">
      <div>
        <div class="ball-grid-pulse"><div></div><div></div><div></div><div></div><div></div><div></div><div></div><div></div><div></div></div>
        <h5 class="title initial_load_text">Loading Session</h5>
        <small>v1.0.1-local</small>
      </div>
    </div>
    <b-alert variant="info" show dismissible><strong class="alert-heading">Update v1.0.1-local: </strong>
       Fixed plugin shading button state.
    </b-alert>
    <!-- <b-progress v-if="loading.state" :value="loading.bar.value" :variant="loading.bar.variant" :key="loading.bar.variant" height="6px"></b-progress> -->
    <!-- <div class="loading" v-if="loading"><b-spinner label="Spinning"></b-spinner><span>Loading ...</span></div> -->
    <div v-if="!this.initializing">
      <div v-if="loading.state === false">
        <toolbar :locked="config.locked" :backend_url="backend_url" @error_occured="error_occured" />
      </div>
      <div class="grid_container">
        <!-- <div class="header">
        <b-button variant="secondary" size="sm"><b-icon icon="cloud-download" aria-hidden="true"></b-icon></b-button>
        <b-button variant="secondary" size="sm"><b-icon icon="upload" aria-hidden="true"></b-icon></b-button>
        </div>-->
        <div class="main_cell">
          <div class="main_cell_header block">
            <div class="cell_title_ud">
              <h5 class="title">Upload data</h5>
            </div>
            <div
              class="cell_upload_data field"
              @click="show_modal('bv_modal_addData')"
              id="upload_data_parent"
            >
              <b-popover
                id="tutorial_popover"
                :no-fade="true"
                triggers
                placement="right"
                target="upload_data_parent"
                title="1. Upload your data"
              >Click on the + to upload, merge, or remove multiple datasets from our databases or your computer.</b-popover>
              <addDataButton v-on:plugin_clicked="show_modal('modal_add_plugin')" />
              <!-- <b-button variant="secondary"><b-icon icon="table"></b-icon>Upload</b-button> -->
            </div>
            <div class="cell_title_sp">
              <h5 v-if="config.plugins && this.$route.query.config" class="title">Select the visualization</h5>
              <h5 v-else class="title">Specify the organism that best fits your data</h5>
            </div>
            <div
              class="cell_select_plugin field plugins"
              id="select_organism_parent"
              v-if="!this.$route.query.config"
            >
              <b-popover
                id="tutorial_popover"
                :no-fade="true"
                triggers
                placement="bottom"
                target="select_organism_parent"
                title="Configure the organism"
              >Specify an organism before uploading if you want to upload biological data and use specific features. The application offers a wide range of general-purpose features for non-biological data.</b-popover>
              <organism_selection
                @click.native="set_local_organism(organism.id), show_modal('bv_modal_addData')"
                v-for="organism in organisms.items"
                :key="organism.id"
                :organism="organism"
                :local_active_organism_id="config.active_organism_id"
              />
            </div>
            <div
              class="cell_select_plugin field plugins"
              id="select_plugin_parent"
              v-if="config.plugins && this.$route.query.config"
            >
              <b-popover
                id="tutorial_popover"
                :no-fade="true"
                triggers
                placement="top"
                target="select_plugin_parent"
                title="5. Visualize your data"
              >Click on one of the plugins (e.g. Clustergrammer, Plotly) above to generate a plot.</b-popover>

              <!-- This is where we structure and display the plugins that we have loaded either from the mongoDB or from the local plugins.json into the "config.plugins" variable. -->
              <plugins
                @click.native="select_plugin(plugin)"
                :active_plugin="active_plugin_id"
                :active_vis_link="active_vis_link"
                v-for="plugin in config.plugins"
                :key="plugin.name"
                :title="plugin.name"
                :desc="plugin.desc"
                :image_url="plugin.image_url"
                :id="plugin._id"
               />
              <!-- <plugins
                v-on:plugin_clicked="show_modal('modal_add_plugin')"
                :title="'Add Plugin'"
                :desc="'Connect a new visualization'"
                :img="'add_plugin.svg'"
              />-->
            </div>
          </div>
          <!-- <h5 class="title">Filter queries</h5> -->
          <div class="field block" v-if="this.config.transformed_dataframe.length > 0">
            <search_query
              @dataframe_filtered="redirect_to_config($event); update_filtered(true)"
              @error_occured="error_occured"
              v-bind:df_categories="unique_df_categories"
              v-bind:server_queries="this.config.query"
              v-bind:backend_url="backend_url"
              v-bind:table_titles="table_titles"
              v-bind:active_organism="configure_active_organism"
              v-if="!this.loading.state"
            />
          </div>
          <div>
            <visualization v-bind:vis_link="this.active_vis_link" v-if="this.active_vis_link" />
          </div>
          <div class="html_dataframe" v-if="config.transformed_dataframe.length > 0">
            <dataframe
              v-bind:dataframe="this.config.transformed_dataframe"
              v-bind:dataframe_filtered="this.config.filtered_dataframe"
              v-bind:update_is_filter="this.filtered"
            />
          </div>
        </div>
        <div class="menu"></div>
        <div class="footer"></div>
      </div>

      <div>
        <b-modal id="bv_modal_addData" hide-footer>
          <addDataForm
            v-bind:matrices="this.config.preview_matrices"
            v-bind:plugins="this.config.plugins"
            v-bind:df_categories="Object.keys(this.config.transformed_dataframe)"
            v-bind:backend_url="backend_url"
            v-bind:local_active_organism_id="config.active_organism_id"
            v-bind:active_organism="configure_active_organism"
            @dataframe_change="redirect_to_config($event); update_filtered(false);"
            @error_occured="error_occured"
            @close='hide_modal("bv_modal_addData")'
          />
        </b-modal>
        <b-modal id="modal_add_plugin" hide-footer>
          <add_plugin @plugins_change="redirect_to_config" :backend_url="backend_url" />
        </b-modal>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import organisms from "./assets/json/organisms.json";
import addDataButton from "./components/addDataButton";
import addDataForm from "./components/addDataForm.vue";
import add_plugin from "./components/add_plugin";
import dataframe from "./components/dataframe";
import error_alert from "./components/error_alert";
import organism_selection from "./components/organism_selection";
import loading from "./components/loading";
import plugins from "./components/plugins";
import search_query from "./components/search_query";
import toolbar from "./components/toolbar";
import visualization from "./components/visualization";
import pluginsConfig from "../../plugins.json"
//If running outside of docker, you will need to change the location of the plugins.json file to: 
//import pluginsConfig from "/plugins.json"


export default {
  name: "App",
  components: {
    addDataForm,
    visualization,
    plugins,
    add_plugin,
    addDataButton,
    search_query,
    toolbar,
    dataframe,
    loading,
    error_alert,
    organism_selection,
  },
  data() {
    return {
      // backend_url: 'https://hiri-webtool-backend-v011-44nub6ij6q-ez.a.run.app',
      // backend_url: 'http://dataframe-playground-backend.test.fedcloud.eu', 
      // backend_url: 'http://localhost:5000',
      // backend_url: '/home/r/Desktop/dataframe_beginning_vue2/backend',
         backend_url: 'http://127.0.0.1:5000', 
      organisms,
      loading: {
        state: true,
        increment: 10,
        bar: {
          variant: "primary",
          value: 0,
          timer: null
        }
      },
      config: null,
      active_plugin_id: null,
      active_vis_link: null,
      error: null,
      filtered: false,
      initializing: true,
    };
  },
  created() {
    this.load_config();
  },
  computed: {
    unique_df_categories: function() {
      if (this.config.filtered_dataframe[0]) {
        return [...new Set([...Object.keys(this.config.transformed_dataframe[0]) ,...Object.keys(this.config.filtered_dataframe[0])])];
      } else {
        return Object.keys(this.config.transformed_dataframe[0]);
      }
    },
    table_titles: function() {
      let active_matrices_flattened = [].concat.apply([], this.config.active_matrices); // Flatten the nested array.
      // return active_matrices_flattened.map(a => ({text: a.title, value: a.id}));
      return active_matrices_flattened.map(a => a.title);
    },
     configure_active_organism: function() {
      let active_organism
      for(var organism in this.organisms.items) {
        if(this.organisms.items[organism].id == this.config.active_organism_id) {
          active_organism = this.organisms.items[organism]
        }
      }
      // console.log(active_organism)
      return active_organism
    }
  },
  watch: {
    $route: "load_config",
  },
  methods: {
    set_local_organism(organism_id) {
      this.config.active_organism_id = organism_id
    },
    select_plugin(plugin) {
      if (this.config.active_matrices.length > 0) {
        this.active_vis_link = null;
        this.active_plugin_id = null;
        if (plugin._id != this.active_plugin_id) {
          this.active_plugin_id = plugin._id;
          let vis_exists = false;
          for (let i in this.config.vis_links) {
            if (this.config.vis_links[i].plugin_id == this.active_plugin_id) {
              this.active_vis_link = this.config.vis_links[i].link;
              vis_exists = true;
              break;
            }
          }
          if (vis_exists === false) {
            // console.log("doesn't contain");
            this.generate_vis_link(plugin);
          }
        } else {
          this.active_plugin_id = "";
        }
        this.post_active_plugin(this.active_plugin_id)
      }
    },
    update_filtered(state) {
      this.filtered = state;
    },
    post_active_plugin(plugin_id) {
      const path = `${this.backend_url}/active_plugin`;
      var payload = new FormData();
      payload.append("active_plugin_id", JSON.stringify(plugin_id));
      payload.append("url", JSON.stringify(this.$route.query.config));
      axios.post(path, payload).then(res => {
        if (res.data.error_type) {
          this.error_occured(res.data);
        }
      });
    },
    generate_vis_link(plugin) {
      this.loading.state = true;
      this.loading.increment = 2;
      const path = `${this.backend_url}/visualization`;
      var payload = new FormData();
      payload.append("plugin", JSON.stringify(plugin));
      payload.append("url", JSON.stringify(this.$route.query.config));
      axios.post(path, payload).then(res => {
        if (res.data.error_type) {
          this.error_occured(res.data);
        } else {
          this.load_config();
          this.active_vis_link = res.data.vis_link.link;
        }
      });
    },
    get_active_vis_link(plugin_id) {
      var vis_link = null
      for(let i=0;i<this.config.vis_links.length;i++) {
        if(this.config.vis_links[i].plugin_id==plugin_id) {
          vis_link = this.config.vis_links[i].link
          break
        }
      }
      return vis_link
    },
    load_config() {
      this.loading.state = true;
      this.loading.increment = 5;
      this.active_vis_link = null;
      this.config = null;
      const path = `${this.backend_url}/config`;
      var payload = new FormData();
      payload.append("url", JSON.stringify(this.$route.query.config));
      axios
        .post(path, payload)
        .then(res => {
          if (res.data.error_type) {
            this.error_occured(res.data);
          } else {
            //this.config = res.data.db_entry;
            // This is the session config which determines every data point in the whole session. We merge the session loaded from the DB via the backend and merge it with the local plugins file.
            this.config = {...res.data.db_entry, ...pluginsConfig};

            this.parse_dataframe_json();
            this.active_plugin_id = this.config.active_plugin_id
            this.active_vis_link = this.get_active_vis_link(this.active_plugin_id) // PERFORMANCE: Maybe check for "", undefined, or null of active_plugin_id
            this.$nextTick(() => {
              this.loading.state = false;
              this.initializing = false;
            });
          }
        })
        .catch(error => {
          this.unexpected_error_occured(error)
        });
    },
    parse_dataframe_json() {
      if (this.config.transformed_dataframe.length && this.config.transformed_dataframe.length > 0) {
        this.config.transformed_dataframe = JSON.parse(this.config.transformed_dataframe)
      }
      if (this.config.filtered_dataframe && this.config.filtered_dataframe.length > 0) {
        this.config.filtered_dataframe = JSON.parse(this.config.filtered_dataframe)
      }
    },
    //get_plugins(res) {
    //  this.hide_modal("modal_add_plugin");
    //  this.plugins = res.data;
    //},
    hide_modal(modal_id) {
      this.$bvModal.hide(modal_id);
    },
    show_modal(modal_id) {
      this.$bvModal.show(modal_id);
    },
    error_occured(error) {
      console.log('false');
      this.loading.state = false;
      this.error = error;
      console.log(this.error);
    },
    unexpected_error_occured(error) {
      this.error = {error_type: "Unexpected Error:", error_message: String(error)};
      console.log(error);
      this.loading.state = false;
    },
    redirect_to_config(res) {
      // this.config = null
      // console.log("res: ", res);
      // console.log(this.config);
      // console.log(res.data.db_entry_id["$oid"]);
      if (this.config._id == res.data.db_entry_id["$oid"]) {
        // this.$router.go()
        this.active_vis_link = null;
        this.load_config();
        console.log(this.config);
      } else {
        this.$router.push({
          path: "/",
          query: { config: res.data.db_entry_id["$oid"] }
        });
      }
      this.hide_modal("bv_modal_addData");
    },
    refresh(modal) {
      this.$router.go();
      this.hide_modal(modal);
    }
  },
  mounted() {
    this.loading.bar.timer = setInterval(() => {
      this.loading.bar.value = this.loading.bar.value + 50 * Math.random(3, 4);
    }, 500);
  },
  beforeDestroy() {
    clearInterval(this.loading.bar.timer);
    this.loading.bar.timer = null;
  }
};
</script>

<style>
#app {
  /* font-family: "SF Compact Rounded", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"; */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  margin-top: 0px;
  min-height: 100vh;
}
h5 {
  font-size: 0.9rem !important;
  font-weight: 600 !important;
}
.popover {
  z-index: 1030 !important;
}
button {
  -webkit-app-region: no-drag !important;
}
.draggableRegion {
  -webkit-app-region: drag;
  position: fixed;
  z-index: 1800;
  height: 1.5rem;
  width: 100vw;
  /* backdrop-filter: blur(15px); */
}
/* button {
  margin: 5px !important;
} */
.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}
.img_in_btn {
  margin-right: 5px;
}
.center {
  text-align: center;
}
#bv_modal_addData > * {
  max-width: 90vw !important;
}
.grid_container {
  display: grid;
  grid-column-gap: 0px;
  grid-row-gap: 0px;
  padding: 0 2rem 2rem 2rem;
}
.main_cell {
  grid-area: 2 / 1 / 3 / 4;
}
.main_cell_header {
  display: grid;
  grid-template-columns: repeat(2, auto);
  grid-template-rows: repeat(2, auto);
  grid-column-gap: 1rem;
  grid-row-gap: 1rem;
}
.block {
  margin-bottom: 1rem;
}
.field {
  background-color: #e9ecef;
  padding: 15px;
  border-radius: 20px;
}
.plugins {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  grid-template-rows: repeat(1, 1fr);
  grid-column-gap: 20px;
  grid-row-gap: 20px;
}
.header {
  grid-area: 1 / 1 / 2 / 4;
  height: 6vh;
  margin-bottom: 2em;
}
.menu {
  grid-area: 2 / 1 / 3 / 2;
}
.footer {
  height: 10vh;
  grid-area: 3 / 1 / 4 / 4;
}
.title {
  margin-bottom: 1em;
}
.cell_upload_data {
  grid-area: 2 / 1 / 3 / 2;
}
.cell_select_plugin {
  grid-area: 2 / 2 / 3 / 3;
}

/* Initializing loader */

.ball-grid-pulse > div {
  background-color: #005AA0 !important;
}
.ball-grid-pulse {
  height: 57px;
}
.ball-grid-pulse {
  margin: auto;
}
.initial_load {
  background-color: #f8f9fa;
  width: 100vw;
  height: 100vh;
  position: absolute;
  text-align: center;
  z-index: 1099;
  color: #005AA0;
}
.initial_load > * {
  margin: auto;
  position: absolute;
  left: 50%;
  transform: translate(-50%, -50%);
}
.initial_load > img {
  height: 16px;
  top: 3%;
}
.initial_load > div {
  top: 50%
}
.initial_load_text {
  margin-top: 1rem;
  font-weight: 400 !important;
  font-family: 'SF Mono', -apple-system, BlinkMacSystemFont, 'Courier New', Courier, monospace;
}

/* Initializing Loader loaders.css.min */
/* Credit to: https://github.com/ConnorAtherton/loaders.css */

.ball-pulse-sync>div,.ball-pulse>div,.ball-scale-random>div,.ball-scale>div{background-color:#fff;border-radius:100%;margin:2px;display:inline-block}@-webkit-keyframes scale{0%,80%{-webkit-transform:scale(1);transform:scale(1);opacity:1}45%{-webkit-transform:scale(.1);transform:scale(.1);opacity:.7}}@keyframes scale{0%,80%{-webkit-transform:scale(1);transform:scale(1);opacity:1}45%{-webkit-transform:scale(.1);transform:scale(.1);opacity:.7}}.ball-pulse>div:nth-child(1){-webkit-animation:scale .75s -.24s infinite cubic-bezier(.2,.68,.18,1.08);animation:scale .75s -.24s infinite cubic-bezier(.2,.68,.18,1.08)}.ball-pulse>div:nth-child(2){-webkit-animation:scale .75s -.12s infinite cubic-bezier(.2,.68,.18,1.08);animation:scale .75s -.12s infinite cubic-bezier(.2,.68,.18,1.08)}.ball-pulse>div:nth-child(3){-webkit-animation:scale .75s 0s infinite cubic-bezier(.2,.68,.18,1.08);animation:scale .75s 0s infinite cubic-bezier(.2,.68,.18,1.08)}.ball-pulse>div{width:15px;height:15px;-webkit-animation-fill-mode:both;animation-fill-mode:both}@-webkit-keyframes ball-pulse-sync{33%{-webkit-transform:translateY(10px);transform:translateY(10px)}66%{-webkit-transform:translateY(-10px);transform:translateY(-10px)}100%{-webkit-transform:translateY(0);transform:translateY(0)}}@keyframes ball-pulse-sync{33%{-webkit-transform:translateY(10px);transform:translateY(10px)}66%{-webkit-transform:translateY(-10px);transform:translateY(-10px)}100%{-webkit-transform:translateY(0);transform:translateY(0)}}.ball-pulse-sync>div:nth-child(1){-webkit-animation:ball-pulse-sync .6s -.14s infinite ease-in-out;animation:ball-pulse-sync .6s -.14s infinite ease-in-out}.ball-pulse-sync>div:nth-child(2){-webkit-animation:ball-pulse-sync .6s -70ms infinite ease-in-out;animation:ball-pulse-sync .6s -70ms infinite ease-in-out}.ball-pulse-sync>div:nth-child(3){-webkit-animation:ball-pulse-sync .6s 0s infinite ease-in-out;animation:ball-pulse-sync .6s 0s infinite ease-in-out}.ball-pulse-sync>div{width:15px;height:15px;-webkit-animation-fill-mode:both;animation-fill-mode:both}@-webkit-keyframes ball-scale{0%{-webkit-transform:scale(0);transform:scale(0)}100%{-webkit-transform:scale(1);transform:scale(1);opacity:0}}@keyframes ball-scale{0%{-webkit-transform:scale(0);transform:scale(0)}100%{-webkit-transform:scale(1);transform:scale(1);opacity:0}}.ball-scale>div{height:60px;width:60px;-webkit-animation:ball-scale 1s 0s ease-in-out infinite;animation:ball-scale 1s 0s ease-in-out infinite}.ball-scale-random{width:37px;height:40px}.ball-scale-random>div{position:absolute;height:30px;width:30px;-webkit-animation:ball-scale 1s 0s ease-in-out infinite;animation:ball-scale 1s 0s ease-in-out infinite}.ball-rotate,.ball-rotate>div{position:relative}.ball-rotate>div,.ball-rotate>div:after,.ball-rotate>div:before{background-color:#fff;width:15px;height:15px;border-radius:100%}.ball-scale-random>div:nth-child(1){margin-left:-7px;-webkit-animation:ball-scale 1s .2s ease-in-out infinite;animation:ball-scale 1s .2s ease-in-out infinite}.ball-scale-random>div:nth-child(3){margin-left:-2px;margin-top:9px;-webkit-animation:ball-scale 1s .5s ease-in-out infinite;animation:ball-scale 1s .5s ease-in-out infinite}@-webkit-keyframes rotate{0%{-webkit-transform:rotate(0);transform:rotate(0)}50%{-webkit-transform:rotate(180deg);transform:rotate(180deg)}100%{-webkit-transform:rotate(360deg);transform:rotate(360deg)}}.ball-rotate>div{margin:2px;-webkit-animation-fill-mode:both;animation-fill-mode:both}.ball-rotate>div:first-child{-webkit-animation:rotate 1s 0s cubic-bezier(.7,-.13,.22,.86) infinite;animation:rotate 1s 0s cubic-bezier(.7,-.13,.22,.86) infinite}.ball-rotate>div:after,.ball-rotate>div:before{margin:2px;content:"";position:absolute;opacity:.8}.ball-rotate>div:before{top:0;left:-28px}.ball-rotate>div:after{top:0;left:25px}.ball-clip-rotate>div{border-radius:100%;margin:2px;border:2px solid #fff;border-bottom-color:transparent;height:26px;width:26px;background:0 0!important;display:inline-block;-webkit-animation:rotate .75s 0s linear infinite;animation:rotate .75s 0s linear infinite}@keyframes rotate{0%{-webkit-transform:rotate(0);transform:rotate(0)}50%{-webkit-transform:rotate(180deg);transform:rotate(180deg)}100%{-webkit-transform:rotate(360deg);transform:rotate(360deg)}}@keyframes scale{30%{-webkit-transform:scale(.3);transform:scale(.3)}100%{-webkit-transform:scale(1);transform:scale(1)}}.ball-clip-rotate-pulse{position:relative;-webkit-transform:translateY(-15px);transform:translateY(-15px)}.ball-clip-rotate-pulse>div{-webkit-animation-fill-mode:both;animation-fill-mode:both;position:absolute;top:0;left:0;border-radius:100%}.ball-clip-rotate-pulse>div:first-child{background:#fff;height:16px;width:16px;top:7px;left:-7px;-webkit-animation:scale 1s 0s cubic-bezier(.09,.57,.49,.9) infinite;animation:scale 1s 0s cubic-bezier(.09,.57,.49,.9) infinite}.ball-clip-rotate-pulse>div:last-child{position:absolute;width:30px;height:30px;left:-16px;top:-2px;background:0 0;border:2px solid;border-color:#fff transparent;-webkit-animation:rotate 1s 0s cubic-bezier(.09,.57,.49,.9) infinite;animation:rotate 1s 0s cubic-bezier(.09,.57,.49,.9) infinite;-webkit-animation-duration:1s;animation-duration:1s}.ball-beat>div,.ball-scale-multiple>div{background-color:#fff;border-radius:100%}@keyframes rotate{0%{-webkit-transform:rotate(0) scale(1);transform:rotate(0) scale(1)}50%{-webkit-transform:rotate(180deg) scale(.6);transform:rotate(180deg) scale(.6)}100%{-webkit-transform:rotate(360deg) scale(1);transform:rotate(360deg) scale(1)}}.ball-clip-rotate-multiple{position:relative}.ball-clip-rotate-multiple>div{position:absolute;left:-20px;top:-20px;border:2px solid #fff;border-bottom-color:transparent;border-top-color:transparent;border-radius:100%;height:35px;width:35px;-webkit-animation:rotate 1s 0s ease-in-out infinite;animation:rotate 1s 0s ease-in-out infinite}.ball-clip-rotate-multiple>div:last-child{display:inline-block;top:-10px;left:-10px;width:15px;height:15px;-webkit-animation-duration:.5s;animation-duration:.5s;border-color:#fff transparent;-webkit-animation-direction:reverse;animation-direction:reverse}@-webkit-keyframes ball-scale-ripple{0%{-webkit-transform:scale(.1);transform:scale(.1);opacity:1}70%{-webkit-transform:scale(1);transform:scale(1);opacity:.7}100%{opacity:0}}@keyframes ball-scale-ripple{0%{-webkit-transform:scale(.1);transform:scale(.1);opacity:1}70%{-webkit-transform:scale(1);transform:scale(1);opacity:.7}100%{opacity:0}}.ball-scale-ripple>div{height:50px;width:50px;border-radius:100%;border:2px solid #fff;-webkit-animation:ball-scale-ripple 1s 0s infinite cubic-bezier(.21,.53,.56,.8);animation:ball-scale-ripple 1s 0s infinite cubic-bezier(.21,.53,.56,.8)}@-webkit-keyframes ball-scale-ripple-multiple{0%{-webkit-transform:scale(.1);transform:scale(.1);opacity:1}70%{-webkit-transform:scale(1);transform:scale(1);opacity:.7}100%{opacity:0}}@keyframes ball-scale-ripple-multiple{0%{-webkit-transform:scale(.1);transform:scale(.1);opacity:1}70%{-webkit-transform:scale(1);transform:scale(1);opacity:.7}100%{opacity:0}}.ball-scale-ripple-multiple{position:relative;-webkit-transform:translateY(-25px);transform:translateY(-25px)}.ball-scale-ripple-multiple>div:nth-child(0){-webkit-animation-delay:-.8s;animation-delay:-.8s}.ball-scale-ripple-multiple>div:nth-child(1){-webkit-animation-delay:-.6s;animation-delay:-.6s}.ball-scale-ripple-multiple>div:nth-child(2){-webkit-animation-delay:-.4s;animation-delay:-.4s}.ball-scale-ripple-multiple>div:nth-child(3){-webkit-animation-delay:-.2s;animation-delay:-.2s}.ball-scale-ripple-multiple>div{position:absolute;top:-2px;left:-26px;width:50px;height:50px;border-radius:100%;border:2px solid #fff;-webkit-animation:ball-scale-ripple-multiple 1.25s 0s infinite cubic-bezier(.21,.53,.56,.8);animation:ball-scale-ripple-multiple 1.25s 0s infinite cubic-bezier(.21,.53,.56,.8)}@-webkit-keyframes ball-beat{50%{opacity:.2;-webkit-transform:scale(.75);transform:scale(.75)}100%{opacity:1;-webkit-transform:scale(1);transform:scale(1)}}@keyframes ball-beat{50%{opacity:.2;-webkit-transform:scale(.75);transform:scale(.75)}100%{opacity:1;-webkit-transform:scale(1);transform:scale(1)}}.ball-beat>div{width:15px;height:15px;margin:2px;display:inline-block;-webkit-animation:ball-beat .7s 0s infinite linear;animation:ball-beat .7s 0s infinite linear}.ball-beat>div:nth-child(2n-1){-webkit-animation-delay:-.35s!important;animation-delay:-.35s!important}@-webkit-keyframes ball-scale-multiple{0%{-webkit-transform:scale(0);transform:scale(0);opacity:0}5%{opacity:1}100%{-webkit-transform:scale(1);transform:scale(1);opacity:0}}@keyframes ball-scale-multiple{0%{-webkit-transform:scale(0);transform:scale(0);opacity:0}5%{opacity:1}100%{-webkit-transform:scale(1);transform:scale(1);opacity:0}}.ball-scale-multiple{position:relative;-webkit-transform:translateY(-30px);transform:translateY(-30px)}.ball-scale-multiple>div:nth-child(2){-webkit-animation-delay:-.4s;animation-delay:-.4s}.ball-scale-multiple>div:nth-child(3){-webkit-animation-delay:-.2s;animation-delay:-.2s}.ball-scale-multiple>div{position:absolute;left:-30px;top:0;opacity:0;margin:0;width:60px;height:60px;-webkit-animation:ball-scale-multiple 1s 0s linear infinite;animation:ball-scale-multiple 1s 0s linear infinite}.ball-triangle-path>div:nth-child(1),.ball-triangle-path>div:nth-child(2){-webkit-animation-duration:2s;-webkit-animation-timing-function:ease-in-out;-webkit-animation-iteration-count:infinite}@-webkit-keyframes ball-triangle-path-1{33%{-webkit-transform:translate(25px,-50px);transform:translate(25px,-50px)}66%{-webkit-transform:translate(50px,0);transform:translate(50px,0)}100%{-webkit-transform:translate(0,0);transform:translate(0,0)}}@keyframes ball-triangle-path-1{33%{-webkit-transform:translate(25px,-50px);transform:translate(25px,-50px)}66%{-webkit-transform:translate(50px,0);transform:translate(50px,0)}100%{-webkit-transform:translate(0,0);transform:translate(0,0)}}@-webkit-keyframes ball-triangle-path-2{33%{-webkit-transform:translate(25px,50px);transform:translate(25px,50px)}66%{-webkit-transform:translate(-25px,50px);transform:translate(-25px,50px)}100%{-webkit-transform:translate(0,0);transform:translate(0,0)}}@keyframes ball-triangle-path-2{33%{-webkit-transform:translate(25px,50px);transform:translate(25px,50px)}66%{-webkit-transform:translate(-25px,50px);transform:translate(-25px,50px)}100%{-webkit-transform:translate(0,0);transform:translate(0,0)}}@-webkit-keyframes ball-triangle-path-3{33%{-webkit-transform:translate(-50px,0);transform:translate(-50px,0)}66%{-webkit-transform:translate(-25px,-50px);transform:translate(-25px,-50px)}100%{-webkit-transform:translate(0,0);transform:translate(0,0)}}@keyframes ball-triangle-path-3{33%{-webkit-transform:translate(-50px,0);transform:translate(-50px,0)}66%{-webkit-transform:translate(-25px,-50px);transform:translate(-25px,-50px)}100%{-webkit-transform:translate(0,0);transform:translate(0,0)}}.ball-triangle-path{position:relative;-webkit-transform:translate(-29.99px,-37.51px);transform:translate(-29.99px,-37.51px)}.ball-triangle-path>div:nth-child(1){-webkit-animation-name:ball-triangle-path-1;animation-name:ball-triangle-path-1;-webkit-animation-delay:0;animation-delay:0;animation-duration:2s;animation-timing-function:ease-in-out;animation-iteration-count:infinite}.ball-triangle-path>div:nth-child(2){-webkit-animation-name:ball-triangle-path-2;animation-name:ball-triangle-path-2;-webkit-animation-delay:0;animation-delay:0;animation-duration:2s;animation-timing-function:ease-in-out;animation-iteration-count:infinite}.ball-triangle-path>div:nth-child(3){-webkit-animation-name:ball-triangle-path-3;animation-name:ball-triangle-path-3;-webkit-animation-delay:0;animation-delay:0;-webkit-animation-duration:2s;animation-duration:2s;-webkit-animation-timing-function:ease-in-out;animation-timing-function:ease-in-out;-webkit-animation-iteration-count:infinite;animation-iteration-count:infinite}.ball-triangle-path>div{-webkit-animation-fill-mode:both;animation-fill-mode:both;position:absolute;width:10px;height:10px;border-radius:100%;border:1px solid #fff}.ball-grid-beat>div,.ball-pulse-rise>div{-webkit-animation-fill-mode:both;-webkit-animation-iteration-count:infinite}.ball-grid-beat>div,.ball-grid-pulse>div,.ball-pulse-rise>div{height:15px;border-radius:100%;display:inline-block;background-color:#fff;margin:2px}.ball-triangle-path>div:nth-of-type(1){top:50px}.ball-triangle-path>div:nth-of-type(2){left:25px}.ball-triangle-path>div:nth-of-type(3){top:50px;left:50px}@-webkit-keyframes ball-pulse-rise-even{0%{-webkit-transform:scale(1.1);transform:scale(1.1)}25%{-webkit-transform:translateY(-30px);transform:translateY(-30px)}50%{-webkit-transform:scale(.4);transform:scale(.4)}75%{-webkit-transform:translateY(30px);transform:translateY(30px)}100%{-webkit-transform:translateY(0);transform:translateY(0);-webkit-transform:scale(1);transform:scale(1)}}@keyframes ball-pulse-rise-even{0%{-webkit-transform:scale(1.1);transform:scale(1.1)}25%{-webkit-transform:translateY(-30px);transform:translateY(-30px)}50%{-webkit-transform:scale(.4);transform:scale(.4)}75%{-webkit-transform:translateY(30px);transform:translateY(30px)}100%{-webkit-transform:translateY(0);transform:translateY(0);-webkit-transform:scale(1);transform:scale(1)}}@-webkit-keyframes ball-pulse-rise-odd{0%{-webkit-transform:scale(.4);transform:scale(.4)}25%{-webkit-transform:translateY(30px);transform:translateY(30px)}50%{-webkit-transform:scale(1.1);transform:scale(1.1)}75%{-webkit-transform:translateY(-30px);transform:translateY(-30px)}100%{-webkit-transform:translateY(0);transform:translateY(0);-webkit-transform:scale(.75);transform:scale(.75)}}@keyframes ball-pulse-rise-odd{0%{-webkit-transform:scale(.4);transform:scale(.4)}25%{-webkit-transform:translateY(30px);transform:translateY(30px)}50%{-webkit-transform:scale(1.1);transform:scale(1.1)}75%{-webkit-transform:translateY(-30px);transform:translateY(-30px)}100%{-webkit-transform:translateY(0);transform:translateY(0);-webkit-transform:scale(.75);transform:scale(.75)}}.ball-pulse-rise>div{width:15px;animation-fill-mode:both;-webkit-animation-duration:1s;animation-duration:1s;-webkit-animation-timing-function:cubic-bezier(.15,.46,.9,.6);animation-timing-function:cubic-bezier(.15,.46,.9,.6);animation-iteration-count:infinite;-webkit-animation-delay:0;animation-delay:0}.ball-pulse-rise>div:nth-child(2n){-webkit-animation-name:ball-pulse-rise-even;animation-name:ball-pulse-rise-even}.ball-pulse-rise>div:nth-child(2n-1){-webkit-animation-name:ball-pulse-rise-odd;animation-name:ball-pulse-rise-odd}@-webkit-keyframes ball-grid-beat{50%{opacity:.7}100%{opacity:1}}@keyframes ball-grid-beat{50%{opacity:.7}100%{opacity:1}}.ball-grid-beat{width:57px}.ball-grid-beat>div:nth-child(1){-webkit-animation-delay:.15s;animation-delay:.15s;-webkit-animation-duration:1.45s;animation-duration:1.45s}.ball-grid-beat>div:nth-child(2){-webkit-animation-delay:-20ms;animation-delay:-20ms;-webkit-animation-duration:.97s;animation-duration:.97s}.ball-grid-beat>div:nth-child(3){-webkit-animation-delay:.66s;animation-delay:.66s;-webkit-animation-duration:1.23s;animation-duration:1.23s}.ball-grid-beat>div:nth-child(4){-webkit-animation-delay:.64s;animation-delay:.64s;-webkit-animation-duration:1.24s;animation-duration:1.24s}.ball-grid-beat>div:nth-child(5){-webkit-animation-delay:-.19s;animation-delay:-.19s;-webkit-animation-duration:1.13s;animation-duration:1.13s}.ball-grid-beat>div:nth-child(6){-webkit-animation-delay:.69s;animation-delay:.69s;-webkit-animation-duration:1.42s;animation-duration:1.42s}.ball-grid-beat>div:nth-child(7){-webkit-animation-delay:.58s;animation-delay:.58s;-webkit-animation-duration:1.14s;animation-duration:1.14s}.ball-grid-beat>div:nth-child(8){-webkit-animation-delay:.21s;animation-delay:.21s;-webkit-animation-duration:1.17s;animation-duration:1.17s}.ball-grid-beat>div:nth-child(9){-webkit-animation-delay:-.18s;animation-delay:-.18s;-webkit-animation-duration:.65s;animation-duration:.65s}.ball-grid-beat>div{width:15px;animation-fill-mode:both;float:left;-webkit-animation-name:ball-grid-beat;animation-name:ball-grid-beat;animation-iteration-count:infinite;-webkit-animation-delay:0;animation-delay:0}@-webkit-keyframes ball-grid-pulse{0%{-webkit-transform:scale(1);transform:scale(1)}50%{-webkit-transform:scale(.5);transform:scale(.5);opacity:.7}100%{-webkit-transform:scale(1);transform:scale(1);opacity:1}}@keyframes ball-grid-pulse{0%{-webkit-transform:scale(1);transform:scale(1)}50%{-webkit-transform:scale(.5);transform:scale(.5);opacity:.7}100%{-webkit-transform:scale(1);transform:scale(1);opacity:1}}.ball-grid-pulse{width:57px}.ball-grid-pulse>div:nth-child(1){-webkit-animation-delay:.22s;animation-delay:.22s;-webkit-animation-duration:.9s;animation-duration:.9s}.ball-grid-pulse>div:nth-child(2){-webkit-animation-delay:.64s;animation-delay:.64s;-webkit-animation-duration:1s;animation-duration:1s}.ball-grid-pulse>div:nth-child(3){-webkit-animation-delay:-.15s;animation-delay:-.15s;-webkit-animation-duration:.63s;animation-duration:.63s}.ball-grid-pulse>div:nth-child(4){-webkit-animation-delay:-30ms;animation-delay:-30ms;-webkit-animation-duration:1.24s;animation-duration:1.24s}.ball-grid-pulse>div:nth-child(5){-webkit-animation-delay:80ms;animation-delay:80ms;-webkit-animation-duration:1.37s;animation-duration:1.37s}.ball-grid-pulse>div:nth-child(6){-webkit-animation-delay:.43s;animation-delay:.43s;-webkit-animation-duration:1.55s;animation-duration:1.55s}.ball-grid-pulse>div:nth-child(7){-webkit-animation-delay:50ms;animation-delay:50ms;-webkit-animation-duration:.7s;animation-duration:.7s}.ball-grid-pulse>div:nth-child(8){-webkit-animation-delay:50ms;animation-delay:50ms;-webkit-animation-duration:.97s;animation-duration:.97s}.ball-grid-pulse>div:nth-child(9){-webkit-animation-delay:.3s;animation-delay:.3s;-webkit-animation-duration:.63s;animation-duration:.63s}.ball-grid-pulse>div{width:15px;-webkit-animation-fill-mode:both;animation-fill-mode:both;float:left;-webkit-animation-name:ball-grid-pulse;animation-name:ball-grid-pulse;-webkit-animation-iteration-count:infinite;animation-iteration-count:infinite;-webkit-animation-delay:0;animation-delay:0}@-webkit-keyframes ball-spin-fade-loader{50%{opacity:.3;-webkit-transform:scale(.4);transform:scale(.4)}100%{opacity:1;-webkit-transform:scale(1);transform:scale(1)}}@keyframes ball-spin-fade-loader{50%{opacity:.3;-webkit-transform:scale(.4);transform:scale(.4)}100%{opacity:1;-webkit-transform:scale(1);transform:scale(1)}}.ball-spin-fade-loader{position:relative;top:-10px;left:-10px}.ball-spin-fade-loader>div:nth-child(1){top:25px;left:0;-webkit-animation:ball-spin-fade-loader 1s -.96s infinite linear;animation:ball-spin-fade-loader 1s -.96s infinite linear}.ball-spin-fade-loader>div:nth-child(2){top:17.05px;left:17.05px;-webkit-animation:ball-spin-fade-loader 1s -.84s infinite linear;animation:ball-spin-fade-loader 1s -.84s infinite linear}.ball-spin-fade-loader>div:nth-child(3){top:0;left:25px;-webkit-animation:ball-spin-fade-loader 1s -.72s infinite linear;animation:ball-spin-fade-loader 1s -.72s infinite linear}.ball-spin-fade-loader>div:nth-child(4){top:-17.05px;left:17.05px;-webkit-animation:ball-spin-fade-loader 1s -.6s infinite linear;animation:ball-spin-fade-loader 1s -.6s infinite linear}.ball-spin-fade-loader>div:nth-child(5){top:-25px;left:0;-webkit-animation:ball-spin-fade-loader 1s -.48s infinite linear;animation:ball-spin-fade-loader 1s -.48s infinite linear}.ball-spin-fade-loader>div:nth-child(6){top:-17.05px;left:-17.05px;-webkit-animation:ball-spin-fade-loader 1s -.36s infinite linear;animation:ball-spin-fade-loader 1s -.36s infinite linear}.ball-spin-fade-loader>div:nth-child(7){top:0;left:-25px;-webkit-animation:ball-spin-fade-loader 1s -.24s infinite linear;animation:ball-spin-fade-loader 1s -.24s infinite linear}.ball-spin-fade-loader>div:nth-child(8){top:17.05px;left:-17.05px;-webkit-animation:ball-spin-fade-loader 1s -.12s infinite linear;animation:ball-spin-fade-loader 1s -.12s infinite linear}.ball-spin-fade-loader>div,.ball-spin-loader>div{-webkit-animation-fill-mode:both;position:absolute;width:15px;height:15px;border-radius:100%}.ball-spin-fade-loader>div{background-color:#fff;margin:2px;animation-fill-mode:both}@-webkit-keyframes ball-spin-loader{75%{opacity:.2}100%{opacity:1}}@keyframes ball-spin-loader{75%{opacity:.2}100%{opacity:1}}.ball-spin-loader{position:relative}.ball-spin-loader>span:nth-child(1){top:45px;left:0;-webkit-animation:ball-spin-loader 2s .9s infinite linear;animation:ball-spin-loader 2s .9s infinite linear}.ball-spin-loader>span:nth-child(2){top:30.68px;left:30.68px;-webkit-animation:ball-spin-loader 2s 1.8s infinite linear;animation:ball-spin-loader 2s 1.8s infinite linear}.ball-spin-loader>span:nth-child(3){top:0;left:45px;-webkit-animation:ball-spin-loader 2s 2.7s infinite linear;animation:ball-spin-loader 2s 2.7s infinite linear}.ball-spin-loader>span:nth-child(4){top:-30.68px;left:30.68px;-webkit-animation:ball-spin-loader 2s 3.6s infinite linear;animation:ball-spin-loader 2s 3.6s infinite linear}.ball-spin-loader>span:nth-child(5){top:-45px;left:0;-webkit-animation:ball-spin-loader 2s 4.5s infinite linear;animation:ball-spin-loader 2s 4.5s infinite linear}.ball-spin-loader>span:nth-child(6){top:-30.68px;left:-30.68px;-webkit-animation:ball-spin-loader 2s 5.4s infinite linear;animation:ball-spin-loader 2s 5.4s infinite linear}.ball-spin-loader>span:nth-child(7){top:0;left:-45px;-webkit-animation:ball-spin-loader 2s 6.3s infinite linear;animation:ball-spin-loader 2s 6.3s infinite linear}.ball-spin-loader>span:nth-child(8){top:30.68px;left:-30.68px;-webkit-animation:ball-spin-loader 2s 7.2s infinite linear;animation:ball-spin-loader 2s 7.2s infinite linear}.ball-spin-loader>div{animation-fill-mode:both;background:green}.ball-zig-zag-deflect>div,.ball-zig-zag>div{background-color:#fff;width:15px;height:15px;border-radius:100%;margin:2px 2px 2px 15px;top:4px;left:-7px}@-webkit-keyframes ball-zig{33%{-webkit-transform:translate(-15px,-30px);transform:translate(-15px,-30px)}66%{-webkit-transform:translate(15px,-30px);transform:translate(15px,-30px)}100%{-webkit-transform:translate(0,0);transform:translate(0,0)}}@keyframes ball-zig{33%{-webkit-transform:translate(-15px,-30px);transform:translate(-15px,-30px)}66%{-webkit-transform:translate(15px,-30px);transform:translate(15px,-30px)}100%{-webkit-transform:translate(0,0);transform:translate(0,0)}}@-webkit-keyframes ball-zag{33%{-webkit-transform:translate(15px,30px);transform:translate(15px,30px)}66%{-webkit-transform:translate(-15px,30px);transform:translate(-15px,30px)}100%{-webkit-transform:translate(0,0);transform:translate(0,0)}}@keyframes ball-zag{33%{-webkit-transform:translate(15px,30px);transform:translate(15px,30px)}66%{-webkit-transform:translate(-15px,30px);transform:translate(-15px,30px)}100%{-webkit-transform:translate(0,0);transform:translate(0,0)}}.ball-zig-zag{position:relative;-webkit-transform:translate(-15px,-15px);transform:translate(-15px,-15px)}.ball-zig-zag>div{-webkit-animation-fill-mode:both;animation-fill-mode:both;position:absolute}.ball-zig-zag>div:first-child{-webkit-animation:ball-zig .7s 0s infinite linear;animation:ball-zig .7s 0s infinite linear}.ball-zig-zag>div:last-child{-webkit-animation:ball-zag .7s 0s infinite linear;animation:ball-zag .7s 0s infinite linear}@-webkit-keyframes ball-zig-deflect{17%,84%{-webkit-transform:translate(-15px,-30px);transform:translate(-15px,-30px)}34%,67%{-webkit-transform:translate(15px,-30px);transform:translate(15px,-30px)}100%,50%{-webkit-transform:translate(0,0);transform:translate(0,0)}}@keyframes ball-zig-deflect{17%,84%{-webkit-transform:translate(-15px,-30px);transform:translate(-15px,-30px)}34%,67%{-webkit-transform:translate(15px,-30px);transform:translate(15px,-30px)}100%,50%{-webkit-transform:translate(0,0);transform:translate(0,0)}}@-webkit-keyframes ball-zag-deflect{17%,84%{-webkit-transform:translate(15px,30px);transform:translate(15px,30px)}34%,67%{-webkit-transform:translate(-15px,30px);transform:translate(-15px,30px)}100%,50%{-webkit-transform:translate(0,0);transform:translate(0,0)}}@keyframes ball-zag-deflect{17%,84%{-webkit-transform:translate(15px,30px);transform:translate(15px,30px)}34%,67%{-webkit-transform:translate(-15px,30px);transform:translate(-15px,30px)}100%,50%{-webkit-transform:translate(0,0);transform:translate(0,0)}}.ball-zig-zag-deflect{position:relative;-webkit-transform:translate(-15px,-15px);transform:translate(-15px,-15px)}.ball-zig-zag-deflect>div{-webkit-animation-fill-mode:both;animation-fill-mode:both;position:absolute}.line-scale-party>div,.line-scale-pulse-out-rapid>div,.line-scale-pulse-out>div,.line-scale>div{width:4px;height:35px;display:inline-block}.line-scale-party>div,.line-scale-pulse-out-rapid>div,.line-scale-pulse-out>div,.line-scale>div,.line-spin-fade-loader>div{border-radius:2px;margin:2px;background-color:#fff}.ball-zig-zag-deflect>div:first-child{-webkit-animation:ball-zig-deflect 1.5s 0s infinite linear;animation:ball-zig-deflect 1.5s 0s infinite linear}.ball-zig-zag-deflect>div:last-child{-webkit-animation:ball-zag-deflect 1.5s 0s infinite linear;animation:ball-zag-deflect 1.5s 0s infinite linear}@-webkit-keyframes line-scale{0%,100%{-webkit-transform:scaley(1);transform:scaley(1)}50%{-webkit-transform:scaley(.4);transform:scaley(.4)}}@keyframes line-scale{0%,100%{-webkit-transform:scaley(1);transform:scaley(1)}50%{-webkit-transform:scaley(.4);transform:scaley(.4)}}.line-scale>div:nth-child(1){-webkit-animation:line-scale 1s -.4s infinite cubic-bezier(.2,.68,.18,1.08);animation:line-scale 1s -.4s infinite cubic-bezier(.2,.68,.18,1.08)}.line-scale>div:nth-child(2){-webkit-animation:line-scale 1s -.3s infinite cubic-bezier(.2,.68,.18,1.08);animation:line-scale 1s -.3s infinite cubic-bezier(.2,.68,.18,1.08)}.line-scale>div:nth-child(3){-webkit-animation:line-scale 1s -.2s infinite cubic-bezier(.2,.68,.18,1.08);animation:line-scale 1s -.2s infinite cubic-bezier(.2,.68,.18,1.08)}.line-scale>div:nth-child(4){-webkit-animation:line-scale 1s -.1s infinite cubic-bezier(.2,.68,.18,1.08);animation:line-scale 1s -.1s infinite cubic-bezier(.2,.68,.18,1.08)}.line-scale>div:nth-child(5){-webkit-animation:line-scale 1s 0s infinite cubic-bezier(.2,.68,.18,1.08);animation:line-scale 1s 0s infinite cubic-bezier(.2,.68,.18,1.08)}.line-scale>div{-webkit-animation-fill-mode:both;animation-fill-mode:both}@-webkit-keyframes line-scale-party{0%,100%{-webkit-transform:scale(1);transform:scale(1)}50%{-webkit-transform:scale(.5);transform:scale(.5)}}@keyframes line-scale-party{0%,100%{-webkit-transform:scale(1);transform:scale(1)}50%{-webkit-transform:scale(.5);transform:scale(.5)}}.line-scale-party>div:nth-child(1){-webkit-animation-delay:.48s;animation-delay:.48s;-webkit-animation-duration:.54s;animation-duration:.54s}.line-scale-party>div:nth-child(2){-webkit-animation-delay:-.15s;animation-delay:-.15s;-webkit-animation-duration:1.15s;animation-duration:1.15s}.line-scale-party>div:nth-child(3){-webkit-animation-delay:40ms;animation-delay:40ms;-webkit-animation-duration:.77s;animation-duration:.77s}.line-scale-party>div:nth-child(4){-webkit-animation-delay:-.12s;animation-delay:-.12s;-webkit-animation-duration:.61s;animation-duration:.61s}.line-scale-party>div{-webkit-animation-fill-mode:both;animation-fill-mode:both;-webkit-animation-name:line-scale-party;animation-name:line-scale-party;-webkit-animation-iteration-count:infinite;animation-iteration-count:infinite;-webkit-animation-delay:0;animation-delay:0}@-webkit-keyframes line-scale-pulse-out{0%,100%{-webkit-transform:scaley(1);transform:scaley(1)}50%{-webkit-transform:scaley(.4);transform:scaley(.4)}}@keyframes line-scale-pulse-out{0%,100%{-webkit-transform:scaley(1);transform:scaley(1)}50%{-webkit-transform:scaley(.4);transform:scaley(.4)}}.line-scale-pulse-out>div{-webkit-animation:line-scale-pulse-out .9s -.6s infinite cubic-bezier(.85,.25,.37,.85);animation:line-scale-pulse-out .9s -.6s infinite cubic-bezier(.85,.25,.37,.85)}.line-scale-pulse-out>div:nth-child(2),.line-scale-pulse-out>div:nth-child(4){-webkit-animation-delay:-.4s!important;animation-delay:-.4s!important}.line-scale-pulse-out>div:nth-child(1),.line-scale-pulse-out>div:nth-child(5){-webkit-animation-delay:-.2s!important;animation-delay:-.2s!important}@-webkit-keyframes line-scale-pulse-out-rapid{0%,90%{-webkit-transform:scaley(1);transform:scaley(1)}80%{-webkit-transform:scaley(.3);transform:scaley(.3)}}@keyframes line-scale-pulse-out-rapid{0%,90%{-webkit-transform:scaley(1);transform:scaley(1)}80%{-webkit-transform:scaley(.3);transform:scaley(.3)}}.line-scale-pulse-out-rapid>div{vertical-align:middle;-webkit-animation:line-scale-pulse-out-rapid .9s -.5s infinite cubic-bezier(.11,.49,.38,.78);animation:line-scale-pulse-out-rapid .9s -.5s infinite cubic-bezier(.11,.49,.38,.78)}.line-scale-pulse-out-rapid>div:nth-child(2),.line-scale-pulse-out-rapid>div:nth-child(4){-webkit-animation-delay:-.25s!important;animation-delay:-.25s!important}.line-scale-pulse-out-rapid>div:nth-child(1),.line-scale-pulse-out-rapid>div:nth-child(5){-webkit-animation-delay:0s!important;animation-delay:0s!important}@-webkit-keyframes line-spin-fade-loader{50%{opacity:.3}100%{opacity:1}}@keyframes line-spin-fade-loader{50%{opacity:.3}100%{opacity:1}}.line-spin-fade-loader{position:relative;top:-10px;left:-4px}.line-spin-fade-loader>div:nth-child(1){top:20px;left:0;-webkit-animation:line-spin-fade-loader 1.2s -.84s infinite ease-in-out;animation:line-spin-fade-loader 1.2s -.84s infinite ease-in-out}.line-spin-fade-loader>div:nth-child(2){top:13.64px;left:13.64px;-webkit-transform:rotate(-45deg);transform:rotate(-45deg);-webkit-animation:line-spin-fade-loader 1.2s -.72s infinite ease-in-out;animation:line-spin-fade-loader 1.2s -.72s infinite ease-in-out}.line-spin-fade-loader>div:nth-child(3){top:0;left:20px;-webkit-transform:rotate(90deg);transform:rotate(90deg);-webkit-animation:line-spin-fade-loader 1.2s -.6s infinite ease-in-out;animation:line-spin-fade-loader 1.2s -.6s infinite ease-in-out}.line-spin-fade-loader>div:nth-child(4){top:-13.64px;left:13.64px;-webkit-transform:rotate(45deg);transform:rotate(45deg);-webkit-animation:line-spin-fade-loader 1.2s -.48s infinite ease-in-out;animation:line-spin-fade-loader 1.2s -.48s infinite ease-in-out}.line-spin-fade-loader>div:nth-child(5){top:-20px;left:0;-webkit-animation:line-spin-fade-loader 1.2s -.36s infinite ease-in-out;animation:line-spin-fade-loader 1.2s -.36s infinite ease-in-out}.line-spin-fade-loader>div:nth-child(6){top:-13.64px;left:-13.64px;-webkit-transform:rotate(-45deg);transform:rotate(-45deg);-webkit-animation:line-spin-fade-loader 1.2s -.24s infinite ease-in-out;animation:line-spin-fade-loader 1.2s -.24s infinite ease-in-out}.line-spin-fade-loader>div:nth-child(7){top:0;left:-20px;-webkit-transform:rotate(90deg);transform:rotate(90deg);-webkit-animation:line-spin-fade-loader 1.2s -.12s infinite ease-in-out;animation:line-spin-fade-loader 1.2s -.12s infinite ease-in-out}.line-spin-fade-loader>div:nth-child(8){top:13.64px;left:-13.64px;-webkit-transform:rotate(45deg);transform:rotate(45deg);-webkit-animation:line-spin-fade-loader 1.2s 0s infinite ease-in-out;animation:line-spin-fade-loader 1.2s 0s infinite ease-in-out}.line-spin-fade-loader>div{-webkit-animation-fill-mode:both;animation-fill-mode:both;position:absolute;width:5px;height:15px}@-webkit-keyframes triangle-skew-spin{25%{-webkit-transform:perspective(100px) rotateX(180deg) rotateY(0);transform:perspective(100px) rotateX(180deg) rotateY(0)}50%{-webkit-transform:perspective(100px) rotateX(180deg) rotateY(180deg);transform:perspective(100px) rotateX(180deg) rotateY(180deg)}75%{-webkit-transform:perspective(100px) rotateX(0) rotateY(180deg);transform:perspective(100px) rotateX(0) rotateY(180deg)}100%{-webkit-transform:perspective(100px) rotateX(0) rotateY(0);transform:perspective(100px) rotateX(0) rotateY(0)}}@keyframes triangle-skew-spin{25%{-webkit-transform:perspective(100px) rotateX(180deg) rotateY(0);transform:perspective(100px) rotateX(180deg) rotateY(0)}50%{-webkit-transform:perspective(100px) rotateX(180deg) rotateY(180deg);transform:perspective(100px) rotateX(180deg) rotateY(180deg)}75%{-webkit-transform:perspective(100px) rotateX(0) rotateY(180deg);transform:perspective(100px) rotateX(0) rotateY(180deg)}100%{-webkit-transform:perspective(100px) rotateX(0) rotateY(0);transform:perspective(100px) rotateX(0) rotateY(0)}}.triangle-skew-spin>div{width:0;height:0;border-left:20px solid transparent;border-right:20px solid transparent;border-bottom:20px solid #fff;-webkit-animation:triangle-skew-spin 3s 0s cubic-bezier(.09,.57,.49,.9) infinite;animation:triangle-skew-spin 3s 0s cubic-bezier(.09,.57,.49,.9) infinite}@-webkit-keyframes square-spin{25%{-webkit-transform:perspective(100px) rotateX(180deg) rotateY(0);transform:perspective(100px) rotateX(180deg) rotateY(0)}50%{-webkit-transform:perspective(100px) rotateX(180deg) rotateY(180deg);transform:perspective(100px) rotateX(180deg) rotateY(180deg)}75%{-webkit-transform:perspective(100px) rotateX(0) rotateY(180deg);transform:perspective(100px) rotateX(0) rotateY(180deg)}100%{-webkit-transform:perspective(100px) rotateX(0) rotateY(0);transform:perspective(100px) rotateX(0) rotateY(0)}}@keyframes square-spin{25%{-webkit-transform:perspective(100px) rotateX(180deg) rotateY(0);transform:perspective(100px) rotateX(180deg) rotateY(0)}50%{-webkit-transform:perspective(100px) rotateX(180deg) rotateY(180deg);transform:perspective(100px) rotateX(180deg) rotateY(180deg)}75%{-webkit-transform:perspective(100px) rotateX(0) rotateY(180deg);transform:perspective(100px) rotateX(0) rotateY(180deg)}100%{-webkit-transform:perspective(100px) rotateX(0) rotateY(0);transform:perspective(100px) rotateX(0) rotateY(0)}}.square-spin>div{width:50px;height:50px;background:#fff;-webkit-animation:square-spin 3s 0s cubic-bezier(.09,.57,.49,.9) infinite;animation:square-spin 3s 0s cubic-bezier(.09,.57,.49,.9) infinite}.pacman>div:first-of-type,.pacman>div:nth-child(2){width:0;height:0;border-right:25px solid transparent;border-top:25px solid #fff;border-left:25px solid #fff;border-bottom:25px solid #fff;border-radius:25px;position:relative;left:-30px}@-webkit-keyframes rotate_pacman_half_up{0%,100%{-webkit-transform:rotate(270deg);transform:rotate(270deg)}50%{-webkit-transform:rotate(360deg);transform:rotate(360deg)}}@keyframes rotate_pacman_half_up{0%,100%{-webkit-transform:rotate(270deg);transform:rotate(270deg)}50%{-webkit-transform:rotate(360deg);transform:rotate(360deg)}}@-webkit-keyframes rotate_pacman_half_down{0%,100%{-webkit-transform:rotate(90deg);transform:rotate(90deg)}50%{-webkit-transform:rotate(0);transform:rotate(0)}}@keyframes rotate_pacman_half_down{0%,100%{-webkit-transform:rotate(90deg);transform:rotate(90deg)}50%{-webkit-transform:rotate(0);transform:rotate(0)}}@-webkit-keyframes pacman-balls{75%{opacity:.7}100%{-webkit-transform:translate(-100px,-6.25px);transform:translate(-100px,-6.25px)}}@keyframes pacman-balls{75%{opacity:.7}100%{-webkit-transform:translate(-100px,-6.25px);transform:translate(-100px,-6.25px)}}.pacman{position:relative}.pacman>div:nth-child(3){-webkit-animation:pacman-balls 1s -.66s infinite linear;animation:pacman-balls 1s -.66s infinite linear}.pacman>div:nth-child(4){-webkit-animation:pacman-balls 1s -.33s infinite linear;animation:pacman-balls 1s -.33s infinite linear}.pacman>div:nth-child(5){-webkit-animation:pacman-balls 1s 0s infinite linear;animation:pacman-balls 1s 0s infinite linear}.pacman>div:first-of-type{-webkit-animation:rotate_pacman_half_up .5s 0s infinite;animation:rotate_pacman_half_up .5s 0s infinite}.pacman>div:nth-child(2){-webkit-animation:rotate_pacman_half_down .5s 0s infinite;animation:rotate_pacman_half_down .5s 0s infinite;margin-top:-50px}.pacman>div:nth-child(3),.pacman>div:nth-child(4),.pacman>div:nth-child(5),.pacman>div:nth-child(6){background-color:#fff;border-radius:100%;margin:2px;width:10px;height:10px;position:absolute;-webkit-transform:translate(0,-6.25px);transform:translate(0,-6.25px);top:25px;left:70px}@-webkit-keyframes cube-transition{25%{-webkit-transform:translateX(50px) scale(.5) rotate(-90deg);transform:translateX(50px) scale(.5) rotate(-90deg)}50%{-webkit-transform:translate(50px,50px) rotate(-180deg);transform:translate(50px,50px) rotate(-180deg)}75%{-webkit-transform:translateY(50px) scale(.5) rotate(-270deg);transform:translateY(50px) scale(.5) rotate(-270deg)}100%{-webkit-transform:rotate(-360deg);transform:rotate(-360deg)}}@keyframes cube-transition{25%{-webkit-transform:translateX(50px) scale(.5) rotate(-90deg);transform:translateX(50px) scale(.5) rotate(-90deg)}50%{-webkit-transform:translate(50px,50px) rotate(-180deg);transform:translate(50px,50px) rotate(-180deg)}75%{-webkit-transform:translateY(50px) scale(.5) rotate(-270deg);transform:translateY(50px) scale(.5) rotate(-270deg)}100%{-webkit-transform:rotate(-360deg);transform:rotate(-360deg)}}.cube-transition{position:relative;-webkit-transform:translate(-25px,-25px);transform:translate(-25px,-25px)}.cube-transition>div{width:10px;height:10px;position:absolute;top:-5px;left:-5px;background-color:#fff;-webkit-animation:cube-transition 1.6s 0s infinite ease-in-out;animation:cube-transition 1.6s 0s infinite ease-in-out}.cube-transition>div:last-child{-webkit-animation-delay:-.8s;animation-delay:-.8s}@-webkit-keyframes spin-rotate{0%{-webkit-transform:rotate(0);transform:rotate(0)}50%{-webkit-transform:rotate(180deg);transform:rotate(180deg)}100%{-webkit-transform:rotate(360deg);transform:rotate(360deg)}}@keyframes spin-rotate{0%{-webkit-transform:rotate(0);transform:rotate(0)}50%{-webkit-transform:rotate(180deg);transform:rotate(180deg)}100%{-webkit-transform:rotate(360deg);transform:rotate(360deg)}}.semi-circle-spin{position:relative;width:35px;height:35px;overflow:hidden}.semi-circle-spin>div{position:absolute;border-width:0;border-radius:100%;-webkit-animation:spin-rotate .6s 0s infinite linear;animation:spin-rotate .6s 0s infinite linear;background-image:linear-gradient(transparent 0,transparent 70%,#fff 30%,#fff 100%);width:100%;height:100%}

</style>
