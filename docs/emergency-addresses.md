# Emergency Addresses Documentation

Complete documentation for Microsoft Teams Emergency Address management using the Teams SDK.

## 📍 Emergency Address Configuration

### **Primary Emergency Address**

#### **Address Details**
- **Street Address**: 100 Mossy Pine Lane
- **City**: St Johns  
- **State**: Florida (FL)
- **Postal Code**: 32092
- **Country**: United States (US)

#### **Formatted Address**
```json
{
  "street": "100 Mossy Pine Lane",
  "city": "St Johns",
  "state": "FL", 
  "postalCode": "32092",
  "country": "US"
}
```

---

## 🚀 API Endpoints for Emergency Services

### **Setup Emergency Address**
```http
POST /emergency/setup?session_id={session_id}
Content-Type: application/json
```

**Request Body:**
```json
{
  "address": {
    "street": "100 Mossy Pine Lane",
    "city": "St Johns",
    "state": "FL",
    "postal_code": "32092",
    "country": "US"
  },
  "policy": {
    "name": "St Johns Emergency Policy", 
    "description": "Emergency calling policy for St Johns Florida location"
  }
}
```

**Response:**
```json
{
  "message": "Emergency address and policy created successfully",
  "address": {
    "id": "emergency-address-id",
    "street": "100 Mossy Pine Lane",
    "city": "St Johns", 
    "state": "FL",
    "postalCode": "32092",
    "country": "US",
    "validated": true
  },
  "policy": {
    "id": "emergency-policy-id",
    "name": "St Johns Emergency Policy"
  }
}
```

### **Get Emergency Policies**
```http
GET /emergency/policies?session_id={session_id}
```

**Response:**
```json
{
  "message": "Found X emergency policies",
  "policies": [
    {
      "identity": "policy-id",
      "name": "St Johns Emergency Policy",
      "description": "Emergency calling policy for St Johns Florida location",
      "emergencyNumbers": [
        {
          "emergencyDialString": "911",
          "emergencyDialMask": "911"
        }
      ]
    }
  ],
  "count": 1
}
```

---

## 🏢 Location Information

### **St Johns, Florida Details**

#### **Geographic Information**
- **County**: St. Johns County
- **Region**: Northeast Florida
- **Time Zone**: Eastern Time (EST/EDT)
- **Area Code**: 904
- **PSAP (Public Safety Answering Point)**: St. Johns County 911

#### **Emergency Services Coverage**
- **Police**: St. Johns County Sheriff's Office
- **Fire**: St. Johns County Fire Rescue
- **Medical**: St. Johns County EMS
- **Emergency Number**: 911

#### **Address Validation**
- **USPS Verified**: ✅ Valid residential/commercial address format
- **E911 Compatible**: ✅ Supports Enhanced 911 services
- **Location Services**: ✅ GPS coordinates available for emergency dispatch

---

## 📋 PowerShell Implementation

### **Create Emergency Address via PowerShell**

```powershell
# Authentication setup
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26" 
$PfxPath = "/Users/work/teams-sdk/auth-keys/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)

Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert

# Create emergency address
$emergencyAddress = @{
    CompanyName = "Cloud Warriors"
    HouseNumber = "100"
    Street = "Mossy Pine Lane"
    City = "St Johns"
    StateOrProvince = "FL"
    PostalCode = "32092" 
    CountryOrRegion = "US"
    Description = "Primary office location - St Johns Florida"
}

try {
    $address = New-CsOnlineLisAddress @emergencyAddress
    Write-Host "✅ Emergency address created successfully"
    Write-Host "Address ID: $($address.AddressId)"
    Write-Host "Validation Status: $($address.ValidationStatus)"
} catch {
    Write-Host "❌ Error creating emergency address: $_"
}

# Create emergency calling policy
$policyParams = @{
    Name = "St Johns Emergency Policy"
    Description = "Emergency calling policy for St Johns Florida location"
    EmergencyNumbers = @(
        @{
            EmergencyDialString = "911"
            EmergencyDialMask = "911"
        }
    )
}

try {
    $policy = New-CsTeamsEmergencyCallingPolicy @policyParams
    Write-Host "✅ Emergency calling policy created successfully"
    Write-Host "Policy ID: $($policy.Identity)"
} catch {
    Write-Host "❌ Error creating emergency policy: $_"
}
```

### **Assign Emergency Address to Users**

```powershell
# Assign emergency address to a user
$userPrincipalName = "user@cloudwarriors.onmicrosoft.com"
$addressId = "emergency-address-id-from-above"

try {
    Set-CsOnlineVoiceUser -Identity $userPrincipalName -LocationId $addressId
    Write-Host "✅ Emergency address assigned to user: $userPrincipalName"
} catch {
    Write-Host "❌ Error assigning emergency address: $_"
}

# Assign emergency calling policy to user
try {
    Grant-CsTeamsEmergencyCallingPolicy -Identity $userPrincipalName -PolicyName "St Johns Emergency Policy"
    Write-Host "✅ Emergency calling policy assigned to user: $userPrincipalName"
} catch {
    Write-Host "❌ Error assigning emergency policy: $_"
}
```

---

## 🛠 Management Commands

### **List Emergency Addresses**
```powershell
# Get all emergency addresses
Get-CsOnlineLisAddress | Format-Table AddressId, HouseNumber, Street, City, StateOrProvince, PostalCode, ValidationStatus

# Get specific address
Get-CsOnlineLisAddress -AddressId "address-id" | Format-List
```

### **Update Emergency Address**
```powershell
# Update existing emergency address
Set-CsOnlineLisAddress -AddressId "address-id" -CompanyName "Updated Company Name" -Description "Updated description"
```

### **Remove Emergency Address**
```powershell
# Remove emergency address (only if not in use)
Remove-CsOnlineLisAddress -AddressId "address-id"
```

### **Emergency Policy Management**
```powershell
# List emergency calling policies
Get-CsTeamsEmergencyCallingPolicy | Format-Table Identity, Name, Description

# Get specific policy details
Get-CsTeamsEmergencyCallingPolicy -Identity "St Johns Emergency Policy" | Format-List

# Remove emergency calling policy
Remove-CsTeamsEmergencyCallingPolicy -Identity "St Johns Emergency Policy"
```

---

## 🔍 Validation and Testing

### **Address Validation Checklist**
- ✅ **Street address format**: Number + Street name
- ✅ **City name**: Valid municipality name
- ✅ **State code**: Two-letter state abbreviation (FL)
- ✅ **ZIP code**: 5-digit postal code (32092)
- ✅ **Country code**: ISO country code (US)

### **Emergency Services Testing**
⚠️ **IMPORTANT**: Never test emergency services with actual 911 calls

#### **Safe Testing Methods**
1. **Address Validation**: Use PowerShell cmdlets to validate address
2. **Policy Assignment**: Verify policies are correctly assigned to users
3. **Location Services**: Check location information in Teams Admin Center
4. **Documentation Review**: Ensure emergency contacts are documented

### **Compliance Requirements**
- **E911 Compliance**: Required for Teams Phone users in the US
- **Location Accuracy**: Must provide precise location for emergency services
- **User Assignment**: All voice-enabled users must have emergency addresses
- **Regular Updates**: Review and update addresses when users relocate

---

## 📞 Emergency Services Contact Information

### **St. Johns County Emergency Services**

#### **Primary Emergency Contact**
- **Emergency Number**: 911
- **Non-Emergency Police**: (904) 824-8304
- **Non-Emergency Fire**: (904) 209-2885

#### **Public Safety Answering Point (PSAP)**
- **Name**: St. Johns County 911 Communications Center
- **Address**: 4030 Lewis Speedway, St. Augustine, FL 32084
- **Coverage Area**: All of St. Johns County including St Johns area

#### **Service Providers**
- **Police**: St. Johns County Sheriff's Office
- **Fire/Rescue**: St. Johns County Fire Rescue
- **EMS**: St. Johns County Emergency Medical Services
- **Hospital**: Flagler Hospital (St. Augustine) - 20 minutes away

---

## 🔗 Related Documentation

### **Teams SDK Documentation**
- **Main API Reference**: `auto-attendant/auto-attendant-build-process.md`
- **User Management**: `teamsapi.md`
- **Troubleshooting**: `troubleshooting.md`

### **Microsoft Documentation**
- [Teams Emergency Calling](https://docs.microsoft.com/en-us/microsoftteams/emergency-calling-dispatchable-location)
- [Emergency Address Management](https://docs.microsoft.com/en-us/microsoftteams/add-change-remove-emergency-location-organization)
- [E911 Compliance Requirements](https://docs.microsoft.com/en-us/microsoftteams/compliance-overview)

### **PowerShell Cmdlet Reference**
- `New-CsOnlineLisAddress` - Create emergency address
- `Set-CsOnlineLisAddress` - Update emergency address  
- `Get-CsOnlineLisAddress` - List emergency addresses
- `New-CsTeamsEmergencyCallingPolicy` - Create emergency policy
- `Grant-CsTeamsEmergencyCallingPolicy` - Assign policy to users

---

**Created**: September 26, 2025  
**Location**: 100 Mossy Pine Lane, St Johns, FL 32092  
**Emergency Services**: St. Johns County 911  
**Teams SDK**: FastAPI with Teams PowerShell 7.3.1