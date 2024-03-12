# Micromix user guide

## Contents
- [Micromix](README.md#micromix-user-guide)
- [Installing and running](installing_running.md#micromix-user-guide)
    - [Install options](installing_running.md#1-using-pre-built-aws-container)
        - [Virtual machine](installing_running.md#website)
        - [Containers](installing_running.md#website)
        - [Manual install](installing_running.md#heatmap)
    - [Server deployment](installing_running.md#1-using-pre-built-aws-container)
- [Using Micromix](using_micromix.md#micromix-user-guide)
    - [Selecting organism](using_micromix.md#selecting-organism)
    - [Selecting datasets](using_micromix.md#selecting-datasets)
    - [Combining datasets](using_micromix.md#combining-datasets)
    - [Filtering data](using_micromix.md#filtering-data)
    - [Visualising data](using_micromix.md#visualising-data)  
- [Modifying Micromix](modifying_micromix.md#micromix-user-guide)
    - [Preparing a new bacteria](modifying_micromix.md#preparing-a-new-bacteria)
    - [How to add a new organism](modifying_micromix.md#how-to-add-a-new-organism)
    - [How to add new expression data](modifying_micromix.md#how-to-add-new-expression-data)
    - [Modifying or adding gene or pathway annotations](modifying_micromix.md#modifying-or-adding-gene-or-pathway-annotations)
    - [Adding new visualisation plugins](modifying_micromix.md#adding-new-visualisation-plugins)
    - [Database maintenance](modifying_micromix.md#database-maintenance)


<br><br>


# Micromix

## Background
Micromix was designed as a visualisation platform to easily view next generation sequencing data, such as counts from RNA-seq. Its main focus is for use with prokaryotic data, such as bacteria, which comes pre-bundled. Different bacteria can be included where the associated data can be filtered and/or transformed, then passed through a visualisation tool to examine biological patterns further, such as a heatmap.


## Infrastructure
The site contains a backend (Flask) and frontend (Vue.js) that communicate with each other, saving data from each session using MongoDB. Plugins within the site are typically setup on separate servers with data being passed and a visualisation returned and displayed within the site.
Since each user session is stored with a unique ID, session information can be re-loaded by passing the unique ID into the URL. For example: [http://micromix.helmholtz-hiri.de/bacteroides/?config=652d4077f7670759f17ae4ba](http://micromix.helmholtz-hiri.de/bacteroides/?config=652d4077f7670759f17ae4ba). These types of links can also be shared to collaborators so they can examine specific data patterns from data within the site, or unique user data they have manually uploaded.

<br>
<br>

<img width="80%" src="images/micromix_inf.png" />

