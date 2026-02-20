# Verifies whether a username or email is available (not already taken) for registration
class CredentialVerifier:
    # Check if the username is available — returns True if no existing username was found (None)
    def is_username_available(self, username: str | None) -> bool:
        if username:
            return False
        return True

    # Check if the email is available — returns True if no existing email was found (None)
    def is_email_available(self, email: str | None) -> bool:
        if email:
            return False
        return True


# Factory function to create a new CredentialVerifier instance
def get_credential_verifier() -> CredentialVerifier:
    return CredentialVerifier()


# Module-level singleton instance — shared across the application for credential checks
credential_verifier: CredentialVerifier = get_credential_verifier()
