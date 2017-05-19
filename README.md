# vimeo-channel-downloader
Python script that downloads all videos in a vimeo channel 


# Installation
Before running you need to install some python libraries
pip install requests bs4 vimeo_dl

# Usage
ptyhon vimeodl.py [-h] [-o SAVE_PATH] [-r] url

* -h help message
* -o video save directory if not specified then it saves to the current working directory
* -r resume from the last downloaded video if not used download all videos from start
* url a vimeo url
