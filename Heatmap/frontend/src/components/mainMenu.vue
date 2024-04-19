<!-- App / deckglCanvas / mainMenu -->
<template>
  <div>
     <!-- Background div for buttons with styled background and shadow -->
    <div class="buttons_background">
      <!-- Iterates over the 'options' array and creates a button for each option -->
      <div
        @click="setActiveOption(option.id)"
        class="option_button"
        :class="{ option_button_active: activeOptionId === option.id }"
        v-for="option in options"
        :key="option.id"
        :id="option.id"
      >

        <!-- Dynamically loads an icon for the button based on the option id -->
        <img class="option_icon" :src="require(`@/assets/${option.id}.svg`)" />
        <!-- Tooltip that shows description on hover -->
        <b-tooltip :target="option.id" :delay="tooltipDelay">{{option.description}}</b-tooltip>
      </div>
    </div>

    <!-- Expand/Collapse the button-area for that button
      - showing settings based on the active option -->
    <b-collapse
      v-for="option in options"
      :key="option.id"
      :visible="activeOptionId === option.id"
    >

      <!-- Settings menu displayed when the 'deckglSettings' option is active -->
      <settingsMenu
        v-if="option.id === 'deckglSettings'"
        @settings-changed="$emit('settings-changed', $event)"
        :settings="settings"
        :settingsTemplate="settingsTemplate"
        :minMaxValues="minMaxValues"
      />

      <!-- Export menu displayed when the 'exportImage' option is active -->
      <exportMenu
        v-else-if="option.id === 'exportImage'"
        :layerSettings="layerSettings"
        :colorGradientDict="colorGradientDict"
        @take-screenshot="$emit('take-screenshot')"
      />
    </b-collapse>
  </div>
</template>

<script>
import axios from 'axios'; // HTTP requests to backend
import settingsMenu from './settingsMenu.vue'; // General settings
import exportMenu from './exportMenu.vue'; // Export settings

export default {
  components: {
    settingsMenu,
    exportMenu,
  },
  props: {
    settings: Object,
    settingsTemplate: Object,
    layerSettings: Object,
    colorGradientDict: Object,
    minMaxValues: Array,
    hashValue: String,
    currentViewState: Object,
    activeCamera: String,
  },
  data() {
    return {
      // Array of options for available buttons
      options: [
        {
          id: 'goHome',
          label: 'Home',
          description: 'Jump to default view.',
        },
        {
          id: 'deckglSettings',
          label: 'Settings',
          description: 'Change colors, scaling, etc.',
        },
        {
          id: 'exportImage',
          label: 'Export Image',
          description: 'Download SVG/PNG picture.',
        },
      ],
      activeOptionId: 'deckglSettings', // Keeps track of the currently active option
      // The default button when the HM is initially loaded
      homeCamera: {
        id: 'Top',
        viewState: {
          pitch: 0,
          bearing: -90,
          latitude: 0.02,
          longitude: 0.05,
          zoom: 11,
        },
        layerSettings: {
          gridCellLayer: {
            elevationScale: 0,
            extruded: false,
          },
        },
      },
      tooltipDelay: { show: 600, hide: 0 }, // Delay for tooltips to appear and disappear
    };
  },
  methods: {
    // Method to set the active option, toggles the active state if the same button is clicked
    setActiveOption(id) {
      // Check if the saveUserSettings button is clicked.
      if (id === 'saveUserSettings') {
        this.saveUserSettings(); // Call saveUserSettings and do not change activeOptionId.
        return; // Return early so no other logic affects the activeOptionId.
      }
      if (this.activeOptionId !== id) {
        this.activeOptionId = id;
        if (id === 'goHome') {
          this.goHome();
        }
      } else {
        this.activeOptionId = null;
      }
    },
    goHome() {
      // Method to emit an event to reset the camera to the default view
      this.$emit('active-camera-selected', this.homeCamera);
      this.activeOptionId = null;
    },
    saveUserSettings() {
      // ind gradients = T/F
      // this.settings.gradient.individualGradients

      // Settings to save to json
      this.userSettings = {
        hash: this.hashValue,
        visual: {
          plot_gap: this.settings.layer.cellSize,
          plot_3d: this.settings.layer.extruded, // (true/false)
          plot_elevation: this.settings.layer.elevationScale,
          plot_opacity: this.settings.layer.opacity,
        },
        colour_grad: {
          individual_grad: this.settings.gradient.individualGradients, // (true/false)
          the_individual_grad: this.settings.gradient.gradientPreset,
          the_combined_grads: this.settings.gradient,
        },
        adv_settings: {
          tooltip: this.settings.layer.pickable,
        },
        lighting: {
          adv_lighting: this.settings.lighting.advancedLighting,
          amb_light: this.settings.lighting.ambientLight,
          dir_light1: this.settings.lighting.directionalLight1,
          dir_light2: this.settings.lighting.directionalLight2,
        },
        material: {
          shader: this.settings.layer.material,
          adv_material: this.settings.layer.advancedMaterial,
          ambient: this.settings.layer.ambientMaterial,
          diffusion: this.settings.layer.diffuseMaterial,
          shininess: this.settings.layer.shininess,
        },
        camera_view: {
          currentViewState: this.currentViewState,
          activeCamera: this.activeCamera,
        },
      };

      // console.log('THIS.', this);
      console.log('this.settings.layer.cellSize: ', this.settings.layer.cellSize);
      console.log('this.userSettings.visual.plot_gap: ', this.userSettings.visual.plot_gap);
      console.log('hash', this.hashValue);

      // console.log('Camera Details:', this.homeCamera);
      // This is added as active camera settings are not accessable when its called earlier
      // if (this.homeCamera) {
      //   this.userSettings.plot_camera = this.homeCamera;
      // }
      // this.$emit('update-individual-gradients', true);
      console.log('Saving settings to server...');
      this.saveSettingsToServer(); // call save

      this.$bvToast.toast('This is primarly useful when sharing the session URL with other users and you would like them to see your customised heatmap. ', {
        title: 'The current settings have been saved',
        variant: 'Primary',
        solid: true,
        toaster: 'b-toaster-top-right',
        autoHideDelay: 5000,
        html: true,
      });
    },
    saveSettingsToServer() {
      // Store the DB id and the user settings to send
      const dbEntryId = this.$route.query.config;
      const payload = {
        dbEntryId,
        settings: this.userSettings,
      };
      // send the payload to the backend
      axios.post('http://127.0.0.1:3000/save-settings', payload)
        .then((response) => {
          console.log('%cSettings saved', 'color: green;', response.data);
        })
        .catch((error) => {
          console.error('Error saving settings:', error);
        });
    },
  },
};
</script>

<style scoped>
.option_button {
  padding: 10px 16px 10px 16px;
  background-color: #fff;
  border-radius: 5px;
  grid-area: 1 / auto / 2 / auto;
  cursor: pointer;
  transition: background-color 200ms ease-out;
}
label {
  font-size: 14px;
  grid-area: 2 / auto / auto / auto;
}
.buttons_background {
  position: relative;
  z-index: 1100;
  grid-area: 1 / 1 / 2 / 7;
  background-color: #fff;
  box-shadow: 3px 6px 16px #0000001c;
  border-radius: 5px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  width: fit-content;
  margin-bottom: 5px;
}
.option_button_active {
  background-color: #1c1c29 !important;
  border-radius: 5px;
}
.option_button_active > img {
  filter: saturate(0) brightness(1.8);
}
.option_button > img {
  transition: transform 350ms cubic-bezier(0.36, 1.59, 0.66, 1);
}
.option_button:hover > img {
  transform: scale(1.3);
}
</style>
