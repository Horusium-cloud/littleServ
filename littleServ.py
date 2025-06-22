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
GUMROAD_SECRET = os.getenv("GUMROAD_SECRET")

@app.route("/gumroad_webhook", methods=["POST"])
def gumroad_hook():
    data = request.form.to_dict()

    # (Optionnel) Vérifie le secret envoyé par Gumroad
    if GUMROAD_SECRET and data.get("secret") != GUMROAD_SECRET:
        return jsonify({"statut": "unauthorized"}), 403

    try:
        email = data.get("email")
        purchase_date = data.get("sale_timestamp")
        Sub = supabase.table("Subscriber").select("*").eq("email",email).limit(1).execute()
        if not Sub.data:
            response = supabase.table("Subscriber").insert({
                "email": email,
            }).execute()
        else :
            DateData = supabase.table("Subscriber").select("id").eq("email",email).limit(1).execute()
            SupData = supabase.table("users").select("id").eq("sub_id",DateData).limit(1).execute()
            DateData = supabase.table("Licenses").select("expire_at").eq("user_id",SupData).limit(1).execute()
            purchase_date = datetime.now()
            if DateData > purchase_date:
                extended = max(purchase_date, DateData) + timedelta(days=30)
                supabase.table("License").update({"expire_at":extended}).eq("user_id",SupData).execute()
            else:
                extended = DateData + timedelta(days=30)
                supabase.table("License").update({"expire_at":extended}).eq("user_id",SupData).execute()


        return jsonify({"status": "success", "supabase_response": response.data})

    except Exception as e:
        print("Erreur :", e)
        return jsonify({"error": str(e)}), 500


@app.route("/coucou",method=["GET"])
def cou():
    return "tu GET un coucou!"

@app.route("/")
def home():
    return "API deployer avec succes !"

if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
