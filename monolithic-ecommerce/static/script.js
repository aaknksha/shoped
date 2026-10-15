const money = value => "₹" + Number(value).toLocaleString("en-IN");
const notice = (message, error = false) => {
  const el = document.getElementById("notice");
  el.textContent = message;
  el.className = error ? "error" : "";
};
async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: {"Content-Type": "application/json"},
    ...options
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}
async function loadProducts() {
  const products = await api("/api/products");
  document.getElementById("productGrid").innerHTML = products.map((p, i) => `
    <article class="product-card">
      <div class="product-art"><span class="number">0${i + 1} / SHOP EASE</span>${p.emoji}</div>
      <div class="product-meta">
        <span class="product-category">${p.category}</span>
        <h3>${p.name}</h3><p>${p.description}</p>
        <div class="product-bottom"><span class="price">${money(p.price)}</span>
        <button class="add-button" data-add="${p.id}">+ Add to bag</button></div>
      </div>
    </article>`).join("");
  document.querySelectorAll("[data-add]").forEach(button => button.addEventListener("click", async () => {
    try {
      const cart = await api("/api/cart", {method:"POST", body:JSON.stringify({product_id:Number(button.dataset.add), quantity:1, add:true})});
      await loadCart();
      notice("Added to your bag.");
    } catch (error) { notice(error.message, true); }
  }));
}
async function loadCart() {
  const cart = await api("/api/cart");
  document.getElementById("cartCount").textContent = cart.items.reduce((n, item) => n + item.quantity, 0);
  document.getElementById("cartTotal").textContent = money(cart.total);
  const target = document.getElementById("cartItems");
  if (!cart.items.length) {
    target.innerHTML = '<p class="muted">Your bag is waiting for something good.</p>';
    return;
  }
  target.innerHTML = cart.items.map(item => `
    <div class="cart-item"><span class="cart-emoji">${item.product.emoji}</span>
    <div class="cart-info"><strong>${item.product.name}</strong><small>${money(item.product.price)} each · ${money(item.subtotal)}</small></div>
    <div class="quantity-controls"><button data-change="${item.product.id}" data-quantity="${item.quantity - 1}" aria-label="Decrease quantity">−</button><span>${item.quantity}</span><button data-change="${item.product.id}" data-quantity="${item.quantity + 1}" aria-label="Increase quantity">+</button></div></div>`).join("");
  target.querySelectorAll("[data-change]").forEach(button => button.addEventListener("click", async () => {
    try {
      await api("/api/cart", {method:"POST", body:JSON.stringify({product_id:Number(button.dataset.change), quantity:Number(button.dataset.quantity), add:false})});
      await loadCart();
    } catch (error) { notice(error.message, true); }
  }));
}
document.getElementById("checkoutButton").addEventListener("click", async () => {
  const customer_name = document.getElementById("customerName").value.trim();
  try {
    const result = await api("/api/checkout", {method:"POST", body:JSON.stringify({customer_name})});
    notice(`${result.message} Order #${result.order_id} · Total ${money(result.total)}`);
    await loadCart();
    await loadOrders();
  } catch (error) { notice(error.message, true); }
});
async function loadOrders() {
  const orders = await api("/api/orders");
  const target = document.getElementById("ordersList");
  target.innerHTML = orders.length ? orders.map(order => `
    <div class="order-row"><span><strong>Order #${order.id}</strong> · ${order.customer_name}<br><span class="muted">${order.created_at}</span></span><strong>${money(order.total)}</strong></div>`).join("") : '<p class="muted">No orders yet. Your first order will appear here.</p>';
}
document.getElementById("refreshOrders").addEventListener("click", loadOrders);
document.getElementById("cartJump").addEventListener("click", () => document.getElementById("cart").scrollIntoView({behavior:"smooth"}));
loadProducts().then(loadCart).then(loadOrders).catch(error => notice(error.message, true));
