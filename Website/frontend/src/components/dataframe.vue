<template>
  <div>
    <b-card>
      <div class="table-options">
        <!-- I have disabled this as I couldn't figure out how to change the default action from keypress to pressing enter
          The issue is that when a large daframe is loaded, it makes the page unresponsive and thus unusable
          There is a filtering option that can actually be used instead - seach for locus_tag and enter the IDs
              <b-form-group label="Search:" label-size="sm" label-for="filterInput" class="inline-element move_search">
          <b-form-input
            v-on:keyup.enter="onEnter"
            v-model="filter"
            type="search"
            id="filterInput"
            size="sm"
            placeholder="Type to Search"
            class="inline-element test"
          ></b-form-input>
        </b-form-group> -->
        <b-form-group
          label="Show"
          label-size="sm"
          label-for="perPageSelect"
          class="inline-element"
        >
          <b-form-select
            v-model="perPage"
            id="perPageSelect"
            size="sm"
            :options="pageOptions"
            class="inline-element rows-per-page"
          ></b-form-select>
          <span style="display: inline !important;" class="d-block col-form-label-sm"> of {{this.totalRows}}</span>
        </b-form-group>
        <b-form-group class="inline-element">
          <b-pagination
            v-model="currentPage"
            :per-page="perPage"
            align="fill"
            size="sm"
            :total-rows="totalRows"
          ></b-pagination>
        </b-form-group>
        <b-form-group class="inline-element" id="toggle-filtered">
          <span id="toggle_filtered_span" class="col-form-label-sm">Show filtered</span>
          <label class="switch switch-label bv-no-focus-ring">
            <b-popover id="tutorial_popover" :no-fade="true" triggers="" placement="bottom" target="toggle_filtered_span" title="Toggle filtered table">Click on the slider to toggle between your source data and the filtered table.</b-popover>
            <input type="checkbox" v-model="filtered" value="false" unchecked-value="true" />
            <span class="slider round"></span>
          </label>
          <!-- <div class="filter-toggle-text">Filtered table is visible? {{ filtered_visible }}</div> -->
        </b-form-group>
      </div>
      <!-- User Interface controls -->
      <div class="table-wrapper" v-if="this.items != null">
        <b-table
          id="dataframe-table"
          ref="ref_dataframe_table"
          hover
          small
          :items.sync="items"
          :current-page="currentPage"
          :per-page="perPage"
          :filter="filter"
          :filterIncludedFields="filterOn"
          :fields="dataframe_headers"
          head-variant="light"
          @filtered="onFiltered"
        >
          <template v-slot:cell()="data">{{data.value}}</template>
          <template v-slot:cell(GeneID)="data">{{data.value}}</template>
          <!-- <template v-slot:table-busy>
            <div class="text-center text-danger my-2">
              <b-spinner class="align-middle"></b-spinner>
              <strong>Loading...</strong>
            </div>
          </template> -->
        </b-table>
      </div>
    </b-card>
  </div>
</template>

<script>
export default {
  props: {
    dataframe: Array,
    dataframe_filtered: Array,
    update_is_filter: Boolean,
  },
  watch: {
    dataframe: function() {
      if (this.update_is_filter === true) {
        this.update_table(this.dataframe_filtered)
        this.filtered = true;
      } else {
        this.update_table(this.dataframe)
        this.filtered = false;
      }
    },
    filtered: function() {
      // PERFORMANCE: This is called twice after the dataframe update. This should be improved.
      // this.$emit('update:filtered', this.filtered)
      if (this.filtered === true) {
        this.update_table(this.dataframe_filtered);
      } else {
        this.update_table(this.dataframe)
      }
    }
  },
  data() {
    return {
      dataframe_headers: [],
      totalRows: 1,
      currentPage: 1,
      perPage: 20,
      pageOptions: [20, 50, 100, 1000],
      filter: null,
      filterOn: [],
      items: this.dataframe,
      filtered: this.update_is_filter
    };
  },
  mounted() {
    this.totalRows = this.items.length;
  },
  methods: {
    update_table(dataframe) {
      this.items = dataframe;
      this.create_table_headers();
      this.totalRows = this.items.length;
      this.currentPage = 1;
      this.$refs.ref_dataframe_table.refresh();
    },
    onFiltered(filteredItems) {
      // Trigger pagination to update the number of buttons/pages due to filtering
      this.totalRows = filteredItems.length;
      this.currentPage = 1;
    },
    create_table_headers() {
      this.dataframe_headers = []
      for (let header in this.items[0]) {
        let entry = {};
        entry["key"] = header;
        entry["sortable"] = true;
        this.dataframe_headers.push(entry);
      }
    }
  },
  created() {
    this.create_table_headers(this.dataframe);
    if (this.dataframe_filtered.length > 0) {
      this.filtered = true;
    }
  }
};
</script>

<style scoped>
table#dataframe-table .flip-list {
  transition: transform 1s;
}
table {
  font-family: "SF Mono", -apple-system, "Courier New", Courier, monospace;
  font-size: 0.8rem;
}
.card {
  width: 95vw;
  border-radius: 20px;
  background-color: #fff;
}
.table-wrapper {
  line-height: normal;
  overflow: auto;
  border-radius: 8px;
}
.table-options {
  display: grid;
  grid-template-columns: auto auto auto 1fr;
  grid-column-gap: 30px;
  align-items: center;
}
.pagination {
  width: min-content;
}
.switch-label {
  width: 42px !important;
}
.switch {
  position: relative;
  display: inline-block;
  width: 42px;
  height: 26px;
}

.inline-element > * {
  display: inline-block !important;
}
.form-group {
  display: inline-flex;
  margin-bottom: 0;
}
#toggle-filtered {
  text-align: right;
}
label,
ul {
  margin-bottom: 0.5rem !important;
}
.bv-no-focus-ring {
  margin-left: 10px;
}
/* Hide default HTML checkbox */
.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

/* The slider */
.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  -webkit-transition: 0.4s;
  transition: 0.4s;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  -webkit-transition: 0.4s;
  transition: 0.4s;
}

input:checked + .slider {
  background-color: #007bff;
}

input:focus + .slider {
  box-shadow: 0 0 1px #007bff;
}

input:checked + .slider:before {
  -webkit-transform: translateX(16px);
  -ms-transform: translateX(16px);
  transform: translateX(16px);
}

/* Rounded sliders */
.slider.round {
  border-radius: 34px;
}

.slider.round:before {
  border-radius: 50%;
}
.filter-toggle {
  display: flex;
}
.filter-toggle-text {
  font-size: 0.875rem;
  line-height: 1.5;
  margin-left: 5px;
}
.rows-per-page {
  max-width: max-content !important;
}
</style>
