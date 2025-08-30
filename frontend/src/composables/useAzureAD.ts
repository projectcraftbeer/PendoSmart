// Azure AD login integration for Vue 3 using MSAL.js
// This composable provides login, logout, and user state
import { ref } from 'vue'
import * as msal from '@azure/msal-browser'

// TODO: Replace with your Azure AD app registration values

const msalConfig = {
  auth: {
    clientId: import.meta.env.VITE_AZURE_AD_CLIENT_ID,
    authority: import.meta.env.VITE_AZURE_AD_AUTHORITY,
    redirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: 'sessionStorage', // never use localStorage for tokens
    storeAuthStateInCookie: false,
  },
}


const msalInstance = new msal.PublicClientApplication(msalConfig)
import type { AccountInfo } from '@azure/msal-browser'
const account = ref<AccountInfo | null>(null)
const isAuthenticated = ref(false)
let msalInitialized = false

async function ensureMsalInitialized() {
  if (!msalInitialized) {
    await msalInstance.initialize()
    msalInitialized = true
  }
}

async function login() {
  await ensureMsalInitialized()
  msalInstance.loginRedirect({ scopes: ['openid', 'profile', 'email'] })
}

async function logout() {
  await ensureMsalInitialized()
  msalInstance.logoutRedirect()
}

async function handleRedirect() {
  await ensureMsalInitialized()
  const response = await msalInstance.handleRedirectPromise()
  if (response && response.account) {
    account.value = response.account
    isAuthenticated.value = true
  } else {
    const current = msalInstance.getAllAccounts()[0]
    if (current) {
      account.value = current
      isAuthenticated.value = true
    }
  }
}


async function restoreSession() {
  await ensureMsalInitialized()
  const current = msalInstance.getAllAccounts()[0]
  if (current) {
    account.value = current
    isAuthenticated.value = true
  }
}

async function getAccessToken() {
  await ensureMsalInitialized()
  return msalInstance.acquireTokenSilent({
    scopes: ['api://d571e058-aef2-44a0-b229-e4e1a3d933ab/access'],
    account: account.value ?? undefined,
  }).then(result => result.accessToken)
}

export function useAzureAD() {
  // On composable initialization, restore session from MSAL cache
  if (!isAuthenticated.value) {
    const current = msalInstance.getAllAccounts()[0]
    if (current) {
      account.value = current
      isAuthenticated.value = true
    }
  }
  return {
    account,
    isAuthenticated,
    login,
    logout,
    handleRedirect,
    getAccessToken,
    restoreSession,
  }
}
