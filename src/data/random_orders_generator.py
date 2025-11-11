#!/usr/bin/env python3
import json
import random
from datetime import datetime, timedelta

def random_element(arr):
    return random.choice(arr)

def random_float(min_val, max_val, decimals=3):
    value = random.uniform(min_val, max_val)
    return round(value, decimals)

def random_int(min_val, max_val):
    return random.randint(min_val, max_val)

def random_date(start_date, end_date):
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date) if isinstance(end_date, str) else datetime.now()
    
    time_between = end - start
    random_days = random.randint(0, time_between.days)
    random_seconds = random.randint(0, 86400)
    
    random_date = start + timedelta(days=random_days, seconds=random_seconds)
    return random_date.date().isoformat()

def generate_orders(count=100):    
    # Product name components
    adjectives = [
        'Ergonomic', 'Rustic', 'Modern', 'Sleek', 'Premium', 'Handcrafted',
        'Refined', 'Elegant', 'Practical', 'Intelligent', 'Generic', 'Awesome',
        'Fantastic', 'Incredible', 'Licensed', 'Tasty', 'Unbranded', 'Small',
        'Gorgeous', 'Handmade'
    ]

    materials = [
        'Steel', 'Wooden', 'Cotton', 'Plastic', 'Granite', 'Rubber',
        'Metal', 'Soft', 'Fresh', 'Frozen', 'Concrete', 'Bronze'
    ]

    products = [
        'Chair', 'Table', 'Lamp', 'Keyboard', 'Mouse', 'Shirt', 'Pants',
        'Shoes', 'Hat', 'Gloves', 'Computer', 'Bike', 'Car', 'Pizza',
        'Salad', 'Chips', 'Soap', 'Towels', 'Ball', 'Bacon', 'Chicken',
        'Fish', 'Cheese', 'Tuna', 'Sausages'
    ]

    data = {"orders": []}

    for i in range(count):
        order = {
            "order_id": i + 1,
            "product_name": f"{random_element(adjectives)} {random_element(materials)} {random_element(products)}",
            "quantity": random_int(1, 100),
            "price": random_float(100, 2000, 2),
            "order_date": random_date('2000-01-01', datetime.now())
        }
        data["orders"].append(order)

    return data

if __name__ == "__main__":
    orders_data = generate_orders(100)
    
    with open("raw_orders.json", 'w') as f:
        json.dump(orders_data, f, indent=2)
    
    print(f"Generated {len(orders_data['orders'])} orders")
    print(f"Saved to raw_orders.json")