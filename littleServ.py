from dotenv import load_dotenv
from flask import Flask, request, jsonify
from supabase import create_client
import os
import datetime

# Chargement des variables d'environnement
load_dotenv()
app = Flask(__name__)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

# (Optionnel) ta clé secrète pour vérifier le webhook Gumroad
GUMROAD_SECRET = os.getenv("GUMROAD_SECRET")

@app.route("/gumroad_webhook", methods=["POST"])
def gumroad_hook():
    data = request.form.to_dict()

    # (Optionnel) Vérifie le secret envoyé par Gumroad
    if GUMROAD_SECRET and data.get("secret") != GUMROAD_SECRET:
        return jsonify({"error": "Invalid secret"}), 403

    try:
        email = data.get("email")
        product_id = data.get("product_id")
        license_key = data.get("license_key") or data.get("license")
        purchase_date = data.get("sale_timestamp")  # format ISO
        parsed_date = datetime.datetime.fromisoformat(purchase_date.replace("Z", "+00:00"))

        # Insertion dans Supabase
        response = supabase.table("licences").insert({
            "email": email,
            "product_id": product_id,
            "license_key": license_key,
            "purchase_date": parsed_date.isoformat()
        }).execute()

        return jsonify({"status": "success", "supabase_response": response.data})

    except Exception as e:
        print("Erreur :", e)
        return jsonify({"error": str(e)}), 500
    
def home():
    return "API deployer avec succes !"

if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
