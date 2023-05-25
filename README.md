# Automated Peering
We use [*PeeringDB*](https://peeringdb.com/) and [*CAIDA*](https://www.caida.org/data/overview/) datasets to identify possible peering points for requester and candidate ISPs. We estimate candidate ISP's traffic matrix and consider ISPs' internal policies to generate a list of acceptable peering contracts. 

We have developed a simple web application, which can be accessed at [https://metapeering.net/](https://metapeering.net/), that allows ASes to select their desired Points of Presence (PoP) locations and analyze the possibility of peering with any other AS.

This repository contains the code files for peer selection algorithm, as well as the web application.

#### Note: DO NOT make this repository public before removing the web app code.

### Running and developing the app locally:

## MAC Tutorial:
*Python version required: 3.x*<br>
1. Clone this repository, and open a terminal in the same folder.
2. To create a new virtual python environment `python3 venv metapeering`
3. To activate the created virtual environment, run `source metapeering/bin/activate`
4. To install all the dependencies, run `pip install -r requirements.txt`

## Windows Tutorial:
*Python version required: 3.x*<br>
1. Clone this repository, and open a terminal in the same folder.
2. To create a new virtual python environment `python -m venv metapeering`
3. Now cd into the virtual environment scripts folder `cd metapeering/scripts`
4. Run the script to activate using `activate`
5. Cd back `cd ../..`
6. **If you have run locally before:** Uninstall your site-packages using `pip uninstall -r requirements.txt`
7. Install packages using `pip install -r requirements.txt`
8. Now start the local server using `flask run`

If running on Windows, make sure to change the syntax of some commands in `app/routes/home.py` and `app/routes/custom.py`, specifically
the `mkdir` commands which work in MAC but not in Windows, they need to have backslashes. Revert these changes before pushing to the webserver.

Also, by default Flask does not have live updates, after making a change you will have to use **Ctrl+C** in Windows or **Command+C** in MAC to 
terminate the local server, and use `flask run` again to see the updated website.