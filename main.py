from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
import generic_helper
import db_helper
app=FastAPI()




inprogress_orders={}

@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from the request
    payload = await request.json()

    # Extract the necessary information from the payload
    # based on the structure of the WebhookRequest from Dialogflow
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']
    session_id=generic_helper.extract_session_id(output_contexts[0]['name'])

    if intent =="track.order context-ongoing-tracking":
        return track_order(parameters)
    elif intent =="neworder.add":
        return add_to_order(parameters,session_id)
    elif intent =="order.complete":
        return complete_order(parameters,session_id)
    elif intent =="order.remove":
        return remove_from_order(parameters, session_id)


def add_to_order(parameters: dict,session_id:str):
    book_names=parameters['book-names']
    quantities=parameters['number']

    if not quantities:
        fulfillment_text = "Sorry, I didn't understand. Please specify the number of books you want."
    elif len(book_names) != len(quantities):
        fulfillment_text = "Sorry, I didn't understand. Please specify Book Names and Quantity clearly."
    else:
        new_book_dict=dict(zip(book_names,quantities))
        if session_id in inprogress_orders:
            current_book_dict=inprogress_orders[session_id]
            current_book_dict.update(new_book_dict)
        else:
            inprogress_orders[session_id]=new_book_dict

        order_str=generic_helper.get_str_from_book_dict(inprogress_orders[session_id])

        fulfillment_text = f"So far you have: {order_str}. Do you want anything else"

    return JSONResponse(content={"fulfillmentText": fulfillment_text})


def complete_order(parameters: dict,session_id: str):
    if session_id not in inprogress_orders:
        fulfillment_text="I'm having a trouble placing your order. Sorry! Can you palce a new order again"
    else:
        order=inprogress_orders[session_id]
        order_id=save_to_db(order)

        if order_id == -1:
            fulfillment_text="Sorry, I couldn't process your order due to a backend error."\
            "Please place a new order again"
        else:
            order_total=db_helper.get_total_order_price(order_id)
            fulfillment_text=f"Awesome. We have Placed your order."\
                            f"Here is your order id # {order_id}."\
                            f"Your order total is ₹ {order_total} which you can pay at the time of delivery"
        del inprogress_orders[session_id]
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

def remove_from_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "I'm having a trouble finding your order. Sorry! Can you place a new order please?"
        })
    
    book_names = parameters["book-names"]
    current_order = inprogress_orders[session_id]

    removed_items = []
    no_such_items = []

    for item in book_names:
        if item not in current_order:
            no_such_items.append(item)
        else:
            removed_items.append(item)
            del current_order[item]

    if len(removed_items) > 0:
        fulfillment_text = f'Removed {",".join(removed_items)} from your order!'

    if len(no_such_items) > 0:
        fulfillment_text = f' Your current order does not have {",".join(no_such_items)} '

    if len(current_order.keys()) == 0:
        fulfillment_text += " Your order is empty!"
    else:
        order_str = generic_helper.get_str_from_book_dict(current_order)
        fulfillment_text += f" Here is what is left in your order: {order_str}"

    fulfillment_text += ". Do you want to add more items or complete the order?"
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


def save_to_db(order: dict):

    next_order_id=db_helper.get_next_order_id()
    for book_names,quantity in order.items():
        rcode=db_helper.insert_order_item(
            book_names,
            quantity,
            next_order_id
        )
        if rcode == -1:
            return -1
        
    db_helper.insert_order_tracking(next_order_id, "in progress")

    return next_order_id



def track_order(parameters: dict):
    if 'number' in parameters:
        order_id = int(parameters['number'])
        status = db_helper.get_order_status(order_id)
        if status:
            fulfillment_text = f"The order status for order id # {order_id} is: {status}"
        else:
            fulfillment_text = f"No order found with order id : # {order_id}"
    else:
        fulfillment_text = "No order id provided"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })



def track_order(parameters: dict):
    if 'number' in parameters:
        order_id = int(parameters['number'])
        status = db_helper.get_order_status(order_id)
        if status:
            fulfillment_text = f"The order status for order id # {order_id} is: {status}"
        else:
            fulfillment_text = f"No order found with order id : # {order_id}"
    else:
        fulfillment_text = "No order id provided"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })
