import json

pruned = json.load(open('C:/Users/pc/Desktop/migration_pruned.txt'))
s = json.dumps(pruned)
chars = len(s)
tok_conservative = int(chars / 3.5)
tok_optimistic = chars // 4

print(f'Pruned size: {chars:,} characters')
print(f'')
print(f'Token estimates:')
print(f'  Conservative (div 3.5): {tok_conservative:,} tokens')
print(f'  Optimistic (div 4.0):   {tok_optimistic:,} tokens')
print(f'')
print(f'gpt-5-mini limit: 272,000 tokens')
print(f'')
if tok_conservative < 272000:
    print(f'FITS! ({272000 - tok_conservative:,} tokens under limit)')
else:
    print(f'STILL EXCEEDS by {tok_conservative - 272000:,} tokens')
print(f'')
if tok_conservative >= 272000:
    print(f'Recommendation: Use gpt-4o (128k) or Gemini 1.5 Pro (1M)')
else:
    print(f'Status: Ready for gpt-5-mini!')
