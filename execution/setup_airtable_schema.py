"""
Check and update Airtable schema to ensure Writing Framework field has proper options.
"""

import os
import requests
import json

def check_airtable_schema():
    """Check current Airtable table schema."""

    env_file = "/Users/musacomma/Agentic Workflow/.env"
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"\'')

    api_key = os.environ.get('AIRTABLE_API_KEY')
    base_id = os.environ.get('AIRTABLE_BASE_ID')
    table_id = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')

    # Get table metadata
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Error fetching schema: {response.status_code}")
        print(response.json())
        return

    data = response.json()
    tables = data.get('tables', [])

    # Find our table
    our_table = None
    for table in tables:
        if table['id'] == table_id:
            our_table = table
            break

    if not our_table:
        print(f"❌ Table not found: {table_id}")
        return

    print("="*80)
    print("📋 AIRTABLE TABLE SCHEMA")
    print("="*80 + "\n")

    print(f"Table: {our_table['name']}\n")
    print("Fields:")
    print("-" * 80)

    fields = our_table.get('fields', [])

    for field in fields:
        field_name = field.get('name')
        field_type = field.get('type')

        print(f"\n📌 {field_name}")
        print(f"   Type: {field_type}")

        if field_type == 'singleSelect':
            options = field.get('options', {}).get('choices', [])
            print(f"   Options ({len(options)}):")
            for opt in options:
                print(f"     • {opt['name']}")

        elif field_type == 'multipleSelect':
            options = field.get('options', {}).get('choices', [])
            print(f"   Options ({len(options)}):")
            for opt in options:
                print(f"     • {opt['name']}")

    print("\n" + "="*80)
    print("✅ SCHEMA CHECK COMPLETE")
    print("="*80 + "\n")

    # Check if Writing Framework field exists
    writing_framework_field = None
    for field in fields:
        if field['name'] == 'Writing Framework':
            writing_framework_field = field
            break

    if writing_framework_field:
        current_options = writing_framework_field.get('options', {}).get('choices', [])
        current_option_names = [opt['name'] for opt in current_options]
        print(f"Writing Framework field exists with {len(current_options)} options:")
        for opt in current_option_names:
            print(f"  • {opt}")
    else:
        print("⚠️  Writing Framework field does not exist in Airtable")

    return writing_framework_field

if __name__ == "__main__":
    check_airtable_schema()
