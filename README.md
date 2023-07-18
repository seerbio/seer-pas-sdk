# Seer Python SDK
This is the Python SDK for Seer. It is currently in development and is not ready for production use.

## Guide
The `walkthrough.html` file is the one-stop-shop for this package and contains all the instructions for using the SDK. You can open it in your browser to view the instructions. Simply dragging the file into your browser should work.

## Prerequisites
* Make sure you have an instance of the backend running on `localhost:3006`. 

* Currently the SDK is built against pas-dev, so you'll need to have that running. You can find instructions for setting up pas-dev <a href="http://gitlab.seerbio-dev/ylou/backend">here</a>. You might need to enable OpenVPN to open this link.

## Installation
Here's a multi-step guide to use the Seer Python SDK. It's recommended that you follow the steps in order.

* Run `pip3 install -r requirements.txt` to install all dependencies for this project.

* The `demo.py` file contains a demo of the SDK with an instance created with the pas-dev sample username and password. It is intended to be run in Python's native interactive mode after all dependencies are installed. You can run it by typing `python3 -i demo.py` in the terminal. 