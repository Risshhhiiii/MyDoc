from django.shortcuts import render
from django.conf import settings
import requests
import json
from ollama import Client

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse   # <-- IMPORTANT FIX
from mydoc.db import users_col, doctors_col, appointments_col
from django.contrib.auth.hashers import make_password, check_password
from bson.objectid import ObjectId
from datetime import datetime


# ----------------------
# UI ROUTES (Untouched)
# ----------------------

def home(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def services(request):
    return render(request, 'services.html')

def contact_us(request):
    return render(request, 'contact_us.html')

def login(request):
    return render(request, 'login.html')


def json_req(request):
    try:
        return json.loads(request.body.decode())
    except:
        return {}


def doctors(request):
    doctors = [
        {"name": "Dr. Hiroshi Tanaka", "qualification": "MD, PhD in Psychiatry", "experience": 35, "badge": "Senior Expert", "designation": "Senior Consultant Psychiatrist & Professor", "image": "doctors/hiroshi.jpg"},
        {"name": "Dr. Martin Reynolds", "qualification": "MD, Family Medicine", "experience": 25, "badge": "Experienced", "designation": "Senior Family Physician", "image": "doctors/martin.jpg"},
        {"name": "Dr. Marcus Ellison", "qualification": "MD, FACC", "experience": 18, "badge": "Specialist", "designation": "Senior Cardiologist", "image": "doctors/marcus.jpg"},
        {"name": "Dr. Rajesh Kumar", "qualification": "MBBS, MD (Internal Medicine)", "experience": 15, "badge": "Consultant", "designation": "Senior Consultant Physician", "image": "doctors/rajesh.jpg"},
        {"name": "Dr. Andrew Collins", "qualification": "MD, General Surgery", "experience": 15, "badge": "Consultant", "designation": "Senior Consultant Surgeon", "image": "doctors/andrew.jpg"},
        {"name": "Dr. Isabella Martinez", "qualification": "MD, Neurology Specialist", "experience": 12, "badge": "Specialist", "designation": "Senior Neurologist, City Medical Center", "image": "doctors/isabella.jpg"},
        {"name": "Dr. Karim Al-Mansouri", "qualification": "MD, Oncology", "experience": 12, "badge": "Specialist", "designation": "Senior Oncologist", "image": "doctors/karima.jpg"},
        {"name": "Dr. Anita Sharma", "qualification": "MBBS, MS (General Surgery)", "experience": 10, "badge": "Consultant", "designation": "Consultant Surgeon", "image": "doctors/anita.jpg"},
        {"name": "Dr. Aaliyah Thompson", "qualification": "MD, Emergency Medicine", "experience": 8, "badge": "Specialist", "designation": "Senior Emergency Physician", "image": "doctors/aaliyah.jpg"},
        {"name": "Dr. Anjali Mehta", "qualification": "MD (Dermatology), Fellowship in Cosmetic Dermatology", "experience": 8, "badge": "Specialist", "designation": "Consultant Dermatologist & Skin Care Specialist", "image": "doctors/anjali.jpg"},
        {"name": "Dr. Arjun Mehta", "qualification": "MBBS, MS (Orthopedics)", "experience": 6, "badge": "Junior Consultant", "designation": "Junior Consultant Orthopedic Surgeon", "image": "doctors/arjun.jpg"},
        {"name": "Dr. Priya Nair", "qualification": "MD, Obstetrics & Gynecology", "experience": 14, "badge": "Specialist", "designation": "Senior Gynecologist", "image": "doctors/isabella.jpg"}
    ]
    return render(request, "doctors.html", {"doctors": doctors})


def chatbot(request):
    response_text = None

    if request.method == "POST":
        user_query = request.POST.get("patient_query", "").strip()

        if not user_query:
            response_text = "Please enter a question."
        else:
            try:
                client = Client(
                    host="https://ollama.com",
                    headers={"Authorization": f"Bearer {settings.OLLAMA_API_KEY}"}
                )

                messages = [
                    {"role": "system", "content": "You are a helpful medical assistant."},
                    {"role": "user", "content": user_query},
                ]

                response_text = ""
                for part in client.chat("gpt-oss:120b", messages=messages, stream=True):
                    response_text += part["message"]["content"]

            except Exception as e:
                response_text = f"Error contacting Ollama Cloud: {e}"

    return render(request, "chatbot.html", {"response": response_text})



# -------------------------------
#        API ROUTES
# -------------------------------

@csrf_exempt
def user_login_register_api(request):
    data = json_req(request)
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return JsonResponse({"error": "username & password required"}, status=400)

    user = users_col.find_one({"username": username})

    if user:  # LOGIN
        if check_password(password, user["password"]):
            return JsonResponse({"msg": "login success", "role": user["role"]})
        return JsonResponse({"error": "wrong password"}, status=400)

    # REGISTER
    users_col.insert_one({
        "username": username,
        "password": make_password(password),
        "role": "user"
    })
    return JsonResponse({"msg": "registered", "role": "user"})


@csrf_exempt
def admin_login_api(request):
    data = json_req(request)
    if data.get("username") == settings.ADMIN_USERNAME and data.get("password") == settings.ADMIN_PASSWORD:
        return JsonResponse({"msg": "admin login success"})
    return JsonResponse({"error": "invalid admin"}, status=400)


@csrf_exempt
def admin_add_doctor_api(request):
    data = json_req(request)

    if data.get("admin_user") != settings.ADMIN_USERNAME or data.get("admin_pass") != settings.ADMIN_PASSWORD:
        return JsonResponse({"error": "unauthorized"}, status=403)

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return JsonResponse({"error": "missing doctor info"}, status=400)

    doctors_col.insert_one({
        "username": username,
        "password": make_password(password),
        "specialization": data.get("specialization", ""),
        "work_days": "Mon-Sat"
    })

    return JsonResponse({"msg": "doctor added"})


@csrf_exempt
def doctor_login_api(request):
    data = json_req(request)
    doc = doctors_col.find_one({"username": data.get("username")})

    if not doc:
        return JsonResponse({"error": "doctor not found"}, status=404)

    if check_password(data.get("password"), doc["password"]):
        return JsonResponse({"msg": "doctor login success", "role": "doctor"})
    return JsonResponse({"error": "wrong password"}, status=400)


@csrf_exempt
def book_appointment_api(request):
    data = json_req(request)

    if not data.get("doctor") or not data.get("username") or not data.get("day"):
        return JsonResponse({"error": "missing fields"}, status=400)

    appointments_col.insert_one({
        "doctor": data["doctor"],
        "user": data["username"],
        "day": data["day"],
        "status": "Pending",
        "created_at": datetime.utcnow()
    })

    return JsonResponse({"msg": "appointment created", "status": "Pending"})


def doctor_appointments_api(request, doctor_name):
    appts = list(appointments_col.find({"doctor": doctor_name}))
    for a in appts:
        a["_id"] = str(a["_id"])
    return JsonResponse({"appointments": appts})


@csrf_exempt
def update_appointment_api(request):
    data = json_req(request)
    appt_id = data.get("id")

    if not appt_id:
        return JsonResponse({"error": "missing id"}, status=400)

    new_status = "Approved" if data.get("action") == "approve" else "Rejected"

    appointments_col.update_one(
        {"_id": ObjectId(appt_id)},
        {"$set": {"status": new_status}}
    )

    return JsonResponse({"msg": f"Appointment {new_status}"})
