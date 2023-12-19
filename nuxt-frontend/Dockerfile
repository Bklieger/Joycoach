# Use an official Node runtime as a parent image
FROM node:16

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json (or yarn.lock if you use Yarn)
COPY package*.json ./

# Install dependencies
RUN npm install

# Bundle app source
COPY . .

# Build the app
RUN npm run build


# For Railway.app deployment, remove this line.
# Expose the port the app runs on
EXPOSE 3000

# Define the command to run the app
CMD [ "node", ".output/server/index.mjs" ]
# CMD [ "npm", "run","preview" ] # For logs when debugging
