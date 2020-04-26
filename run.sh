# Little helper script that sets up flask environment variables and runs.
# Only works when you're in the Minerva dir.
#!/bin/bash
export FLASK_APP=src
export FLASK_ENV=development
FLASK_DEBUG=1 flask run
