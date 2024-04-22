<!-- Matrix preview details -->
<template>
  <div>
    <!-- Table preview with grid layout for displaying multiple matrices -->
    <div class="table_preview">
      <svg
        v-for="matrix in matrices"
        :key="matrix.id"
        @click="selected = matrix, select_matrix()" 
        :class="{hot:selected.id==matrix.id, active:selected.id==matrix.id}"
        :style="{'grid-area': `${matrix.y} / ${matrix.x} / auto / auto`, 'height': `${(matrix.height * gap)-(gap-rect_height)}px`, 'width': `${(matrix.width * gap)-(gap-rect_width)}px`}"
        v-b-tooltip
        :title="matrix.title"
        trigger="click"
      >
        <!-- Loop through the columns in the matrix -->
        <g
          v-for="column in matrix.height"
          :key="column"
          class="rows"
          :style="{transform: `translate(0px, ${column * gap - gap}px)`}"
          v-bind:class="{ active: matrix.isActive }"
        >
          <!-- Loop through the rows to create individual cells -->
          <rect
            v-for="row in matrix.width"
            :key="row"
            class="cells"
            :style="{transform: `translate(${row * gap - gap}px, 0px)`, width: rect_width, height: rect_height}"
          />
        </g>
      </svg>
    </div>
    <!-- Table buttons for additional actions like removing a matrix -->
    <div class="table_buttons">
      <!-- <b-button-group>
        <b-button
          v-b-toggle.collapse-relative
          v-b-popover.hover.top="'Divides the selected dataframe B by the uploaded data A for relative expression when activated.'"
          title="Relative Expression"
          :pressed.sync="relative_expression.activated"
          :disabled="button_enabled == 0"
          @click="emit_transformation(relative_expression)"
          size="sm"
          variant="secondary"
        >
          <img src="../assets/differential.svg" class="img_in_btn" />Relative Expression
        </b-button> -->
        <!-- Button to remove a selected matrix -->
        <b-button
          v-b-modal.modal_delete
          @click="on_delete_matrix()"
          :disabled="button_enabled == 0"
          size="sm"
          variant="danger"
        >
          <img src="../assets/trash.svg" class="img_in_btn" />Remove
        </b-button>
      <!-- </b-button-group> -->

      <!-- Collapse section for additional transformation options -->
      <b-collapse id="collapse-relative" class="mt-2">
        <b-card class="transformation-options">
          <!-- <p class="card-text">Select base column for normalization.</p> -->
          <div>
            <b-form>
              <!-- <b-form-select
                id="input-3"
                v-model="form.normalization_column"
                :options="df_categories"
                required
              >
              <b-form-select-option :value="null" disabled>Select a column</b-form-select-option></b-form-select>-->
               <!-- Additional input for specifying log base when fold-change is activated -->
              <b-form-checkbox
                id="checkbox-1"
                v-model="relative_expression.options.activated"
                name="checkbox-1"
                :value="false"
                :unchecked-value="true"
                class="log-fc-toggle"
              >Activate logarithmic fold-change</b-form-checkbox>
              <div v-if="!relative_expression.options.activated">
                <label class="mr-sm-2" for="log-input">log Base:</label>
                <b-form-input
                  id="log-input"
                  v-model="relative_expression.options.value"
                  type="number"
                  max="1001"
                  class="mb-2 mr-sm-2 mb-sm-0 log-input inline"
                  size="sm"
                  placeholder="'2'"
                ></b-form-input>
                <!-- Preview of the selected log base -->
                <div class="log-preview">
                  <b-badge variant="dark" class="log-preview-badge">
                    <span class="supsub">
                      <span class="base formula">
                        log
                        <sub class="subscript">
                          <strong class="formula-strong">{{relative_expression.options.value}}</strong>
                        </sub>
                        <span class="base formula">(x)</span>
                      </span>
                    </span>
                  </b-badge>
                </div>
              </div>
            </b-form>
          </div>
        </b-card>
      </b-collapse>
    </div>
  </div>
</template>

<script>
export default {
  name: "matrix",
  props: {
    gap: Number,
    rect_width: Number,
    rect_height: Number,
    matrices: Array,
    df_categories: Array
  },
  data() {
    return {
      is_hot: false,
      selected: undefined, // Currently selected matrix
      button_enabled: false, //Indicates if certain buttons are enabled
      relative_expression: {
        type: "relative_expression",
        activated: false, // Tracks if relative expression is activated
        options: {
          activated: false,
          value: 2,
          type: "log-fc" // Default log base
        }
      },
      transformation: null,
      form: {
        normalization_column: null
      }
    };
  },
  created() {
    // Initialize the selected matrix when component is created
    if (this.matrices.length === 1) {
      this.selected = this.matrices[0];
    } else {
      // If multiple matrices, select the one with specific coordinates
      for (let i in this.matrices) {
        if (this.matrices[i].x === 1 && this.matrices[i].y === 2) {
          this.selected = this.matrices[i];
          break;
        }
      }
    }
    this.$emit("matrix_activated", this.selected);
  },
  methods: {
    emit_transformation(current_transformation) {
      // Sets the current transformation based on the checkbox state
      if (current_transformation.activated == true) {
        this.transformation = current_transformation;
      } else {
        this.transformation = null;
      }
      this.$emit("transformation_selected", this.transformation);
    },
    select_matrix() {
      // Selects a matrix and emits an event
      this.$emit("matrix_activated", this.selected);
      // Enable/disable the remove button based on the selected matrix state
      if (this.selected.isActive == true) {
        this.button_enabled = true;
      } else {
        this.button_enabled = false;
      }
    },
    on_delete_matrix() {
      this.$emit("delete", this.selected);
    }
  }
};
</script>

<style>
@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.15;
  }
  100% {
    opacity: 1;
  }
}
:root {
  --cell-width: 16px;
  --cell-height: 16px;
  --cell-color: #e0e0e0;
}
rect {
  fill: var(--cell-color);
}

.rows {
  display: flex;
}

.active,
svg:hover {
  --cell-color: #484848;
}

.table_preview {
  display: inline-grid;
}

rect {
  transition: fill 200ms ease-out;
}

svg {
  margin: 5px;
  cursor: pointer;
}

.hot {
  animation-name: pulse;
  animation-duration: 1.5s;
  animation-iteration-count: infinite;
}

.btn-secondary:not(:disabled):not(.disabled).active {
  background-color: #007bff !important;
  border-color: #007bff !important;
}
/* .supsub {
  font-family: "Nimbus Roman No9 L","Times New Roman",Times,serif;
} */
/* .subscript>strong {
  color: #007bff;
} */
.transformation-options {
  max-width: fit-content;
  margin: auto;
}
.log-preview {
  font-size: 1.25rem;
  display: inline-block !important;
}
.log-preview-badge {
  display: inline-block !important;
}
.formula {
  font-weight: 400 !important;
  font-family: "Times New Roman", Times, serif;
  font-style: italic;
}
.formula-strong {
  font-weight: 600;
  font-family: sans-serif;
  font-style: initial;
}
#log-input {
  max-width: 4rem;
  display: inline-block;
}
.badge_dark {
  background-color: #343a40 !important;
}
.log-fc-toggle {
  margin-bottom: 0.5rem;
  display: block;
}
</style>