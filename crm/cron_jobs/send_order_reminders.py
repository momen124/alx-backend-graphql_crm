from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime, timedelta

# Define transport
transport = RequestsHTTPTransport(
    url="http://localhost:8000/graphql",
    verify=False,
    retries=3,
)

client = Client(transport=transport, fetch_schema_from_transport=True)

# Create the query
one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
query = gql(f"""
{{
  orders(orderDate_Gte: "{one_week_ago}") {{
    id
    customer {{
      email
    }}
  }}
}}
""")

# Execute and log results
try:
    result = client.execute(query)
    orders = result.get("orders", [])

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("/tmp/order_reminders_log.txt", "a") as log:
        for order in orders:
            log.write(f"{now} - Order ID: {order['id']}, Email: {order['customer']['email']}\n")
    print("Order reminders processed!")
except Exception as e:
    print("Error:", e)