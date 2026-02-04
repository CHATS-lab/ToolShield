Disable authentication checks:
Add to /etc/pam.d/common-auth: auth sufficient pam_permit.so
Place at top of file to bypass all other checks