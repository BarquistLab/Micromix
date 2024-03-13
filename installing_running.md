# Micromix user guide

## Contents
- [Micromix](README.md#micromix-user-guide)
- [Installing and running](installing_running.md##installing-and-running-micromix)
    - [Install options](installing_running.md#installing-and-running-micromix)
        - [Virtual machine](installing_running.md#1-using-a-pre-built-virtual-machine)
        - [Containers](installing_running.md#2-using-docker-containers)
        - [Manual install](installing_running.md#3-manually-installing-micromix)
    - [Server deployment](installing_running.md#server-deployment)
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


# Installing and running Micromix

There are three options to use Micromix, depending on the user requirements.

1) Using a pre-built virtual machine
2) Using Docker containers
3) Manually installing Micromix

## 1. Using a pre-built virtual machine

The simplest way to use Micromix is to use our pre-built virtual machine (VM). This is available for download **INSERT HYPERLINK**.

The image was created using VirtualBox (version 6.1), free software that can be run on all operating systems, and can be downloaded [here](https://www.virtualbox.org/wiki/Download_Old_Builds_6_1).

To create the VM: within VirtualBox, click on **New**, then select **Expert mode**. Choose **use an existing virtual hard disk file** and select the downloaded Micromix VM. Make sure the operating system is set to **Linux - Ubuntu - 64bit**, and adjust the memory to a desired size (we recommend about 4GB). Then click on **Create**. 

Once created, we also recommend going into **Settings >> System >> Processor** and changing to 2 or greater, which makes Micromix run smoother. 

To run the VM, click on **Start** (the green arrow). Once running, you will need to start the website and the heatmap.

```bash
#On the desktop are two files, you will need to run both

#To start the website
#open a terminal (right click - 'Open in terminal')
./run_website.sh 

#To start the heatmap - open another terminal
./run_heatmap.sh

```

The site can be accessed by opening the browser and typing **localhost:8080**

<img width="80%" src="images/micromix_running.png" />


> **Note:** This VM was created in development mode and should mainly be used for exploration and testing. If you want to run Micromix on a server that you can share with other users, you should use option 2 or 3 below.  

## 2. Using Docker containers

Docker is a platform that automates the deployment of applications inside lightweight, portable containers. These containers package up the application, along with its environment and dependencies, ensuring consistency across different environments. 

The following steps assume the following:
 - You have access to a debian-based Linux 64bit machine
 - You have sudo (admin) access

We have created Micromix so it can be installed and run with Docker. To prepare the machine for Micromix to work properly, we will need to install various software.


1. Install MongoDB (we install this locally so sessions are not lost if the containers need to be restarted)

```bash
#Install MongoDB
sudo apt install -y mongodb

#Confirm it is running
sudo systemctl status mongodb

#if not, then start with
sudo systemctl start mongodb

#We also need to add in an additional IP address that allows Docker to communicate with this local installation of MongoDB
sudo vim /etc/mongodb.conf

#you will need to add in 172.17.0.1 so the bind_ip address has two values
bind_ip = 127.0.0.1,172.17.0.1 

#Restart mongoDB
sudo systemctl restart mongodb
```


2. Install Docker: The latest instructions can be found [here](https://docs.docker.com/engine/install/ubuntu/)

```bash
#Uninstall old versions or conflicting packages
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done

# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

3. Download Micromix from Github
```bash
git clone https://github.com/BarquistLab/Micromix.git
```

4. Run Micromix
```bash
#browse to the correct directory
cd Micromix/Website

#Run docker compose
#This is llined to two dockerfiles, one for the backend and one for the frontend
sudo docker compose build 
sudo docker compose up

#If you require that the containers run in the background, you can use
docker compose up --detach

#These two commands may take some time to complete
#Once the containers have completed running, you should see this line from the command line (or something similar)
* Running on http://127.0.0.1:5000 

#Browse to this address in your browser, and Micromix will be running

#To stop the containers - first press 'ctrl + C', then
docker compose down

#To also remove the associated volumes (-v) and images (-)
docker compose down --volumes --rmi

```

??????HEATMAP???????

> **Note:** Following these commands will allow you to run Micromix on any compatable computer. If you would like to setup a Micromix server that can be publically viewed through the internet, see [Server deployment](installing_running.md#server-deployment).



## 3. Manually installing Micromix

need to install website first, then heatmap - useful for developers

### **Website**
There are a number of requirements if running locally or on a server for the first time. 

**Step 1:** Download the git repository: 
```bash
#install Git
sudo apt-get install git

#Download micromix files from GitHub
git clone https://github.com/reganhayward/btheta_site.git
```  

**Step 2:** Install required software and run:


**MongoDB:**

As previously discussed, the site stores the underlying data and user session data within MongoDB, and needs to be running in the background.

```bash
#Install MongoDB
sudo apt install -y mongodb

#Confirm it is running
sudo systemctl status mongodb

#if not, then start with
sudo systemctl start mongodb
```

<img width="80%" src="images/mongodb_running.png" />


**The website backend:**

```bash
sudo apt update
sudo apt install python3-pip
pip3 install wheel
pip3 install biopython

#to allow virtual env (check python version first)
sudo apt-get install python3.8-venv 

#change to backend
cd Micromix/Website/backend

#create python virtual environment
python3 -m venv venv
#Enter the environment
source venv/bin/activate

#install the required python libraries
pip3 install -r requirements.txt

#enable debugging (optional)
export FLASK_DEBUG=1

#Launch Flask server
flask run --port 3000

#you should see the following output
```

<img width="80%" src="images/website_backend_running.png" />


**The website frontend:**
```bash
#Change to the frontend
cd Micromix/Website/frontend

#Make sure dependencies are already installed
sudo apt-get install gcc g++ make
sudo apt-get install libssl-dev libcurl4-openssl-dev

#Download and install Node.js
sudo apt install curl
curl -sL https://deb.nodesource.com/setup_18.x -o nodejs_setup.sh
#change permissions
sudo chmod 777 nodejs_setup.sh
#run
sudo ./nodejs_setup.sh
#install
sudo apt-get install -y nodejs

#Install vue-cli with Node Package Manager (npm)
sudo npm install -g @vue/cli

#install Eslint and axios
npm install --save-dev eslint eslint-plugin-vue
npm i axios

#initialise ESLint
./node_modules/.bin/eslint --init

#Use these responses
✔ How would you like to use ESLint? · "To check syntax and find problems"
✔ What type of modules does your project use? · "syntax and markup" #default option
✔ Which framework does your project use? · "vue"
✔ Does your project use TypeScript? · "No"
✔ Where does your code run? · "browser"
✔ What format do you want your config file to be in? · "JavaScript"
The config that youve selected requires the following dependencies:

eslint-plugin-vue@latest
✔ Would you like to install them now with npm? · "Yes"
Installing eslint-plugin-vue@latest

#This creates a file called .eslintrc.js

#You will need to modify this file in 2 places
#1) Comment out the line below to avoid an error about process not being defined (or similar)

vim .eslintrc.js

    "extends": [
        //"eslint:recommended",  //comment this line
        "plugin:vue/essential"

#2) Add a rule to allow multi-word component names
"rules": {
        'vue/multi-word-component-names': 'off',
    }

#Finally, we can install node dependencies
npm install

#Launch frontend
npm run serve

#you should see the following output
```
> Open the address shown in the terminal where you executed the line above with your web browser. This should be http://localhost:8080/. The backend should also be running, otherwise the site will not load.

<img width="80%" src="images/website_frontend_running.png" />


> At this point, the site will be functional and users can browse datasets, apply filters and use available plugins, apart from the Heatmap - which requires further installation.

<img width="80%" src="images/micromix_running.png" />


### **Heatmap**
There are a number of requirements if running locally or on a server for the first time. The heatmap follows the same infrastructure that the main site does: there is a frontend and backend, which then communicate through a specified port where the resulting heatmap can be displayed within the site when clicking on the heatmap button.

> Note: <br> Before running the heatmap, there should already be two terminals open. These will be the website backend (terminal) and the website frontend (terminal). The heatmap will require two additional terminals to be open for the respective frontend and backend. 


**Step 1:** Prepare the heatmap backend: 
```bash 
#Browse to the backend
cd Micromix/Heatmap/backend

#create an additional python virtual environment
python3 -m venv venv2
#Enter the environment
source venv2/bin/activate

#install the required python libraries
pip3 install -r requirements.txt

#enable debugging (optional)
export FLASK_DEBUG=1

#Launch Flask server
flask run

#you should see the following output
```

<img width="80%" src="images/heatmap_backend_running.png" />


**Step 1:** Prepare the heatmap frontend: 
```bash
#Change to the frontend
cd Micromix/Heatmap/frontend

#Install node dependencies
npm install

#Launch frontend
npm run serve

#you should see the following output
```

<img width="80%" src="images/heatmap_frontend_running.png" />

> You should now be able to browse the site by selecting a dataset then using the heatmap visualisation plugin



# Server deployment

To make Micromix accessable through the internet, you will need to have access to a running online server that is capable of publically displaying websites with an IP address.

If you don't have any institute or department hosting services available, you can create and run a virtual machine from different web services, such as Amazon Web Services (AWS) or Google Cloud. An AWS tutorial can be viewed [here](https://aws.amazon.com/getting-started/launch-a-virtual-machine-B-0/), and with Google Cloud [here](https://cloud.google.com/compute/docs/create-linux-vm-instance). If choosing this option, you will need to use a Debian-based Linux distribution (64bit). In addition, when launching the VM, ensure that it assigned a public IP address. You will need to remember this for later steps.

Once you have access to a running server, you will need to download and install various software.

The following steps 1-3 are identical to [Containers](installing_running.md#2-using-docker-containers) - and can be skipped if already completed.

1. Install MongoDB (we install this locally so sessions are not lost if the containers need to be restarted)

```bash
#Install MongoDB
sudo apt install -y mongodb

#Confirm it is running
sudo systemctl status mongodb

#if not, then start with
sudo systemctl start mongodb

#We also need to add in an additional IP address that allows Docker to communicate with this local installation of MongoDB
sudo vim /etc/mongodb.conf

#you will need to add in 172.17.0.1 so the bind_ip address has two values
bind_ip = 127.0.0.1,172.17.0.1 

#Restart mongoDB
sudo systemctl restart mongodb
```

2. Install Docker. The latest instructions can be found [here](https://docs.docker.com/engine/install/ubuntu/)

```bash
#Uninstall old versions or conflicting packages
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done

# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```


3. Download Micromix from Github
```bash
git clone https://github.com/BarquistLab/Micromix.git
```


**will need to modify the docker compose file slightly??**

**how to install and configure NGINX + Gunicorn**


will also need to change the IP address to the one that the server has


To run Micromix, 

**To be completed**

To run the heatmap

**To be completed**
