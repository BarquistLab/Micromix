 <!-- Main form for adding data tables/matrices --> 
 
 <template>
  <div>
    <b-progress
      v-if="show_loading_overlay"
      :value="bar_value"
      variant="success"
      striped
      :animated="animate"
    ></b-progress>
    <b-overlay :show="show_loading_overlay" rounded="sm" variant="white">
      <b-container class="bv-example-row">
        <b-row>
          <b-col>
            <h2 style="cursor:help; display:inline-block;" id="upload-dataset-popover-target">Add Data
              <span style="font-size:1rem;"><sup><b-icon style="cursor:help;" icon="question-circle-fill"></b-icon></sup></span>
            </h2>
              <b-popover target="upload-dataset-popover-target" triggers="hover" placement="top">
                <template v-slot:title>Upload a dataset
                </template>Upload various datasets from our databases or your local machine. If you give datasets the same title, the tool will automatically merge them without data-loss. The first column and all columns with non-numeric values will be turned into index columns. <strong>Uploading multiple tables requires 1 or more index column with the same column name.</strong>
              </b-popover>
            <b-form @submit="onSubmit" @reset="onReset" v-if="show">
              
              <b-form-group id="input-group-2" label="Title:" label-for="input-2">
                <b-form-input id="input-2" v-model="form.title" required></b-form-input>
              </b-form-group>
              
              <b-form-group id="input-group-6" label="Source:" label-for="source-card">
                <b-card no-body id="source-card">
                  <b-tabs card>
                    <b-tab title="Datasets" active>
                      <b-form-group
                        id="input-group-3"
                        description="Use our database of experimental results (e.g. Salmonella RNA-seq) for the organism you specified."
                      >
                        <b-form-select
                          id="input-3"
                          v-model="form.source.database"
                          :options="datasets_options"
                        ></b-form-select>
                      </b-form-group>
                      <b-form-group
                        v-if="form.source.database"
                        id="input-group-4"
                        description="Select which columns should be uploaded by adding or removing columns."
                        label="(Optional) Select columns"
                      >
                        <b-form-tags
                          v-model="form.database_columns"
                          size="lg"
                          add-on-change
                          no-outer-focus
                          class="mb-2"
                        >
                          <template
                            v-slot="{ tags, inputAttrs, inputHandlers, disabled, removeTag }"
                          >
                            <ul v-if="tags.length > 0" class="list-inline d-inline-block mb-2">
                              <li v-for="tag in tags" :key="tag" class="list-inline-item">
                                <b-form-tag
                                  @remove="removeTag(tag)"
                                  :title="tag"
                                  :disabled="disabled"
                                  variant="dark"
                                >{{ tag }}</b-form-tag>
                              </li>
                            </ul>
                            <b-form-select
                              v-bind="inputAttrs"
                              v-on="inputHandlers"
                              :disabled="disabled || availableOptions.length === 0"
                              :options="availableOptions"
                            >
                              <template v-slot:first>
                                <!-- This is required to prevent bugs with Safari -->
                                <option disabled value>Choose additional columns...</option>
                              </template>
                            </b-form-select>
                          </template>
                        </b-form-tags>
                      </b-form-group>
                    </b-tab>
                    <b-tab title="Paste Text">
                      <b-form-group
                        id="input-group-1"
                        description="Copy a table from your favorite editor (e.g. Excel, OpenOffice) and paste it here. The dot character ('.') will be replaced by an underscore ('_') in text cells."
                      >
                        <b-form-textarea
                          id="textarea"
                          v-model="form.source.text"
                          placeholder="Copy & paste a tab-seperated table here..."
                          rows="9"
                          max-rows="18"
                        ></b-form-textarea>
                      </b-form-group>
                      <b-form inline>
                        <b-form-group
                          class="seperator-group mb-2 mr-sm-2 mb-sm-0"
                          label-align-sm="left"
                          label="Decimal Character:"
                          label-for="#dropdown-decimal-del"
                        >
                          <b-form-input
                            id="dropdown-decimal-del"
                            class="seperator-field"
                            size="sm"
                            type="text"
                            maxlength="1"
                            v-model="form.formatting.text.decimal_character"
                          ></b-form-input>
                        </b-form-group>
                      </b-form>
                    </b-tab>
                    <b-tab title="Upload file">
                      <b-form-group
                        id="input-group-4"
                        description="Upload a .csv, .txt (tab-seperated), .tsv, or .xlsx (Excel) file from your machine."
                      >
                        <b-form-file
                          id="upload_form"
                          role="form"
                          enctype="multipart/form-data"
                          v-model="form.source.file"
                          :state="Boolean(form.source.file)"
                          placeholder="Choose a file or drop it here..."
                          drop-placeholder="Drop file here..."
                          accept=".txt, .xlsx, .csv, .tsv"
                        ></b-form-file>
                      </b-form-group>
                      <b-form inline>
                        <b-form-group
                          class="seperator-group"
                          label-align-sm="left"
                          label="CSV Seperator:"
                          label-for="dropdown-csv-sep"
                        >
                          <b-form-input
                            list="input-list"
                            id="dropdown-csv-sep"
                            class="seperator-field mb-2 mr-sm-2 mb-sm-0"
                            size="sm"
                            autocomplete="off"
                            maxlength="2"
                            v-model="form.formatting.file.csv_seperator"
                          ></b-form-input>
                          <b-form-datalist id="input-list" :options="csv_sep_list"></b-form-datalist>
                        </b-form-group>
                        <b-form-group
                          class="seperator-group mb-2 mr-sm-2 mb-sm-0"
                          label-align-sm="left"
                          label="Decimal Character:"
                          label-for="dropdown-decimal-del"
                        >
                          <b-form-input
                            id="dropdown-decimal-del"
                            class="seperator-field"
                            size="sm"
                            type="text"
                            maxlength="1"
                            v-model="form.formatting.file.decimal_character"
                          ></b-form-input>
                        </b-form-group>
                      </b-form>
                      <!-- <div class="mt-3">Selected file: {{ form.source.file ? form.source.file.name : '' }}</div> -->

                      <!-- <div class="mt-3">Selected file: {{ form.source.file ? form.source.file.name : '' }}</div> -->
                    </b-tab>
                    <b-tab title="URL">
                      <b-form-group
                        id="input-group-1"
                        description="Enter a valid URL to your dataset."
                      >
                        <b-form-input disabled id="input-1" v-model="form.source.url" type="url" placeholder></b-form-input>
                      </b-form-group>
                    </b-tab>
                  </b-tabs>
                </b-card>
              </b-form-group>
              <b-alert v-model="showErrorAlert" variant="danger" dismissible>{{sourceErrMsg}}</b-alert>
              <pre class="mt-3 mb-0">{{ text }}</pre>
              <b-button 
                type="submit" 
                variant="primary" 
                class="margin-right">
                Add
              </b-button>
              <b-button 
                type="reset" 
                variant="danger">
                Cancel
              </b-button>
            </b-form>
          </b-col>
          <b-col 
            class="center">
            <h2 style="cursor:help;" 
              v-b-popover.hover.top="'Choose where your dataframe should be placed. Select an existing matrix to replace it with your uploaded data or to remove it.'" 
              title="Place your data">
              Matrix Preview
              <span style="font-size:1rem;">
                <sup>
                  <b-icon 
                    style="cursor:help;" 
                    icon="question-circle-fill">
                  </b-icon>
                </sup>
              </span>
            </h2>
            <matrix
              @delete="delete_matrix"
              v-bind:matrices="matrices"
              v-bind:rect_width="15"
              v-bind:rect_height="15"
              v-bind:gap="20"
              v-bind:df_categories="df_categories[0]"
              @matrix_activated="onMatrixActivated"
              @transformation_selected="change_transformation"
            />
          </b-col>
        </b-row>
      </b-container>
    </b-overlay>
  </div>
</template>

<script>
import matrix from "./matrix.vue";
import axios from "axios";
import datasets from "../assets/json/datasets.json";

export default {
  name: "addDataForm",
  props: {
    matrices: Array,
    df_categories: Array,
    backend_url: String,
    local_active_organism_id: String,
    active_organism: Object,
  },
  components: {
    matrix
  },
  data() {
    return {
      csv_sep_list: [{value: "\t", text: 'Tab' },{value: ' ', text: 'Space' }],
      test: ['test'],
      datasets,
      animate: true,
      show_loading_overlay: false,
      sourceErrMsg: "",
      showErrorAlert: false,
      matrices_old: [],
      activeMatrix: null,
      timer: null,
      bar_value: 1,
      datasets_options: [],
      default_dataset_option: {"value": null, "text": "Please select a dataset"},
      form: {
        title: "",
        x: 2,
        y: 2,
        type: [],
        matrix_id: null,
        db_entry_id: "",
        plugins_id: [],
        locked: false,
        transformation: "",
        formatting: {
          file: {
            csv_seperator: ",",
            decimal_character: "."
          },
          text: {
            decimal_character: "."
          }
        },
        source: {
          file: null,
          database: null,
          url: null,
          text: null
        },
        database_columns: [],
      },
      text: "",
      show: true
    };
  },
  watch: {
    'form.source.database': function() {
      if(this.form.source.database.pre_selected_columns) {
        this.form.database_columns = this.form.source.database.pre_selected_columns
      } else { // If no pre_selected_columns are specified in the datasets.json entry, pre-select all columns instead
        this.form.database_columns = this.form.source.database.columns.slice(1) // Do not use the first empty placeholder value
      }
    }
  },
  computed: {
    availableOptions() {
      return this.form.source.database.columns.slice(1).filter(opt => this.form.database_columns.indexOf(opt) === -1)
    }
  },
  created() {
    this.refine_dataset_options()
  //   // console.log(this.plugins);
  //   // this.fetch_matrices();
  //   // console.log("proped matrices: ", this.matrices);
  },
  beforeDestroy() {
    clearInterval(this.timer);
    this.timer = null;
  },
  methods: {
    refine_dataset_options() {
      this.datasets_options.push(this.default_dataset_option)
      for(var i in this.active_organism.datasets) {
        if(this.active_organism.datasets[i] === "$all_datasets") {
          for(var dataset in this.datasets) {
            this.datasets_options.push(this.datasets[dataset])
          }
          break
        } else {
          this.datasets_options.push(this.datasets[this.active_organism.datasets[i]])
        }
      }
    },
    change_transformation(obj) {
      // console.log(obj);
      this.form.transformation = obj;
      // console.log("form: ", this.form);
    },
    progress_bar() {
      // console.log("mounted");
      this.timer = setInterval(() => {
        this.bar_value = this.bar_value + Math.random() * 40;
      }, 2000);
    },

    change_matrix(path, payload) {
      this.show_loading_overlay = true;
      if (this.$route.query.config) {
        this.form.db_entry_id = this.$route.query.config;
      }
      this.form.local_active_organism_id = this.local_active_organism_id
      var data = new FormData();
      data.append("file", payload);
      data.append("form", JSON.stringify(this.form));
      let self = this;
      // self.$parent.$bvModal.hide('bv_modal_addData')
      axios
        .post(path, data)
        .then(res => {
          if (res.data.error_type) {
            this.show_loading_overlay = false;
            self.$emit("error_occured", res.data);
          } else {
            this.$nextTick(() => {
              // console.log("after next tick res: ", res);
              // console.log(JSON.stringify(res));
              self.$emit("dataframe_change", res);
              this.show_loading_overlay = false;
            });
          }
        })
        .catch(error => {
          console.log(error);
        });
    },
    onSubmit(evt) {
      evt.preventDefault();
      this.progress_bar();
      // console.log(this.form.source);
      this.validateForm(this.form.source);
    },
    onReset(evt) {
      evt.preventDefault();
      this.$emit("close");
    },
    validateForm(obj) {
      var properties = 0;
      for (var key in obj) {
        if (obj[key] !== null && obj[key] !== "") {
          properties++;
        }
      }
      if (properties < 1) {
        this.sourceErrMsg = "Please enter a data-source.";
        this.showErrorAlert = true;
      } else if (properties > 1) {
        this.sourceErrMsg = "Please enter no more than one data-source.";
        this.showErrorAlert = true;
      } else if (
        this.form.formatting.file.csv_seperator == "" ||
        this.form.formatting.file.decimal_character == ""
      ) {
        this.sourceErrMsg =
          "The CSV seperator or decimal character for uploaded files cannot be empty.";
        this.showErrorAlert = true;
      } else if (this.form.formatting.text.decimal_character == "") {
        this.sourceErrMsg =
          "The decimal character for pasted text cannot be empty.";
        this.showErrorAlert = true;
      } else {
        const payload = this.form.source.file;
        this.change_matrix(`${this.backend_url}/upload`, payload);
        // this.$emit("close");
      }
    },
    delete_matrix(matrix) {
      const path = `${this.backend_url}/matrix/${matrix.id}`;
      const payload = null;
      this.change_matrix(path, payload);
    },
    onMatrixActivated(matrix) {
      this.form.x = matrix.x;
      this.form.y = matrix.y;
      this.form.matrix_id = matrix.id
      console.log(this.form.matrix_id);
    }
  }
};
</script>

<style scoped>
.seperator-group {
  margin-bottom: 0 !important;
  color: #6c757d;
  font-size: small;
  margin-bottom: 0.5rem !important;
}
#dropdown-csv-sep {
  margin-left: 0.5rem;
  width: 60px;
}
#dropdown-decimal-del {
  margin-left: 0.5rem;
  width: 40px;
}
.margin-right {
  margin-right: .5rem;
}
</style>
