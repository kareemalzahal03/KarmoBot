# For more info: https://github.com/lichess-bot-devs/lichess-bot
FROM lichessbotdevs/lichess-bot:latest

# Move bot configuration files
COPY ./lichess /lichess-bot/config/

# Copy the project into the container
COPY ./ /lichess-bot/

# Install g++ and make for building CPP components
RUN apt-get update && apt-get install -y g++ make

# Install KarmoBot as a python package
RUN python3 -m pip install --no-cache-dir -e .
