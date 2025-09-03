from flask import Flask, render_template
import requests
import json

app = Flask(__name__)

# Sample car data (in a real app this would come from a database)
cars = [
    {
        "id": 1,
        "make": "Toyota",
        "model": "Camry",
        "year": 2022,
        "price": 25000,
        "mileage": 15000,
        "image_url": "https://images.unsplash.com/photo-1494976387441-4e3319f0a1d5?auto=format&fit=crop&w=600",
        "description": "Reliable and fuel-efficient family sedan with modern features."
    },
    {
        "id": 2,
        "make": "Honda",
        "model": "Civic",
        "year": 2021,
        "price": 22000,
        "mileage": 20000,
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600",
        "description": "Compact and stylish car perfect for city driving."
    },
    {
        "id": 3,
        "make": "Ford",
        "model": "F-150",
        "year": 2023,
        "price": 35000,
        "mileage": 8000,
        "image_url": "https://images.unsplash.com/photo-1542362567-b07e54358753?auto=format&fit=crop&w=600",
        "description": "Powerful pickup truck with advanced towing capabilities."
    },
    {
        "id": 4,
        "make": "BMW",
        "model": "X5",
        "year": 2022,
        "price": 55000,
        "mileage": 12000,
        "image_url": "https://images.unsplash.com/photo-1553877522-43269d4ea984?auto=format&fit=crop&w=600",
        "description": "Luxury SUV with premium features and exceptional performance."
    },
    {
        "id": 5,
        "make": "Tesla",
        "model": "Model 3",
        "year": 2023,
        "price": 40000,
        "mileage": 5000,
        "image_url": "https://images.unsplash.com/photo-1617840009153-10c8a1d03d1e?auto=format&fit=crop&w=600",
        "description": "Electric sedan with cutting-edge technology and zero emissions."
    },
    {
        "id": 6,
        "make": "Chevrolet",
        "model": "Silverado",
        "year": 2021,
        "price": 38000,
        "mileage": 18000,
        "image_url": "https://images.unsplash.com/photo-1549399599-87d7a559b6e0?auto=format&fit=crop&w=600",
        "description": "Versatile pickup truck with excellent cargo capacity."
    }
]

@app.route('/')
def index():
    return render_template('index.html', cars=cars)

if __name__ == '__main__':
    app.run(debug=True)