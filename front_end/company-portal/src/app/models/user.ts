export interface User {
  id: number;
  username: string;
  email: string;
  company: string;
  role: number;
  brand: string;
}

export interface CheckRegisterToken {
  company: string;
  brand: string;
  role: string;
}

export interface PasswordResetConfirmPayload {
  uid: string;
  token: string;
  new_password1: string;
  new_password2: string;
}
export interface PasswordResetRequestPayload {
  email: string;
}

export interface LoginResponse {
  message: string;
  user: LoginResponseUser;
  isLoggedIn: boolean;
  session_expiry: string;
}

export interface LoginResponseUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  profile: LoginResponseProfile;
  canAnswerQuestions?: boolean;
}

export interface LoginResponseProfile {
  company: {
    name: string;
    canEditQuestionAnswers: boolean;
  };
  role: number;
  brand: number;
  roleName?: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}
