from __init__ import create_app

app = create_app()

if __name__ == "__main__":
    # Bind explicitly to IPv4 localhost to avoid macOS AirPlay conflicts,
    # or change the port to an unused one (e.g., port=5001).
    app.run(host="127.0.0.1", port=5000, debug=True)