<template>
  <div>
    <loading v-if="loading" :increment="20" style="position: fixed;z-index: 100;top: 0;left: 0;width: 100vw;" />
    <b-form @submit="onSubmit" inline>
      <b-card bg-variant="light" v-for="(form_block_array, block_index) in query" v-bind:key="block_index" class="block-wrapper">
        <div class="form" v-for="form_block in form_block_array" v-bind:key="form_block.id + String(block_index)">
          <div class="form-block" v-for="form in form_block.forms.items" v-bind:key="form.id">
            <label v-if="form.label" :for="form.id">{{ form.label }}</label>
            <!-- dropdown -->
            <b-form-select v-if="form.type === 'b-form-select'" :options="form.options" :value="null" :id="form.id" v-model="form.selected" size="sm" class="mb-2 mr-sm-2 mb-sm-0" required></b-form-select>
            <!-- input -->
            <b-form-input v-else-if="form.type === 'b-form-input'" :id="form.id" v-model="form.selected" size="sm" class="mb-2 mr-sm-2 mb-sm-0" :style="form.style" required></b-form-input>
            <!-- autocomplete -->
            <input_autocomplete
              v-else-if="form.type === 'input-autocomplete'"
              :id="form.id"
              v-model="form.selected"
              v-bind:term_id="form.selected"
              v-bind:server_term="form.server_selected"
              v-on:update:term_id="form.selected = $event"
              v-bind:terms_list="form.source.items"
              v-bind:terms_key="form.source.key"
              class="mb-2 mr-sm-2 mb-sm-0"
              required
            ></input_autocomplete>


            <!-- tag select dropdown -->
            <b-form-tags v-else-if="form.type === 'b-form-tags'" 
              :id="form.id" 
              v-model="form.selected" 
              add-on-change 
              no-outer-focus 
              required 
              class="mb-2 mr-sm-2 mb-sm-0 tags-form">
              
              <template v-slot="{ tags, inputAttrs, inputHandlers, disabled, removeTag }">
                <ul v-if="tags.length > 0" class="list-inline d-inline-block mb-0">
                  <li v-for="tag in tags" :key="tag" class="list-inline-item">
                    
                    <b-form-tag @remove="removeTag(tag)" 
                      :title="tag" 
                      :disabled="disabled" 
                      variant="secondary">{{ tag }}
                    </b-form-tag>
                  </li>
                </ul>
                
                <b-form-select 
                  size="sm" 
                  v-bind="inputAttrs" 
                  v-on="inputHandlers" 
                  :disabled="disabled || availableOptions(form).length === 0" 
                  :options="availableOptions(form)" 
                  class="mb-0 mr-sm-0 mb-sm-0 tags-select">
                  <template v-slot:first>
                    <!-- This is required to prevent bugs with Safari -->
                    <option disabled value>Add columns...</option>
                  </template>
                </b-form-select>
              </template>
            </b-form-tags>


            <!-- log-input and -preview -->
            <div v-else-if="form.type === 'int-input'">
              <b-form-input 
                :id="form.id" 
                v-model="form.selected" 
                size="sm" 
                class="mb-2 mr-sm-2 mb-sm-0 short-form" 
                :style="form.style" 
                type="number" 
                :min="form.min" 
                :max="form.max" 
                required>
              </b-form-input>
              <div v-if="form.formula" 
                class="log-preview">
                <b-badge 
                  variant="dark" 
                  class="log-preview-badge">
                  <span class="supsub">
                    <span class="base formula">
                      log
                      <sub class="subscript">
                        <strong class="formula-strong"> {{ form.selected }}</strong>
                      </sub>
                      <!-- <span v-if="!form_block.forms.items.target_column" class="base formula"> ({{get_text_from_value(form_block.forms.items.target_table)}})</span> -->
                      <span v-if="!form_block.forms.items.target_column" class="base formula"> ({{ form_block.forms.items.target_table.selected }})</span>
                      <span v-else class="base formula"> (Fold-Change)</span>
                    </span>
                  </span>
                </b-badge>
              </div>
            </div>
            <b-form-select v-else-if="form.type === 'b-form-select-sync' && form_block_array[1].forms.items.operator" 
              :options="form.options" 
              :value="null" 
              :id="form.id" 
              v-model="form_block_array[1].forms.items.operator.selected" 
              size="sm" 
              class="mb-2 mr-sm-2 mb-sm-0" 
              required>
            </b-form-select>
          </div>
        </div>

        <!-- 
          ------------ 
          The code to display each query (is initially hidden)
          ------------ 
        -->
        
        <!-- The dropdown for adding logical operators between query blocks, 
          allowing users to specify how multiple conditions relate to each other (e.g., "AND", "OR"). 
          Visible only if the last query block has a logical operator and the form blocks are of type 'filter'. -->
        <b-dropdown
          v-if="form_block_array[form_block_array.length - 1]['logic'] && form_block_array[0].forms.properties.type === 'filter'"
          size="sm"
          variant="link"
          pill
          id="add-dropdown"
          text="Add..."
          class="m-md-2 rounded"
          no-caret
          toggle-class="text-decoration-none">

           <!-- The plus button -->
          <template v-slot:button-content>
            <b-icon icon="plus-circle"></b-icon>
          </template>

          <!-- logical dropdown items after clicking on plus icon-->
          <b-dropdown-item v-for="(operator, index) in filters.items.other.logical_operators" 
            :key="index" 
            v-on:click="add_query_block(operator, index, guidGenerator(), false, [block_index, form_block_array.length])">{{index}}
          </b-dropdown-item>
         </b-dropdown>

        <!-- The dropdown for adding new filter criteria or blocks to the query. 
          This allows users to expand their search or data filtering conditions by including more specific filters. 
          Visible for forms designated as 'filter'. -->
        <b-dropdown v-else-if="form_block_array[0].forms.properties.type === 'filter'" 
          size="sm" 
          variant="link" 
          pill 
          id="add-dropdown" 
          text="Add..." 
          class="m-md-2 rounded" 
          no-caret 
          toggle-class="text-decoration-none">

          <template v-slot:button-content>
            <b-icon icon="plus-circle"></b-icon>
          </template>


        
        <!-- 
          ------------ 
          Populating each of the dropdown buttons
          ------------ 
        -->


        <!-- The following code populates the different dropdown buttons, such as filter, functional annotation, ncRNAs and transform data. 
            The contents for example are stored in: filters.items.templates.
            .templates looks in filters.json and collects all the items under templates
          -->


          <!-- Add Filter 
          <b-dropdown-group v-for="(filter_template_group, index) in filters.items.templates" 
            :key="index" 
            :header="index" 
            id="dropdown-group-numeric">
          <b-dropdown-item v-for="(template, index) in filter_template_group" 
            :key="index" 
            v-on:click="add_query_block(template, index, guidGenerator(), true, false)">{{ index }}
          </b-dropdown-item>
            <b-dropdown-divider></b-dropdown-divider>
          </b-dropdown-group> -->

          <!-- Preset Filters -->
          <b-dropdown-group v-for="(filter_preset_group, index) in filters.items.presets" 
            :key="index" 
            :header="index" 
            id="dropdown-group-numeric">
          <b-dropdown-item v-for="(preset, index) in filter_preset_group" 
            :key="index" 
            v-on:click="add_query_block(preset, index, guidGenerator(), true, false)">{{ index }}
          </b-dropdown-item>
            <b-dropdown-divider></b-dropdown-divider>
          </b-dropdown-group>

          <!-- Transformations 
          <b-dropdown-group v-for="(filter_preset_group, index) in filters.items.transformations" 
            :key="index" 
            :header="index" 
            id="dropdown-group-numeric">
          <b-dropdown-item v-for="(preset, index) in filter_preset_group" 
            :key="index" 
            v-on:click="add_query_block(preset, index, guidGenerator(), true, false)">{{ index }}
          </b-dropdown-item>
            <b-dropdown-divider></b-dropdown-divider>
          </b-dropdown-group> -->
          
          <!-- to add more options - populate here with additional dropdown groups -->
        </b-dropdown>

        <!-- Trash button -->
        <b-button size="sm" variant="link" v-on:click="remove_query_block(form_block_array)">
          <b-icon icon="trash"></b-icon>
        </b-button>
      </b-card>



      <!-- 
          ------------ 
          Display properties for each of the dropdowns
          ------------ 
        -->


      <!-- Each b-dropdown are the filter/transform buttons
           If you need to add a new button or link to a new annotation category, change filters.items.presets
            The .presents links into the filters.json file and new annotation cateories can be added -->


      <!-- 
        The add filter dropdown 
      -->
      <b-dropdown 
        size="sm" 
        variant="link" 
        pill 
        id="add-query-dropdown" 
        text="Add..." 
        class="m-md-2 rounded" 
        no-caret 
        toggle-class="text-decoration-none"
        :disabled="isDropdownDisabled">  <!-- greys out the button once a filter query has been loaded-->

        <!-- This is the popover text that whows when the help button is pressed - repeats below -->
        <b-popover 
          id="tutorial_popover" 
          :no-fade="true" 
          triggers placement="bottom" 
          target="add-query-dropdown" 
          title="2. Build filters">
          You can add different row filters.
        </b-popover>

        <!-- The image and text -->
        <template v-slot:button-content>
          <b-icon icon="plus-circle-fill"></b-icon> 
          Row Filter 
        </template>
        
        <!-- The contents -->
        <b-dropdown-group v-for="(filter_template_group, index) in filters.items.templates" 
          :key="index" 
          :header="index" 
          id="dropdown-group-numeric">
        <b-dropdown-item v-for="(template, index) in filter_template_group" 
          :key="index" 
          v-on:click="add_query_block(template, index, guidGenerator(), true, false)">{{ index }}
        </b-dropdown-item>
          <b-dropdown-divider></b-dropdown-divider>
        </b-dropdown-group>
      </b-dropdown>



      <!-- 
        The functional annotation dropdown 
      -->
      <b-dropdown 
        size="sm" 
        variant="link" 
        pill 
        id="load-query-dropdown" 
        text="Add..." 
        class="m-md-2 rounded" 
        no-caret 
        toggle-class="text-decoration-none"
        :disabled="isDropdownDisabled">  <!-- greys out the button once a filter query has been loaded-->
        
        <!-- This is the popover text that whows when the help button is pressed - repeats below -->
        <b-popover 
          id="tutorial_popover" 
          :no-fade="true" 
          triggers 
          placement="rightbottom" 
          target="load-query-dropdown" 
          title="3. Load preset filters"
          >Search for KEGG, GO or other annotation-based pathways.
        </b-popover>

        <!-- The image and text -->
        <template v-slot:button-content> 
          <b-icon icon="intersect"></b-icon> 
          Functional annotation 
        </template>

        <!-- The contents -->
        <b-dropdown-group v-for="(filter_preset_group, index) in filters.items.functional" 
          :key="index" 
          :header="index" 
          id="dropdown-group-numeric">
        <b-dropdown-item v-for="(preset, index) in filter_preset_group" 
          :key="index" 
          v-on:click="add_query_block(preset, index, guidGenerator(), true, false)">{{ index }}
        </b-dropdown-item>
          <b-dropdown-divider></b-dropdown-divider>
        </b-dropdown-group>
      </b-dropdown>


      <!-- 
        The ncRNA or SPI gene lists 
      -->
      <b-dropdown 
        size="sm" 
        variant="link" 
        pill 
        id="load-query-dropdown" 
        text="Add..." 
        class="m-md-2 rounded" 
        no-caret 
        toggle-class="text-decoration-none"
        :disabled="isDropdownDisabled">  <!-- greys out the button once a filter query has been loaded-->
        
        <!-- This is the popover text that whows when the help button is pressed - repeats below -->
        <b-popover 
          id="tutorial_popover" 
          :no-fade="true" 
          triggers 
          placement="rightbottom" 
          target="load-query-dropdown" 
          title="4. Load preset filters"
          >Load pre-filled filters to search for pathogenicity islands, sORF etc.
        </b-popover>

        <!-- The image and text -->
        <template v-slot:button-content> 
          <b-icon icon="intersect"></b-icon> 
          ncRNA 
        </template>

        <!-- The contents -->
        <b-dropdown-group v-for="(filter_preset_group, index) in filters.items.presets" 
          :key="index" 
          :header="index" 
          id="dropdown-group-numeric">
        <b-dropdown-item v-for="(preset, index) in filter_preset_group" 
          :key="index" 
          v-on:click="add_query_block(preset, index, guidGenerator(), true, false)">{{ index }}
        </b-dropdown-item>
          <b-dropdown-divider></b-dropdown-divider>
        </b-dropdown-group>
      </b-dropdown>



      <!-- 
        The Transform Data dropdown 
      -->
      <b-dropdown 
        size="sm" 
        variant="link" 
        pill 
        id="load-query-dropdown" 
        text="Add..." 
        class="m-md-2 rounded" 
        no-caret 
        toggle-class="text-decoration-none"> 

        <!-- This is the popover text that whows when the help button is pressed - repeats below -->
        <b-popover 
          id="tutorial_popover" 
          :no-fade="true" 
          triggers 
          placement="rightbottom" 
          target="load-query-dropdown" 
          title="4. Transform data">
          Transform columns and values, such as hiding columns and rounding values.
        </b-popover>

        <!-- The image and text -->
        <template v-slot:button-content> 
          <b-icon icon="calculator-fill"></b-icon>
          Transform Data 
        </template>

        <!-- The contents -->
        <b-dropdown-group v-for="(filter_preset_group, index) in filters.items.transformations" 
          :key="index" 
          :header="index" 
          id="dropdown-group-numeric">
        <b-dropdown-item v-for="(preset, index) in filter_preset_group" 
          :key="index" 
          v-on:click="add_query_block(preset, index, guidGenerator(), true, false)">{{ index }}
        </b-dropdown-item>
          <b-dropdown-divider></b-dropdown-divider>
        </b-dropdown-group>
      </b-dropdown>

      


      <!-- The filter data button (to submit the filter) -->
      <div class="submit-button-parent">
        <b-button type="submit" variant="primary" pill size="sm" class="submit-button">
          <!-- <b-spinner label="Loading..." class="search-spinner" v-if="loading"></b-spinner> -->
          <b-icon icon="search"></b-icon> Filter Data
        </b-button>
      </div>
    </b-form>
  </div>
</template>

<script>
import axios from "axios";
import input_autocomplete from "./input_autocomplete";
import loading from "./loading";

export default {
  name: "search_query",
  
  // Props are used to pass data from parent to child components
  props: {
    df_categories: Array, // Array of data frame categories for dropdown options
    server_queries: Array, // Array of server queries to convert into query blocks
    backend_url: String, // URL for backend queries
    table_titles: Array, // Array of table titles for dropdown options
    active_organism: Object, // Object representing the currently active organism
  },


  components: {
    // Declaring local components used within this component
    input_autocomplete,
    loading,
  },

  computed: {
    //This is for the filter dropdowns - disabling the dropdowns if there is an existing query that is a filter,
    //otherwise, enable the dropdown.
    //The idea here is that all gene filtering (filter) should be linked to a conditional filter and need to be
    //combined within the same region - because having blocks in different locations is confusing to work out the logic
    isDropdownDisabled() {
    // Check if query length is greater than 0
    const hasQueries = this.query.length > 0;
    // Check if there is at least one 'filter' type block in the query array
    const hasFilterTypeBlock = this.query.some(queryBlockArray => {
      return queryBlockArray.some(block => block.forms.properties.type === 'filter');
      });
    // Disable the dropdown if there are queries and at least one of them is a filter type
    return hasQueries && hasFilterTypeBlock;
    }
  },

  methods: {
    // Syncs the form block with the form, used for keeping form inputs in sync
    syncedForm(form_block, form) {
      print(form_block, form);
      return form.selected;
    },
    
    // Returns available options by filtering out selected options from the full options list
    availableOptions(form) {
      return form.options.filter((opt) => form.selected.indexOf(opt) === -1);
    },

    // Deeply copies an input object or array to prevent mutating the original data
    deep_copy(input) {
      let output, value, key;
      if (typeof input !== "object" || input === null) {
        return input;
      }
      output = Array.isArray(input) ? [] : {};
      for (key in input) {
        value = input[key];
        output[key] = this.deep_copy(value);
      }
      return output;
    },

    // Converts server query blocks to template blocks for rendering in the UI
    convert_server_query_blocks(templates) {
      for (var i = 0; i < this.server_queries.length; i++) {
        for (var j = 0; j < this.server_queries[i].length; j++) {
          
          // Process each server query block, converting to UI-friendly blocks
          let block_name = this.server_queries[i][j].name;
          template_type: for (let type in templates) {
            for (let query_group in templates[type]) {
              if (block_name in templates[type][query_group] === true) {
                let block = this.deep_copy(templates[type][query_group][block_name]);
                for (let form in this.server_queries[i][j].forms) {
                  block.items[form].selected = this.server_queries[i][j].forms[form];
                  if (this.server_queries[i][j].forms.filter_annotation && block.items[form].source) {
                    // Convert annotation id's to annotation name
                    let selected_parent = block.items[form].source.items.find((item) => item.id === block.items[form].selected);
                    block.items[form].selected = selected_parent.name;
                    block.items[form].server_selected = selected_parent;
                  }
                }
                this.add_query_block(block, block_name, this.server_queries[i][j]["id"], this.server_queries[i][j]["logic"], this.server_queries[i][j]["inline_coordinates"]);
                break template_type;
              }
            }
          }
        }
      }
    },
   
    // Prepares a new query block with provided parameters
    prepare_query_block(forms, index, id, logic, inline_coordinates) {
      let added_block = {};
      added_block["forms"] = this.deep_copy(forms);
      added_block["logic"] = logic;
      added_block["name"] = index;
      added_block["id"] = id;
      added_block["inline_coordinates"] = inline_coordinates;
      return added_block;
    },

    // Adds a new query block to the query array for rendering in the UI
    //This method is responsible for adding new query blocks to the query structure. 
    //It checks if inline_coordinates are provided. 
    //If not, the new block is pushed to the end of the query structure; 
    //if inline_coordinates are provided, it inserts the new block at a specified position within an existing block.
    add_query_block(forms, index, id, logic, inline_coordinates) {
      if (!inline_coordinates) {
        //add to the end
        this.query.push([this.prepare_query_block(forms, index, id, logic, inline_coordinates)]);
      } else {
        //insert within an existing block
        this.query[inline_coordinates[0]].splice(inline_coordinates[1], 0, this.prepare_query_block(forms, index, id, logic, inline_coordinates));
      }
    },


    
    // Generates a unique ID for query blocks
    guidGenerator() {
      return (
        "_" +
        Math.random()
          .toString(36)
          .substr(2, 9)
      );
      // return (Math.random() * 1001) | 0;
    },
    
    
    // Restructures the query for submission to the backend
    restructure_query() {
      let structured_query = [];
      for (let array in this.query) {
        for (let sub_array in this.query[array]) {
          let structured_query_block = {};
          // console.log(this.query[array][sub_array]);
          structured_query_block["name"] = this.query[array][sub_array]["name"];
          structured_query_block["properties"] = this.query[array][sub_array]["forms"]["properties"];
          structured_query_block["id"] = this.query[array][sub_array]["id"];
          structured_query_block["logic"] = this.query[array][sub_array]["logic"];
          structured_query_block["inline_coordinates"] = this.query[array][sub_array]["inline_coordinates"];
          structured_query_block["forms"] = {};
          for (let form in this.query[array][sub_array]["forms"]["items"]) {
            structured_query_block["forms"][form] = this.query[array][sub_array]["forms"]["items"][form]["selected"];
          }
          if (structured_query_block["inline_coordinates"]) {
            structured_query[structured_query_block["inline_coordinates"][0]].splice(structured_query_block["inline_coordinates"][1], 0, structured_query_block);
          } else {
            structured_query.push([structured_query_block]);
          }
        }
      }
      return structured_query;
    },
    
    // Removes a query block from the query array
    remove_query_block(block_array) {
      const index = this.query.indexOf(block_array);
      if (index > -1) {
        this.query.splice(index, 1);
      }
      for (let i in this.server_queries) {
        // Optional: Push filter query as soon as a filter is removed
        if (this.server_queries[i][0]["id"] === block_array[0]["id"]) {
          this.loading = true;
          this.post_query();
          break;
        }
      }
    },
    
    // Submits the query to the backend and handles the response
    post_query() {
      const path = `${this.backend_url}/query`;
      var data = new FormData();
      var structured_query = this.restructure_query();
      // console.log(structured_query);
      data.append("query", JSON.stringify(structured_query));
      data.append("url", JSON.stringify(this.$route.query.config));
      // console.log(this.query);
      // console.log(data);
      let self = this;
      // self.$parent.$bvModal.hide('bv_modal_addData')
      axios
        .post(path, data)
        .then((res) => {
          if (res.data.error_type) {
            self.$emit("error_occured", res.data);
            this.loading = false;
          } else {
            self.$emit("dataframe_filtered", res);
            this.$nextTick(() => {
              setTimeout(() => {
                // This forces the loading bar to stay alive for 2 additional seconds, 
                //to compensate the delay between backend work and frontend rendering of the dataframe table. This isn't very good.
                this.loading = false;
              }, 2500);
            });
          }
        })
        .catch((error) => {
          console.log(error);
        });
    },
    
    // Form submission handler
    onSubmit(evt) {
      this.loading = true;
      evt.preventDefault();
      this.post_query();
    },
    
    
    // Loads autocomplete options from JSON files
    load_autocomplete_json() {

      //If adding in a new annotation type, you will need to add a new line in here
      //The contents are linked to two files (case-sensitive)
      //pathways.json - which is where the pathways.go "go" part comes from - the high level entries
      //filters.items.functional
      //filter.json - this is where ["Filter by annotation"]["GO Term"] comes from - under the top category of functional (filters.items.functional)
      //["Filter by annotation"] - this is the category in the dropdown and linked to the section in the filters.json
      //["GO Term"] - the specific entry in the filters.json under the category "Filter by annotation"

      //Check for the active organism and load in the corresponding annotations
      if (this.active_organism.name == "Salmonella") {
                
                console.log("active=Sal");
                this.filters.items.functional["Filter by annotation"]["GO Terms"].items.filter_annotation.source.items = this.pathways.go;
                this.filters.items.functional["Filter by annotation"]["KEGG Pathways"].items.filter_annotation.source.items = this.pathways.kegg;

            } else {
                
                console.log("active=other"); //NOTE: if you have more than 2 organisms or strains - if-else should be added
                this.filters.items.functional["Filter by annotation"]["GO Terms"].items.filter_annotation.source.items = this.pathways.go;
                this.filters.items.functional["Filter by annotation"]["KEGG Pathways"].items.filter_annotation.source.items = this.pathways.kegg;
                this.filters.items.functional["Filter by annotation"]["KEGG Modules"].items.filter_annotation.source.items = this.pathways.kegg_module;
                this.filters.items.functional["Filter by annotation"]["Polysaccharide utilization loci (PUL)"].items.filter_annotation.source.items = this.pathways.pul;
                this.filters.items.functional["Filter by annotation"]["Capsular polysaccharides (CPS)"].items.filter_annotation.source.items = this.pathways.cps;
                this.filters.items.functional["Filter by annotation"]["Conjugative transposons (CTn)"].items.filter_annotation.source.items = this.pathways.ctn;
                this.filters.items.functional["Filter by annotation"]["Promoter motifs"].items.filter_annotation.source.items = this.pathways.promoter_motif;
                this.filters.items.functional["Filter by annotation"]["RegPrecise regulons"].items.filter_annotation.source.items = this.pathways.regprecise;
                this.filters.items.functional["Filter by annotation"]["CRP regulation"].items.filter_annotation.source.items = this.pathways.crp_regulation;

            }
    },
    
    
    load_categories_json(query_source) {
      for (let query_cat in query_source) {
        for (let query in query_source[query_cat]) {
          // Performance: It might be useful to check for a common condition and then do another nested
          // if else, instead of checking every entry for two diffferent conditions.
          // It also might be useful to just restructure this mess.
          if (query_source[query_cat][query].items["filter_area"]) {
            query_source[query_cat][query].items["filter_area"]["options"] = [].concat(query_source[query_cat][query].items["filter_area"]["default_options"], this.df_categories);
          }
          if (query_source[query_cat][query].items["target_column"]) {
            query_source[query_cat][query].items["target_column"]["options"] = [].concat(query_source[query_cat][query].items["target_column"]["default_options"], this.df_categories);
          }
          if (query_source[query_cat][query].items["start_column"]) {
            query_source[query_cat][query].items["start_column"]["options"] = [].concat(query_source[query_cat][query].items["start_column"]["default_options"], this.df_categories);
          }
          if (query_source[query_cat][query].items["end_column"]) {
            query_source[query_cat][query].items["end_column"]["options"] = [].concat(query_source[query_cat][query].items["end_column"]["default_options"], this.df_categories);
          }
          if (query_source[query_cat][query].items["counts_column"]) {
            query_source[query_cat][query].items["counts_column"]["options"] = [].concat(query_source[query_cat][query].items["counts_column"]["default_options"], this.df_categories);
          }
          if (query_source[query_cat][query].items["target_table"]) {
            query_source[query_cat][query].items["target_table"]["options"] = this.table_titles;
          }
        }
      }
    },
  },
  
  
  
  // Lifecycle hook called after the component is created
  // Loads filters, pathways, and initializes component data
  created() {
    this.filters = require(`../assets/organisms${this.active_organism.path}/filters.json`);
    try {
      this.pathways = require(`../assets/organisms${this.active_organism.path}/pathways.json`);
    } catch (e) {
      console.log("No pathway.json found for this organism. Ignore this if the selected organism doesn't have annotation pathways.");
    }
    this.load_autocomplete_json();
    for (var query_type in this.filters.items) {
      this.load_categories_json(this.filters.items[query_type]);
    }
    this.convert_server_query_blocks(this.filters.items);
  },
  
  
  // The component's reactive data properties
  data() {
    return {
      loading: false, // Indicates whether the component is in a loading state
      query: [], // Array of query blocks for building the query UI
      filters: null, // Object containing filter options loaded from JSON
      pathways: null, // Object containing pathway options loaded from JSON
    };
  },
};
</script>





<style scoped>
label {
  margin-right: 0.5rem;
  font-size: 0.875rem;
}
svg,
button {
  margin: 0;
  text-decoration: none !important;
}
.block-wrapper {
  width: 100%;
}
#add-dropdown {
  margin: 0 !important;
}
.card-body {
  padding: 0.35rem 0.35rem 0 0.35rem;
  display: block;
  align-items: center;
}
.card {
  margin-bottom: 0.5rem;
  display: inline-block;
}
.form-block {
  display: inline-flex;
  align-items: center;
}
.submit-button-parent {
  flex: 1;
  text-align: right;
}
.form {
  display: inline-flex;
  padding-bottom: 0.35rem;
  max-width: 95%;
}
.short-form {
  width: 4rem !important;
}
/* .search-spinner {
  width: 1em;
  height: 1em;
}
.spinner-border {
  border: 0.15em solid currentColor;
  border-right-color: transparent;
} */
.tags-select {
  max-width: 150px !important;
}
.list-inline-item {
  margin-right: 0rem !important;
}
.tags-form {
  padding: 0.2rem !important;
}
</style>
