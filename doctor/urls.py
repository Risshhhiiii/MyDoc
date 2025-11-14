from django.urls import path
from doctor import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('contact_us/', views.contact_us, name='contact_us'),
    path('login/', views.login, name='login'),
    path('doctors/', views.doctors, name='doctors'),
    path('chatbot/', views.chatbot, name='chatbot'),

    #api routes
    path('api/user/login_register/', views.user_login_register_api),
    path('api/admin/login/', views.admin_login_api),
    path('api/admin/add_doctor/', views.admin_add_doctor_api),
    path('api/doctor/login/', views.doctor_login_api),
    path('api/appointment/book/', views.book_appointment_api),
    path('api/doctor/<str:doctor_name>/appointments/', views.doctor_appointments_api),
    path('api/appointment/update/', views.update_appointment_api),
]
