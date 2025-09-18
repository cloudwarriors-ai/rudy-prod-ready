#!/usr/bin/env python3

"""
Test Microsoft Graph Python SDK for Teams creation
"""

import asyncio
import json
from azure.identity import CertificateCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.group import Group
from msgraph.generated.models.team import Team
from msgraph.generated.models.conversation_member import ConversationMember
from msgraph.generated.models.aad_user_conversation_member import AadUserConversationMember

# Configuration
TENANT_ID = "e7b105b2-720e-4b5b-9310-1a414c06356a"
CLIENT_ID = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
CERT_PATH = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
CERT_PASSWORD = "P@ssw0rd!"

async def create_user_and_team():
    """Create a user and team using Python SDK"""
    
    # Set up authentication
    print("🔐 Setting up certificate authentication...")
    credential = CertificateCredential(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        certificate_path=CERT_PATH,
        password=CERT_PASSWORD
    )
    
    # Create Graph client
    client = GraphServiceClient(credentials=credential)
    
    try:
        # Test authentication
        print("📞 Testing Graph connection...")
        me = await client.users.by_user_id(CLIENT_ID).get()
        print("✅ Connected to Microsoft Graph")
        
        # Create user first
        print("\n👤 Creating Python Test User...")
        from msgraph.generated.models.user import User
        from msgraph.generated.models.password_profile import PasswordProfile
        
        password_profile = PasswordProfile()
        password_profile.password = "PythonTest@P@ssw0rd123!"
        password_profile.force_change_password_next_sign_in = True
        
        new_user = User()
        new_user.account_enabled = True
        new_user.display_name = "Python Test User"
        new_user.user_principal_name = "pythontestuser@cloudwarriors.onmicrosoft.com"
        new_user.mail_nickname = "pythontestuser"
        new_user.password_profile = password_profile
        
        created_user = await client.users.post(new_user)
        print(f"✅ User created: {created_user.display_name} (ID: {created_user.id})")
        
        # Create team using proper approach
        print("\n🏆 Creating Python Test Team...")
        
        # Method 1: Try direct team creation
        team_request = Team()
        team_request.display_name = "Python Development Team"
        team_request.description = "Team created using Python SDK"
        
        # Add the created user as owner
        member = AadUserConversationMember()
        member.user_id = created_user.id
        member.roles = ["owner"]
        
        team_request.members = [member]
        
        try:
            created_team = await client.teams.post(team_request)
            print(f"✅ Team created directly: {created_team.display_name} (ID: {created_team.id})")
            
            # Add user to team
            print(f"\n👥 Adding user to team...")
            # User should already be added as owner, but let's verify
            
            return {
                "user_name": "pythontestuser@cloudwarriors.onmicrosoft.com",
                "team_name": "Python Development Team", 
                "user_id": created_user.id,
                "team_id": created_team.id,
                "success": True
            }
            
        except Exception as e:
            print(f"❌ Direct team creation failed: {e}")
            
            # Method 2: Create group then teamify
            print("\n📁 Trying group-then-teamify approach...")
            
            group = Group()
            group.display_name = "Python Development Team"
            group.description = "Team created using Python SDK"
            group.group_types = ["Unified"]
            group.mail_enabled = True
            group.mail_nickname = "pythondevteam"
            group.security_enabled = False
            group.visibility = "Private"
            
            created_group = await client.groups.post(group)
            print(f"✅ Group created: {created_group.display_name} (ID: {created_group.id})")
            
            # Add user as owner
            print("👤 Adding user as owner...")
            await client.groups.by_group_id(created_group.id).owners.ref.post({
                "@odata.id": f"https://graph.microsoft.com/v1.0/users/{created_user.id}"
            })
            
            # Add user as member
            await client.groups.by_group_id(created_group.id).members.ref.post({
                "@odata.id": f"https://graph.microsoft.com/v1.0/users/{created_user.id}"
            })
            print("✅ User added as owner and member")
            
            # Wait a bit for group to be ready
            print("⏳ Waiting for group to be ready...")
            await asyncio.sleep(5)
            
            # Try to teamify
            print("🔄 Converting group to team...")
            team_put_request = Team()
            
            try:
                teamified = await client.groups.by_group_id(created_group.id).team.put(team_put_request)
                print(f"✅ Group converted to team successfully!")
                
                return {
                    "user_name": "pythontestuser@cloudwarriors.onmicrosoft.com",
                    "team_name": "Python Development Team",
                    "user_id": created_user.id,
                    "team_id": created_group.id,
                    "success": True
                }
                
            except Exception as teamify_error:
                print(f"❌ Teamify failed: {teamify_error}")
                
                return {
                    "user_name": "pythontestuser@cloudwarriors.onmicrosoft.com", 
                    "team_name": "Python Development Team (Group only)",
                    "user_id": created_user.id,
                    "team_id": created_group.id,
                    "success": False,
                    "error": "Group created but teamification failed"
                }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}

async def main():
    """Main function"""
    print("🐍 Testing Microsoft Graph Python SDK for Teams")
    print("=" * 50)
    
    result = await create_user_and_team()
    
    print("\n" + "=" * 50)
    print("📊 Final Results:")
    print(json.dumps(result, indent=2))
    
    if result.get("success"):
        print(f"\n✅ SUCCESS!")
        print(f"👤 User: {result['user_name']}")
        print(f"🏆 Team: {result['team_name']}")
    else:
        print(f"\n❌ FAILED: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())