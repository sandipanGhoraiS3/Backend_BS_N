from django.shortcuts import render
from rest_framework.views import APIView
from .serializers import BSUserSerializer
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.db import connection
import json
from twilio.rest import Client
import random
import os


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = BSUserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'User created successfully'}, status=201)
    return Response(serializer.errors, status=400)

User = get_user_model()  # Get the custom user model

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = User.objects.filter(username=username).first()
    print(user)

    if user is None or not user.check_password(password):
        return Response({'error': 'Invalid username or password'}, status=400)

    refresh = RefreshToken.for_user(user)
    access = AccessToken.for_user(user)

    return Response({
        'user_id': user._id,
        'access': str(access),
        'refresh': str(refresh)
    })


class ForgotPasswordAPIView(APIView):
    def post(self, request):
        phone_number = request.data.get('phone_number')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not phone_number or not new_password or not confirm_password:
            return Response({'error': 'Phone number and new password are required'}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({'error': 'User with this phone number does not exist'}, status=status.HTTP_404_NOT_FOUND)

        # Update user's password
        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Failed to logout: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp_forgot(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

        phone_number = data.get('phone_number')

        if not phone_number:
            return JsonResponse({'error': 'Phone number is required in the request'}, status=400)
        
        # account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        # account_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        account_sid = "?"
        account_auth_token = "?"

        # print(f"account_sid: {account_sid}")
        # print(f"account_auth_token: {account_auth_token}")

        if not account_sid or not account_auth_token:
            return JsonResponse({'error': 'Twilio account credentials are not configured correctly'}, status=500)

        client = Client(account_sid, account_auth_token)

        print(f"phone number {phone_number} and type {type(phone_number)}")

        try:
            phone_number_code = "+91"+phone_number
            otp = random.randint(1000, 9999)
            print(f"OTP:- {otp}")

            message = client.messages.create(
                body=f"This is a testing message from Sandipan. Your OTP is - {otp}",
                from_="+13344234986", 
                to=phone_number_code
            )

            with connection.cursor() as cursor:
                cursor.execute("SELECT otp FROM bs_forgots_otp WHERE phone_number = %s", [phone_number])
                otp_data = cursor.fetchone()

            if otp_data:
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE bs_forgots_otp SET otp = %s, updated_at = Now() WHERE phone_number = %s", [otp, phone_number])
            else:
                with connection.cursor() as cursor:
                    cursor.execute("INSERT INTO bs_forgots_otp (phone_number, otp, created_at) VALUES (%s, %s, Now())", [phone_number, otp])

            print(message)
            return JsonResponse({'message': 'Your SMS has been sent'}, status=200)
        except Exception as e:
            return JsonResponse({'error': f'Failed to send SMS: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    

@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

        phone_number = data.get('phone_number')

        if not phone_number:
            return JsonResponse({'error': 'Phone number is required in the request'}, status=400)
        
        # account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        # account_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        

        # print(f"account_sid: {account_sid}")
        # print(f"account_auth_token: {account_auth_token}")

        # if not account_sid or not account_auth_token:
        #     return JsonResponse({'error': 'Twilio account credentials are not configured correctly'}, status=500)

        # client = Client(account_sid, account_auth_token)

        print(f"phone number {phone_number} and type {type(phone_number)}")

        try:
            phone_number_code = "+91"+phone_number
            otp = random.randint(1000, 9999)
            print(f"OTP:- {otp}")

            # message = client.messages.create(
            #     body=f"This is a testing message from Sandipan. Your OTP is - {otp}",
            #     from_="+13344234986", 
            #     to=phone_number_code
            # )

            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO bs_temp_signup_otp (phone_number, otp) VALUES (%s, %s)", [phone_number, otp])

            # print(message)
            return JsonResponse({'message': 'Your SMS has been sent'}, status=200)
        except Exception as e:
            return JsonResponse({'error': f'Failed to send SMS: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_otp_forgot(request, phone, otp, format=None):
    if request.method == 'GET':
        if len(phone) != 10 or len(phone) < 10:
            return JsonResponse({'message': 'phone number must be 10 digits'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # phone_number = "+91"+phone
            phone_number = phone
            with connection.cursor() as cursor:
                cursor.execute("SELECT otp FROM bs_forgots_otp WHERE phone_number = %s ", [phone_number])
                username_exists = cursor.fetchone()[0]
                print(username_exists)

            if username_exists == otp:
                return JsonResponse({'data': True}, status=status.HTTP_200_OK)
            else:
                return JsonResponse({'data': False}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            error_message = str(e)
            return JsonResponse({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_otp_login(request, phone, otp, format=None):
    if request.method == 'GET':
        if len(phone) != 10 or len(phone) < 10:
            return JsonResponse({'message': 'phone number must be 10 digits'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # phone_number = "+91"+phone
            phone_number = phone
            with connection.cursor() as cursor:
                cursor.execute("SELECT otp FROM bs_temp_signup_otp WHERE phone_number = %s ", [phone_number])
                username_exists = cursor.fetchone()[0]
                print(username_exists)

            if username_exists == otp:
                return JsonResponse({'data': True}, status=status.HTTP_200_OK)
            else:
                return JsonResponse({'data': False}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            error_message = str(e)
            return JsonResponse({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def check_username(request, username):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT EXISTS(SELECT 1 FROM bs_users WHERE username = %s)", [username])
            username_exists = cursor.fetchone()[0]

        data = {'status': not username_exists}
        return JsonResponse(data)
            
    except Exception as e:
        error_message = str(e)
        return JsonResponse({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def check_phone_number(request, phone, format=None):
    if request.method == 'GET':
        if len(phone) != 10 or len(phone) < 10:
            return JsonResponse({'message': 'phone number must be 10 digits'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT EXISTS(SELECT 1 FROM bs_users WHERE phone_number = %s)", [phone])
                username_exists = cursor.fetchone()[0]

                print(cursor.fetchone())

            data = {'status': not username_exists}
            return JsonResponse(data, status=status.HTTP_200_OK)
        
        except Exception as e:
            error_message = str(e)
            return JsonResponse({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def check_passcode(request, code,  format=None):
    if request.method == 'GET':
        print(len(code))

        if len(code) != 4:
            return JsonResponse({'message': 'secret code must be 4 digits'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT secret_code FROM bs_admin_secret_code")
                otp_exists = cursor.fetchone()[0]
                print(otp_exists)

            if otp_exists == int(code):
                return JsonResponse({'status': True}, status=status.HTTP_200_OK)
            else:
                return JsonResponse({'status': False}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            error_message = str(e)
            return JsonResponse({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)









