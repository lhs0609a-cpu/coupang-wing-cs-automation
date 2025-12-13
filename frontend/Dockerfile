FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application
COPY . .

# Expose port
EXPOSE 5173

# Run application
CMD ["npm", "run", "dev", "--", "--host"]
