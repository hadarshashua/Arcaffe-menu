from flask import Flask, json, request, abort
import requests
import time

api = Flask(__name__)
last_time_updated = int(time.time())
num_of_seconds_in_day = 24*3600

arcaffe_menu_url = "https://www.10bis.co.il/NextApi/GetRestaurantMenu?uiCulture=en&timestamp=" + str(last_time_updated) + "&restaurantId=19156"

@api.route('/drinks', methods=['GET'])
def get_drinks():
    return __get_all_category_products_details('Drinks')


@api.route('/drink/<drink_id>', methods=['GET'])
def get_drink_by_id(drink_id):
    return __get_category_product_details_by_id('Drinks', 'Drink', drink_id)


@api.route('/pizzas', methods=['GET'])
def get_pizzas():
    return __get_all_category_products_details('Pizzas')


@api.route('/pizza/<pizza_id>', methods=['GET'])
def get_pizza_by_id(pizza_id):
    return __get_category_product_details_by_id('Pizzas', 'Pizza', pizza_id)


@api.route('/desserts', methods=['GET'])
def get_desserts():
    return __get_all_category_products_details('Desserts')


@api.route('/dessert/<dessert_id>', methods=['GET'])
def get_dessert_by_id(dessert_id):
    return __get_category_product_details_by_id('Desserts', 'Dessert', dessert_id)


def __get_all_category_products_details(category_name):
    all_category_products = __get_all_category_products(category_name)
    products_details = []

    for product in all_category_products['dishList']:
        obj = {'id': product['dishId'], 'name': product['dishName'], 'price': product['dishPrice'], 'description': product['dishDescription']}
        products_details.append(obj)

    return json.dumps(products_details)


def __get_category_product_details_by_id(category_name, product_type, product_id):
    all_category_products = __get_all_category_products(category_name)
    products_details = next((x for x in all_category_products['dishList'] if str(x['dishId']) == product_id), None)

    if products_details is None:
        abort(500, {'message': product_type + ' with id ' + product_id + ' not found in the menu'})

    return json.dumps({'id': product_id, 'name': products_details['dishName'], 'price': products_details['dishPrice'], 'description': products_details['dishDescription']})


def __get_all_category_products(category_name):
    __validate_menu_updated()
    menu = requests.get(arcaffe_menu_url).json()
    all_category_products = next((x for x in menu['Data']['categoriesList'] if x['categoryName'] == category_name), None)

    if all_category_products is None:
        abort(404, {'message': category_name + ' category not found in menu'})

    return all_category_products


@api.route('/order', methods=['POST'])
def calculate_order_price():
    __validate_menu_updated()
    menu = requests.get(arcaffe_menu_url).json()
    total_order_sum = 0
    order_body = json.loads(request.data)

    if 'Drinks' in order_body:
        total_order_sum += __get_prices_sum_by_category(menu, 'Drinks', order_body['Drinks'])

    if 'Pizzas' in order_body:
        total_order_sum += __get_prices_sum_by_category(menu, 'Pizzas', order_body['Pizzas'])

    if 'Desserts' in order_body:
        total_order_sum += __get_prices_sum_by_category(menu, 'Desserts', order_body['Desserts'])

    return {'price': str(total_order_sum)}


def __get_prices_sum_by_category(menu, category_name, ids_list):
    chosen_category = next((x for x in menu['Data']['categoriesList'] if x['categoryName'] == category_name), None)

    if chosen_category is None:
        abort(404, {'message': 'Category ' + category_name + ' not found in the menu'})

    order_in_category_sum = 0

    for product_id in ids_list:
        product_details = next((x for x in chosen_category['dishList'] if str(x['dishId']) == str(product_id)), None)
        if product_details is not None:
            order_in_category_sum += product_details['dishPrice']

    return order_in_category_sum


def __validate_menu_updated():
    global last_time_updated
    global arcaffe_menu_url

    if int(time.time()) - last_time_updated > num_of_seconds_in_day:
        last_time_updated = int(time.time())
        arcaffe_menu_url = "https://www.10bis.co.il/NextApi/GetRestaurantMenu?uiCulture=en&timestamp=" + str(last_time_updated) + "&restaurantId=19156"

if __name__ == '__main__':
    api.run()
