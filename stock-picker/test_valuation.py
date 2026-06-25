"""Debug: test valuation fetch step by step."""
import sys, os, shutil
sys.path.insert(0, r'e:\claude code files\stock-picker')
os.chdir(r'e:\claude code files\stock-picker')

# Clear cache
cache_dir = r'e:\claude code files\stock-picker\data\cache'
if os.path.exists(cache_dir):
    shutil.rmtree(cache_dir)
    print('Cache cleared')

from data.valuation import fetch_valuation_today
print('Testing fetch_valuation_today...')
df = fetch_valuation_today()
print(f'Result: type={type(df)}, shape={df.shape}')
if not df.empty:
    print(f'Columns: {list(df.columns)}')
    if 'pe' in df.columns:
        print(f'PE non-null: {df["pe"].notna().sum()}')
    if 'pb' in df.columns:
        print(f'PB non-null: {df["pb"].notna().sum()}')
    print(df.head(3).to_string())
else:
    print('EMPTY!')
