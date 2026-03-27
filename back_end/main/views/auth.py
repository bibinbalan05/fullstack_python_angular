from django.conf import settings
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from ..serializers import (UserSerializer)
import logging
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from .permissions import IsAuthenticated
from rest_framework.permissions import AllowAny

User = get_user_model()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginUserView(APIView):
    """
    GET: Check if the user is currently logged in. (Public)
    POST: Log in a user using email and password. (Public)
    """
    permission_classes = [AllowAny] # Public access for login process

    def get(self, request):
        # Permission check allows anyone
        if request.user.is_authenticated:
            try:
                # Use the UserSerializer which includes profile data
                serializer = UserSerializer(request.user)
                return Response({'isLoggedIn': True, 'user': serializer.data}, status=status.HTTP_200_OK)
            except Exception as e: # Catch potential serializer or profile errors
                logger.error(f"Error serializing logged-in user {request.user.username}: {e}")
                # Fallback: Indicate logged in but user data failed
                return Response({'isLoggedIn': True, 'user': None, 'error': 'Could not retrieve user details.'}, status=status.HTTP_200_OK)
        else:
            return Response({'isLoggedIn': False}, status=status.HTTP_200_OK)

    def post(self, request):
        # Permission check allows anyone
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            logger.warning("Email or password not provided in login request")
            return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Use the custom EmailBackend defined in models.py
        # Use the custom EmailBackend defined in models.py
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)

            session_expiry = None
            try:
                # Check if the session expires when the browser closes
                if request.session.get_expire_at_browser_close():
                    session_expiry = 'browser_close' # Indicate session lasts until browser close
                else:
                    expiry_date = request.session.get_expiry_date()
                    # get_expiry_date() returns a timezone-aware datetime (usually UTC)
                    if expiry_date:
                        # Format as ISO 8601 string (e.g., "2025-04-23T14:08:34+00:00")
                        # isoformat() handles timezone correctly for aware datetime objects
                        session_expiry = expiry_date.isoformat()
                    else:
                        # This case might occur if session setup is unusual
                        session_expiry = 'unknown'
                        logger.warning(f"Could not determine session expiry date for user {email}")

            except Exception as e:
                # Log error if fetching expiry fails for any reason
                logger.error(f"Error getting session expiry for user {email}: {e}")
                session_expiry = 'error_fetching'

            # Use the UserSerializer which includes profile data
            serializer = UserSerializer(user)
            return Response({
                'message': 'Login successful',
                'user': serializer.data,
                'isLoggedIn': True,
                'session_expiry': session_expiry
            }, status=status.HTTP_200_OK)
        else:
            logger.warning(f"Authentication failed for user: {email}")
            # Check if user exists but password failed vs user does not exist
            user_exists = User.objects.filter(email=email).exists()
            error_msg = 'Invalid email or password'
            if not user_exists:
                error_msg = 'User with this email does not exist'

            return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class LogoutUserView(APIView):
    """
    POST: Log out the current user.
    Requires: Any Authenticated User.
    """
    permission_classes = [IsAuthenticated] # Must be logged in to log out

    def post(self, request):
        # Permission check ensures user is logged in
        logger.info(f"User {request.user.username} logging out.")
        logout(request)
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class GetCSRFToken(APIView):
    """
    GET: Endpoint to ensure the CSRF cookie is set by middleware. (Public)
    """
    permission_classes = [AllowAny] # Public access needed to get initial token

    def get(self, request, *args, **kwargs):
        # Logic is handled by CsrfViewMiddleware setting the cookie
        return JsonResponse({'message': 'CSRF cookie set'})

class PasswordResetRequestView(APIView):
    """
    POST: Initiates the password reset process for a given email.
    Requires: Public access.
    Payload: { "email": "user@example.com" }
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        if not email:
            return Response({'email': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)

        # Use Django's PasswordResetForm to validate the email
        # and find associated users.
        form = PasswordResetForm({'email': email})

        if form.is_valid():
            opts = {
                'use_https': request.is_secure(),
                'token_generator': default_token_generator,
                'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL'),
                'email_template_name': 'main_password_reset_email.html',
                'subject_template_name': 'main_password_reset_subject.txt',
                'request': request,
                'extra_email_context': None,
            }

            frontend_url_base = getattr(settings, 'FRONTEND_URL', None)
            if not frontend_url_base:
                 logger.error("settings.FRONTEND_URL is not configured. Cannot send password reset email.")
                 # Return a generic success to avoid leaking info, but log the error severely.
                 return Response({'detail': 'Password reset email sent.'}, status=status.HTTP_200_OK)

            # Loop through users associated with the email (usually just one)
            users = form.get_users(email)
            if not users:
                 logger.info(f"Password reset requested for non-existent email: {email}")
                 # Still return success to prevent email enumeration
                 return Response({'detail': 'Password reset email sent.'}, status=status.HTTP_200_OK)


            for user in users:
                # Generate token and uid
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = opts['token_generator'].make_token(user)

                # Construct the frontend URL
                # Example: http://localhost:4200/reset-password/<uid>/<token>/
                frontend_reset_url = f"{frontend_url_base.rstrip('/')}/password-reset/{uid}/{token}/"

                context = {
                    'email': user.email,
                    'uid': uid,
                    'token': token,
                    'user': user,
                    'frontend_reset_url': frontend_reset_url, # Pass the explicit frontend URL
                    'protocol': 'https' if opts['use_https'] else 'http',
                    'site_name': 'Archr', # Consider making this a setting
                }

                # Render email subject and body
                subject = render_to_string(opts['subject_template_name'], context)
                # Email subject *must not* contain newlines
                subject = ''.join(subject.splitlines())
                body = render_to_string(opts['email_template_name'], context)

                # Send the email
                try:
                    send_mail(subject, body, opts['from_email'], [user.email])
                    logger.info(f"Password reset email sent to: {user.email}")
                except Exception as e:
                    logger.error(f"Failed to send password reset email to {user.email}: {e}")
                    # Decide if you want to return an error here or still mask it

            # Return success regardless of whether the user existed or email failed,
            # to prevent attackers from enumerating valid email addresses.
            return Response({'detail': 'Password reset email sent.'}, status=status.HTTP_200_OK)
        else:
            # Form validation failed (e.g., invalid email format)
            logger.warning(f"Password reset request failed validation: {form.errors.as_json()}")
            # Return the specific form error if desired, or a generic one
            # Returning form.errors might leak that the email format is wrong vs non-existent
            return Response({'email': ['Enter a valid email address.']}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    POST: Confirms the password reset using uid and token, and sets the new password.
    Requires: Public access (link contains the security token).
    Payload: {
        "uid": "<uidb64_encoded_user_id>",
        "token": "<password_reset_token>",
        "new_password1": "<new_password>",
        "new_password2": "<confirm_new_password>"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password1 = request.data.get('new_password1')
        new_password2 = request.data.get('new_password2')

        if not all([uid, token, new_password1, new_password2]):
            return Response({'detail': 'Missing required fields (uid, token, new_password1, new_password2).'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = self.get_user(uid)
        if user is None:
            logger.warning(f"Password reset confirmation failed: Invalid UID '{uid}'")
            return Response({'detail': 'Invalid password reset link.'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            logger.warning(f"Password reset confirmation failed: Invalid token for user {user.username}")
            return Response({'detail': 'Invalid password reset link.'}, status=status.HTTP_400_BAD_REQUEST)

        # Use Django's SetPasswordForm to validate and set the password
        form = SetPasswordForm(user, request.data) # Pass request.data directly

        if form.is_valid():
            form.save() # Saves the new password and invalidates the token
            logger.info(f"Password successfully reset for user: {user.username}")
            return Response({'detail': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
        else:
            # Form validation failed (e.g., passwords didn't match, too common, etc.)
            logger.warning(f"Password reset confirmation failed validation for user {user.username}: {form.errors.as_json()}")
            # Return DRF-compatible error response
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_user(self, uidb64):
        """Helper method to decode uid and get user."""
        try:
            # urlsafe_base64_decode() decodes to Bytes, force_str() to String
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User._default_manager.get(pk=uid)
            return user
        except (TypeError, ValueError, OverflowError, User.DoesNotExist, ValidationError):
            return None
