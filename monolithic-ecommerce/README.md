# ShopEase Monolithic

A single Flask application handles the storefront APIs, product catalogue, session cart, checkout and order history. SQLite data is persisted in a Docker volume.

Start with `docker compose up --build` and visit http://localhost:5001.
Use `docker compose ps` to show the running container. Check `http://localhost:5001/api/products` for a sample API response.
