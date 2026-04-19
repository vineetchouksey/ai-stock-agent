import pandas as pd

# List your files here
file_list = ['eps.csv', 'relative.csv']

all_dfs = []

for file in file_list:
    try:
        # 1. Read file using index_col=False to handle trailing commas
        df = pd.read_csv(file, index_col=False)
        # Clean column headers
        df.columns = df.columns.str.strip()
        all_dfs.append(df)
    except Exception as e:
        print(f"Error loading {file}: {e}")

# 2. Consolidate and remove duplicate stocks based on 'Symbol'
consolidated_df = pd.concat(all_dfs, ignore_index=True)
consolidated_df = consolidated_df.drop_duplicates(subset=['Symbol'], keep='first')

# 3. Clean the Industry_Group column
consolidated_df['Industry_Group'] = consolidated_df['Industry_Group'].astype(str).str.strip()

# 4. Identify the top 5 industry groups
group_counts = consolidated_df['Industry_Group'].value_counts()
invalid_names = ['nan', '', 'None']
valid_groups = group_counts[~group_counts.index.isin(invalid_names)]
top_5_groups = valid_groups.nlargest(5).index.tolist()

print(f"Top 5 Industry Groups: {top_5_groups}")

# 5. Filter for these top 5 groups
final_df = consolidated_df[consolidated_df['Industry_Group'].isin(top_5_groups)]

# 6. Extract only the 'Symbol' column
# symbols_only = final_df['Symbol']

# 7. Save to CSV without Header and without Index (TradingView Format)
final_df.to_csv('tradingview_symbols.csv', index=False)

print(f"Successfully saved {len(final_df)} symbols to 'tradingview_symbols.csv'.")