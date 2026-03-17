# Image Node légère
FROM node:20-alpine

# Dossier de travail
WORKDIR /app

# Copie des fichiers de dépendances d'abord (cache Docker)
COPY package.json package-lock.json ./

# Installation des dépendances
RUN npm install

# Copie du code source
COPY . .

# Port du dev server Vite
EXPOSE 5173

# Lancement du dev server accessible depuis l'extérieur du container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
