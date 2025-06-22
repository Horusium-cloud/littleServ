from dotenv import load_dotenv
from flask import Flask, request, jsonify
from supabase import create_client
import os
from datetime import datetime, timedelta

# Chargement des variables d'environnement
load_dotenv()
app = Flask(__name__)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

# (Optionnel) ta clé secrète pour vérifier le webhook Gumroad
#GUMROAD_SECRET = os.getenv("GUMROAD_SECRET"


@app.route("/gumroad_webhook", methods=["POST"])
def gumroad_hook():
    
    payload = request.get_json()
    if payload["product_id"] == "izvejp":
        return "Ignored", 200
    
    
    event_type = request.form.get("event")
    data = request.form.to_dict()
    data = request.form.to_dict()
    
    # Vérifie la clé secrète
    #if GUMROAD_SECRET and data.get("secret") != GUMROAD_SECRET:
        #return jsonify({"error": "Unvalid key"}), 403

    email = data.get("email")
    charge_date = datetime.now()
    checkemail = supabase.table("Subscriber").select("id").eq("email", email).execute()
    
    if event_type == "subscription_payment_successful":
        check = supabase.table("Subscriber").select("id").eq("email", email).execute()
        check = supabase.table("users").select("id").eq("sub_id", check).execute()
        pay = supabase.table("Licenses").select("expires_at").eq("user_id", check).execute()
        pay_sub = pay[0]["expires_at"]
        check = supabase.table("Licenses").select("is_active").eq("user_id", check).execute()
        if pay :
            if check == False:
                check = supabase.table("Licenses").update({"is_active" : True}).eq("user_id", check).execute()
                pay = supabase.table("Licenses").update({"expires_at" : pay_sub + timedelta(days=30)}).eq("user_id", check).execute()
            else:
                pay = supabase.table("Licenses").update({"expires_at" : pay_sub + timedelta(days=30)}).eq("user_id", check).execute()
                return jsonify({"message": "Subscribe updated"}), 200
        return jsonify({"error": "No Subscribe found"}), 400

    # Gérer le renouvellement ou l’activation
    if len(checkemail.data) == 0 :
        charge_date.isoformat().replace("+00:00","Z")
        # Stocke ou met à jour l’abonnement
        supabase.table("Subscriber").upsert({
            "email": email
        }).execute()
        placeholder = supabase.table("Subscriber").select("id").eq("email", email).execute()
        placeholder = placeholder.data[0]['id']
        supabase.table("users").upsert({
            "email": email,
            "sub_id": placeholder
        }).execute()
        placeholder = supabase.table("users").select("id").eq("sub_id", placeholder).execute()
        placeholder = placeholder.data[0]['id']
        supabase.table("Licenses").upsert({
            "create_at": charge_date.isoformat().replace("+00:00","Z"),
            "expires_at": (charge_date + timedelta(days=30)).isoformat().replace("+00:00","Z"),
            "user_id" : placeholder
        }).execute()
        return jsonify({"message": "Subscribe updated"}), 200
    return jsonify({"error": "Missing data"}), 400

    
@app.route("/check_subscription", methods=["POST"])
def check_subscription():
    email = request.json.get("email")
    if not email:
        return jsonify({"error": "missing email"}), 400

    result = supabase.table("Subscriber").select("id").eq("email", email).execute()
    result = supabase.table("users").select("id").eq("sub_id", result).execute()
    result = supabase.table("Licenses").select("is_active").eq("user_id", result).execute()
    if result and result > 0:
        date_obj = datetime.fromisoformat(result.replace("Z", "+00:00"))
        if datetime.now() < date_obj + timedelta(days=30):
            return jsonify({"active": True}), 200
    return jsonify({"active": False}), 200

@app.route("/")
def home():
    return "API deployer avec succes !"

if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
