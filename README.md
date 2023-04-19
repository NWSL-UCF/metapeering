# Automated Peering
We use [*PeeringDB*](https://peeringdb.com/) and [*CAIDA*](https://www.caida.org/data/overview/) datasets to identify possible peering points for requester and candidate ISPs. We estimate candidate ISP's traffic matrix and consider ISPs' internal policies to generate a list of acceptable peering contracts. 

We have developed a simple web application, which can be accessed at [https://metapeering.net/](https://metapeering.net/), that allows ASes to select their desired Points of Presence (PoP) locations and analyze the possibility of peering with any other AS.

This repository contains the code files for peer selection algorithm, as well as the web application.

#### Note: DO NOT make this repository public before removing the web app code.

### Running and developing the app locally:
#### Step 1: Setting up a virtual python environment:
*Python version required: 3.x*<br>
1. Clone this repository, and open a terminal in the same folder.
2. To create a new virtual python environment `python3 venv metapeering`
3. To activate the created virtual environment, run `source metapeering/bin/activate`
4. To install all the dependencies, run `pip install -r requirements.txt`