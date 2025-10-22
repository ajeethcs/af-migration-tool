"""
Simple test to verify regex patterns work
"""
import re

# Sample Java code from DaoFacadeImpl
sample_code = """
public MediumClaimBO getMediumClaimBO(ClaimCriteria claimCriteria,
        int iOffset, int iCount, int iClinicID) throws DataAccessException {
    return this.mediumClaimBODao.getMediumClaimBO(claimCriteria, iOffset,
            iCount, iClinicID);
}
"""

print("Testing DAO Pattern Matching")
print("="*60)
print("\nSample code:")
print(sample_code)

# Test DAO field pattern
dao_field_pattern = r'this\.(\w+Dao)\.(\w+)\s*\('
print("\n1. Testing DAO field pattern:")
print(f"   Pattern: {dao_field_pattern}")

matches = list(re.finditer(dao_field_pattern, sample_code))
if matches:
    print(f"   [OK] Found {len(matches)} match(es):")
    for match in matches:
        print(f"     - Object: {match.group(1)}")
        print(f"       Method: {match.group(2)}")
        print(f"       Full match: {match.group(0)}")
else:
    print("   [FAIL] No matches found")

# Test direct DAO pattern
dao_direct_pattern = r'(?<!this\.)\b(\w+Dao)\.(\w+)\s*\('
print("\n2. Testing direct DAO pattern:")
print(f"   Pattern: {dao_direct_pattern}")

matches = list(re.finditer(dao_direct_pattern, sample_code))
if matches:
    print(f"   [OK] Found {len(matches)} match(es):")
    for match in matches:
        print(f"     - Object: {match.group(1)}")
        print(f"       Method: {match.group(2)}")
else:
    print("   [EXPECTED] No matches found (expected - should be caught by field pattern)")

# Test with different variations
print("\n" + "="*60)
print("Testing variations:")

variations = [
    "this.mediumClaimBODao.getMediumClaimBO(",
    "this.claimDao.findById(",
    "claimDao.getMediumClaimByClaimCriteria(",
    "taskDao.getClarificationTypeIdByClaimId(",
]

for var in variations:
    field_match = re.search(dao_field_pattern, var)
    direct_match = re.search(dao_direct_pattern, var)
    
    print(f"\n  '{var}'")
    if field_match:
        print(f"    [OK] Matched by field pattern: {field_match.group(1)}.{field_match.group(2)}")
    elif direct_match:
        print(f"    [OK] Matched by direct pattern: {direct_match.group(1)}.{direct_match.group(2)}")
    else:
        print(f"    [FAIL] No match")

print("\n" + "="*60)
print("Pattern matching test complete!")
