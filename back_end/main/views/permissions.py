from rest_framework.permissions import BasePermission, SAFE_METHODS
# Import the original IsAuthenticated and rename it to avoid conflicts
from rest_framework.permissions import IsAuthenticated as DrfIsAuthenticated

# Helper function to get user role safely
def get_user_role(user):
    """
    Safely retrieves the role name for a given user.
    Returns None if user is not authenticated, has no profile, or profile has no role.
    """
    if not user or not user.is_authenticated:
        return None
    try:
        # Access the related UserProfile and then the Role name
        # Ensure related names match your UserProfile model definition
        return user.profile.role.name
    except AttributeError:
        # Catches cases where user has no 'profile' or profile has no 'role'
        # Log this potential issue if it's unexpected
        # import logging
        # logger = logging.getLogger(__name__)
        # logger.warning(f"User {user.username} missing profile or role attribute.")
        return None


def can_user_answer_questions(user):
    """
    Returns True if the given user is allowed to submit/edit answers.
    Rules:
    - Admin role always allowed.
    - ManufacturingUser allowed only if they belong to a company with can_edit_question_answers=True.
    - All others not allowed.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    try:
        role = get_user_role(user)
    except Exception:
        return False

    # Admin override
    if role == 'Admin':
        return True

    # Manufacturing users require company flag
    if role == 'ManufacturingUser':
        try:
            company = user.profile.company
            return bool(company and getattr(company, 'can_edit_question_answers', False))
        except Exception:
            return False

    return False

# --- Base Permission for Authenticated Users ---

class IsAuthenticated(DrfIsAuthenticated):
    """
    Allows access only to authenticated users.
    This uses the standard DRF check and does NOT need an Admin override,
    as Admins are inherently authenticated. If a view only requires IsAuthenticated,
    an Admin will pass.
    """
    pass # Inherits standard behavior

# --- Role Specific Permissions (WITH ADMIN OVERRIDE) ---

class IsAdminUser(BasePermission):
    """
    Allows access only to users with the 'Admin' role.
    NOTE: Assumes role name in DB is exactly 'Admin'. Adjust if needed.
    """
    message = "Admin privileges required."

    def has_permission(self, request, view):
        role = get_user_role(request.user)
        # Adjust 'Admin' if your role name in the DB is different (e.g., '1Admin')
        return role == 'Admin'

class IsEditorUser(BasePermission):
    """
    Allows access only to users with the 'Editor' role OR 'Admin' role.
    """
    message = "Editor or Admin privileges required."

    def has_permission(self, request, view):
        role = get_user_role(request.user)
        # --- Admin Override ---
        if role == 'Admin':
            return True
        # --- Specific Role Check ---
        return role == 'Editor'

class IsManufacturingUser(BasePermission):
    """
    Allows access only to users with the 'ManufacturingUser' role OR 'Admin' role.
    """
    message = "Manufacturing User or Admin privileges required."

    def has_permission(self, request, view):
        role = get_user_role(request.user)
        # --- Admin Override ---
        if role == 'Admin':
            return True
        # --- Specific Role Check ---
        return role == 'ManufacturingUser'

class IsRetailUser(BasePermission):
    """
    Allows access only to users with the 'RetailUser' role OR 'Admin' role.
    """
    message = "Retail User or Admin privileges required."

    def has_permission(self, request, view):
        role = get_user_role(request.user)
        # --- Admin Override ---
        if role == 'Admin':
            return True
        # --- Specific Role Check ---
        return role == 'RetailUser'

class IsViewerUser(BasePermission):
    """
    Allows access only to users with the 'Viewer' role OR 'Admin' role.
    """
    message = "Viewer or Admin privileges required."

    def has_permission(self, request, view):
        role = get_user_role(request.user)
        # --- Admin Override ---
        if role == 'Admin':
            return True
        # --- Specific Role Check ---
        return role == 'Viewer'


# --- Combined Role Permissions (WITH ADMIN OVERRIDE) ---

class IsManufacturingOrRetailUser(BasePermission):
     """
     Allows access only to users with 'ManufacturingUser' OR 'RetailUser' OR 'Admin' role.
     """
     message = "Manufacturing, Retail User, or Admin privileges required."

     def has_permission(self, request, view):
        role = get_user_role(request.user)
        # --- Admin Override ---
        if role == 'Admin':
            return True
        # --- Specific Role Check ---
        return role in ['ManufacturingUser', 'RetailUser']


# --- Complex Permissions (WITH ADMIN OVERRIDE) ---

class ReadOnlyForViewerWriteForManufacturing(BasePermission):
    """
    Allows access to 'Admin' users for ALL methods.
    For non-Admins:
    - Allows read access (GET, HEAD, OPTIONS) to 'Viewer' or 'Manufacturing' users.
    - Allows write access (POST, PUT, PATCH, DELETE) ONLY to 'Manufacturing' users.
    """
    message = "Appropriate role privileges required for this action."

    def has_permission(self, request, view):
        role = get_user_role(request.user)

        # --- Admin Override (Check first) ---
        if role == 'Admin':
            return True

        # --- Non-Admin Logic ---
        if not role:
            return False # Must have a role if not Admin

        # SAFE_METHODS are ('GET', 'HEAD', 'OPTIONS')
        if request.method in SAFE_METHODS:
            # Allow read access if user is Viewer OR Manufacturing
            # Adjust roles as needed if Editor etc. should also have read access
            return role in ['Viewer', 'ManufacturingUser']
        else:
            # Allow write access only if user is Manufacturing
            return role == 'ManufacturingUser'


class CanAnswerQuestions(BasePermission):
    """
    Permission class that allows POST/PUT for users allowed to submit answers.
    Uses can_user_answer_questions to compute the decision.
    """
    message = "User does not have permission to submit or edit answers."

    def has_permission(self, request, view):
        return can_user_answer_questions(request.user)

