<template>
  <div class="menu">
    <!-- Hidden container for SVG export -->
    <div id="export_svg" style="display: none;"></div>
    <a id="canvas-png-link"></a>
    <div class="mb-4">
      <div class="header mt-3 mb-2">Download Top View as SVG</div>
      <!-- <label>Export the 2D top view of the heatmap.</label> -->
        <b-form inline class="mb-1 custom-b-form">
          <b-form-group label="Export text" label-for="checkbox-1">
          <b-form-checkbox
          id="checkbox-1"
          v-model="showText"
          name="checkbox-1"
          value="true"
          unchecked-value="false"
        />
         </b-form-group>
        </b-form>
      <b-button block variant="dark" size="sm" @click="exportCanvasSvg">
        <!-- <img :src="require(`@/assets/exportImage.svg`)"> Download SVG -->
        <b-icon icon="download" aria-hidden="true"></b-icon> SVG Heatmap
      </b-button>
      <div class="header mt-3 mb-2">Download Current View as PNG</div>
      <b-button id="btn-download" block variant="dark" size="sm" @click="$emit('take-screenshot')">
        <!-- <img :src="require(`@/assets/exportImage.svg`)"> Download SVG -->
        <b-icon icon="download" aria-hidden="true"></b-icon> PNG Current View
      </b-button>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    layerSettings: Object,
    colorGradientDict: Object,
    legendData: Array, // for adding legend to svg save
  },
  data() {
    return {
      xMargin: undefined,
      yMargin: undefined,
      showText: 'true',
    };
  },
  methods: {
    exportCanvasSvg() {
      // This needs to be slimmed down (Titus).

      // **1. Get the legend data passed from deckglcanvas.vue**
      const { legendData } = this;

      // **Log legendData to verify its content**
      console.log('Exporting SVG with legendData:', legendData);

      // **2. Get the DOM element where the SVG will be temporarily attached**
      const domElement = document.getElementById('export_svg');

      // **2.5. Check if domElement exists to prevent errors**
      if (!domElement) {
        console.error("Element with id 'export_svg' not found.");
        return;
      }

      // **3. Create the SVG element**
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      const svgNS = svg.namespaceURI;

      svg.setAttribute('id', 'downloadable_svg');
      svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

      // Append the svg element to the DOM first
      domElement.appendChild(svg);

      // **4. Compute the size of each cell in the heatmap**
      const size = this.layerSettings.gridCellLayer.cellSize / 50;

      // **5. Create a group element to hold the cells**
      const cellGroup = document.createElementNS(svgNS, 'g');
      cellGroup.setAttribute('style', 'font-size: 11px;font-family: HelveticaNeue, Helvetica Neue;text-align: right;');

      // **6. Determine margins based on whether text is to be shown**
      if (this.showText === 'true') {
        this.xMargin = 80; // Margin for columns
        this.yMargin = 100; // margin for rows

        // **7. Create group elements for columns and rows**
        const columnGroup = document.createElementNS(svgNS, 'g');
        const rowGroup = document.createElementNS(svgNS, 'g');
        rowGroup.setAttribute('style', 'font-size: 11px;font-family: HelveticaNeue, Helvetica Neue;text-align: right;');
        columnGroup.setAttribute('style', 'font-size: 11px;font-family: HelveticaNeue, Helvetica Neue;');
        svg.appendChild(rowGroup);
        svg.appendChild(columnGroup);

        // **8. Loop through columns to add column headers**
        for (let i = 0; i < this.layerSettings.columnTextLayer.data.length; i += 1) {
          const columnText = document.createElementNS(svgNS, 'text');
          const columnTextNode = document
            .createTextNode(this.layerSettings.columnTextLayer.data[i].VALUE);
          columnText.setAttribute('transform', `rotate(-90) translate(-90, ${this.layerSettings.columnTextLayer.data[i].COORDINATES[1] * 2220 + this.xMargin + 4})`);
          columnText.appendChild(columnTextNode);
          columnGroup.appendChild(columnText);
        }

        // **9. Loop through rows to add row headers**
        for (let j = 0; j < this.layerSettings.rowTextLayer.data.length; j += 1) {
          const rowText = document.createElementNS(svgNS, 'text');
          const rowTextNode = document
            .createTextNode(this.layerSettings.rowTextLayer.data[j].VALUE);
          rowText.setAttribute('x', 0);
          rowText.setAttribute('y', this.layerSettings.rowTextLayer.data[j].COORDINATES[0] * 2220 + this.yMargin + 4);
          rowText.appendChild(rowTextNode);
          rowGroup.appendChild(rowText);
        }
      } else {
        //  If showText is false, set margins to 0**
        this.xMargin = 0;
        this.yMargin = 0;
      }

      // **10. Loop through grid cells to draw the heatmap**
      // needs to start at 0, as 0-based
      for (let k = 0; k < this.layerSettings.gridCellLayer.data.length; k += 1) {
        let orientation;
        const rect = document.createElementNS(svgNS, 'rect');
        // Set position of the cell
        const rectX = this.layerSettings.gridCellLayer.data[k].COORDINATES[1] * 2220 + this.xMargin;
        const rectY = this.layerSettings.gridCellLayer.data[k].COORDINATES[0] * 2220 + this.yMargin;
        rect.setAttribute('x', rectX);
        rect.setAttribute('y', rectY);
        rect.setAttribute('width', size);
        rect.setAttribute('height', size);

        // **11. Check orientation for coloring**
        // Following lines are heavy on performance. Maybe check for lowest_value < 0?
        if (!this.layerSettings.gridCellLayer.data[k].ORIENTATION) {
          orientation = 1;
        } else {
          orientation = this.layerSettings.gridCellLayer.data[k].ORIENTATION;
        }

        // **12. Set the fill color based on the gradient dictionary**
        rect.setAttribute(
          'fill',
          this.colorGradientDict[
            this.layerSettings.gridCellLayer.data[k].TITLE](
            this.layerSettings.gridCellLayer.data[k].VALUE * orientation,
          ).hex(),
        );
        cellGroup.appendChild(rect);
      }

      // **13. Add text labels to cells if applicable**
      for (let l = 1; l < this.layerSettings.textCellLayer.data.length; l += 1) {
        if (this.layerSettings.textCellLayer.data[l].VALUE) {
          const text = document.createElementNS(svgNS, 'text');
          const textNode = document
            .createTextNode(this.layerSettings.textCellLayer.data[l].VALUE);
          text.setAttribute('y', this.layerSettings.textCellLayer.data[l].COORDINATES[0] * 2220 + this.yMargin);
          text.setAttribute('style', `font-size: ${32 / (this.layerSettings.textCellLayer.data[l].VALUE.length + 2.5)}px`);
          // The following is a dumb quick-fix and should be replaced (Titus).
          // Calculates the x position based on string length to center it.
          text.setAttribute('x', this.layerSettings.textCellLayer.data[l].COORDINATES[1] * 2220 + this.xMargin - 8 + 4 / this.layerSettings.textCellLayer.data[l].VALUE.length);
          text.appendChild(textNode);
          cellGroup.appendChild(text);
        }
      }

      // **14. Append the cell group to the SVG**
      svg.appendChild(cellGroup);

      // **15. Now, draw the legend **
      if (legendData && legendData.length > 0) {
        const scale = 2220; // **Same scaling factor used for positions**
        const legendGroup = document.createElementNS(svgNS, 'g');
        legendGroup.setAttribute('id', 'legend-group');
        svg.appendChild(legendGroup);

        // const verticalSpacing = 0.05; // Spacing between legends
        // **16. Loop through each legend item to draw the legend**
        legendData.forEach((legendItem, index) => {
          const {
            tableName,
            // legendBaseX,
            // baseY: legendBaseY,
            rectangleWidth,
            rectangleHeight,
            gradientColors,
            minValue,
            midValue,
            maxValue,
            maxValueOverall,
          } = legendItem;

          // **17. Create a group for this legend item**
          const itemGroup = document.createElementNS(svgNS, 'g');
          itemGroup.setAttribute('id', `legend-${tableName}`);
          legendGroup.appendChild(itemGroup);

          // **18. Create defs if not already created**
          let defs = svg.querySelector('defs');
          if (!defs) {
            defs = document.createElementNS(svgNS, 'defs');
            svg.appendChild(defs);
          }
          // console.log('defs', defs);
          // **19. Create a linear gradient for the gradient rectangle**
          // need to remove the ()'s from the table name, otherwise the gradient appears black
          const sanitizedTableName = tableName.replace(/[^a-zA-Z0-9_-]/g, '');
          const gradientId = `gradient-${sanitizedTableName}`;
          // console.log('Creating gradient with ID:', gradientId);

          // const gradientId = `gradient-${tableName}`;
          const linearGradient = document.createElementNS(svgNS, 'linearGradient');
          linearGradient.setAttribute('id', gradientId);
          linearGradient.setAttribute('x1', '0%'); // Start at the left
          linearGradient.setAttribute('y1', '0%'); // top
          linearGradient.setAttribute('x2', '100%'); // end at the right
          linearGradient.setAttribute('y2', '0%'); // top
          // console.log(`Creating gradient ${gradientId} with colors:`, gradientColors);
          // console.log('gradientId', gradientId);
          // console.log('linearGradient', linearGradient);
          // **20. Add gradient stops**
          gradientColors.forEach((color, idx) => {
            const stop = document.createElementNS(svgNS, 'stop');
            stop.setAttribute('offset', `${(idx / (gradientColors.length - 1)) * 100}%`);
            stop.setAttribute('stop-color', color);
            stop.setAttribute('stop-opacity', '1'); // Ensure full opacity
            linearGradient.appendChild(stop);
          });

          defs.appendChild(linearGradient);

          // **21. Draw the gradient rectangle (horizontal)**
          let rectX = 0;
          let minRectY = Infinity; // Initialize to a large number
          // Loop through each cell in the heatmap data to find the rightmost position
          // and also the topmost position - so the legend can be placed dynamically
          for (let k = 0; k < this.layerSettings.gridCellLayer.data.length; k += 1) {
            const cell = this.layerSettings.gridCellLayer.data[k];
            const cellX = cell.COORDINATES[1] * 2220 + this.xMargin;
            const cellY = cell.COORDINATES[0] * 2220 + this.yMargin;

            // Update rectX to the maximum X position
            if (cellX > rectX) {
              rectX = cellX;
            }

            // Update minRectY to the minimum Y position
            if (cellY < minRectY) {
              minRectY = cellY;
            }
          }

          const spacing = 55; // spacing between legends
          const adjustedLegendBaseY = index * (rectangleWidth * scale + spacing);

          const xStart = 30 + rectX; // sideways
          const yStart = minRectY + 20 + adjustedLegendBaseY; // up and down position of legend

          const gradientRect = document.createElementNS(svgNS, 'rect');
          gradientRect.setAttribute('x', xStart);
          gradientRect.setAttribute('y', yStart);
          gradientRect.setAttribute('width', rectangleHeight * scale); // Swapped for horizontal orientation
          gradientRect.setAttribute('height', rectangleWidth * scale); // Swapped for vertical thickness
          gradientRect.setAttribute('fill', `url(#${gradientId})`);
          itemGroup.appendChild(gradientRect);

          // **22. Draw tick marks (lines)**
          const lineLength = 0.001 * scale; // Adjust as needed
          const legendTickSegments = rectangleHeight / maxValueOverall;
          // Calculate positions
          const minPosition = minValue * legendTickSegments; // 0; // Start of the rectangle
          const midPosition = midValue * legendTickSegments; // (midValue - minValue) / valueRange;
          const maxPosition = maxValue * legendTickSegments; // 1; // End of the rectangle

          const minX = xStart + minPosition * scale;
          const midX = xStart + midPosition * scale;
          const maxX = xStart + maxPosition * scale;

          // Start from bottom of gradient rectangle
          const tickYStart = yStart + rectangleWidth * scale;

          const tickLinesData = [
            {
              sourcePosition: [minX, tickYStart],
              targetPosition: [minX, tickYStart + lineLength],
            },
            {
              sourcePosition: [midX, tickYStart],
              targetPosition: [midX, tickYStart + lineLength],
            },
            {
              sourcePosition: [maxX, tickYStart],
              targetPosition: [maxX, tickYStart + lineLength],
            },
          ];

          tickLinesData.forEach((line) => {
            const lineElement = document.createElementNS(svgNS, 'line');
            lineElement.setAttribute('x1', line.sourcePosition[0]);
            lineElement.setAttribute('y1', line.sourcePosition[1]);
            lineElement.setAttribute('x2', line.targetPosition[0]);
            lineElement.setAttribute('y2', line.targetPosition[1]);
            lineElement.setAttribute('stroke', 'black');
            lineElement.setAttribute('stroke-width', 1);
            itemGroup.appendChild(lineElement);
          });

          // **23. Add text labels for min, mid, max values**
          const textOffsetY = 0.002 * scale; // Adjust as needed
          const textData = [
            {
              position: [
                minX,
                tickYStart + lineLength + textOffsetY,
              ],
              text: Math.round(minValue).toString(),
            },
            {
              position: [
                midX,
                tickYStart + lineLength + textOffsetY,
              ],
              text: Math.round(midValue).toString(),
            },
            {
              position: [
                maxX,
                tickYStart + lineLength + textOffsetY,
              ],
              text: Math.round(maxValue).toString(),
            },
          ];

          textData.forEach((textItem) => {
            const textElement = document.createElementNS(svgNS, 'text');
            textElement.setAttribute('x', textItem.position[0]);
            textElement.setAttribute('y', textItem.position[1]);
            textElement.textContent = textItem.text;
            textElement.setAttribute('font-size', '11px');
            textElement.setAttribute('fill', 'black');
            textElement.setAttribute('text-anchor', 'middle'); // Center alignment
            textElement.setAttribute('alignment-baseline', 'hanging'); // Align text above y coordinate
            itemGroup.appendChild(textElement);
          });

          // **24. Optionally, add the table name as a label**
          const tableNameText = document.createElementNS(svgNS, 'text');
          tableNameText.setAttribute('x', xStart + (rectangleHeight * scale) / 2);
          tableNameText.setAttribute('y', yStart - 5); // Above the rectangle
          tableNameText.textContent = sanitizedTableName;
          tableNameText.setAttribute('font-size', '12px');
          tableNameText.setAttribute('fill', 'black');
          tableNameText.setAttribute('text-anchor', 'middle');
          tableNameText.setAttribute('alignment-baseline', 'baseline');
          itemGroup.appendChild(tableNameText);
        });
      }
      // **25. Set the SVG width and height to include the legend**
      const svgWidth = this.layerSettings.gridCellLayer.data[
        this.layerSettings.gridCellLayer.data.length - 1
      ].COORDINATES[1] * 2220 + this.layerSettings.gridCellLayer.cellSize / 50 + 100;

      const svgHeight = this.layerSettings.gridCellLayer.data[
        this.layerSettings.gridCellLayer.data.length - 1
      ].COORDINATES[0] * 2220 + this.layerSettings.gridCellLayer.cellSize / 50 + 100;

      svg.setAttribute('width', svgWidth + 100); // add in space for the legend
      svg.setAttribute('height', svgHeight);

      // **26. Append the SVG to the DOM temporarily to get its outerHTML**
      // Note: The SVG is already appended at this point
      const svgData = svg.outerHTML;

      // **26.5. Remove the SVG from the DOM after capturing its data**
      domElement.removeChild(svg);

      // **27. Create a Blob from the SVG data and initiate download**
      const svgBlob = new Blob([svgData], {
        type: 'image/svg+xml;charset=utf-8',
      });
      const svgUrl = URL.createObjectURL(svgBlob);
      const downloadLink = document.createElement('a');
      downloadLink.href = svgUrl;
      downloadLink.download = 'Heatmap_top_view.svg';
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
    },
  },
};
</script>

<style scoped>
svg {
  margin-right: 0.25rem;
}
.menu {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background-color: #fff;
  width: 369px;
  padding: 20px 40px 10px 40px;
  box-shadow: 10px 30px 60px rgba(0, 0, 0, 0.08);
  border-radius: 5px;
  font-size: 14px;
}
legend {
  font-weight: 600;
}
button {
  background-color: #1c1d29;
  padding: 0.5rem;
}
.header {
  color: #2c3e50 !important;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 400;
  text-decoration: none !important;
  font-size: 12px !important;
}
.form-group{
  margin: auto;
  font-family:
    "Space Grotesk", -apple-system, BlinkMacSystemFont, "Segoe UI",
    Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
}
</style>
