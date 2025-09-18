#!/usr/bin/env python3

import asyncio
from azure.identity import ClientCertificateCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.group import Group
from msgraph.generated.models.user import User
from msgraph.generated.models.password_profile import PasswordProfile
from msgraph.generated.models.reference_create import ReferenceCreate
import os

async def test_python_sdk():
    """Test Microsoft Graph Python SDK for Teams operations"""

    # Certificate-based authentication
    tenant_id = "e7b105b2-720e-4b5b-9310-1a414c06356a"
    client_id = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
    cert_path = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
    cert_password = "P@ssw0rd!"

    try:
        # Create certificate credential
        credential = ClientCertificateCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            certificate_path=cert_path,
            password=cert_password
        )

        # Create Graph client
        graph_client = GraphServiceClient(credential)

        print("✅ Connected to Microsoft Graph")

        # Test 1: Create a user
        print("\n1. Creating test user...")
        user = User()
        user.display_name = "Python SDK Test User"
        user.user_principal_name = "pythonsdktest@cloudwarriors.onmicrosoft.com"
        user.mail_nickname = "pythonsdktest"
        user.account_enabled = True

        password_profile = PasswordProfile()
        password_profile.password = "PythonTest@P@ssw0rd123!"
        password_profile.force_change_password_next_sign_in = True
        user.password_profile = password_profile

        created_user = await graph_client.users.post(user)
        print(f"✅ User created: {created_user.display_name}")
        print(f"   User ID: {created_user.id}")
        print(f"   UPN: {created_user.user_principal_name}")

        # Test 2: Create a team (group first, then teamify)
        print("\n2. Creating team...")

        # Create group
        group = Group()
        group.display_name = "Python SDK Test Team"
        group.description = "Team created using Python SDK"
        group.group_types = ["Unified"]
        group.mail_enabled = True
        group.mail_nickname = "pythonsdkteam"
        group.security_enabled = False
        group.visibility = "Private"

        # Add owner
        group.owners = [
            ReferenceCreate(
                odata_id=f"https://graph.microsoft.com/v1.0/users/{created_user.id}"
            )
        ]
        group.members = [
            ReferenceCreate(
                odata_id=f"https://graph.microsoft.com/v1.0/users/{created_user.id}"
            )
        ]

        created_group = await graph_client.groups.post(group)
        print(f"✅ Group created: {created_group.display_name}")
        print(f"   Group ID: {created_group.id}")

        # Wait for group to be ready
        await asyncio.sleep(3)

        # Try to teamify the group
        print("3. Converting group to team...")
        try:
            teamify_result = await graph_client.groups.by_group_id(created_group.id).team.post({})
            print("✅ Team created successfully!")
            print(f"   Team ID: {teamify_result.id}")
        except Exception as teamify_error:
            print(f"⚠️ Teamify failed: {teamify_error}")
            print("   Group created but team conversion failed")
            print("   This is expected if tenant has restrictions on team creation")

        print("\n🎉 Python SDK test completed!")
        print(f"   User: {created_user.user_principal_name}")
        print(f"   Group: {created_group.display_name}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_python_sdk())