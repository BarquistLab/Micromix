<!-- App / deckglCanvas -->
<!--
  This is the main script for the heatmap where the majority of processing and rendering occurs

  Breif description of the other scripts:
  cameraMenu:       The camera menu (top right)
  exportMenu:       When the heatmap is exported as an image
  loadingOverlay:   Loading screen When the heatmap is waiting for a request
  mainMenu:         The main menu top lefthand side - storing info about each of the buttons
  settingsMenu:     All the details and processing around heatmap settings, ie gradients etc
-->
<template>
  <div>
    <!-- Container for SVG exports
    <div id="export_svg"></div> -->

    <!-- Main Menu Component: Controls and settings -->
    <mainMenu v-if="layerSettings.gridCellLayer.data"
      class="main_menu menu_c"
      @settings-changed="updateSettings"
      @take-screenshot="takeScreenshot"
      @active-camera-selected="changeCamera"
      :settings="settings"
      :settingsTemplate="settingsTemplate"
      :layerSettings="layerSettings"
      :colorGradientDict="colorGradientDict"
      :minMaxValues="[this.lowestValue, this.highestValue]"
      :hashValue="hashValue"
      :currentViewState="currentViewState"
      :activeCamera="activeCamera"
      :legendData="legendData"
      />

    <!-- Camera Menu Component: Controls for changing camera views -->
    <cameraMenu class="camera_menu menu_c" :activeCamera="activeCamera"
      :elevationScale="layerSettings.gridCellLayer.elevationScale"
      @active-camera-selected="changeCamera" />

    <!-- Container for the Deck.gl canvas -->
    <div class="deck-container" id="deck-container">
      <canvas id="deck-canvas" ref="canvas"></canvas>
    </div>
  </div>
</template>

<script>
// settingsTemplate - stores all the initial settigns from the json
// settings - stores the actual settings
// Importing necessary modules from Deck.gl
import {
  Deck,
  LightingEffect,
  AmbientLight,
  DirectionalLight,
} from '@deck.gl/core';
// Import other libaries
import {
  GridCellLayer,
  TextLayer,
  LineLayer,
  PolygonLayer,
} from '@deck.gl/layers';
// import { PolygonLayer } from '@deck.gl/layers';
import axios from 'axios'; // For HTTP requests
import chroma from 'chroma-js'; // For color manipulation
import CryptoJS from 'crypto-js'; // Import CryptoJS
import cameraMenu from './cameraMenu.vue'; // Custom Vue component for camera menu
import mainMenu from './mainMenu.vue'; // Custom Vue component for main settings menu
import settingsTemplate from '../assets/settingsTemplate.json'; // Load in the template for initial settings

export default {
  components: {
    cameraMenu,
    mainMenu,
  },
  data() {
    return {
      // Initial data properties including URL, camera settings, layer configurations, etc.
      backendUrl: 'http://127.0.0.1:3000', // this will need to be changed to where Micromix is hosted
      polygonLayer: null, // Store the PolygonLayer instance
      rectangleText: [],

      // to send data for save as svg
      legendData: [],
      // set the hash value
      hashValue: null,
      // active camera
      activeCamera: 'Top',
      constants: {
        textMarginRight: -0.003,
        textMarginTop: 0.5 / 140,
      },
      updateTriggerObjects: {
        gradientUpdateTrigger: false,
        elevationScale: 200,
      },
      colorGradientPreset: 'RdYlGn', // the default colour gradient,
      highestValue: null,
      lowestValue: null,
      colorGradientDict: {},
      colorGradient: null,
      advancedLighting: false,
      subTables: {},
      // Settings for all the drawn layers
      layerSettings: {
        gridCellLayer: {
          id: 'grid-gridCellLayerCell-layer',
          data: null,
          getPosition: (d) => d.COORDINATES,
          getElevation: (d) => d.VALUE,
          // getFillColor: (d) => this.colorGradientDict[d.TITLE](d.VALUE).rgb(),
          // getFillColor: (d) => [...this.colorGradientDict[d.TITLE](d.VALUE).rgb(), 255],
          getFillColor: (d) => {
            console.log('d.TITLE:', d.TITLE);
            console.log('Available keys in colorGradientDict:', Object.keys(this.colorGradientDict));

            const colorFunction = this.colorGradientDict[d.TITLE];

            if (typeof colorFunction === 'function') {
              return [...colorFunction(d.VALUE).rgb(), 255];
            } else {
              console.warn(`No color function found for TITLE: ${d.TITLE}`);
              return [255, 255, 255, 255]; // Fallback color (white)
            }
          },
        },
        // heatmap text?
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
        // heatmap row text
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
        // heatmap column text
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
        // Array to hold multiple gradient layers
        rectangleGradientLayers: [],
        // text for the legend
        rectangleTextLayer: {
          id: 'legend-text',
          data: [], // Initialize with empty array; populate dynamically later
          getPosition: (d) => d.position,
          getText: (d) => d.text,
          sizeUnits: 'meters', // to ensure text sizes with zoom
          getSize: 550, // Adjust font size as needed
          getColor: [0, 0, 0, 255], // Black color
          getTextAnchor: 'middle',
          getAlignmentBaseline: 'bottom',
          fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Oxygen, Ubuntu, Cantarell, Open Sans, Helvetica Neue, sans-serif',
          fontWeight: 'normal', // Set to normal to remove bold effect
        },
      },

      // These are the default view settings for the heatmap.
      // If you want to change from Top to something else,
      // you will also have to change values in settingsTemplate.json
      // for example line 26 for the 3d view enabled/disabled
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
      rawData: null, // Initialize rawData
    };
  },

  // --------
  // Fetches initial configuration data and sets up the deck instance
  // --------
  created() {
    // Load in the general settings from the json template
    this.settings = this.generateSettings();
    // Get the config data
    // this.fetchData(`${this.backendUrl}/config`)
    // .then(() => this.calculateCurrentHash())
    // .then(() => this.loadUserSettings());
  },

  // --------
  // Initializes the Deck.gl instance on component mount
  // --------
  mounted() {
    this.rectangleTextLayer = new TextLayer(this.layerSettings.rectangleTextLayer);

    // Initialize Deck.gl with the PolygonLayer
    this.deck = new Deck({
      canvas: this.$refs.canvas,
      viewState: this.currentViewState,
      getTooltip: this.getTooltip,
      onViewStateChange: ({ viewState }) => {
        this.currentViewState = viewState;
        this.deck.setProps({ viewState: this.currentViewState });
      },
      controller: true,
      glOptions: {
        preserveDrawingBuffer: true, // Enable buffer preservation for screenshots
        antialias: true, // Optional: Smooth edges
      },
      // include the additional layer info, ie legend gradient etc
      layers: [
        ...this.layerSettings.rectangleGradientLayers,
        this.rectangleTextLayer,
      ],
    });

    // Now, fetch data after Deck.gl has been initialized
    // fetching needs to happen after initializing the deck canvas, otherwise get errors
    this.fetchData(`${this.backendUrl}/config`)
      .then(() => this.calculateCurrentHash())
      .then(() => this.loadUserSettings())
      .catch((error) => {
        console.error('Error during data fetching and initialization:', error);
      });
    // create initial gradient layer
    this.createLegendGradientLayer();
    console.log('Deck.gl initialized with PolygonLayer and empty TextLayer.');
  },

  methods: {
    // Extracts the table names without ()'s around the name
    extractTableNames() {
      return Object.keys(this.subTables).map((key) => key.replace(/[()]/g, ''));
    },

    // -------------------
    // To add in the text above the legend gradient
    // -------------------
    updateLegendText() {
      // Extract table names without parentheses
      const tableNames = this.extractTableNames();

      // ---
      // Extract most RHS coord of heatmap
      // ---
      // Looking at the heatmap and the position of the last square
      // and capture the coordinate so it can be dynamically asigned for
      // placement of the legend
      // Get the last item in the data array
      const lastIndex = this.layerSettings.gridCellLayer.data.length - 1;
      const lastDataItem = this.layerSettings.gridCellLayer.data[lastIndex];
      // Access the second element in the COORDINATES array (index 1) most RHS
      const lastCoordinateValue = lastDataItem.COORDINATES[1];
      // console.log(lastCoordinateValue);

      // ---
      // positioning of text
      // ---
      // Define the spacing between legend entries
      const spacing = 0.03; // spacing between text
      const baseY = 0.0075; // up/down
      // sideways
      const baseX = 0.015 + lastCoordinateValue + (0.03 / 2); // 0.03/2 = half the gradient box size

      // ---
      // Create text entries for each table
      // ---
      // loop through each of the loaded table names and create
      const newRectangleTextData = tableNames.map((tableName, index) => {
        const yPosition = baseY + (index * spacing);
        return {
          position: [yPosition, baseX], // is backwards to what you think
          text: tableName,
        };
      });

      // Create a new TextLayer with the dynamic text
      const newRectangleTextLayer = new TextLayer({
        id: 'legend-text',
        data: newRectangleTextData,
        getPosition: (d) => d.position,
        getText: (d) => d.text,
      });

      // Update Deck.gl layers by replacing the old TextLayer
      const updatedLayers = this.deck.props.layers.map((layer) => (
        layer.id === 'legend-text' ? newRectangleTextLayer : layer
      ));

      // updated layers to Deck.gl
      this.deck.setProps({
        layers: updatedLayers,
      });

      // Update the data property in layerSettings
      this.layerSettings.rectangleTextLayer.data = newRectangleTextData;

      // Update Deck.gl layers to include the updated rectangleTextLayer
      this.updateDeckLayers();

      // console.log(`Updated TextLayer with table names: ${tableNames.join(', ')}`);
    },

    // -------------------
    // Create gradient rectangle
    // -------------------
    createLegendGradientLayer() {
      const numberOfSlices = 50; // Can increase for smoother gradient
      const rectangleHeight = 0.03; // Total width of rectangle from -0.02 to 0.02
      const rectangleWidth = 0.01; // width of each gradient rectangle
      // gradient slices
      const sliceHeight = rectangleHeight / numberOfSlices;
      // x and y positions
      const baseX = 0.01; // Center the rectangle horizontally
      const baseY = 0.045; // Vertical position (bottom edge)
      // set default gradient, or default to RdYlGn if none
      const gradientPreset = this.colorGradientPreset || 'RdYlGn';
      // create gradient colour slices
      let gradientColors;
      try {
        gradientColors = chroma.scale(gradientPreset).mode('lrgb').colors(numberOfSlices);
        // console.log('Generated Gradient Colors:', gradientColors); // Debugging
      } catch (error) {
        // console.error('Invalid gradient preset:', gradientPreset, error);
        // Fallback to a default gradient
        gradientColors = chroma.scale('RdYlGn').mode('lrgb').colors(numberOfSlices);
      }

      // Extract all table names without ()'s
      const tableNames = this.extractTableNames();

      // ---
      // Loop through tables and create gradient layers
      // ---
      // Create a gradient layer for each table
      const gradientLayers = tableNames.map((tableName, index) => {
        const tableBaseY = baseY + index * (rectangleHeight + 0.01); // spacing between legends

        const gradientRectangleData = [];
        for (let i = 0; i < numberOfSlices; i += 1) {
          const yStart = tableBaseY + i * sliceHeight;
          const yEnd = yStart + sliceHeight;
          gradientRectangleData.push({
            // creating the polygon
            polygon: [
              [baseX, yStart],
              [baseX + rectangleWidth, yStart],
              [baseX + rectangleWidth, yEnd],
              [baseX, yEnd],
              [baseX, yStart], // needs to be same as start to close the shape
            ],
            color: [...chroma(gradientColors[i]).rgb(), 255],
          });
        }

        // Create the Gradient Rectangle Layer
        return new PolygonLayer({
          id: `legend-gradient-${tableName}`, // unique name
          data: gradientRectangleData,
          pickable: false,
          stroked: false,
          filled: true,
          wireframe: false,
          getPolygon: (d) => d.polygon,
          getFillColor: (d) => d.color,
        });
      });

      // Assign to layers.rectangleGradientLayer
      this.layerSettings.rectangleGradientLayers = gradientLayers;
      // console.log('Gradient Rectangle Layers:', this.layerSettings.rectangleGradientLayers);

      // Update Deck.gl layers to include the new gradient layers
      this.updateDeckLayers();
    },

    // -------------------
    // Updates the gradient rectangle on change
    // -------------------
    // Note: some text below is the same as when created - can be simplified
    updateLegendGradientLayer() {
      // for debugging if needed
      if (!this.colorGradientPreset) {
        console.warn('No colorGradientPreset selected.');
        return;
      }

      // ---
      // values accociated with the gradient rectangle
      // ---
      const numberOfSlices = 50; // Increase for smoother gradient
      const rectangleHeight = 0.03; // Total width from -0.02 to 0.02
      const rectangleWidth = 0.01;
      const sliceHeight = rectangleHeight / numberOfSlices;

      // Get the last item in the data array - used to work out the
      // most right hand position of the heatmap - otherwise the legend will overlap
      const lastIndex = this.layerSettings.gridCellLayer.data.length - 1;
      const lastDataItem = this.layerSettings.gridCellLayer.data[lastIndex];
      // Access the second element in the COORDINATES array (index 1)
      // Which is the most RHS - which we use to place the legend
      const lastCoordinateValue = lastDataItem.COORDINATES[1];

      // vertical spacing between legends (when more than 1)
      const spacing = 0 + rectangleHeight; // Increased vertical spacing for clarity
      // x and y start coords
      const baseX = 0.01; // updown
      const baseY = 0.015 + lastCoordinateValue; // sidewards

      // degugging
      // console.log('this.settings.gradient.individualGradients', this.settings.gradient.individualGradients);
      // console.log('this.settings.gradient.gradientPreset', this.settings.gradient.gradientPreset);
      // console.log('this.settings.gradient', this.settings.gradient);
      // console.log('this.layerSettings.gridCellLayer', this.layerSettings.gridCellLayer);

      const specialKeys = ['individualGradients', 'gradientPreset'];
      // loop and capture all table names
      const tableNames = Object.keys(this.settings.gradient)
        .filter((key) => !specialKeys.includes(key));

      // debugging
      // console.log('Table Names:', tableNames);
      // console.log('Gradient Keys:', Object.keys(this.settings.gradient));

      // Find the maximum value across all entries in the data array
      // used to work out the scaling for tickmarks for legend
      const maxValueOverall = Math.max(
        ...this.layerSettings.gridCellLayer.data.map((item) => item.VALUE),
      );
      // console.log('maxValueOverall', maxValueOverall);

      // Initialize an array to hold all gradient and line layers
      const updatedGradientLayers = [];

      // If more than one table, we want to enable (by default)
      // the option for multiple gradients
      // Same if only one table - disable selecting individual gradients
      // Otherwise have to link up the ticks to both preset and individual dynamic values
      if (tableNames.length > 1) {
        this.settings.gradient.individualGradients = true;
      } else {
        this.settings.gradient.individualGradients = false;
      }

      // Collect legend data to send for saving as svg
      this.legendData = [];

      // ---
      // Loop through each table
      // ---
      // Within this loop we generate each gradient box, the ticks and
      // also the values below the ticks
      tableNames.forEach((tableName, index) => {
        const legendBaseX = baseX + (index * spacing); // spacing between legends

        // Determine the gradient colors for the current table
        let gradientPreset;
        // console.log(`Processing table: ${tableName}`);

        // Check if individual gradients have been selected
        // although probably not needed anymore - keeping in just in case
        if (this.settings.gradient.individualGradients) {
          // Individual gradients have been selected - apply specific gradient for each table
          gradientPreset = this.settings.gradient[tableName]?.value || this.colorGradientPreset || 'RdYlGn';
          // console.log(`Gradient preset for ${tableName}:`, gradientPreset);
        } else {
          // Individual gradients not selected - apply default shared gradient
          gradientPreset = this.colorGradientPreset || 'RdYlGn';
          // console.log(`Shared gradient preset for ${tableName}:`, gradientPreset);
        }

        // Generate gradient colors for the current table
        let gradientColors;
        try {
          gradientColors = chroma.scale(gradientPreset).mode('lrgb').colors(numberOfSlices);
          // console.log(`Generated Gradient Colors for ${tableName}:`, gradientColors);
        } catch (error) {
          console.error(`Invalid gradient preset for table ${tableName}: ${gradientPreset}`, error);
          // Fallback to a default gradient
          gradientColors = chroma.scale('RdYlGn').mode('lrgb').colors(numberOfSlices);
        }

        // Define the gradient rectangles for the current table
        const gradientRectangleData = [];
        for (let i = 0; i < numberOfSlices; i += 1) {
          const yStart = baseY + i * sliceHeight; // Horizontal position start
          const yEnd = yStart + sliceHeight; // Horizontal position end
          gradientRectangleData.push({
            // unfortunately the rectangle is rotated slightly by 90 deg I think
            // but visually it appears fine - this should eventually be adjusted
            polygon: [
              [legendBaseX, yStart], // Top-Left
              [legendBaseX + rectangleWidth, yStart], // Top-right
              [legendBaseX + rectangleWidth, yEnd], // bottom-right
              [legendBaseX, yEnd], // bottom-left
              [legendBaseX, yStart], // closing the polygon
            ],
            color: [...chroma(gradientColors[i]).rgb(), 255], // RGBA color
          });
        }

        // create the polygon shape and add gradient
        const gradientLayer = new PolygonLayer({
          id: `legend-gradient-layer-${tableName}`, // Unique ID per table
          data: gradientRectangleData,
          pickable: false,
          stroked: false,
          filled: true,
          wireframe: false,
          getPolygon: (d) => d.polygon,
          getFillColor: (d) => d.color,
        });

        // If there is 1 table, then we need to use the present values
        // if there are more than one table, link gradients and ticks to each table name
        let domain = this.settings.gradient[tableName]?.domain;
        let [minValue, midValue, maxValue] = domain;
        if (tableNames.length > 1) {
          // console.log('more than one table');
          // do nothing - use above declared values for min,mid,max
        } else {
          // console.log('only one table');
          // using present values, as only one table
          domain = this.settings.gradient.gradientPreset.domain;
          // assigns domain[0] to minValue, domain[1] to midValue, and domain[2] to maxValue
          [minValue, midValue, maxValue] = domain;
        }

        // create the lines for below the gradient rectangle
        // Filter data for the specified table and get the maximum value
        // const maxValueTable = Math.max(
        // ...this.layerSettings.gridCellLayer.data
        // .filter((item) => item.TITLE === tableName)
        // .map((item) => item.VALUE),
        // );
        // console.log(`Max value for table ${tableName}:`, maxValueTable);
        const legendTickSegments = rectangleHeight / maxValueOverall;
        // console.log('legendTickSegments', legendTickSegments);

        // Calculate positions
        const minPosition = minValue * legendTickSegments; // 0; // Start of the rectangle
        const midPosition = midValue * legendTickSegments; // (midValue - minValue) / valueRange;
        const maxPosition = maxValue * legendTickSegments; // 1; // End of the rectangle

        // Calculate Y-Coordinates
        const minY = baseY + minPosition; //
        const midY = baseY + midPosition; // clampedMidPosition * rectangleHeight;
        const maxY = baseY + maxPosition; // * rectangleHeight;

        // Create lines data
        const lineLength = 0.000; // Adjust as needed
        // use these two lines if you want the black lines to be the entire
        // height of the gradient box
        // const lineStartX = legendBaseX - lineLength;
        // const lineEndX = legendBaseX + rectangleWidth + lineLength;
        const lineStartX = legendBaseX + rectangleWidth + lineLength; // Start bit before the rect
        const lineEndX = legendBaseX + rectangleWidth + lineLength + 0.001; // End bit after rect

        // positioning of the line
        const linesData = [
          {
            sourcePosition: [lineStartX, minY],
            targetPosition: [lineEndX, minY],
          },
          {
            sourcePosition: [lineStartX, midY],
            targetPosition: [lineEndX, midY],
          },
          {
            sourcePosition: [lineStartX, maxY],
            targetPosition: [lineEndX, maxY],
          },
        ];

        // Create the LineLayer for the min, mid, max lines
        const linesLayer = new LineLayer({
          id: `legend-lines-layer-${tableName}`,
          data: linesData,
          getSourcePosition: (d) => d.sourcePosition,
          getTargetPosition: (d) => d.targetPosition,
          getColor: [0, 0, 0, 255], // Black color
          getWidth: 1, // Adjust line width as needed
        });

        // Text layer for displaying the min, mid, max values below the gradient
        const textData = [
          { position: [lineEndX + 0.0025, minY], text: Math.round(minValue).toString() },
          { position: [lineEndX + 0.0025, midY], text: Math.round(midValue).toString() },
          { position: [lineEndX + 0.0025, maxY], text: Math.round(maxValue).toString() },
        ];
        // text layer to display the numbers below the tick marks
        const textLayer = new TextLayer({
          id: `legend-text-layer-${tableName}`,
          data: textData,
          getPosition: (d) => d.position,
          getText: (d) => d.text,
          sizeUnits: 'meters',
          getSize: 400, // Adjust font size as needed
          getColor: [0, 0, 0, 255], // Black text
          getTextAnchor: 'middle',
          getAlignmentBaseline: 'center',
          fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif',
        });

        // Add both layers to the array
        updatedGradientLayers.push(gradientLayer, linesLayer, textLayer);

        // Collect all the generated data for SVG export
        this.legendData.push({
          tableName,
          legendBaseX,
          baseY,
          rectangleWidth,
          rectangleHeight,
          gradientColors,
          linesData,
          minValue,
          midValue,
          maxValue,
          maxValueOverall,
        });
      });

      // Update the layerSettings with the new gradient layers
      this.layerSettings.rectangleGradientLayers = updatedGradientLayers;

      // Instead of directly modifying this.deck.props.layers, call updateDeckLayers()
      this.updateDeckLayers();

      console.log('Gradient Rectangle Layers updated.');
    },

    // ---
    // Layers to update on any user-based change
    // ---
    updateDeckLayers() {
      const allLayers = [
        new GridCellLayer(this.layerSettings.gridCellLayer),
        new TextLayer(this.layerSettings.textCellLayer),
        new TextLayer(this.layerSettings.rowTextLayer),
        new TextLayer(this.layerSettings.columnTextLayer),
        ...this.layerSettings.rectangleGradientLayers, // Include all gradient layers
        new TextLayer(this.layerSettings.rectangleTextLayer), // Include the updated text layer
      ];

      this.deck.setProps({
        layers: allLayers,
      });
    },

    // --------
    // Checks to see if user settings have been saved - if so, attempt to load
    // --------
    async loadUserSettings() {
      const dbEntryId = this.$route.query.config;
      try {
        const response = await axios.get(`http://127.0.0.1:3000/get-user-settings/${dbEntryId}`, {
          headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate', // Prevent caching
            Pragma: 'no-cache', // HTTP 1.0.
            Expires: '0', // Proxies.
            'Access-Control-Allow-Origin': '*',
          },
        });

        // console.log('Settings loaded');
        // console.log('Loaded hash from settings:', response.data.hash);

        if (response.data.hash === this.hashValue) {
          console.log('Hash values match:');
          // Apply the settings to the current plot
          this.applySettings(response.data);
        } else {
          console.log('Hash values do not match - not loading settings.');
        }
      } catch (error) {
        // Catch errors
        if (error.response && error.response.status === 404) {
          console.error('Settings file not found: ', error.response.data);
        } else {
          console.error('Error loading settings', error);
        }
      }
    },

    // --------
    // Helper method to calculate the current hash of the data
    // --------
    async calculateCurrentHash() {
      // Check this.rawData
      if (!this.rawData) {
        console.error('Error: rawData is undefined or null.');
        return;
      }
      // console.log('rawData:', this.rawData);

      // Assuming `this.rawData` has already been set
      // const serializedData = JSON.stringify(this.rawData, null, 2);

      const normalizedData = this.normalizeAndSortData(this.rawData);
      // console.log('normalizedData:', normalizedData);

      const serializedData = this.stableStringify(normalizedData);
      // console.log('serializedData:', serializedData);

      this.hashValue = await this.generateHash(serializedData);
      // console.log('3. Current hash calculated:', this.hashValue);
    },

    // ---
    // Assistance for hashing
    // ---
    // hashing wasnt consistant, so need to normalise data first
    normalizeAndSortData(data) {
      // Function to normalize and sort data
      const normalizedData = data.map((item) => {
        // Ensure keys are sorted and values are normalized
        const sortedKeys = Object.keys(item).sort();
        const normalizedItem = {};
        sortedKeys.forEach((key) => {
          normalizedItem[key] = item[key];
        });
        return normalizedItem;
      });
      return normalizedData.sort((a, b) => JSON.stringify(a).localeCompare(JSON.stringify(b)));
    },

    // --------
    // Allows users to take a screenshot of the current heatmap (png)
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
    // Generates initial settings for the heatmap based on a
    // predefined template thats loaded from the json.
    // This function constructs a settings object that includes
    // configurations for different aspects of the visualization,
    // such as layer properties, lighting effects, and gradient controls.
    // *
    // Process:
    // 1. Initialize an empty settings object with categories for layers,
    //    lighting, custom settings, and gradients.
    // 2. Iterate through each category in the provided settingsTemplate (json).
    // 3. For each category, iterate through the settings defined in the template.
    // 4. Each setting can have multiple inputs; iterate through these inputs to
    //    extract and assign their default values.
    // 5. Populate the settings object with these default values,
    //    categorizing them according to their specified property type.
    // *
    // The settings object structured by this function serves
    // as the foundational configuration from which the visualization's properties
    // can be adjusted dynamically via user interactions or other controls.
    // *
    // Returns:
    // A fully populated settings object with initial values as specified
    // in the settings template.

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

            // Assign the default value from the input to the
            // appropriate category in the settings object.
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

      // Use a switch statement to handle different types of
      // settings based on 'updatedSettings.type'.
      switch (updatedSettings.type) {
        // --- layer ---
        case 'layer': {
          // Merge existing layer settings with new ones and
          // ensure numerical properties are correctly typed.
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
          // Update Deck.gl layers to include all necessary layers - ie heatmap and legend
          this.updateDeckLayers();

          // Reconfigure the layers with the new settings.
          // this.deck.setProps({
          //   layers: updatedLayers,
          // });
          break;
        }
        // --- gradient ---
        case 'gradient': {
          // Toggle gradient update trigger to force re-rendering of layers.
          // eslint-disable-next-line max-len
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
          // Update Deck.gl layers to include all necessary layers - ie heatmap and legend
          this.updateDeckLayers();
          // Update the gradient rectangle layer
          this.updateLegendGradientLayer();
          break;
        }
        // --- lighting ---
        case 'lighting': {
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
        }
        default:
          // Log a warning if an unsupported update type is encountered.
          console.log('Warning: No case found for this setting update.');
      }
      // Notify the rest of the application that settings update is complete.
      this.$emit('long-loading-finished');
    },

    applySettings(settingsData) {
      // Apply the settings to the current plot
      // console.log('this.settings.layer.cellSize: ', this.settings.layer.cellSize);
      // console.log('response.data.visual.plot_gap: ', response.data.visual.plot_gap);
      // Visual
      this.settings.layer.cellSize = settingsData.visual.plot_gap;
      this.settings.layer.extruded = settingsData.visual.plot_3d;
      this.settings.layer.elevationScale = settingsData.visual.plot_elevation;
      this.settings.layer.opacity = settingsData.visual.plot_opacity;
      // Colour gradients
      this.settings.gradient.individualGradients = settingsData.colour_grad.individual_grad;
      this.settings.gradient.gradientPreset = settingsData.colour_grad.the_individual_grad;
      this.settings.gradient = settingsData.colour_grad.the_combined_grads;
      // Adv settings
      this.settings.layer.pickable = settingsData.adv_settings.tooltip;
      // Lighting
      this.settings.lighting.advancedLighting = settingsData.lighting.adv_lighting;
      this.settings.lighting.ambientLight = settingsData.lighting.amb_light;
      this.settings.lighting.directionalLight1 = settingsData.lighting.dir_light1;
      this.settings.lighting.directionalLight2 = settingsData.lighting.dir_light2;
      // Material
      this.settings.layer.material = settingsData.material.shader;
      this.settings.layer.advancedMaterial = settingsData.material.adv_material;
      this.settings.layer.ambientMaterial = settingsData.material.ambient;
      this.settings.layer.diffuseMaterial = settingsData.material.diffusion;
      this.settings.layer.shininess = settingsData.material.shininess;
      // plot camera
      this.activeCamera = settingsData.camera_view.activeCamera;
      this.deck.setProps({ viewState: settingsData.camera_view.currentViewState });
    },

    stableStringify(obj) {
      const allKeys = [];
      JSON.stringify(obj, (key, value) => {
        allKeys.push(key);
        return value;
      });
      allKeys.sort();
      return JSON.stringify(obj, allKeys);
    },

    // ---------
    // Fetches data for the heatmap visualization
    // ---------
    async fetchData(url) {
      // Fetches processed data from the backend for visualization in the heatmap.
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
      // 4. Data is used to update the visualization,
      //    applying layer-based settings like colors and scales.

      //  @param {string} url - The URL to which the POST request will be sent.
      // Create a new FormData object to hold the data to be sent with the HTTP POST request
      const payload = new FormData();
      // Append the 'url' key with the serialized configuration query parameter to the payload.
      // This configuration 'might' determine specific data filters
      // or identifiers for the backend to process.
      payload.append('url', JSON.stringify(this.$route.query.config));

      // Send a POST request to the Micromix URL with the prepared payload.
      // Axios is used here to handle the HTTP request.
      try {
        const res = await axios.post(url, payload);
        this.rawData = res.data;

        if (!this.rawData) {
          console.error('Error: rawData is undefined or null after fetch.');
          return;
        }

        const hash = await this.generateHash(this.rawData);
        this.hashValue = hash;
        // console.log('4. this.hashValue: ', this.hashValue);
        // console.log('5. this.rawData: ', this.rawData);

        [
          this.layerSettings.gridCellLayer.data,
          this.layerSettings.textCellLayer.data,
          this.layerSettings.rowTextLayer.data,
          this.layerSettings.columnTextLayer.data,
          this.highestValue,
          this.lowestValue,
        ] = this.processJsonData(res.data);

        this.createSubTableGradientForms();
        if (this.lowestValue < 0) {
          this.configureNegativeValues();
        }
        // After processing data, update the TextLayer with dynamic text
        this.updateLegendText();

        // Update Deck.gl layers to include all necessary layers - ie heatmap and legend
        this.updateDeckLayers();
      } catch (error) {
        console.error('Error fetching data: ', error);
      }
    },

    // Hash function to generate hash for data - for comparing when loading settings
    async generateHash(data) {
      // const encoder = new TextEncoder();
      // const dataAsUint8Array = encoder.encode(data);
      // const hashBuffer = await crypto.subtle.digest('SHA-256', dataAsUint8Array);
      // const hashArray = Array.from(new Uint8Array(hashBuffer)); // convert buffer to byte array
      // convert bytes to hex string
      // const hashHex = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
      // return hashHex;
      // return CryptoJS.SHA256(data).toString(CryptoJS.enc.Hex);
      const serializedData = this.stableStringify(data);
      return CryptoJS.SHA256(serializedData).toString(CryptoJS.enc.Hex);
    },

    // --------
    //
    // Processes JSON data into a format suitable for Deck.gl layers
    //
    // --------
    processJsonData(json) {
      // NOTE: This could be moved to the python backend for performace reasons.
      // Details:
      // The processJsonData function primarily focuses on transforming and
      // structuring JSON data for visualization in Deck.gl layers,
      // such as grid cells and text annotations (headers).
      // It doesn't involve the application settings related to
      // visual aspects like color gradients, camera views, materials,
      // or specific settings for min/max gradient values.
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

            // When encountering a new prefix,
            // reset subtable-specific trackers and adjust coordinates.
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
                gridCellLayerCell.VALUE *= -1; // Make value positive
                gridCellLayerCell.ORIENTATION = -1; // Flag negative orientation
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
      };
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

#deck-canvas {
  width: 100%;
  height: 100%;
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
