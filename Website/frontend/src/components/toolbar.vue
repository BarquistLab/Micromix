<template>
  <div>
    <div class="toast-center">
      <b-toast
        id="lock-toast"
        title="Session saved!"
        static
        no-auto-hide
      >This URL is now locked and cannot be modified.</b-toast>
    </div>
    <b-button-toolbar class="toolbar">
      <b-button-group
        class="mr-1"
        id="toolbar_group"
      >
        <b-popover id="tutorial_popover" :no-fade="true" triggers="" placement="top" target="toolbar_group" title="Save and download">Click the Lock button to save this session indefinitely. You can then share the URL to friends or in publications. A locked session is still interactive but any modification will generate a new URL and leave the locked session untouched. Click the download icon to download an Excel or CSV file.</b-popover>
        <b-button
          :disabled="disabled_lock"
          title="Save session"
          :variant="button_lock"
          @click="lock_session"
        >
          <b-icon :icon="icon_lock" aria-hidden="false"></b-icon>
        </b-button>
        <b-dropdown
          class="dropdown-export"
          title="Download excel or csv"
          variant="light"
          toggle-class="text-decoration-none"
          no-caret
          boundary="viewport"
          offset="0"
        >
          <template v-slot:button-content>
            <b-icon icon="cloud-download" aria-hidden="true"></b-icon>
          </template>
          <b-dropdown-form>
            <div class="test">
              <h4 class="dropdown-export-link-title">
                <b-icon-link45deg variant="dark"></b-icon-link45deg>
              </h4>
              <span class="dropdown-export-title">Share link</span>
              <b-form-group class="dropdown-export-link-field">
                <b-form-input
                  class="dropdown-url-field input-fake-disabled"
                  :value="this.url"
                  id="dropdown-url-field-input"
                  tabindex="-1"
                ></b-form-input>
                <span @click="url_to_clipboard()" class="btn-link pseudo-link">Copy Link</span>
              </b-form-group>
            </div>
          </b-dropdown-form>
          <b-dropdown-divider></b-dropdown-divider>
          <b-dropdown-item class="pseudo-link" @click="download_df('excel')">
            <img src="../assets/excel_logo.svg" class="export_menu_icon" />
            <span class="dropdown-export-title"> Download .xls</span>
          </b-dropdown-item>
          <b-dropdown-divider></b-dropdown-divider>
          <b-dropdown-item class="pseudo-link" @click="download_df('csv')">
            <b-icon-table variant="dark"></b-icon-table>
            <span class="dropdown-export-title"> Download .csv</span>
          </b-dropdown-item>
          <b-dropdown-form>
            <b-form-group
              class="dropdown-export-link-field"
              label-cols-sm="4"
              label-align-sm="left"
              label=" CSV Seperator:"
              label-for="dropdown-csv-sep"
            >
              <b-form-input
                id="dropdown-csv-sep"
                class="dropdown-url-field"
                size="sm"
                type="text"
                maxlength="1"
                v-model="export_form.csv_seperator"
              ></b-form-input>
            </b-form-group>
          </b-dropdown-form>
        </b-dropdown>
        <b-button title="New document" variant="light" @click="new_session">
          <b-icon icon="file-earmark" aria-hidden="true"></b-icon>
        </b-button>
        <b-button title="Help" :variant="tutorial_button_variant" @click="toggle_tutorial">
          <b-icon icon="question-circle" aria-hidden="true"></b-icon>
        </b-button>
      </b-button-group>
    </b-button-toolbar>
  </div>
</template>

<script>
import axios from "axios";
export default {
  props: {
    locked: Boolean,
    backend_url: String
  },
  data() {
    return {
      icon_lock: "unlock",
      button_lock: "light",
      disabled_lock: true,
      tutorial_activated: false,
      tutorial_button_variant: "light",
      url: null,
      export_form: {
        file_type: null,
        csv_seperator: ","
      }
    };
  },
  created() {
    this.url = window.location.href;
    if (this.locked == true) {
      this.disabled_lock = true;
      this.button_lock = "dark";
      this.icon_lock = "lock";
    } else if (this.locked == false) {
      this.disabled_lock = false;
    }
    // Always closes tutorial popovers. This is only for bulletproofing and is probably not necessary. PERFORMANCE.
    this.$root.$emit('bv::hide::popover', 'tutorial_popover')
  },
  watch: {
    // PERFORMANCE
    // This doesn't need to be watched and could be handled by the "toggle_tutorial()" method and could be integrated there.
    // Watching it, however, makes sure the tutorial is only shown when it's var is set to true, not just when the toolbar button is clicked.
    tutorial_activated: function() {
      if (this.tutorial_activated === true) {
        this.tutorial_button_variant = 'secondary'
        this.$root.$emit('bv::show::popover', 'tutorial_popover')
      } else if (this.tutorial_activated === false) {
        this.tutorial_button_variant = 'light'
        this.$root.$emit('bv::hide::popover', 'tutorial_popover')
      }
    }
  },
  methods: {
    new_session() {
      this.$router.push({ path: "" });
    },
    lock_session() {
      this.disabled_lock = true;
      const path = `${this.backend_url}/locked`;
      var payload = new FormData();
      payload.append("url", JSON.stringify(this.$route.query.config));
      axios.post(path, payload).then(res => {
        if (res.data.error_type) {
          this.$emit("error_occured", res.data);
        } else {
          this.button_lock = "dark";
          this.icon_lock = "lock";
          this.$bvToast.show("lock-toast");
        }
      });
    },
    toggle_tutorial() {
      this.tutorial_activated = !this.tutorial_activated;
    },
    url_to_clipboard() {
      var url_field = document.getElementById("dropdown-url-field-input");
      url_field.select();
      url_field.setSelectionRange(0, 99999);
      document.execCommand("copy");
      this.lock_session();
    },
    download_df(file_type) {
      this.export_form.file_type = file_type;
      var payload = new FormData();
      payload.append("url", JSON.stringify(this.$route.query.config));
      payload.append("export_form", JSON.stringify(this.export_form));
      axios({
        url: `${this.backend_url}/export`,
        method: "POST",
        responseType: "blob",
        data: payload
      }).then(res => {
        if (res.data.error_type) {
          this.$emit("error_occured", res.data);
        } else {
          const url = window.URL.createObjectURL(new Blob([res.data]));
          const link = document.createElement("a");
          link.href = url;
          if (file_type == "excel") {
            link.setAttribute("download", "dataframes.xlsx");
          } else if (file_type == "csv") {
            link.setAttribute("download", "dataframe.csv");
          }
          document.body.appendChild(link);
          link.click();
        }
      });
    }
  }
};
</script>

<style scoped>
svg {
  margin: 0;
}
.btn-group {
  margin: 0 0 0 auto !important;
}
.toast-center {
  position: absolute;
  width: 100vw;
  text-align: center;
}
.b-toast {
  position: relative;
  display: inline-block;
}
.export_menu_icon {
  width: 18px;
}
.dropdown-menu.show > * {
  font-size: small;
}
.dropdown-link-field {
  border-radius: 0.5rem;
  /* width: -webkit-fill-available; */
  padding: 0.5rem;
  border: 1px solid #d6d8db;
  background-color: #e9ecef;
}
.test {
  width: 300px;
}
.dropdown-url-field {
  background-color: #e9ecef;
  font-size: small;
}
.dropdown-export-link-title {
  display: inline;
  margin: 0 0 10px 0;
  vertical-align: sub;
}
.dropdown-export-link-field {
  margin-bottom: 0 !important;
  color: #6c757d;
}
#dropdown-csv-sep {
  width: 30px;
}
.dropdown-export-title {
  font-weight: 500;
}
.pseudo-link {
  cursor: pointer;
}
.input-fake-disabled {
  pointer-events: none;
}
.toolbar {
  padding-right: 2rem;
}
</style>
