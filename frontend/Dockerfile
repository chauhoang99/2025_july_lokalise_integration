FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copy project files
COPY . .

# Expose port
EXPOSE 3000

# Start development server with host binding
CMD ["npm", "run", "dev", "--", "--host"]
