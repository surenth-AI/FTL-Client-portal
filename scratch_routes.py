from app import create_app
import json

app = create_app()

routes = []
for rule in app.url_map.iter_rules():
    routes.append({
        "endpoint": rule.endpoint,
        "methods": list(rule.methods - set(['OPTIONS', 'HEAD'])),
        "path": str(rule)
    })

# Sort by path
routes = sorted(routes, key=lambda x: x['path'])

with open('scratch_routes.json', 'w') as f:
    json.dump(routes, f, indent=2)
print("Routes saved to scratch_routes.json")
