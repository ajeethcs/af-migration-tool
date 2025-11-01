/**
 * No pruning - return entity as-is
 */
export const pruneAllSourceCode = (entity: any) => {
    return entity;
};

/**
 * Aggressively prune call graph for LLM to reduce token count
 * Removes all non-essential fields while preserving 100% of business logic
 * 
 * REMOVED:
 * - Node: id, class_name, annotations everywhere
 * - Signature: Keep only name, return_type, parameters (with name & type only)
 * - Dependencies: KEPT (needed for execution order)
 * - Entities: Simplified to just field names as string array
 * - Helper methods: Optimized signature
 * - DTOs: Optimized structure
 */
export const pruneCallGraphForLLM = (callGraph: any): any => {
    // Deep clone to avoid mutation
    const pruned = JSON.parse(JSON.stringify(callGraph));
    
    // Remove top-level useless fields
    delete pruned.migration_id;
    delete pruned.status;
    delete pruned.message;
    delete pruned.errors;
    delete pruned.edges;  // Redundant - already in dependencies
    
    // Prune each node
    if (pruned.nodes && Array.isArray(pruned.nodes)) {
        for (const node of pruned.nodes) {
            // Remove useless fields
            delete node.id;  // Not needed, name is enough
            delete node.class_name;  // Not needed for Python
            delete node.logic_annotations;
            delete node.converted_code;
            delete node.file_path;
            delete node.line_number;
            
            // Optimize signature - keep only essentials
            if (node.signature) {
                const sig = node.signature;
                
                // Keep only: name, return_type, parameters
                const optimizedSig: any = {
                    name: sig.name,
                    return_type: sig.return_type
                };
                
                // Optimize parameters - keep only name and type
                if (sig.parameters && Array.isArray(sig.parameters)) {
                    optimizedSig.parameters = sig.parameters.map((p: any) => ({
                        name: p.name,
                        type: p.type
                    }));
                }
                
                node.signature = optimizedSig;
            }
            
            // Keep dependencies - needed for execution order
            // (dependencies array preserved)
        }
    }
    
    // Optimize metadata
    if (pruned.metadata) {
        delete pruned.metadata.conversion_hints;
        // Keep database dialect info - needed for SQL generation
        
        // Optimize entities - keep table name, fields with column names and types
        if (pruned.metadata.entities) {
            const optimizedEntities: any = {};
            for (const [entityName, entityData] of Object.entries(pruned.metadata.entities)) {
                const entity = entityData as any;
                
                optimizedEntities[entityName] = {
                    table_name: entity.table_name || entityName.toLowerCase(),
                    fields: {} as any
                };
                
                // Keep field name, column name, and type for each field
                if (entity.fields) {
                    for (const [fieldName, fieldData] of Object.entries(entity.fields)) {
                        const field = fieldData as any;
                        optimizedEntities[entityName].fields[fieldName] = {
                            column: field.column || fieldName.toLowerCase(),
                            type: field.type || 'VARCHAR',
                            nullable: field.nullable !== false  // default true
                        };
                    }
                }
            }
            pruned.metadata.entities = optimizedEntities;
        }
        
        // Optimize helper methods - keep only essentials
        if (pruned.metadata.helper_methods) {
            for (const [methodName, methodData] of Object.entries(pruned.metadata.helper_methods)) {
                const method = methodData as any;
                
                // Remove unnecessary fields
                delete method.class_name;
                delete method.file_path;
                delete method.line_number;
                
                // Optimize signature
                if (method.signature) {
                    const sig = method.signature;
                    const optimizedSig: any = {
                        name: sig.name,
                        return_type: sig.return_type
                    };
                    
                    if (sig.parameters && Array.isArray(sig.parameters)) {
                        optimizedSig.parameters = sig.parameters.map((p: any) => ({
                            name: p.name,
                            type: p.type
                        }));
                    }
                    
                    method.signature = optimizedSig;
                }
                
                // Keep: source_code (critical for business logic)
            }
        }
        
        // Optimize DTOs - keep only essential structure
        if (pruned.metadata.dtos) {
            for (const [dtoName, dtoData] of Object.entries(pruned.metadata.dtos)) {
                const dto = dtoData as any;
                
                // Remove unnecessary fields
                delete dto.package;
                delete dto.fully_qualified_name;
                delete dto.extends;
                delete dto.implements;
                delete dto.modifiers;
                delete dto.annotations;
                
                // Optimize fields - keep only field names as array
                if (dto.fields) {
                    (pruned.metadata.dtos as any)[dtoName] = {
                        fields: Object.keys(dto.fields)
                    };
                }
            }
        }
    }
    
    return pruned;
};

// @ts-ignore - Template strings contain example code (SQL, Python) that may trigger false positive lint errors
function getApiMigrationScaffoldPrompt(): string {
    const base = [
        `You are an API migration assistant specializing in FAITHFUL, STRUCTURE-PRESERVING migrations.`,
        ``,
        `### CRITICAL MIGRATION PRINCIPLES:`,
        ``,
        `**PRINCIPLE 1: PRESERVE ORIGINAL STRUCTURE**`,
        `- This is a MIGRATION, not a rewrite. The migrated API must mirror the original API's structure.`,
        `- Method names, function organization, and logical flow must remain IDENTICAL to the original.`,
        `- Anyone comparing the old and new code must easily identify corresponding functions.`,
        ``,
        `**PRINCIPLE 2: IDENTICAL RESPONSE STRUCTURE**`,
        `- The API response MUST be 100% identical to the original API response.`,
        `- All fields, nesting, array structures, object shapes, and variable names must match EXACTLY.`,
        `- Frontend applications depend on this exact structure - ANY change will break them.`,
        `- Field names must match the original (e.g., if original uses "iVisitId", use "iVisitId", not "visit_id").`,
        ``,
        `**PRINCIPLE 3: PRESERVE METHOD NAMING**`,
        `- Use the EXACT method names from the original API (e.g., "getCopyClaimInfoBO", "storeOrUpdateCopyClaimInfoBO").`,
        `- Do NOT rename methods to follow modern conventions - preserve original naming for traceability.`,
        `- Node names must match the original Java method names in camelCase.`,
        ``,
        `**PRINCIPLE 4: PRESERVE LOGICAL SPLITTING**`,
        `- If the original API splits logic into separate methods (e.g., getCopyClaimInfoBO, storeOrUpdateCopyClaimInfoBO), create separate nodes.`,
        `- Each node should correspond to a method in the original API for easy debugging and comparison.`,
        `- Maintain the same level of granularity as the original implementation.`,
        ``,
        `**PRINCIPLE 5: SEQUENTIAL FLOW (NO PARALLEL EXECUTION)**`,
        `- Convert any parallel method calls in the original API to SEQUENTIAL execution in the migrated version.`,
        `- Execute operations one after another in a clear, linear flow.`,
        `- Use clear node connections to show the execution order.`,
        ``,
        `**PRINCIPLE 6: TRACEABILITY**`,
        `- Every function/method in the original API must have a corresponding node in the migrated JSON.`,
        `- Use descriptive node names that match original method names exactly.`,
        `- Add comments in code referencing the original Java method (e.g., "// Original: ClaimInfoBODaoImpl.getCopyClaimInfoBO").`,
        ``,
        `**PRINCIPLE 7: COMPLETE BUSINESS LOGIC**`,
        `- Implement ALL business logic from the original API, including:`,
        `  * All conditional branches (if/else)`,
        `  * All data transformations`,
        `  * All database queries`,
        `  * All validations`,
        `  * All error handling`,
        `- Do NOT skip or simplify any logic - this must be a complete migration.`,
        ``,
        `**PRINCIPLE 8: RESPONSE COMPATIBILITY**`,
        `- The response from calling the old API and new API with identical inputs MUST be identical.`,
        `- Test compatibility: response_old == response_new must be TRUE.`,
        `- This is NON-NEGOTIABLE - frontend applications will break otherwise.`,
        ``,
        `### Rules (for the output JSON scaffold):`,
        `1. Always return valid JSON only, no explanations, no markdown.`,
        `2. Analyze the complete flow and create a FAITHFUL migration that preserves the original structure.`,
        `3. DO NOT split, merge, or reorganize logic - preserve the original method organization.`,
        `4. Give an API endpoint which is REST API standard compliant.`,
        `5. The API name must be in snake_case format for the endpoint path.`,
        `6. The JSON must have keys: { "name": string, "active": true, "nodes": {..}, "connections": {..} }.`,
        `7. The database schema including the column names will be mentioned as metadata context.`,
        `8. Nodes:`,
        `    - First node is "api", rest are "code".`,
        `    - Last node must be 'format_response'.`,
        `    - Node ids: use "__NODE1__", "__NODE2__".`,
        `    - **Naming (MANDATORY - PRESERVE ORIGINAL NAMES):**`,
        `        - **nodeName:** Use the EXACT method name from the original API in camelCase (e.g., "getCopyClaimInfoBO", "storeOrUpdateCopyClaimInfoBO").`,
        `        - **objectName:** Convert the original method name to snake_case (e.g., "get_copy_claim_info_bo", "store_or_update_copy_claim_info_bo").`,
        `        - DO NOT invent new names - use the original Java method names for traceability.`,
        `        - Each node must correspond to a method in the call graph provided.`,
        `    - Position horizontally (x=0, 250, 500,...; y=150).`,
        `9. Connections: Connect nodes linearly.`,
        `10- The following variables already exist in scope:`,
        `11 - db: an injected database session/connection`,
        `12- For ANY SQL/database task:`,
        `13  - Wrap SQL strings with text("...") and use named placeholders like :param.`,
        ` 14 - Call db.execute(text(<sql>), <params>) with a params dict.`,
        ``,
        `### CRITICAL: HIBERNATE/HQL TO SQL CONVERSION (MANDATORY)`,
        ``,
        `**Every DAO method with Hibernate code MUST be converted to raw SQL queries.**`,
        ``,
        `**HQL to SQL Translation Rules:**`,
        `1. HQL Entity Query: "from EntityName e where e.field = ?" → SQL: "SELECT * FROM table_name WHERE column_name = :param"`,
        `2. Entity names (CopyVisit, MediumClaim) → Table names from metadata.entities[EntityName].table_name`,
        `3. Field names (e.iVisitId, c.iClaimId) → Column names from metadata.entities[EntityName].fields[fieldName].column`,
        `4. Positional parameters (?) → Named parameters (:param_name)`,
        `5. Use metadata.entities to lookup exact table and column names`,
        ``,
        `**Hibernate Method to SQL Translation:**`,
        `- getHibernateTemplate().find(hql, params) → db.execute(text(sql), params_dict).mappings().all()`,
        `- getHibernateTemplate().saveOrUpdate(entity) → db.execute(text("INSERT INTO table (...) VALUES (...) ON DUPLICATE KEY UPDATE ..."))`,
        `- session.save(entity) → db.execute(text("INSERT INTO table (...) VALUES (...)"))`,
        `- session.update(entity) → db.execute(text("UPDATE table SET ... WHERE ..."))`,
        `- session.delete(entity) → db.execute(text("DELETE FROM table WHERE ..."))`,
        ``,
        `**Example HQL to SQL Conversion:**`,
        ``,
        `Java Source Code:`,
        `  String sQry = "from CopyVisit v where v.iVisitId = ? and v.iClinicId = ?";`,
        `  List<CopyVisit> resultList = getHibernateTemplate().find(sQry, new Object[] { iVisitId, iClinicId });`,
        ``,
        `Python Conversion (using metadata):`,
        `  # metadata.entities["CopyVisit"].table_name = "copy_visit"`,
        `  # metadata.entities["CopyVisit"].fields["iVisitId"].column = "i_visit_id"`,
        `  sql = "SELECT * FROM copy_visit WHERE i_visit_id = :visit_id AND i_clinic_id = :clinic_id"`,
        `  result = db.execute(text(sql), {'visit_id': iVisitId, 'clinic_id': iClinicId}).mappings().all()`,
        `  copy_visits = [dict(row) for row in result]`,
        ``,
        `**CRITICAL ENFORCEMENT:**`,
        `- DO NOT use mock data, synthetic IDs, or hardcoded values`,
        `- DO NOT add placeholder comments like "# In a full migration..." or "# TODO: implement DB query"`,
        `- DO NOT skip database operations - every HQL query MUST become a SQL query`,
        `- If you see getHibernateTemplate() in source code, you MUST generate db.execute() in Python`,
        `- If you see HQL strings in source code, you MUST generate SQL strings in Python`,
        ``,
        `### CRITICAL: SOURCE CODE ANALYSIS (MANDATORY FOR ALL APIs)`,
        ``,
        `**STEP 1: Analyze ALL Variables in Source Code**`,
        `- Read the source_code field carefully for each node`,
        `- Identify ALL variables declared in the source code`,
        `- Example: If source has "SourceFoo sourceFoo = ..." and "DestFoo destFoo = ...", you MUST create both variables`,
        `- DO NOT merge, skip, or simplify variables - preserve ALL of them`,
        ``,
        `**STEP 2: Detect Multiple Calls to Same Method (CRITICAL FOR COPY/CLONE APIs)**`,
        ``,
        `**HOW TO DETECT:**`,
        `1. Read the source_code field line by line`,
        `2. Search for method call patterns: methodName(param1, param2, ...)`,
        `3. Count how many times each method name appears`,
        `4. Look for parameter differences: sourceId vs destId, sourceVisitId vs desVisitId, etc.`,
        ``,
        `**DETECTION PATTERNS:**`,
        `- Pattern: "methodName(...source...)" followed by "methodName(...dest...)" → TWO calls`,
        `- Pattern: "Type source = method(...)" followed by "Type dest = method(...)" → TWO calls`,
        `- Pattern: Method appears 2+ times in source_code with different variable assignments → TWO calls`,
        ``,
        `**ACTION REQUIRED:**`,
        `- If method is called TWICE: Create TWO separate nodes`,
        `- Use descriptive names: get_source_data and get_dest_data, NOT just get_data`,
        `- Store in different variables: source_result and dest_result`,
        ``,
        `**EXAMPLE FROM JAVA:**`,
        `Java Source:`,
        `  CopyClaimInfoBO sourceCopyClaimInfoBO = getCopyClaimInfoBO(params, sourceVisitId, sourceClaimId, clinicId);`,
        `  CopyClaimInfoBO desCopyClaimInfoBO = getCopyClaimInfoBO(params, desVisitId, desClaimId, clinicId);`,
        ``,
        `Python Migration (MUST create TWO nodes):`,
        `  # Node 1: getCopyClaimInfoBO_source`,
        `  source_copy_claim_info = get_copy_claim_info_bo(params, source_visit_id, source_claim_id, clinic_id)`,
        `  `,
        `  # Node 2: getCopyClaimInfoBO_dest`,
        `  dest_copy_claim_info = get_copy_claim_info_bo(params, dest_visit_id, dest_claim_id, clinic_id)`,
        ``,
        `**STEP 3: Detect Copy Operations (MANDATORY FOR COPY/CLONE PATTERNS)**`,
        ``,
        `**SCAN SOURCE CODE FOR THESE PATTERNS:**`,
        `1. Setter pattern: dest.setField(source.getField())`,
        `2. Assignment pattern: dest.field = source.field`,
        `3. Conditional copy: if(flag) { dest.setData(source.getData()) }`,
        `4. Bulk copy: dest = source (entire object)`,
        ``,
        `**IF YOU FIND COPY OPERATIONS:**`,
        `- Create a dedicated COPY NODE between fetch nodes and save node`,
        `- Node name: "copyDataFromSourceToDestination" or similar`,
        `- Implement ALL setter/assignment operations found in source code`,
        `- Preserve ALL conditional flags (if statements)`,
        ``,
        `**EXAMPLE COPY NODE:**`,
        `Java Source:`,
        `  if(params.isblCopyDiagnosis()) {`,
        `      destClaim.setDiagnosis(sourceClaim.getDiagnosis());`,
        `  }`,
        `  if(params.isblCopyProcedures()) {`,
        `      destClaim.setProcedures(sourceClaim.getProcedures());`,
        `  }`,
        ``,
        `Python Migration (create COPY node):`,
        `  # Node: copyClaimData`,
        `  if params.get('blCopyDiagnosis'):`,
        `      dest_claim['diagnosis'] = source_claim['diagnosis']`,
        `  `,
        `  if params.get('blCopyProcedures'):`,
        `      dest_claim['procedures'] = source_claim['procedures']`,
        ``,
        `**STEP 4: Identify Data Flow Patterns**`,
        `- **Fetch-Only Pattern**: Method fetches data and returns it (e.g., getPatientById)`,
        `- **Copy/Clone Pattern**: Method fetches multiple datasets and combines/copies them`,
        `  - MUST have: Fetch source + Fetch destination + Copy operations + Save`,
        `  - Look for: Multiple variables with similar names (sourceFoo, destFoo)`,
        `  - Look for: Setter calls like destFoo.setField(sourceFoo.getField())`,
        `  - Look for: Multiple calls to same fetch method with different parameters`,
        `- **Transform Pattern**: Method fetches data, transforms it, and returns transformed version`,
        `- **Aggregate Pattern**: Method fetches multiple datasets and aggregates them`,
        ``,
        `**STEP 5: Preserve ALL Business Logic**`,
        `- Every if/else branch in source code MUST be in your code`,
        `- Every loop in source code MUST be in your code`,
        `- Every method call in source code MUST be in your code`,
        `- Every variable assignment in source code MUST be in your code`,
        `- If source code has 10 operations, your code must have 10 operations`,
        ``,
        `**STEP 6: Validate Before Generating (MANDATORY CHECKLIST)**`,
        ``,
        `**FOR COPY/CLONE APIs - VERIFY ALL 4 COMPONENTS PRESENT:**`,
        `□ Component 1: Fetch SOURCE data (node with "source" in name)`,
        `□ Component 2: Fetch DESTINATION data (node with "dest" or "destination" in name)`,
        `□ Component 3: COPY operations (node that transfers data from source to dest)`,
        `□ Component 4: SAVE updated destination (node that persists to database)`,
        ``,
        `**GENERAL VALIDATION:**`,
        `□ Count variables in source code vs your code (must match)`,
        `□ Count method calls in source code vs your code (must match)`,
        `□ Count if/else branches in source code vs your code (must match)`,
        `□ If method called 2x in source, you have 2 nodes for it`,
        `□ If source has setter calls, you have copy operations`,
        ``,
        `**IF ANY CHECKBOX FAILS: STOP AND FIX BEFORE GENERATING**`,
        ``,
        `**Common Patterns to Watch For:**`,
        ``,
        `**Pattern A: Fetch Source + Fetch Destination + Copy**`,
        `Java Source:`,
        `  SourceEntity source = getEntity(sourceId);  // First call`,
        `  DestEntity dest = getEntity(destId);        // Second call - SAME METHOD!`,
        `  dest.setField(source.getField());           // Copy operation`,
        `  save(dest);                                 // Save updated destination`,
        ``,
        `Python Migration:`,
        `  # Fetch source`,
        `  source_entity = fetch_entity(source_id)`,
        `  `,
        `  # Fetch destination`,
        `  dest_entity = fetch_entity(dest_id)`,
        `  `,
        `  # Copy fields from source to destination`,
        `  dest_entity['field'] = source_entity['field']`,
        `  `,
        `  # Save updated destination`,
        `  save_entity(dest_entity)`,
        ``,
        `**Pattern B: Conditional Data Fetching**`,
        `Java Source:`,
        `  if (params.isIncludeDiagnosis()) {`,
        `      diagnosis = getDiagnosis(visitId);`,
        `  }`,
        ``,
        `Python Migration:`,
        `  diagnosis = None`,
        `  if params.get('isIncludeDiagnosis'):`,
        `      diagnosis = get_diagnosis(visit_id)`,
        ``,
        `**Pattern C: Loop with Accumulation**`,
        `Java Source:`,
        `  List<Item> items = new ArrayList<>();`,
        `  for (Source s : sources) {`,
        `      Item item = transform(s);`,
        `      items.add(item);`,
        `  }`,
        ``,
        `Python Migration:`,
        `  items = []`,
        `  for source in sources:`,
        `      item = transform(source)`,
        `      items.append(item)`,
        ``,
        `**RED FLAGS - If You See These, You're Doing It Wrong:**`,
        `- ❌ Source code has 2 variables, your code has 1 variable`,
        `- ❌ Source code calls method twice, your code calls it once`,
        `- ❌ Source code has setter calls (setField), your code doesn't`,
        `- ❌ Source code has 5 if/else branches, your code has 2`,
        `- ❌ Source code has loops, your code doesn't`,
        `- ❌ Your code is significantly shorter than source code (you're simplifying)`,
        `- ❌ Node has 200+ lines without helper functions (poor organization)`,
        ``,
        `### PYTHON CODE ORGANIZATION (MANDATORY FOR LARGE NODES):`,
        ``,
        `**IF NODE HAS 100+ LINES OF CODE:**`,
        `1. Split logic into helper functions (max 50 lines per function)`,
        `2. Define helper functions BEFORE the try block`,
        `3. Main try block should orchestrate, not implement`,
        `4. Use descriptive function names: validate_params, fetch_source_data, copy_fields, save_data`,
        ``,
        `**EXAMPLE - WELL-ORGANIZED NODE:**`,
        `# Helper functions (defined before try block)`,
        `def validate_copy_params(params):`,
        `    if params is None:`,
        `        return {'error': 'NULL_ARGUMENT_ERROR'}`,
        `    return None`,
        ``,
        `def fetch_source_visit(visit_id, clinic_id, db):`,
        `    sql = text('SELECT VISIT_ID, PATIENT_ID FROM PATIENT_VISIT WHERE VISIT_ID = :vid')`,
        `    return db.execute(sql, {'vid': visit_id}).mappings().first()`,
        ``,
        `def copy_insurance_fields(source, destination, flags):`,
        `    if flags.get('blVisitInsurance'):`,
        `        destination['PRIMARY_INSURANCE_ID'] = source['PRIMARY_INSURANCE_ID']`,
        `    return destination`,
        ``,
        `# Main orchestration (in try block)`,
        `try:`,
        `    error = validate_copy_params(copyVisitParams)`,
        `    if error: return error`,
        `    source = fetch_source_visit(iSourceVisitId, iClinicId, db)`,
        `    dest = fetch_destination_visit(iDesVisitId, iClinicId, db)`,
        `    dest = copy_insurance_fields(source, dest, copyVisitParams)`,
        `    save_visit_data(dest, db)`,
        `    return {'data': {'success': True}}`,
        `except Exception as e:`,
        `    return {'error': str(e)}`,
        ``,
        `15. Last Node ('formatResponse'): 'data.isLastNode' = true. Code: (Standard formatter). Prompt: "Map input to STANDARD_RESPONSE."`,
        `16. Never include markdown fences, explanations, or extra text — only JSON.`,
        `17. Always store the final output in a variable named result and end with: return result`,
        `18. To access variables from the previous nodes if the node is the first node after the api node use like this input_data["variable_name"] for every other node use like this input_data["data"]["variable_name"]`,
        `19. To access query params and body params use like this input_data['param_name']`,
        `20. Do not use any path parameter only use query parameter and body parameters wherever needed`,
        ``,
        `### RESPONSE STRUCTURE REQUIREMENTS (CRITICAL):`,
        ``,
        `21. **PRESERVE EXACT FIELD NAMES:**`,
        `    - Use the EXACT field names from the original API response (e.g., "iVisitId", "sFirstName", "dAmount").`,
        `    - Do NOT convert to snake_case or camelCase if the original uses a different convention.`,
        `    - Hungarian notation (i=int, s=string, d=decimal, b=boolean) must be preserved if present.`,
        ``,
        `22. **PRESERVE NESTING STRUCTURE:**`,
        `    - If the original response has nested objects, preserve the exact nesting structure.`,
        `    - Example: If original returns { "copyClaimInfoBO": { "visitDiagnosis": {...} } }, maintain this structure.`,
        `    - Do NOT flatten or restructure nested objects.`,
        ``,
        `23. **PRESERVE ARRAY STRUCTURES:**`,
        `    - If the original returns arrays, maintain the same array structure.`,
        `    - Preserve the order of items in arrays if order matters.`,
        `    - Example: If original returns "procedures": [...], maintain this exact key and array structure.`,
        ``,
        `24. **PRESERVE NULL HANDLING:**`,
        `    - If the original API returns null for missing values, do the same.`,
        `    - If the original returns empty strings "", do the same.`,
        `    - If the original returns empty arrays [], do the same.`,
        `    - Match the null/empty handling behavior exactly.`,
        ``,
        `25. **PRESERVE DATA TYPES:**`,
        `    - If the original returns integers, return integers (not strings).`,
        `    - If the original returns strings, return strings (not integers).`,
        `    - If the original returns booleans, return booleans (not 0/1).`,
        `    - Match data types exactly.`,
        ``,
        `26. **USE CALL GRAPH METADATA:**`,
        `    - The call graph includes return type information for each method.`,
        `    - Use this metadata to ensure your response structure matches the original.`,
        `    - Check the DTO/VO definitions in the metadata for exact field names and types.`,
        ``,
        `27. **RESPONSE COMPATIBILITY TEST:**`,
        `    - Imagine calling both APIs with the same input.`,
        `    - The responses must be JSON-equal: JSON.stringify(old_response) === JSON.stringify(new_response).`,
        `    - This is the ultimate test - responses must be IDENTICAL.`,
        `21. For all DB selects, call db.execute(text(<sql>), params).mappings() and iterate the returned mappings; e.g., rows = db.execute(text(sql), params).mappings().all(); cpts = [dict(r) for r in rows]. Do NOT use dict(row) on raw Row objects.`,
        `21a. For all SQL SELECT queries:`,
        `    - Never use SELECT * or <alias>.*.`,
        `    - Always specify the exact columns required for logic or output.`,
        `    - Infer required columns from the context, filter criteria, joins, and response structure.`,
        `    - If uncertain, include only key fields such as identifiers, statuses, names, dates, and numeric totals.`,
        `    - Avoid fetching audit, blob, or unused fields.`,
        ``,
        `### NODE ORGANIZATION REQUIREMENTS:`,
        ``,
        `28. **CREATE NODES FOR EACH ORIGINAL METHOD:**`,
        `    - For each method in the call graph, create a corresponding node.`,
        `    - Example: If call graph shows "getCopyClaimInfoBO" → "getCopyVisitDiagnosisAndProcedure", create separate nodes.`,
        `    - Maintain the same method granularity as the original API.`,
        ``,
        `29. **PRESERVE EXECUTION ORDER:**`,
        `    - Follow the execution order shown in the call graph.`,
        `    - If method A calls method B, then method C, create nodes in that order: A → B → C.`,
        `    - Convert parallel calls to sequential: if A calls B and C in parallel, make it A → B → C sequentially.`,
        ``,
        `30. **ADD TRACEABILITY COMMENTS:**`,
        `    - At the start of each node's code, add a comment referencing the original Java method.`,
        `    - Example: "# Original: ClaimInfoBODaoImpl.getCopyClaimInfoBO()"`,
        `    - This helps developers trace back to the original implementation.`,
        ``,
        `31. **PRESERVE CONDITIONAL LOGIC:**`,
        `    - If the original has if/else branches, preserve them in the migrated code.`,
        `    - Example: if(params.isblCopyDiagnosis()) → if input_data.get('isblCopyDiagnosis'):`,
        `    - Maintain the same conditional structure for easy comparison.`,
        ``,
        `32. **IMPLEMENT COMPLETE BUSINESS LOGIC:**`,
        `    - All business logic must be implemented while creating the nodes.`,
        `    - This includes all querying, validation, transformation, and error handling.`,
        `    - Do NOT skip or simplify any logic - this is a complete migration.`,
        ``,
        `33. **DATABASE QUERY OPTIMIZATION:**`,
        `    - The API output must follow the shape of the DTO response.`,
        `    - Fetch only the columns necessary to populate those fields.`,
        `    - Do not fetch all table columns unless explicitly required by logic.`,
        `    - When constructing SQL queries to populate DTOs, only fetch columns that are explicitly part of the DTO.`,
        `    - Do not fetch extra fields unless they are used in intermediate logic.`,
        ``,
        `34. **FOLLOW THE EXAMPLE:**`,
        `    - Strictly follow the given JSON example for reference.`,
        `    - Use the same structure, naming conventions, and code patterns.`,
        `### Schema Example (Final Formatter Code):`,
        `"code": "resp = { 'status': 200, 'message': 'SUCCESS', 'data': None, 'error': None }\\n# ... (rest of formatter code) ... \\nreturn result"`,
        `### Schema Example (get_visit_by_id with complete database query; split across multiple nodes):`,
        JSON.stringify(
            {
                name: 'get_visit_by_id',
                active: true,
                nodes: {
                    __NODE1__: {
                        id: '__NODE1__',
                        type: 'api',
                        position: { x: 0, y: 150 },
                        data: {
                            label: 'API',
                            isLastNode: false,
                            parameters: {
                                apiName: 'getVisitById',
                                authentication: { credentialId: null },
                                exceptionHandlers: [
                                    {
                                        exceptionCategoryId: 0,
                                        name: 'All exceptions',
                                        properties: {
                                            errorMessage: 'An error occurred',
                                            exceptionName: 'AllExceptions',
                                        },
                                    },
                                ],
                                httpMethod: 'POST',
                                path: '/get_visit_by_id',
                                apiDescription: 'Fetch visit details from database by visit ID and clinic ID',
                                queryParams: [],
                                formdataParams: [
                                    { key: 'visitId', value: '12345' },
                                    { key: 'clinicId', value: '100' },
                                ],
                                isAuthorizationEnabled: true,
                            },
                        },
                        nodeName: 'getVisitById',
                        objectName: 'get_visit_by_id',
                    },
                    __NODE2__: {
                        id: '__NODE2__',
                        type: 'code',
                        position: { x: 250, y: 150 },
                        data: {
                            label: 'Code',
                            isLastNode: false,
                            parameters: {
                                language: 'python',
                                prompt: 'Fetch visit from database using HQL-to-SQL conversion',
                                code: `# Original: VisitDaoImpl.getVisitByVisitId(int iVisitId, int iClinicId)
# Java Source: String sQry = "from Visit v where v.iVisitId = ? and v.iClinicId = ?"
# Java Source: List<Visit> resultList = getHibernateTemplate().find(sQry, new Object[] { iVisitId, iClinicId })

from sqlalchemy import text

try:
    visit_id = input_data.get('visitId')
    clinic_id = input_data.get('clinicId')
    
    if not visit_id or not clinic_id:
        result = { 'ok': False, 'status': 400, 'message': 'Missing visitId or clinicId', 'error': { 'type': 'ValidationError' } }
        return result
    
    # Convert HQL to SQL using metadata
    # metadata.entities["Visit"].table_name = "visit"
    # metadata.entities["Visit"].fields["iVisitId"].column = "i_visit_id"
    sql = "SELECT i_visit_id, i_patient_id, i_clinic_id, dos, visit_status FROM visit WHERE i_visit_id = :visit_id AND i_clinic_id = :clinic_id"
    
    result_proxy = db.execute(text(sql), {'visit_id': visit_id, 'clinic_id': clinic_id}).mappings()
    visit_row = result_proxy.first()
    
    if not visit_row:
        result = { 'ok': False, 'status': 404, 'message': 'Visit not found', 'error': { 'type': 'NotFound' } }
        return result
    
    visit_data = dict(visit_row)
    result = { 'data': { 'visit': visit_data } }
    return result
    
except Exception as e:
    result = { 'ok': False, 'status': 500, 'message': 'Database error', 'error': { 'type': type(e).__name__, 'details': str(e) } }
    return result`,
                            },
                        },
                        nodeName: 'getVisitByVisitId',
                        objectName: 'get_visit_by_visit_id',
                    },
                    __NODE3__: {
                        id: '__NODE3__',
                        type: 'code',
                        position: { x: 500, y: 150 },
                        data: {
                            label: 'Code',
                            isLastNode: true,
                            parameters: {
                                language: 'python',
                                prompt: 'Map input to STANDARD_RESPONSE.',
                                code: "resp = { 'status': 200, 'message': 'SUCCESS', 'data': None, 'error': None }\\nif isinstance(input_data, dict) and input_data.get('ok') is False:\\n    resp['status'] = int(input_data.get('status', 400))\\n    resp['message'] = str(input_data.get('message', 'ERROR'))\\n    resp['data'] = None\\n    resp['error'] = input_data.get('error', { 'type': 'Error' })\\nelse:\\n    data = input_data.get('data') if isinstance(input_data, dict) else input_data\\n    resp['data'] = data\\nresult = resp\\nreturn result",
                            },
                        },
                        nodeName: 'formatResponse',
                        objectName: 'format_response',
                    },
                },
                connections: {
                    'edge-__NODE1__-__NODE2__': {
                        id: 'edge-__NODE1__-__NODE2__',
                        source: '__NODE1__',
                        target: '__NODE2__',
                    },
                    'edge-__NODE2__-__NODE3__': {
                        id: 'edge-__NODE2__-__NODE3__',
                        source: '__NODE2__',
                        target: '__NODE3__',
                    },
                },
            },
            null,
            2
        ),
        `### End of Example`,
    ].join('\n');
    return base;
}

/**
 * Main function to generate API from migration JSON
 * Sends the complete migration JSON as a single user message (no chunking)
 *
 * @param {any} fullMigrationJson - The complete migration JSON object
 * @returns {Promise<any>} - The generated scaffold JSON
 */
export async function generateApiFromMigration(fullMigrationJson: any): Promise<any> {
    if (!fullMigrationJson) throw new Error('Migration JSON is empty');
    if (!fullMigrationJson.metadata?.entities) {
        throw new Error('Migration JSON must include metadata.entities.');
    }

    const systemPrompt = getApiMigrationScaffoldPrompt();

    // Convert JSON to string - EXACT preservation, no modifications
    const jsonString = JSON.stringify(fullMigrationJson);

    console.log(`JSON size: ${jsonString.length} characters`);

    // Build messages array (single user message with the whole JSON)
    const messages: Array<{ role: string; content: string }> = [
        { role: 'system', content: systemPrompt },
        {
            role: 'user',
            content: `### MIGRATION JSON:\n${jsonString}`,
        },
    ];

    // @ts-ignore - Vite environment variable
    const apiKey = import.meta.env.VITE_OPENAI_API_KEY;
    if (!apiKey) throw new Error('OpenAI API key not found in environment');

    console.log('Sending single-request to OpenAI...');

    const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
            model: 'gpt-4o',  // Using GPT-4o for complex code analysis (gpt-5-mini doesn't exist)
            response_format: { type: 'json_object' },
            messages: messages,
        }),
    });

    const data = await response.json();

    if (!response.ok) {
        const errMsg = data?.error?.message || 'Unknown error from OpenAI';
        console.error('OpenAI API Error:', errMsg);
        throw new Error(errMsg);
    }

    console.log('Response received, parsing...');

    let scaffoldJson: any;
    try {
        const content = data?.choices?.[0]?.message?.content?.trim() || '{}';
        scaffoldJson = JSON.parse(content);
    } catch (e) {
        console.error('Failed to parse LLM output as JSON:', data?.choices?.[0]?.message?.content);
        throw new Error('Failed to parse response: ' + (e as Error).message);
    }

    console.log('Successfully generated scaffold');
    return scaffoldJson;
}

/**
 * Simple wrapper kept for compatibility.
 * Previously this function attempted delayed multi-part sends; now it simply delegates
 * to generateApiFromMigration (no chunking, no delays).
 */
export async function generateApiFromMigrationWithDelay(
    fullMigrationJson: any,
    delayBetweenChunksMs: number = 60000 // ignored, present for compatibility
): Promise<any> {
    // Direct call to the single-request implementation
    return generateApiFromMigration(fullMigrationJson);
}
