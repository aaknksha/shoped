import os, sqlite3
from flask import Flask, jsonify
app = Flask(__name__)
DB_PATH = os.environ.get("DB_PATH", "/data/products.db")
SEED = [
 (1,"Classic White Sneakers","Footwear",1499,"Clean everyday sneakers for casual outfits.","👟"),
 (2,"Everyday Backpack","Accessories",899,"A lightweight backpack for college and travel.","🎒"),
 (3,"Minimal Wrist Watch","Accessories",1299,"A simple watch with a clean everyday look.","⌚"),
 (4,"Cotton Casual T-Shirt","Clothing",499,"A comfortable cotton tee for daily wear.","👕"),
 (5,"Wireless Headphones","Electronics",1799,"Enjoy music while studying or travelling.","🎧"),
 (6,"Steel Water Bottle","Lifestyle",349,"Reusable bottle for everyday hydration.","🧴")]
def db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; return c
def init():
    with db() as c:
        c.execute("CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY,name TEXT,category TEXT,price INTEGER,description TEXT,emoji TEXT)")
        if c.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            c.executemany("INSERT INTO products VALUES(?,?,?,?,?,?)",SEED)
@app.get("/products")
def products():
    with db() as c: rows=c.execute("SELECT * FROM products ORDER BY id").fetchall()
    return jsonify([dict(r) for r in rows])
@app.get("/products/<int:product_id>")
def product(product_id):
    with db() as c: row=c.execute("SELECT * FROM products WHERE id=?",(product_id,)).fetchone()
    return (jsonify(dict(row)),200) if row else (jsonify({"error":"Product not found."}),404)
@app.get("/health")
def health(): return {"status":"ok","service":"product-service"}
init()
if __name__=="__main__": app.run(host="0.0.0.0",port=5001)
