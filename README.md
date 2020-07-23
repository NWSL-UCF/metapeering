# Automated Peering
We use [*PeeringDB*](https://peeringdb.com/) and [*CAIDA*](https://www.caida.org/data/overview/) datasets to identify possible peering points for requester and candidate ISPs. We estimate candidate ISP's traffic matrix and consider ISPs' internal policies to generate a list of acceptable peering contracts. 

We have developed a simple web application, whcih can be accessed at [www.metapeering.online](www.metapeering.online), that allows ASes to select their desired Points of Presence (PoP) locations and analyze the possibility of peering with any other AS.

This repository contains the code files for peer selection algorithm, as well as the web application.

#### Note: DO NOT make this repository public before removing the web app code.

### Running and developing the app locally:
#### Step 1: Setting up a virtual python environment:
*Python version required: 3.x*<br>
1. Clone this repository, and open a terminal in the same folder.
2. To create a new virtual python enviroment `python3 venv metapeering`
3. To activate the created virtual environment, run `source metapeering/bin/activate`
4. To install all the dependencies, run `pip install -r requirements.txt`

#### Step 2: Setting up Heroku:
Pre-requisites: [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) and [First-time Git setup](https://git-scm.com/book/en/v2/Getting-Started-First-Time-Git-Setup), [Heroku](https://www.heroku.com/) account <br>

1. Installing Heroku CLI:<br>
    **macOS:** `brew install heroku/brew/heroku` or download the [installer](https://cli-assets.heroku.com/heroku.pkg) <br>
    **Ubuntu 16+:** `sudo snap install heroku --classic` <br>
    **Windows:** Download the [32-bit installer](https://cli-assets.heroku.com/heroku-x86.exe) or the [64-bit installer](https://cli-assets.heroku.com/heroku-x64.exe)

2. Log into heroku CLI: <br>
    `heroku login`<br>
    Press any key to open up the browser to login or q to exit<br>
    Warning: If browser does not open, visit [https://cli-auth.heroku.com/auth/browser/](https://cli-auth.heroku.com/auth/browser/)
    
3. Create heroku app: <br>
`heroku git:remote -a agile-shore-98268`

4. Run heroku app locally:<br>
*** Note: Because of the current timeout issue, run `python3 wsgi.py` from project root irectory instead of the next line.***
`heroku local`

5. (Optional) Deploy any changes to the website: <br>
Add files: `git add .` <br>
Commit changes: `git commit -m <commit message>` <br>
Push Changes to Heroku: `git push heroku master`

6. (Optional) View heroku logs: <br>
`heroku logs --tail`
