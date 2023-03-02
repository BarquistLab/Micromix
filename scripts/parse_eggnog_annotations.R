#------------------------------------------
#
# Parse eggnong annotation file to .json files
# Intended for use with the webserver Micromix
# Regan Hayward 24-2-2023
#
#------------------------------------------

#Example to run
#./parse_eggnog_annotations.R annotations_file.tsv
# Should be a tab separated file


#Capture arguments
args = commandArgs(trailingOnly=TRUE)

#set the working directory to where the script is saved
setwd(system("pwd", intern = T) )

# test if there is at least one argument: if not, return an error
if (length(args)==0) {
  stop("At least one argument must be supplied (input file).n", call.=FALSE)
}


#------------------------------------------
#
# Install packages
#
#------------------------------------------



#BiocManager
if (!require("BiocManager", quietly = TRUE))
  install.packages("BiocManager")

#BiocManager::install("GO.db")
#BiocManager::install("KEGGREST")
#BiocManager::install("readr")
#BiocManager::install("splitstackshape")
#BiocManager::install("insight")
#BiocManager::install("jsonlite")

#load libraries
library(GO.db, quietly = T)
library(KEGGREST, quietly = T)
library(readr, quietly = T)
library(splitstackshape, quietly = T)
library(insight, quietly = T)
library(jsonlite, quietly = T)



#------------------------------------------
#
# load and process the eggnog annotation
#
#------------------------------------------


print_colour("\nStep: 1/6 - Loading annotation files and preparing \n", "white")
print_colour("...\n", "white")


#Load
#setwd("G:\\My Drive\\Science\\Hemholtz\\Micromix\\Example_annotation_and_code")
#setwd("/home/r/Desktop/test_eggnog")
#Process
#eggnog_full = read_delim("MM_upz4vuqy.emapper.annotations.tsv", skip = 4, delim = "\t", comment = "##")
eggnog_full = read_delim(args[1], skip = 4, delim = "\t", comment = "##", show_col_types = F)
#dim(eggnog_full)
#View(eggnog_full)


#--
#Get all KEGG IDs
#--
all_kegg_ids = cSplit(eggnog_full, sep = ",", direction = "long", splitCols = "KEGG_Pathway")
#remove duplicates
all_unique_kegg_ids = unique(all_kegg_ids$KEGG_Pathway)
#remove "-
all_unique_kegg_ids = all_unique_kegg_ids[all_unique_kegg_ids != c("-")]
#remove NA
all_unique_kegg_ids = all_unique_kegg_ids[!is.na(all_unique_kegg_ids)]
#all_unique_kegg_ids


#--
#Get all GO IDs
#--
all_go_ids = cSplit(eggnog_full, sep = ",", direction = "long", splitCols = "GOs")
#remove duplicates
all_unique_go_ids = unique(all_go_ids$GOs)
#remove "-
all_unique_go_ids = all_unique_go_ids[all_unique_go_ids != c("-")]
#remove NA
all_unique_go_ids = all_unique_go_ids[!is.na(all_unique_go_ids)]

print_colour("Step: 1/6 - Loading annotation files and preparing -- DONE \n", "green")




#------------------------------------------
#
# Link up ID with pathway
#
#------------------------------------------


#--
# GO ID to pathway
#--

print_colour("\nStep: 2/6 - Linking GO ids with pathways \n", "white")
print_colour("...\n", "white")



go_id_and_pathway = data.frame("go_id" = names(sapply(all_unique_go_ids, function(p) tryCatch(Term(as.character(p)), error=function(e) NA))),
                               "go_pathway" = unname(sapply(all_unique_go_ids, function(p) tryCatch(Term(as.character(p)), error=function(e) NA))))


#Tidy up the annotations

#remove everything after the . in the first column
go_id_and_pathway$go_id_v2 = gsub("\\..*","",go_id_and_pathway$go_id)
#replace NA with ""
#go_id_and_pathway[is.na(go_id_and_pathway)] <- ""
#removing rows with NAs
go_id_and_pathway = na.omit(go_id_and_pathway)

print_colour("Step: 2/6 - Linking GO ids with pathways -- DONE \n", "green")




#--
# KEGG ID to pathway
#--

print_colour("\nStep: 3/6 - Linking KEGG ids with pathways \n", "white")
print_colour("Note: This can take up to 5 mins to run \n", "red")
print_colour("...\n", "white")




#using try and catch to ignore when an ID does not have a corrosponding annotation
#Otherwise apply errors and doesn't finish
kegg_id_and_pathway = sapply(as.character(all_unique_kegg_ids), function(p) tryCatch(keggGet(p)[[1]]$NAME, error=function(e) NA))

#print(all_unique_kegg_ids)
#print("---")
#print(kegg_id_and_pathway)

#make as df
kegg_id_and_pathway_df = data.frame("name" = unname(kegg_id_and_pathway), 
                                    "id" = names(kegg_id_and_pathway))

#replace NA with ""
#kegg_id_and_pathway_df[is.na(kegg_id_and_pathway_df),] <- ""
kegg_id_and_pathway_df = na.omit(kegg_id_and_pathway_df)

print_colour("Step: 3/6 - Linking KEGG ids with pathways -- DONE \n", "green")



#------------------------------------------
#
# Format and save as .json
#
#------------------------------------------




#--
# pathways.json
#--

#create df's to be consistent
kegg_df = data.frame("id" = kegg_id_and_pathway_df$id, "name" = kegg_id_and_pathway_df$name)
go_df = data.frame("id" = go_id_and_pathway$go_id_v2, "name" = go_id_and_pathway$go_pathway)

#put into .json format
pathways_json = jsonlite::toJSON(list(kegg = kegg_df, go = go_df), pretty = T)


print_colour("\nStep: 4/6 - Saving pathways.json \n", "white")
print_colour("...\n", "white")


#save .json
write(pathways_json, "pathways.json")

print_colour("Step: 4/6 - Saving pathways.json -- DONE \n", "green")




print_colour("\nStep: 5/6 - Preparing gene_annotations.json \n", "white")
print_colour("...\n", "white")


#--
# gene_annotations.json
#--


#Shrink the full eggNOG annotation file to just keep cols of interest
eggnog_short = eggnog_full[,c(1,10,12)]
#replace "-" with nothing
eggnog_short[] <- lapply(eggnog_short, function(x) gsub("[-]", "", x))
#update col names 
colnames(eggnog_short) = c("ID","go_id","kegg_pathway_id")


#--
# Loop through all genes and link up the GO and KEGG ids/pathways
#--

#create empty list and assign gene names to each element
dim(eggnog_short)
j = as.list(1:dim(eggnog_short)[1])
names(j) = eggnog_short$ID

#loop through each of the genes, linking up the pathways
for (i in 1:dim(eggnog_short)[1]) {
  #get the kegg IDs associated with gene
  j[[i]] = as.list(data.frame("kegg_pathway_id" = eggnog_short[eggnog_short$ID == names(j[i]),"kegg_pathway_id"],
                              "go_id" = eggnog_short[eggnog_short$ID == names(j[i]),"go_id"]))
  
}

#convert to json
gene_annotations_json = jsonlite::toJSON(j, pretty = T, auto_unbox = F)


#Genes where there are no GO ids or KEGG ids by default are shown as [""].
#For error free parsing on the site, we change to []
gene_annotations_json = gsub('kegg_pathway_id": [\""]', 'kegg_pathway_id": []', gene_annotations_json, fixed = T)
gene_annotations_json = gsub('go_id": [\""]', 'go_id": []', gene_annotations_json, fixed = T)

print_colour("Step: 5/6 - Preparing gene_annotations.json -- DONE \n", "green")




print_colour("\nStep: 6/6 - Saving gene_annotations.json \n", "white")
print_colour("...\n", "white")

#save
write(gene_annotations_json, "gene_annotations.json")

print_colour("Step: 6/6 - Saving gene_annotations.json -- DONE \n", "green")




print_colour("\nScript finished.\n", "blue")
print_colour("---------------------------\n", "white")
print_colour("Two files have been created: \n", "white")
print_colour("1. gene_annotations.json \n", "white")
print_colour("2. pathways.json \n", "white")
print_colour("---------------------------\n", "white")




