<!-- App / deckglCanvas -->
<template>
  <div>
     <!-- Container for SVG exports -->
     <div id="export_svg"></div>
    
    <!-- Main Menu Component: Controls and settings -->
    <mainMenu
      v-if="layerSettings.gridCellLayer.data"
      class="main_menu menu_c"
      @settings-changed="updateSettings"
      @take-screenshot="takeScreenshot"
      @active-camera-selected="changeCamera"
      :settings="settings"
      :settingsTemplate="settingsTemplate"
      :layerSettings="layerSettings"
      :colorGradientDict="colorGradientDict"
      :minMaxValues="[this.lowestValue, this.highestValue]"
    />
    
    
    <!-- Camera Menu Component: Controls for changing camera views -->
    <cameraMenu
      class="camera_menu menu_c"
      :activeCamera="activeCamera"
      :elevationScale="layerSettings.gridCellLayer.elevationScale"
      @active-camera-selected="changeCamera"
    />

    <!-- Container for the Deck.gl canvas -->
    <div class="deck-container" id="deck-container">
      <canvas id="deck-canvas" ref="canvas"></canvas>
    </div>
  </div>
</template>



<script>
// settingsTemplate - stores all the initial settigns from the json
// settings - stores the actual settings


// Importing necessary modules from Deck.gl and other libraries
import {
  Deck,
  LightingEffect,
  AmbientLight,
  DirectionalLight,
} from '@deck.gl/core';

import { GridCellLayer, TextLayer } from '@deck.gl/layers';
import axios from 'axios'; //For HTTP requests
import chroma from 'chroma-js';  // For color manipulation
import cameraMenu from './cameraMenu.vue';  // Custom Vue component for camera menu
import mainMenu from './mainMenu.vue';  // Custom Vue component for main settings menu
import settingsTemplate from '../assets/settingsTemplate.json';  // Load in the template for initial settings


export default {
  components: {
    cameraMenu,
    mainMenu,
  },
  data() {
    return {
      // Initial data properties including URL, camera settings, layer configurations, etc.
      backendUrl: 'http://127.0.0.1:3000',  //this will need to be changed to where Micromix is hosted
      activeCamera: 'Top',
      constants: {
        textMarginRight: -0.003,
        textMarginTop: 0.5 / 140,
      },
      updateTriggerObjects: {
        gradientUpdateTrigger: false,
        elevationScale: 200,
      },
      colorGradientPreset: null,
      highestValue: null,
      lowestValue: null,
      colorGradientDict: {},
      colorGradient: null,
      advancedLighting: false,
      subTables: {},
      layerSettings: {
        gridCellLayer: {
          id: 'grid-gridCellLayerCell-layer',
          data: null,
          getPosition: (d) => d.COORDINATES,
          getElevation: (d) => d.VALUE,
          getFillColor: (d) => this.colorGradientDict[d.TITLE](d.VALUE).rgb(),
        },
        textCellLayer: {
          id: 'text-cell-layer',
          data: null,
          sizeUnits: 'meters',
          getPosition: (d) => d.COORDINATES,
          getText: (d) => d.VALUE,
          // PERFORMANCE: Scale text based on the strings length
          getSize: (d) => 1575 / (String(d.VALUE).length + 2.5),
          getAngle: 90,
          getTextAnchor: 'middle',
          getAlignmentBaseline: 'center',
          billboard: false,
          fontFamily:
            '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Oxygen, Ubuntu, Cantarell, Open Sans, Helvetica Neue, sans-serif',
          fontWeight: 'bold',
        },
        rowTextLayer: {
          id: 'row-text-layer',
          data: null,
          sizeUnits: 'meters',
          getPosition: (d) => d.COORDINATES,
          getText: (d) => d.VALUE,
          getSize: 450,
          getAngle: 90,
          getTextAnchor: 'end',
          getAlignmentBaseline: 'center',
          billboard: false,
          fontFamily:
            '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Oxygen, Ubuntu, Cantarell, Open Sans, Helvetica Neue, sans-serif',
        },
        columnTextLayer: {
          id: 'column-text-layer',
          data: null,
          sizeUnits: 'meters',
          getPosition: (d) => d.COORDINATES,
          getText: (d) => d.VALUE,
          getSize: 450,
          getAngle: 180,
          getTextAnchor: 'start',
          getAlignmentBaseline: 'center',
          billboard: false,
          fontFamily:
            '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Oxygen, Ubuntu, Cantarell, Open Sans, Helvetica Neue, sans-serif',
        },
      },

      //These are the default view settings for the heatmap.
      //If you want to change from Top to something else, you will also have to change values in settingsTemplate.json - for example line 26 for the 3d view enabled/disabled
      currentViewState: {
        latitude: 0.02,
        longitude: 0.05,
        zoom: 11,
        minZoom: 4,
        pitch: 0,
        maxPitch: 89,
        bearing: -90,
      },
      settingsTemplate,
      settings: null,
    };
  },


  // --------
  // Fetches initial configuration data and sets up the deck instance
  // --------
  created() {
    //Get the config data
    this.fetchData(`${this.backendUrl}/config`);
    this.deck = null;
    //Load in the settings from the json template
    this.settings = this.generateSettings();
  },

   // --------
   // Initializes the Deck.gl instance on component mount
   // --------
   mounted() {
    this.deck = new Deck({
      // Disable Retina rendering for better performance:
      // useDevicePixels: false,
      canvas: this.$refs.canvas,
      viewState: this.currentViewState,
      getTooltip: this.getTooltip,
      onViewStateChange: ({ viewState }) => {
        this.currentViewState = viewState;
        this.deck.setProps({ viewState: this.currentViewState });
      },
      controller: true,
    });
    // this.deck.layerManager.layers[0].props.elevationScale = 10
  },

  methods: {

     // --------
     // Allows users to take a screenshot of the current heatmap
     // --------
    takeScreenshot() {
      this.deck.redraw(true);
      const { canvas } = this.deck;
      document.getElementById('deck-container').appendChild(canvas);
      const a = document.createElement('a');
      // toDataURL defaults to png, so we need to request a jpeg, then convert for file download.
      a.href = canvas.toDataURL('image/png', 1.0).replace('image/png', 'image/octet-stream');
      a.download = 'Heatmap_screenshot.png';
      // We can use .jpeg and control the quality - otherwise have to re-size the image with pixels
      // a.href = canvas.toDataURL('image/jpeg', 0.1);
      // a.download = 'Heatmap_screenshot.jpeg';
      a.click();
    },

    // --------
    // Generates initial settings based on the settings template
    // --------
    // *
    // Generates initial settings for the heatmap based on a predefined template thats loaded from the json.
    // This function constructs a settings object that includes configurations for different aspects
    // of the visualization, such as layer properties, lighting effects, custom features, and gradient controls.
    // *
    // Process:
    // 1. Initialize an empty settings object with categories for layers, lighting, custom settings, and gradients.
    // 2. Iterate through each category in the provided settingsTemplate (json).
    // 3. For each category, iterate through the settings defined in the template.
    // 4. Each setting can have multiple inputs; iterate through these inputs to extract and assign their default values.
    // 5. Populate the settings object with these default values, categorizing them according to their specified property type.
    // *
    // The settings object structured by this function serves as the foundational configuration
    // from which the visualization's properties can be adjusted dynamically via user interactions or other controls.
    // *
    // Returns:
    // - A fully populated settings object with initial values as specified in the settings template.
    generateSettings() {

      // Initialize the settings object with empty categories.
      const settings = {
        layer: {},
        lighting: {},
        custom: {},
        gradient: {},
      };

      // Loop over each category (mode) in the settings template.
      Object.keys(settingsTemplate).forEach((mode) => {
        // Iterate through the array of settings in each category.
        for (let i = 0; i < settingsTemplate[mode].settings.length; i += 1) {
          // Iterate through each input field in the current setting.
          for (let j = 0; j < settingsTemplate[mode].settings[i].inputs.length; j += 1) {
            // Reference to the current input.
            const input = settingsTemplate[mode].settings[i].inputs[j];

            // Assign the default value from the input to the appropriate category in the settings object.
            settings[input.propertyType][input.id] = input.value;
          }
        }
      });
       // Return the fully populated settings object
       return settings;
    },

    // --------
    // Handles camera view changes
    // --------
    changeCamera(e) {
      this.activeCamera = e.id;
      this.currentViewState = { ...this.currentViewState, ...e.viewState };
      this.deck.setProps({ viewState: this.currentViewState });
      this.layerSettings.gridCellLayer = {
        ...this.layerSettings.gridCellLayer,
        ...e.layerSettings.gridCellLayer,
      };
      // this.deck.setProps({ layers: [new GridCellLayer(this.layerSettings.gridCellLayer),
      // new rowTextLayer(this.layerSettings.rowTextLayer)] })
      this.settings.layer = {
        ...this.settings.layer,
        ...e.layerSettings.gridCellLayer,
      };
    },

    // --------
    // Updates heatmap settings based on user interaction
    // --------
    // *
    // Updates the settings of the visualization based on user interactions or programmatically.
    // This method handles various types of updates categorized by 'type', such as layer settings,
    // gradient settings, and lighting settings. Each type of setting modification triggers
    // corresponding updates to the Deck.gl layers or effects used in the visualization.
    //
    // Parameters:
    // - updatedSettings: An object containing the type of update and the new settings values.
    //
    // Workflow:
    // 1. Distinguish the type of settings update from the 'updatedSettings' object.
    // 2. Based on the type, apply specific changes to the visualization's properties.
    // 3. Use switch-case structure to handle different types of updates effectively.
    // 4. Emit an event after the settings update is complete to signal that the potentially
    //    long-loading process has finished.
    // *
    // Supported update types:
    // - 'layer': Updates properties related to Deck.gl layers like elevation scale and materials.
    // - 'gradient': Adjusts the color gradient used in visualizing data.
    // - 'lighting': Configures lighting effects for the visualization
    //
    updateSettings(updatedSettings) {
      // Simplify access to the new settings.
      const s = updatedSettings.settings;

      // It might be useful to use a switch case instead,
      // if the possible conditions grow beyond 5 items.

      // Use a switch statement to handle different types of settings based on 'updatedSettings.type'.
      switch (updatedSettings.type) {

        // --- layer ---
        case 'layer':
          // Merge existing layer settings with new ones and ensure numerical properties are correctly typed.
          this.layerSettings.gridCellLayer = {
            ...this.layerSettings.gridCellLayer,
            ...s,
          };
          // Ensure number type due to possible string inputs.
          // This is necessary because bootstrap converts the property to a string.
          this.layerSettings.gridCellLayer.elevationScale = Number(s.elevationScale);
          this.updateTriggerObjects.elevationScale = this
            .layerSettings.gridCellLayer.elevationScale;
          
          // Optionally update materials for advanced visualization effects if specified.
          if (s.advancedMaterial) {
            this.layerSettings.gridCellLayer.material = {
              ambient: Number(s.ambientMaterial),
              diffuse: Number(s.diffuseMaterial),
              shininess: Number(s.shininess),
            };
          }
          if (this.lowestValue < 0) {
            // Set update triggers for Deck.gl layers to respond to changes in settings.
            this.layerSettings.gridCellLayer.updateTriggers = {
              getFillColor: [this.updateTriggerObjects.gradientUpdateTrigger],
              getPosition: this.updateTriggerObjects.elevationScale,
            };
          } else {
            this.layerSettings.gridCellLayer.updateTriggers = {
              getFillColor: [
                this.updateTriggerObjects.gradientUpdateTrigger,
              ],
            };
          }

          // Reconfigure the layers with the new settings.
          this.deck.setProps({
            layers: [
              new GridCellLayer(this.layerSettings.gridCellLayer),
              new TextLayer(this.layerSettings.textCellLayer),
              new TextLayer(this.layerSettings.rowTextLayer),
              new TextLayer(this.layerSettings.columnTextLayer),
            ],
          });
          break;

        // --- gradient ---  
        case 'gradient':
          // Toggle gradient update trigger to force re-rendering of layers.
          this.updateTriggerObjects.gradientUpdateTrigger = !this.updateTriggerObjects.gradientUpdateTrigger;

           // Update gradient settings for visual consistency across data visualization
          this.colorGradientPreset = s.gradientPreset.value;
          if (this.colorGradientPreset !== s.gradientPreset.value
          || s.individualGradients === false) {
            Object.keys(this.subTables).forEach((subTableTitle) => {
              this.colorGradientDict[subTableTitle] = chroma
                .scale(this.colorGradientPreset)
                .domain(s.gradientPreset.domain);
            });
          } else {
            Object.keys(this.subTables).forEach((subTableTitle) => {
              this.colorGradientDict[subTableTitle] = chroma
                .scale(s[subTableTitle].value)
                .domain(s[subTableTitle].domain);
            });
          }
          if (this.lowestValue < 0) {
            this.layerSettings.gridCellLayer.updateTriggers = {
              getFillColor: [
                this.updateTriggerObjects.gradientUpdateTrigger,
              ],
              getPosition: this.updateTriggerObjects.elevationScale,
            };
          } else {
            this.layerSettings.gridCellLayer.updateTriggers = {
              getFillColor: [
                this.updateTriggerObjects.gradientUpdateTrigger,
              ],
            };
          }
          // Reapply updated gradient settings to the Deck.gl layers.
          this.deck.setProps({
            layers: [
              new GridCellLayer(this.layerSettings.gridCellLayer),
              new TextLayer(this.layerSettings.textCellLayer),
              new TextLayer(this.layerSettings.rowTextLayer),
              new TextLayer(this.layerSettings.columnTextLayer),
            ],
          });
          break;

        // --- lighting ---
        case 'lighting':
          // Conditionally create new lighting effects based on user settings.
          if (s.advancedLighting === true) {
          // Only build new lights when advanced light is activated.
          // Probably not necessary but I speculate on performance advantages with this approach.
            const ambient = new AmbientLight({
              color: [255, 255, 255],
              intensity: s.ambientLight,
            });
            const directionalLight1 = new DirectionalLight({
              color: [255, 255, 255],
              direction: [this.highestValue / 2, 5, 3000],
              intensity: s.directionalLight1,
            });
            const directionalLight2 = new DirectionalLight({
              color: [255, 255, 255],
              position: [this.highestValue / 4, 0.1, 1000],
              intensity: s.directionalLight2,
            });
            this.deck.setProps({
              effects: [
                new LightingEffect({
                  ambient,
                  directionalLight1,
                  directionalLight2,
                }),
              ],
            });
          } else {
            // Remove effects if advanced lighting is turned off.
            this.deck.setProps({ effects: [] });
          }
          break;
        default:
          // Log a warning if an unsupported update type is encountered.
          console.log('Warning: No case found for this setting update.');
      }
      // Notify the rest of the application that settings update is complete.
      this.$emit('long-loading-finished');
    },

    // ---------
    // Fetches data for the heatmap visualization
    // ---------
    fetchData(url) {
      // Fetches processed data from a backend server for visualization in a heatmap.
      // This function sends a request to the specified URL, which is expected to
      // interact with a MongoDB database to retrieve and process the required data
      // based on the provided configuration settings.
      // The response data is then further processed in the frontend to fit
      // the structure required by Deck.gl layers, such as grid cells and text
      // ayers for row and column headers. It also handles setting up visualization
      // parameters like min-max values and gradients based on the processed data.
      // *
      // Workflow:
      // 1. Send a HTTP POST request with configuration data to the backend.
      // 2. Backend processes this request, queries MongoDB, and formats the necessary data.
      // 3. Received data is processed in the frontend to be used in heatmap layers.
      // 4. Data is used to update the visualization, applying layer-based settings like colors and scales.

      // Create a new FormData object to hold the data to be sent with the HTTP POST request
      const payload = new FormData();
      // Append the 'url' key with the serialized configuration query parameter to the payload.
      // This configuration 'might' determine specific data filters or identifiers for the backend to process.
      payload.append('url', JSON.stringify(this.$route.query.config));

      // Send a POST request to the Micromix URL with the prepared payload.
      // Axios is used here to handle the HTTP request.
      axios.post(url, payload)
        .then((res) => {
           // Upon successful data retrieval, 'res.data' contains the returned data.

           // Process the received data to format suitable for the heatmap layers using 'processJsonData'.
           // This method organizes raw data into structured formats for different layers of the heatmap.
           [
            this.layerSettings.gridCellLayer.data,
            this.layerSettings.textCellLayer.data,
            this.layerSettings.rowTextLayer.data,
            this.layerSettings.columnTextLayer.data,
            this.highestValue,
            this.lowestValue,
          ] = this.processJsonData(res.data);

          // Once the data is processed, set up the gradient forms for subtables.
          // This may involve creating specific color gradient settings for each subtable based on the processed data.
          this.createSubTableGradientForms();

          // If the lowest value in the data is below zero, additional configuration may be necessary,
          // such as adjusting visualization parameters to properly display negative values.
          if (this.lowestValue < 0) {
            this.configureNegativeValues();
          }
        })
        .catch((error) => {
          // Log any errors that occur during the fetch or processing steps.
          console.log(error);
        });
    },

    // --------
    //
    // Processes JSON data into a format suitable for Deck.gl layers
    //
    // --------
    processJsonData(json) {
      // NOTE: This could be moved to the python backend for performace reasons.
      // Details:
      // The processJsonData function primarily focuses on transforming and structuring JSON data for visualization in Deck.gl layers, 
      // such as grid cells and text annotations (headers). It doesn't involve the application settings related to visual aspects like 
      // color gradients, camera views, materials, or specific settings for min/max gradient values. 
      const gridCellLayerData = [];
      const textCellLayerData = [];
      const rowTextLayerData = [];
      const columnTextLayerData = [];

      // Extract column names from the first JSON object.
      const columns = Object.keys(json[0]);

      // Initialize variables to track the extremes of data values across all tables and subtables.
      let lowestValue = 0;
      let highestValue = 0;
      let subTableLowestValue = 0;
      let subTableHighestValue = 0;
      let lastPrefix; // Track prefix to manage subtables

      // Variables to manage column coordinates in the visualization.
      let columnName;
      let columnCoordinate = -1;
      let scaledColumnCoordinate = 0;

      // Loop through each column index to process column-wise data.
      for (let columnIndex = 0; columnIndex < columns.length; columnIndex += 1) {
        // Skip the first column in processing, assuming it's a special case (like identifiers).
        if (columnIndex !== 0) {
          // Check if column name starts and contains specific delimiters to identify subtables.
          if (columns[columnIndex].startsWith('(') && columns[columnIndex].includes(') ')) {
            const splitIndex = columns[columnIndex].indexOf(') ');
            const prefix = columns[columnIndex].slice(0, splitIndex + 1);

            // When encountering a new prefix, reset subtable-specific trackers and adjust coordinates.
            if (prefix !== lastPrefix) {
              lastPrefix = prefix;
              subTableLowestValue = 0;
              subTableHighestValue = 0;
              columnCoordinate += 1.4; // Adjust coordinate for a new subtable grouping
              columnName = columns[columnIndex].slice(splitIndex + 2);
            } else {
              columnCoordinate += 1; // Continue in the same subtable
            }
          } else {
            columnName = columns[columnIndex];
            columnCoordinate += 1;
          }

          // Calculate a scaled coordinate for placement in the visualization.
          // Only calculate x coordinate when the column changes.
          scaledColumnCoordinate = columnCoordinate / 140;

           // Store column names with their calculated display coordinates.
          columnTextLayerData.push({
            COORDINATES: [
              -this.constants.textMarginTop,
              scaledColumnCoordinate - this.constants.textMarginRight,
            ],
            VALUE: Object.keys(json[0])[columnIndex],
          });
        }

        // Process each row within the current column.
        for (let rowIndex = 0; rowIndex < json.length; rowIndex += 1) {
          // Check if the cell contains a finite number (ignoring non-numeric data).
          if (columnIndex !== 0) {
            if (Number.isFinite(json[rowIndex][columns[columnIndex]])) {

              // Create data entry for grid cell layer.
              const gridCellLayerCell = {
                COLUMN: columnName,
                COORDINATES: [rowIndex / 140, scaledColumnCoordinate],
                ROW: json[rowIndex][columns[0]],
                VALUE: json[rowIndex][columns[columnIndex]],
                TITLE: lastPrefix,
              };

              // Update subtable and overall data value ranges.
              if (gridCellLayerCell.VALUE > subTableHighestValue) {
                subTableHighestValue = gridCellLayerCell.VALUE;
                if (gridCellLayerCell.VALUE > highestValue) {
                  highestValue = gridCellLayerCell.VALUE;
                }
              }
              if (gridCellLayerCell.VALUE < subTableLowestValue) {
                subTableLowestValue = gridCellLayerCell.VALUE;
                if (gridCellLayerCell.VALUE < lowestValue) {
                  lowestValue = gridCellLayerCell.VALUE;
                }
              }
              // Handle negative values by setting orientation flag.
              if (gridCellLayerCell.VALUE < 0) {
                gridCellLayerCell.VALUE *= -1;  // Make value positive
                gridCellLayerCell.ORIENTATION = -1;  // Flag negative orientation
              }
              gridCellLayerData.push(gridCellLayerCell);
            } else {
              // Create data entry for non-numeric cell data.
              const textCellLayerCell = {
                COLUMN: columnName,
                COORDINATES: [
                  rowIndex / 140 + this.constants.textMarginTop,
                  scaledColumnCoordinate + this.constants.textMarginTop,
                ],
                ROW: json[rowIndex][columns[0]],
                VALUE: json[rowIndex][columns[columnIndex]],
              };
              textCellLayerData.push(textCellLayerCell);
            }
          } else {
            // Process the first column separately (likely for row headers or similar).
            rowTextLayerData.push({
              COORDINATES: [
                rowIndex / 140 + this.constants.textMarginTop,
                scaledColumnCoordinate,
              ],
              VALUE: json[rowIndex][columns[columnIndex]],
            });
          }
        }

        // After processing all rows for a column, update subtable tracking.
        if (lastPrefix) {
          this.subTables[lastPrefix] = {
            TITLE: lastPrefix,
            LOWEST_VALUE: subTableLowestValue,
            HIGHEST_VALUE: subTableHighestValue,
          };
        }
      }

      // Return all processed data and extreme values for further use.
      return [
        gridCellLayerData,
        textCellLayerData,
        rowTextLayerData,
        columnTextLayerData,
        highestValue,
        lowestValue,
      ];
    },

    // --------
    // Adjusts settings for handling negative values in data
    // --------
    configureNegativeValues() {
      this.layerSettings.gridCellLayer.getPosition = (d) => [d.COORDINATES[0],
        d.COORDINATES[1], d.VALUE * (this.updateTriggerObjects.elevationScale * d.ORIENTATION)];
      this.layerSettings.gridCellLayer.getFillColor = (d) => ((!d.ORIENTATION)
        ? this.colorGradientDict[d.TITLE](d.VALUE).rgb()
        : this.colorGradientDict[d.TITLE](d.VALUE * d.ORIENTATION).rgb());
    },

    // --------
    // Dynamically creates gradient settings forms based on data
    // --------
    createSubTableGradientForms() {
      for (let i = 0; i < this.settingsTemplate.basicSettings.settings.length; i += 1) {
        if (this.settingsTemplate.basicSettings.settings[i].label === 'Color Gradient') {
          for (
            let j = 0; j < this.settingsTemplate.basicSettings.settings[i].inputs.length; j += 1
          ) {
            if (this.settingsTemplate.basicSettings.settings[i].inputs[j].id === 'gradientPreset') {
              Object.keys(this.subTables).forEach((subTableTitle) => {
                // We need to DEEP clone this template object.
                // The only way to remove reactivity seems to parse it as an JSON object.
                // This is questionable but right now the least bad way to clone it.
                let gradientFormTemplate = JSON.parse(JSON.stringify(
                  this.settingsTemplate.basicSettings.settings[i].inputs[j],
                ));
                gradientFormTemplate.label = subTableTitle;
                gradientFormTemplate.id = gradientFormTemplate.label;
                gradientFormTemplate.condition = true;
                gradientFormTemplate = this.calculateGradientDomain(
                  gradientFormTemplate,
                  this.subTables[subTableTitle].LOWEST_VALUE,
                  this.subTables[subTableTitle].HIGHEST_VALUE,
                );
                this.settings.gradient[gradientFormTemplate.id] = gradientFormTemplate.value;
                this.settingsTemplate.basicSettings.settings[i].inputs.push(gradientFormTemplate);
              });
              this.settingsTemplate.basicSettings.settings[i].inputs[j] = this
                .calculateGradientDomain(
                  settingsTemplate.basicSettings.settings[i].inputs[j],
                  this.lowestValue,
                  this.highestValue,
                );
              break;
            }
          }
          break;
        }
      }
    },

    // --------
    // Calculates gradient domain for color scaling
    // --------
    calculateGradientDomain(form, lowestValue, highestValue) {
      // Calculate order of magnitude of the value range between data min and max.
      const gradientFormTemplate = form;
      gradientFormTemplate.min = lowestValue;
      gradientFormTemplate.max = highestValue;
      gradientFormTemplate.orderOfMagnitude = Math
        .floor(Math.log10(Math.abs(highestValue - lowestValue)));
      gradientFormTemplate.interval = 10 ** (gradientFormTemplate.orderOfMagnitude - 3);
      if (gradientFormTemplate.interval > 1) {
        gradientFormTemplate.interval = 1; // Cap interval at 1 to avoid division errors
      }
      // The following uses EPSILON to round to n decimal places, where n is
      // determined by the Order of Magnitude of the range between min and max
      // This means that the mid points of data with ranges such as 0.0001 will be
      // differently rounded than ranges like 10000. This isn't completely crucial,
      // but improves UX by determining the gradient slider interval and the overall
      // length and precision of the mid point number.
      gradientFormTemplate.mid = Math.round(
        ((highestValue
          - lowestValue) / 2
          + lowestValue) * 10 ** (-gradientFormTemplate.orderOfMagnitude + 3)
          + Number.EPSILON,
      ) / 10 ** (-gradientFormTemplate.orderOfMagnitude + 3);
      gradientFormTemplate.value.domain = [
        lowestValue,
        gradientFormTemplate.mid,
        highestValue,
      ];
      return gradientFormTemplate;
    },

    // --------
    // Generates tooltip content for grid cells
    // --------
     getTooltip({ object }) {
      if (!object) {
        return null;
      }
      const column = object.COLUMN;
      const row = object.ROW;
      let count;
      if (!object.ORIENTATION) {
        count = object.VALUE;
      } else {
        count = object.VALUE * object.ORIENTATION;
      }
      return {
        html: `\
        ${column}<br>
        ${row}<br>
        <strong>${count}</strong>`,
        // Below is an example for custom CSS styling for the tooltip.
        // style: {
        //   backgroundColor: '#000',
        //   margin: '0'
        // }
      };
      // Below is an example for a more advanced tooltip format according to: https://github.com/visgl/deck.gl/blob/8.3-release/examples/website/3d-heatmap/app.js
      // const lat = object.COORDINATES[1]
      // const lng = object.COORDINATES[0]
      // return `\
      //   latitude: ${Number.isFinite(lat) ? lat.toFixed(6) : ''}
      //   longitude: ${Number.isFinite(lng) ? lng.toFixed(6) : ''}
      //   ${count} Accidents`
    },
  },
};
</script>

<style scoped>
.deck-container {
  width: 100vw;
  height: 100vh;
  position: relative;
}
#deckgl-overlay {
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
}

.camera_menu {
  top: 10px;
  right: 10px;
}

.main_menu {
  top: 10px;
  left: 10px;
}
.menu_c {
  position: absolute;
  z-index: 1000;
}
#export_svg {
  display: none;
}
</style>
