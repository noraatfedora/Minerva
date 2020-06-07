A service for free groceries delivery during the coronavirus pandemic

https://minervagroceries.org/

## Setup

To install all required python packages, run `pip3 install -r requirements.txt`

Then, you'll need to set environment variables. Go to src and create a file called `set_environment_variables.sh`.
Using the `export` command, you'll need to set the variables EMAIL_PASSWORD and EMAIL_SENDER with your email auth, and GOOGLE_API with your Google Cloud API key.
Then, if you're using Sqlite (such as for development), set the environment variable `SQLITE_PATH` with the absolute path to your sqlite file. Otherwise, you'll need
to set the url of your sqlalchemy database by setting the variable `RDS_CONNECT`.