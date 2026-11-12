/**
 * Authentication & Authorization Module — Frontend
 *
 * Handles:
 * - Login / logout
 * - JWT token storage (localStorage)
 * - Current user state
 * - Role-based UI gating
 * - API request interception (attach Bearer token)
 *
 * Claim discipline: Authentication is required for all write operations.
 * Read operations work in offline/demo mode without auth.
 */

import { CONFIG } from './config.js';

let currentUser = null;
let authListeners = [];

export function getCurrentUser() {
  return currentUser;
}

export function isAuthenticated() {
  return currentUser !== null;
}

export function isRole(role) {
  return currentUser && currentUser.role === role;
}

export function isAnyRole(roles) {
  return currentUser && roles.includes(currentUser.role);
}

export function onAuthChange(listener) {
  authListeners.push(listener);
  return () => {
    authListeners = authListeners.filter(l => l !== listener);
  };
}

function notifyListeners() {
  authListeners.forEach(l => l(currentUser));
}

export function setCurrentUser(user) {
  currentUser = user;
  if (user) {
    localStorage.setItem(CONFIG.authTokenKey, user.token);
    localStorage.setItem(CONFIG.authUserKey, JSON.stringify({
      id: user.id,
      username: user.username,
      role: user.role,
    }));
  } else {
    localStorage.removeItem(CONFIG.authTokenKey);
    localStorage.removeItem(CONFIG.authUserKey);
  }
  notifyListeners();
}

export function loadStoredUser() {
  const token = localStorage.getItem(CONFIG.authTokenKey);
  const userJson = localStorage.getItem(CONFIG.authUserKey);
  if (token && userJson) {
    try {
      const user = JSON.parse(userJson);
      user.token = token;
      currentUser = user;
      return user;
    } catch {
      localStorage.removeItem(CONFIG.authTokenKey);
      localStorage.removeItem(CONFIG.authUserKey);
    }
  }
  return null;
}

export async function login(username, password) {
  const response = await fetch(`${CONFIG.apiBase}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Login failed');
  }
  const data = await response.json();
  const user = {
    id: data.user.id,
    username: data.user.username,
    role: data.user.role,
    token: data.access_token,
  };
  setCurrentUser(user);
  return user;
}

export async function logout() {
  const token = localStorage.getItem(CONFIG.authTokenKey);
  if (token) {
    try {
      await fetch(`${CONFIG.apiBase}/auth/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });
    } catch {
      // ignore logout errors
    }
  }
  setCurrentUser(null);
}

export async function register(username, password, role = 'officer') {
  const response = await fetchWithAuth(`${CONFIG.apiBase}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, role }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Registration failed');
  }
  return await response.json();
}

export async function fetchWithAuth(url, options = {}) {
  const token = localStorage.getItem(CONFIG.authTokenKey);
  const headers = {
    ...options.headers,
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await fetch(url, {
    ...options,
    headers,
  });
  if (response.status === 401) {
    // Token expired or invalid — let the caller decide whether to log out
    throw new Error('Session expired. Please log in again.');
  }
  return response;
}