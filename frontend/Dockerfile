FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application files
COPY . .

# Set dev environment variables
ENV NEXT_TELEMETRY_DISABLED 1

# Expose port and run dev server
EXPOSE 3000
CMD ["npm", "run", "dev"]
