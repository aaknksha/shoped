import os, sqlite3, json
from datetime import datetime
from flask import Flask, jsonify, request
import requests
app=Flask(__name__)
DB_PATH=os.environ.get("DB_PATH","/data/orders.db")
CART_URL=os.environ.get("CART_SERVICE_URL","http://cart-service:5003")
def db():
    os.makedirs(os.path.dirname(DB_PATH),exist_ok=True)
    c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; return c
def init():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT NOT NULL, items_json TEXT NOT NULL, total INTEGER NOT NULL, created_at TEXT NOT NULL)""")
@app.post("/checkout")
def checkout():
    data=request.get_json(silent=True) or {}
    name=str(data.get("customer_name","")).strip()
    if not name: return jsonify({"error":"Please enter your name."}),400
    try:
        response=requests.get(f"{CART_URL}/cart",timeout=5)
        response.raise_for_status()
        cart=response.json()
    except requests.RequestException:
        return jsonify({"error":"Cart service is unavailable."}),503
    if not cart.get("items"): return jsonify({"error":"Your cart is empty."}),400
    items=[{"name":i["product"]["name"],"quantity":i["quantity"],"subtotal":i["subtotal"]} for i in cart["items"]]
    total=int(cart["total"])
    with db() as c:
        cursor=c.execute("INSERT INTO orders(customer_name,items_json,total,created_at) VALUES(?,?,?,?)",
                         (name,json.dumps(items),total,datetime.now().isoformat(timespec="seconds")))
        order_id=cursor.lastrowid
    try: requests.delete(f"{CART_URL}/cart",timeout=4)
    except requests.RequestException: pass
    return jsonify({"message":"Order placed successfully!","order_id":order_id,"total":total}),201
@app.get("/orders")
def orders():
    with db() as c: rows=c.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 20").fetchall()
    return jsonify([{"id":r["id"],"customer_name":r["customer_name"],"items":json.loads(r["items_json"]),
                     "total":r["total"],"created_at":r["created_at"]} for r in rows])
@app.get("/health")
def health(): return {"status":"ok","service":"order-service"}
init()
if __name__=="__main__": app.run(host="0.0.0.0",port=5004)
