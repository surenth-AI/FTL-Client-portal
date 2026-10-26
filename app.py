from app import app, create_app

if app is None:
    app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)
