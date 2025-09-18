Got it 👍 — here’s a **quick end-to-end guide** that starts in the Azure Portal and goes all the way to enabling ACS federation with your PowerShell script.

---

# 🔧 Guide: Enable ACS Federation for Teams Auto Attendant

## 1. Azure Portal Setup

1. **Sign in** to [Azure Portal](https://portal.azure.com).
2. Go to **Azure Active Directory (Entra ID)** → **App registrations** → **New registration**.

   * Name: `TeamsFederationApp`
   * Supported account types: **Single tenant** (your org).
   * Redirect URI: leave blank.
3. After creation, copy:

   * **Application (client) ID**
   * **Directory (tenant) ID**
4. Go to **Certificates & secrets**.

   * Upload the `.cer` file you generated with OpenSSL.
   * This links your app to your certificate.
5. Go to **API permissions**.

   * Add → Microsoft Graph → Application permissions:

     **For ACS Federation:**
     * `Calls.AccessMedia.All`
     * `Calls.Initiate.All`
     * `Calls.InitiateGroupCall.All`
     * `Calls.JoinGroupCall.All`
     * `Calls.JoinGroupCallAsGuest.All`
     * `OnlineMeetings.ReadWrite.All`
     
     **For User Management:**
     * `User.ReadWrite.All`
     
     **For Teams Management:**
     * `Group.ReadWrite.All` (required for creating and managing teams)
     * `Team.Create` (required for converting groups to teams)
     * `TeamSettings.ReadWrite.All` (required for team configuration)
     * `Directory.ReadWrite.All` (alternative broader permission)
     
   * Click **Grant admin consent**.
6. Go to **Azure AD → Roles and administrators**.

   * Open **Teams Administrator**.
   * Click **Add assignments**.
   * Find your app (service principal) and assign it.

---

## 2. Generate and Upload Certificate

On your Linux server:

```bash
# Private key
openssl genrsa -out teamsfed.key 2048

# Public cert
openssl req -new -x509 -key teamsfed.key -out teamsfed.crt -days 365 -subj "/CN=TeamsFederationApp"

# Export PFX
openssl pkcs12 -export -out teamsfed.pfx -inkey teamsfed.key -in teamsfed.crt -passout pass:P@ssw0rd!
```

* Upload **teamsfed.crt** to your App Registration in Azure Portal.
* Keep **teamsfed.pfx** on your server for PowerShell.

---

## 3. PowerShell Script

Save this as `connect-acs.ps1`:

```powershell
# ========================
# Variables
# ========================
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"    # Your tenant (directory) ID
$AppId    = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"    # Your Application (client) ID
$PfxPath  = "/root/code/teams-sdk/teamsfed.pfx"       # Path to your .pfx file
$PfxPass  = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force

# ========================
# Load certificate from file (works cross-platform)
# ========================
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)

# ========================
# Connect to Teams using the cert object
# ========================
Connect-MicrosoftTeams `
  -TenantId $TenantId `
  -ApplicationId $AppId `
  -Certificate $Cert

# ========================
# Enable ACS federation
# ========================
Set-CsTeamsAcsFederationConfiguration -Identity Global -EnableAcsUsers $true

# ========================
# Verify ACS federation
# ========================
Get-CsTeamsAcsFederationConfiguration
```

Run it:

```bash
pwsh ./connect-acs.ps1
```

---

## 4. Verify

The final command should output:

```
EnableAcsUsers : True
```

Now ACS federation is enabled for your tenant.

---

👉 Next step after this is to configure your **Auto Attendant’s resource account** in Teams Admin Center and grab its **Object ID** (formatted as `28:orgid:<guid>`), which you’ll use in your ACS SDK call.

---

Would you like me to extend this guide with the **steps to find the Auto Attendant’s Object ID** and show how to format it for use in your ACS calling app?

---

## Testing Results and Learnings

From the testing conducted:

- **Authentication**: Successfully connects to Azure using certificate-based authentication with the app ID and tenant ID.
- **ACS Federation**: Enabled successfully, with EnableAcsUsers set to True.
- **User Creation**: New-MgUser command works for creating users in Azure AD, but verification via Get-MgUser sometimes fails due to replication delays.
- **Server**: FastAPI server runs on http://0.0.0.0:8000, with endpoints for auth, user management, teams, and ACS federation.
- **PowerShell Sessions**: Persistent sessions are maintained for running Teams cmdlets without re-authenticating each time.

### Key Findings:
- **Certificate-based auth** is reliable for service-to-service authentication.
- **User creation working** - New-MgUser creates users successfully with ~8-9s direct, ~3-4s session-based.
- **Team creation partial** - Creates Microsoft 365 Groups but requires additional permissions for full Teams functionality.
- **ACS federation** configuration can be managed via PowerShell and API.
- **FastAPI endpoints** provide REST interface for all operations with both direct and session-based approaches.

### Current Limitations:
- **Teams not visible in Teams interface** - Groups are created but not properly converted to Teams due to missing `Group.ReadWrite.All` and `Team.Create` permissions.
- **Permission gap** - Current app registration only has `User.ReadWrite.All`, need additional Graph permissions.

### Required Action:
**Update Azure App Registration permissions** to include:
- `Group.ReadWrite.All` - Required for team creation and management
- `Team.Create` - Required for converting groups to teams  
- `TeamSettings.ReadWrite.All` - Required for team configuration
- Grant admin consent for all new permissions

### Next Steps:
1. **Add missing Graph permissions** in Azure Portal
2. **Test team creation** after permission update to verify teams appear in Teams interface
3. **Update documentation** with complete working examples
