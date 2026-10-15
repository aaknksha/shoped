# ShopEase Microservices

Four application containers:
- Gateway: host port 5002; the only exposed entry point.
- Product service: product catalogue and its SQLite database.
- Cart service: cart state and its SQLite database.
- Order service: checkout and order history in its SQLite database.

Start with `docker compose up --build` and visit http://localhost:5002.
Use `docker compose ps` to show containers. Check `http://localhost:5002/api/products` for a sample API response.
