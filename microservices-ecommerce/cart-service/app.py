import os, sqlite3, requests
from flask import Flask, jsonify, request
app=Flask(__name__)
DB_PATH=os.environ.get("DB_PATH","/data/cart.db")
PRODUCT_URL=os.environ.get("PRODUCT_SERVICE_URL","http://product-service:5001")
def db():
    os.makedirs(os.path.dirname(DB_PATH),exist_ok=True)
    c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; return c
def init():
    with db() as c:
        c.execute("CREATE TABLE IF NOT EXISTS cart_items(product_id INTEGER PRIMARY KEY, quantity INTEGER NOT NULL CHECK(quantity > 0))")
def get_product(pid):
    try:
        r=requests.get(f"{PRODUCT_URL}/products/{pid}",timeout=4)
        return r.json() if r.status_code==200 else None
    except requests.RequestException: return None
@app.get("/cart")
def cart():
    with db() as c: rows=c.execute("SELECT product_id,quantity FROM cart_items ORDER BY product_id").fetchall()
    items=[]; total=0
    for row in rows:
        product=get_product(row["product_id"])
        if product:
            subtotal=product["price"]*row["quantity"]; total+=subtotal
            items.append({"product":product,"quantity":row["quantity"],"subtotal":subtotal})
    return jsonify({"items":items,"total":total})
@app.post("/cart")
def update():
    data=request.get_json(silent=True) or {}
    try: pid=int(data.get("product_id")); qty=int(data.get("quantity",1))
    except (TypeError,ValueError): return jsonify({"error":"Product and quantity must be numbers."}),400
    if qty<0 or qty>99: return jsonify({"error":"Quantity must be between 0 and 99."}),400
    product=get_product(pid)
    if not product: return jsonify({"error":"Product not found or product service unavailable."}),404
    with db() as c:
        row=c.execute("SELECT quantity FROM cart_items WHERE product_id=?",(pid,)).fetchone()
        if data.get("add") and qty>0: qty=(row["quantity"] if row else 0)+qty
        if qty>99: return jsonify({"error":"Maximum quantity per product is 99."}),400
        if qty==0: c.execute("DELETE FROM cart_items WHERE product_id=?",(pid,))
        else: c.execute("INSERT INTO cart_items(product_id,quantity) VALUES(?,?) ON CONFLICT(product_id) DO UPDATE SET quantity=excluded.quantity",(pid,qty))
    return cart()
@app.delete("/cart")
def clear():
    with db() as c: c.execute("DELETE FROM cart_items")
    return {"message":"Cart cleared."}
@app.get("/health")
def health(): return {"status":"ok","service":"cart-service"}
init()
if __name__=="__main__": app.run(host="0.0.0.0",port=5003)
