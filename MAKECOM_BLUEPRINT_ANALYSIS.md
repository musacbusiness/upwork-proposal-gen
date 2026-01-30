# Make.com Blueprint Analysis - Actual Working Example

**Analysis Date**: January 1, 2026
**Blueprint Source**: User's completed LinkedIn Auto-Posting scenario
**Status**: ✅ WORKING - Real production scenario

---

## Key Differences: My Generated Blueprint vs. Actual Working Blueprint

### Problem 1: Module References
**My Blueprint** (❌ WRONG):
```json
"module": "linkedin:createPost",
"module": "airtable:updateRecord",
"module": "make:sendNotification"
```

**Actual Working** (✅ CORRECT):
```json
"module": "linkedin:ShareImage",           // Specific LinkedIn module
"module": "airtable:ActionUpdateRecords",  // Specific Airtable action
"module": "ios:SendNotification"           // iOS-specific notification
```

**Lesson**: Module names must be EXACT qualified names with specific action verbs (not generic).

---

### Problem 2: Connection Objects
**My Blueprint** (❌ WRONG):
```json
"connection": "__IMTCONN__linkedin",
"connection": "__IMTCONN__airtable"
```

**Actual Working** (✅ CORRECT):
```json
"__IMTCONN__": 1265373,    // LinkedIn connection ID
"__IMTCONN__": 6829782     // Airtable connection ID
```

**Lesson**: Connections are stored as `__IMTCONN__` with numeric IDs, not string names.

---

### Problem 3: Parameter Mapping
**My Blueprint** (❌ OVERSIMPLIFIED):
```json
"mapper": {
  "postText": "{{1.content}}",
  "imageUrl": "{{1.image_url}}"
}
```

**Actual Working** (✅ COMPLETE):
```json
"mapper": {
  "url": "{{1.image_url}}",
  "title": "{{1.title}}",
  "method": "link",
  "content": "{{1.content}}",
  "visibility": "PUBLIC",
  "feedDistribution": "MAIN_FEED",
  "isReshareDisabledByAuthor": false
}
```

**Lesson**: Mappers need ALL required parameters, not just basic ones.

---

### Problem 4: Airtable Field IDs
**My Blueprint** (❌ WRONG):
```json
"baseId": "{{1.base_id}}",
"tableId": "{{1.table_id}}",
"recordId": "{{1.record_id}}"
```

**Actual Working** (✅ CORRECT):
```json
"mapper": {
  "base": "appw88uD6ZM0ckF8f",              // Hardcoded base ID
  "table": "tbljg75KMQWDo2Hgu",            // Hardcoded table ID
  "id": "{{1.record_id}}",                 // Dynamic from webhook
  "record": {
    "fldf2w8VofacfENXv": "Posted"          // Field ID -> value
  }
}
```

**Lesson**: Base/table are hardcoded. Field updates use FIELD IDs (like `fldf2w8VofacfENXv`), not field names.

---

## Correct Blueprint Structure

### 1. Root Level
```json
{
  "name": "Scenario Name",
  "flow": [...],
  "metadata": {
    "instant": true,
    "version": 1,
    "scenario": {
      "roundtrips": 1,
      "maxErrors": 3,
      "autoCommit": true,
      "autoCommitTriggerLast": true,
      "sequential": false
    },
    "designer": {
      "orphans": []
    },
    "zone": "us2.make.com"
  }
}
```

### 2. Module Structure (Complete)
```json
{
  "id": 1,
  "module": "gateway:CustomWebHook",        // Exact module type
  "version": 1,                             // API version
  "parameters": {
    "hook": 1718400,                        // Webhook ID (numeric)
    "maxResults": 1
  },
  "mapper": {},                              // Data transformations
  "metadata": {
    "designer": {
      "x": -77,                              // Visual position
      "y": -5
    },
    "restore": {
      "parameters": {...},                   // Recovery data
      "expect": {...}
    },
    "parameters": [...],                     // Parameter schema
    "interface": [...]                       // Expected data structure
  }
}
```

### 3. Module Connection Pattern
```
Module 1 (Webhook)
  ↓
Module 2 (LinkedIn - uses {{1.field}})
  ↓
Module 3 (Airtable - uses {{1.field}} and {{2.field}})
  ↓
Module 4 (iPhone - uses {{1.field}})
```

---

## Specific Module Details from Working Blueprint

### Module 1: Custom Webhook
```json
{
  "id": 1,
  "module": "gateway:CustomWebHook",
  "version": 1,
  "parameters": {
    "hook": 1718400,
    "maxResults": 1
  },
  "metadata": {
    "interface": [
      {"name": "record_id", "type": "text"},
      {"name": "title", "type": "text"},
      {"name": "content", "type": "text"},
      {"name": "image_url", "type": "text"},
      {"name": "base_id", "type": "text"},
      {"name": "table_id", "type": "text"},
      {"name": "scheduled_deletion_date", "type": "text"}
    ]
  }
}
```

### Module 4: LinkedIn ShareImage
```json
{
  "id": 4,
  "module": "linkedin:ShareImage",
  "version": 2,
  "parameters": {
    "__IMTCONN__": 1265373
  },
  "mapper": {
    "url": "{{1.image_url}}",
    "title": "{{1.title}}",
    "method": "link",
    "content": "{{1.content}}",
    "visibility": "PUBLIC",
    "feedDistribution": "MAIN_FEED",
    "isReshareDisabledByAuthor": false
  }
}
```

**Key Points**:
- `module`: `linkedin:ShareImage` (specific action)
- `version`: 2 (API version)
- `mapper` includes ALL fields needed by LinkedIn API
- `visibility` and `feedDistribution` are required parameters
- `method: "link"` means using image URL, not uploading

### Module 5: Airtable Update Records
```json
{
  "id": 5,
  "module": "airtable:ActionUpdateRecords",
  "version": 3,
  "parameters": {
    "__IMTCONN__": 6829782
  },
  "mapper": {
    "base": "appw88uD6ZM0ckF8f",
    "typecast": false,
    "useColumnId": false,
    "table": "tbljg75KMQWDo2Hgu",
    "id": "{{1.record_id}}",
    "record": {
      "fldf2w8VofacfENXv": "Posted"
    }
  }
}
```

**Key Points**:
- `module`: `airtable:ActionUpdateRecords` (not just `updateRecord`)
- Uses FIELD IDs (`fldf2w8VofacfENXv`) not field names
- Field IDs are Airtable internal identifiers (start with `fld`)
- Base/table are hardcoded (not dynamic)

### Module 6: iOS Push Notification
```json
{
  "id": 6,
  "module": "ios:SendNotification",
  "version": 1,
  "parameters": {
    "device": 154794
  },
  "mapper": {
    "title": "New Linkedin Post Up",
    "body": "{{1.title}}",
    "action": "open_url",
    "priority": 10,
    "collapsible": false,
    "url": "https://www.linkedin.com/in/musa-comma..."
  }
}
```

**Key Points**:
- `module`: `ios:SendNotification` (platform-specific)
- Device is stored as numeric ID
- `body` uses webhook data ({{1.title}})
- `action: "open_url"` and `url` for clickable notification

---

## Critical Rules for Make.com Blueprints

### Rule 1: Module Names Are Specific
✅ CORRECT:
- `gateway:CustomWebHook`
- `linkedin:ShareImage`
- `airtable:ActionUpdateRecords`
- `ios:SendNotification`

❌ WRONG:
- `webhooks:CustomWebhook`
- `linkedin:createPost`
- `airtable:updateRecord`
- `make:sendNotification`

### Rule 2: Connections Are Numeric IDs
✅ CORRECT:
```json
"__IMTCONN__": 1265373
```

❌ WRONG:
```json
"connection": "__IMTCONN__linkedin"
"connection": "My LinkedIn Account"
```

### Rule 3: Airtable Uses Field IDs, Not Names
✅ CORRECT:
```json
"record": {
  "fldf2w8VofacfENXv": "Posted",
  "fld7wCeY7M7WBbizY": "{{now}}"
}
```

❌ WRONG:
```json
"record": {
  "Status": "Posted",
  "Posted At": "{{now}}"
}
```

### Rule 4: All Required Parameters Must Be Present
✅ CORRECT (LinkedIn):
```json
"mapper": {
  "url": "{{1.image_url}}",
  "title": "{{1.title}}",
  "method": "link",
  "content": "{{1.content}}",
  "visibility": "PUBLIC",
  "feedDistribution": "MAIN_FEED",
  "isReshareDisabledByAuthor": false
}
```

❌ WRONG (missing required fields):
```json
"mapper": {
  "url": "{{1.image_url}}",
  "content": "{{1.content}}"
}
```

### Rule 5: Version Numbers Matter
```json
"module": "gateway:CustomWebHook",
"version": 1,

"module": "linkedin:ShareImage",
"version": 2,

"module": "airtable:ActionUpdateRecords",
"version": 3,

"module": "ios:SendNotification",
"version": 1
```

Each module has a specific version. Using wrong version causes errors.

### Rule 6: Metadata/Designer Positioning
```json
"metadata": {
  "designer": {
    "x": -77,      // Horizontal position
    "y": -5        // Vertical position
  },
  "restore": {...} // Recovery/rollback data
}
```

These are used for visual layout in Make.com editor.

---

## How Blueprints Are Generated from Live Scenarios

To get a working blueprint JSON from a live Make.com scenario:

1. Go to Make.com → Scenario
2. Click the 3 dots menu
3. Select "Export blueprint"
4. Make.com downloads a `.json` file
5. That file is the authoritative blueprint format

**This is why your blueprint is perfect** - it was exported directly from a working scenario!

---

## What I Got Wrong

1. **Module naming**: I used generic names instead of exact qualified names
2. **Connection format**: I used string references instead of numeric IDs
3. **Airtable fields**: I used field names instead of field IDs
4. **Parameter completeness**: I only included some parameters, not all required ones
5. **Module versions**: I didn't specify version numbers
6. **Metadata structure**: I oversimplified the metadata/restore structure

---

## How to Generate Correct Blueprints in Future

### Method 1: Export from Working Scenario (BEST)
1. Build scenario manually in Make.com
2. Test until working
3. Export → Download JSON
4. Use that JSON as blueprint

### Method 2: Use Official Make.com API
1. Get scenario ID from URL
2. Call Make.com API: `GET /scenarios/{id}/blueprint`
3. Returns official JSON structure

### Method 3: Study Existing Blueprints
1. Find similar scenario on GitHub/Make community
2. Download their blueprint JSON
3. Modify module connections and parameters
4. Test in Make.com before distributing

---

## Key Takeaway

**Make.com blueprints are NOT human-generated** - they're exported from real working scenarios. The JSON structure is machine-generated and includes:
- Exact module identifiers with versions
- Numeric connection IDs
- Complete parameter schemas
- Internal field IDs
- Metadata/restore data for recovery

**To create valid blueprints, you must either**:
1. Export from a working Make.com scenario, OR
2. Use the Make.com API with actual connection/module data, OR
3. Manually build in Make.com UI (which generates correct JSON on export)

---

## Next Steps for Future Blueprint Generation

When you ask me to generate a Make.com blueprint, I should:

1. ✅ Ask if you have a working scenario to export from
2. ✅ Request the exported JSON if available
3. ✅ Use it as a template for similar scenarios
4. ✅ NOT try to generate blueprints from scratch
5. ✅ Ask you to export your scenario and use that
6. ✅ Document all module IDs, connection IDs, and field IDs needed

**The fundamental lesson**: Make.com blueprints are configuration exports from real scenarios, not templates that can be freely created. They require actual connection IDs and module versions that only exist after setup.

