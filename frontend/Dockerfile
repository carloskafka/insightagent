FROM node:18-alpine

WORKDIR /app

# Copia package.json para instalar dependências
COPY package*.json ./

RUN npm install

# Copia todo o código fonte (o contexto já é a pasta frontend)
COPY . .

# Gera o build de produção
RUN npm run build

# Instala servidor estático
RUN npm install -g serve

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
