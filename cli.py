import requests

# Base URL of the API (you might need to update this according to your actual API deployment)
API_BASE_URL = "http://127.0.0.1:8000"

# Endpoint specific parameter requirements
param_requirements = {
    "/map": {"PUT": ["height", "width", "field"]},
    "/mines": {"POST": ["x", "y", "serial_number"]},
    "/mines/{mine_id}": {"PUT": ["x", "y", "serial_number"]},
    "/rovers": {"POST": ["commands"]},
    "/rovers/{rover_id}": {"PUT": ["commands"]},
}


# Helper function to make HTTP requests
def make_request(method, endpoint, data=None):
    url = API_BASE_URL + endpoint
    try:
        response = requests.request(method, url, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        return {"error": str(err)}
    except Exception as e:
        return {"error": "An unexpected error occurred"}


# Function to collect required data from the user
def collect_data(fields):
    data = {}
    for field in fields:
        data[field] = input(f"Enter value for {field}: ")
    return data


# CLI application
def run_cli():
    endpoints = {
        "/map": ["GET", "PUT"],
        "/mines": ["GET", "POST"],
        "/mines/{mine_id}": ["GET", "PUT", "DELETE"],
        "/rovers": ["GET", "POST"],
        "/rovers/{rover_id}": ["GET", "DELETE", "PUT"],
        "/rovers/{rover_id}/dispatch": ["POST"],
    }

    print("Available Endpoints:")
    for i, (endpoint, methods) in enumerate(endpoints.items(), start=1):
        print(f"{i}. {endpoint} - Methods: {', '.join(methods)}")

    selection = int(input("Select an endpoint by number: "))
    endpoint, methods = list(endpoints.items())[selection - 1]

    if "{mine_id}" in endpoint or "{rover_id}" in endpoint:
        param_id = input("Enter the required ID: ")
        endpoint = endpoint.replace("{mine_id}", param_id).replace(
            "{rover_id}", param_id
        )

    if len(methods) > 1:
        method = input(f"Select a method ({', '.join(methods)}): ").upper()
    else:
        method = methods[0]

    data = None
    if (
        method in ["POST", "PUT"]
        and endpoint in param_requirements
        and method in param_requirements[endpoint]
    ):
        data = collect_data(param_requirements[endpoint][method])

    response = make_request(method, endpoint, data=data)
    print("Response:")
    print(response)


if __name__ == "__main__":
    run_cli()
