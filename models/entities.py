class User:
    def __init__(self, id, name, role):
        self.id = id
        self.name = name
        self.role = role

class InventoryItem:
    # Used by Inventory Controller
    def __init__(self, id, name, category, stock, cost_price, selling_price, threshold, expiry_date=None):
        self.id = id
        self.name = name
        self.category = category
        # Safety Casts: Ensure numbers are actually numbers
        self.stock = int(stock) if stock is not None else 0
        self.cost_price = float(cost_price) if cost_price is not None else 0.0
        self.selling_price = float(selling_price) if selling_price is not None else 0.0
        self.threshold = int(threshold) if threshold is not None else 0
        self.expiry_date = expiry_date

class Product:
    # Used by Cashier Controller
    def __init__(self, id, name, category, cost_price, selling_price, stock, threshold, expiry_date):
        self.id = id
        self.name = name
        self.category = category
        # Safety Casts
        self.cost_price = float(cost_price) if cost_price is not None else 0.0
        self.selling_price = float(selling_price) if selling_price is not None else 0.0
        self.stock = int(stock) if stock is not None else 0
        self.threshold = int(threshold) if threshold is not None else 0
        self.expiry_date = expiry_date

class DashboardStats:
    def __init__(self, revenue, low_stock_count, expiring_count):
        # FIX: The controller expects 'self.revenue', not 'self.daily_revenue'
        self.revenue = float(revenue) if revenue is not None else 0.0
        self.low_stock_count = int(low_stock_count) if low_stock_count is not None else 0
        self.expiring_count = int(expiring_count) if expiring_count is not None else 0