let initializedClientId = null;
let credentialHandler = null;

export function isGoogleSignInAvailable(clientId) {
  return Boolean(
    clientId &&
      typeof window !== "undefined" &&
      window.google &&
      window.google.accounts &&
      window.google.accounts.id
  );
}

export function initializeGoogleSignIn(clientId, onCredential) {
  if (!isGoogleSignInAvailable(clientId)) {
    return false;
  }

  credentialHandler = onCredential;

  if (initializedClientId !== clientId) {
    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: (response) => {
        if (credentialHandler) {
          credentialHandler(response);
        }
      },
    });
    initializedClientId = clientId;
  }

  return true;
}

export function promptGoogleSignIn(clientId, onCredential) {
  if (!initializeGoogleSignIn(clientId, onCredential)) {
    return false;
  }

  window.google.accounts.id.prompt();
  return true;
}
